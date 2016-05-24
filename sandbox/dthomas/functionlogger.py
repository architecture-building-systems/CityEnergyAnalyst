"""
functionlogger.py

Declares the decorator log_args saves a copy (and type information) of all arguments of a function to a sqlite
database and also records the result. The sqlite database is kept in the temporary folder.

Also, use this to figure out what parameters were changed in the call!

Pandas Dataframe, Series and numpy arrays are handled specially.

This can be used to reverse-engineer thorny code bases! Also, as a starting point for unit tests...
"""

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
            session.add(invocation)
            session.commit()
            map(session.refresh, iter(session))
            session.expunge_all()
            session.close()
            self.invocations.append(invocation)
        except:
            import traceback
            traceback.print_exc()

    def log_exit(self, func, result):
        invocation = self.invocations.pop()
        session = Session()
        session.add(invocation)
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
