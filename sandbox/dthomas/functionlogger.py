"""
functionlogger.py

Declares the decorator log_args saves a copy (and type information) of all arguments of a function to a sqlite
database and also records the result. The sqlite database is kept in the temporary folder.

Also, use this to figure out what parameters were changed in the call!

Pandas Dataframe, Series and numpy arrays are handled specially.

This can be used to reverse-engineer thorny code bases! Also, as a starting point for unit tests...
"""
import numpy as np
import pandas as pd
import os
import functools
import inspect
import pickle
from collections import OrderedDict

import itertools

import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Binary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, ForeignKey

import cea.radiation

Base = declarative_base()
Session = sessionmaker()


def connect_to(path):
    engine = create_engine('sqlite:///' + path)
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)
    return engine


class Invocation(Base):
    __tablename__ = 'invocations'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    start = Column(DateTime)
    end = Column(DateTime)
    exception = Column(Boolean)
    rtype = Column(String)
    result = Column(Binary)
    calling_file = Column(String)
    calling_line = Column(Integer)
    calling_function = Column(String)

    def __repr__(self):
        return "<Invocation(id=%s, name='%s', start='%s', end='%s')>" % (
            self.id, self.name, self.start, self.end)


class Parameter(Base):
    __tablename__ = 'parameters'

    id = Column(Integer, primary_key=True)
    call_id = Column(Integer, ForeignKey('invocations.id'))
    name = Column(String, nullable=False)
    ptype = Column(String)
    value = Column(Binary)
    invocation = relationship('Invocation', back_populates='parameters')

    def __repr__(self):
        return "<Parameter(name='%s', ptype='%s')>" % (self.name, self.ptype)


Invocation.parameters = relationship('Parameter', order_by=Parameter.id, back_populates='invocation')


class _LogArgs(object):
    """Logging decorator for function calls"""

    def __init__(self):
        self.invocations = []

    def __call__(self, func):
        """Returns a decorator that wraps `func`. The wrapper will log each call to `func` with arguments passed
        and the results."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.log_entry(func, args, kwargs)
            try:
                result = func(*args, **kwargs)
                self.log_exit(func, result)
            except:
                import traceback
                traceback.print_exc()
                self.log_exit(func, None)  # FIXME: log with an exception!!!
            return result

        return wrapper

    def log_entry(self, func, args, kwargs):
        try:
            args_name = list(OrderedDict.fromkeys(inspect.getargspec(func)[0] + kwargs.keys()))
            args_dict = OrderedDict(list(itertools.izip(args_name, args)) + list(kwargs.iteritems()))

            session = Session()
            invocation = Invocation(name=func.__name__, start=datetime.datetime.now())
            invocation.parameters = [Parameter(name=name, value=self.to_pickle(value), ptype=str(type(value)))
                                     for name, value in args_dict.items()]

            # figure out who called us (top two on call stack are wrapper stuff)
            _, file_name, line_number, function_name, _, _ = inspect.stack()[2]
            invocation.calling_file = file_name
            invocation.calling_function = function_name
            invocation.calling_line = line_number

            session.add(invocation)
            session.commit()
            map(session.refresh, iter(session))
            session.expunge_all()
            session.close()
            self.invocations.append(invocation)
        except:
            import traceback
            traceback.print_exc()
            raise

    def log_exit(self, func, result):
        invocation = self.invocations.pop()
        session = Session()
        session.add(invocation)
        assert invocation.name == func.__name__, "something went wrong with call stack..."
        invocation.end = datetime.datetime.now()
        invocation.rtype = str(type(result))
        invocation.result = self.to_pickle(result)
        session.commit()
        session.close()

    def to_pickle(self, value):
        try:
            return pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        except:
            return repr(value)  # sorry, we tried...


log_args = _LogArgs()




def generate_output(path_to_log, writer):
    def write_line(line=None):
        if line:
            writer.write(line)
        writer.write('\n')


    connect_to(os.path.expandvars(path_to_log))

    session = Session()

    # functions analyzed
    invocations = session.query(fl.Invocation).all()
    function_names = sorted({invocation.name for invocation in invocations})

    # print table of contents
    write_line("# Table of contents")
    for function_name in function_names:
        write_line("- [%s](#%s)\n" % (function_name, anchor_name(function_name)))
    write_line()

    # figure out call structure...

    # print list of functions
    for function_name in function_names:
        write_line("# %s" % function_name)

        invocations = session.query(fl.Invocation).filter(fl.Invocation.name == function_name).all()
        write_line("- number of invocations: %i" % len(invocations))
        durations = [(i.end - i.start).total_seconds() for i in invocations if i.end]
        if durations:
            write_line("- max duration: %s s" % max(durations))
            write_line("- avg duration: %s s" % np.mean(durations))
            write_line("- min duration: %s s" % min(durations))
            write_line("- total duration: %s s" % sum(durations))
        write_line()

        write_line("### Input")
        for parameter in invocations[0].parameters:
            ptypes = sorted({str(p.ptype) for i in invocations for p in i.parameters if p.name == parameter.name})
            write_line("- **%s** `%s`: *%s*" % (parameter.name, ptypes, summary_unpickle(parameter.value)))
        write_line()

        for df_parameter in [p for p in invocations[0].parameters
                             if p.ptype == "<class 'pandas.core.frame.DataFrame'>"]:
            write_line("#### %s:" % df_parameter.name)
            write_line("```\n%s\n```" % pickle.loads(df_parameter.value).describe())
        write_line()
        write_line("### Output")
        write_line("- `%s`: %s" % (sorted({str(i.rtype) for i in invocations}),
                                   summary_unpickle(invocations[0].result)))
        if invocations[0].rtype == "<class 'pandas.core.frame.DataFrame'>":
            write_line("```\n%s\n```" % pickle.loads(invocations[0].result).describe())
        write_line()
        write_line("[TOC](#table-of-contents)")
        write_line("---")
        write_line()


def summary_unpickle(value):
    """Unpickle the value to a string for simple values and a summary for more complicated values (like Dataframe)"""
    try:
        obj = pickle.loads(value)
        if isinstance(obj, pd.DataFrame):
            return obj.shape
        else:
            return obj
    except:
        return '???'


def anchor_name(s):
    """
    return an anchor name for a heading (as in GitHub markdown)
    NOTE: only really works with function names...
    """
    s = s.replace('_', '-')
    s = s.lower()
    return s


def wrap_module(module):
    # wrap all the functions in radiation.py with the logger
    for member in dir(module):
        if inspect.isfunction(getattr(module, member)):
            setattr(module, member, log_args(getattr(module, member)))