"""eval_radiation.py

using the data from the `functionlogger` on the `radiation` script, find out some stuff about the radiation script.
let us see how much we can document automatically...
"""
import numpy as np
import pandas as pd
import functionlogger as fl
import pickle
import os

def main():
    fl.connect_to(os.path.expandvars(r'%TEMP%\cea.radiation.log.sql'))

    session = fl.Session()

    # functions analyzed
    invocations = session.query(fl.Invocation).all()
    function_names = sorted({invocation.name for invocation in invocations})

    for function_name in function_names:
        print "#", function_name

        invocations = session.query(fl.Invocation).filter(fl.Invocation.name == function_name).all()
        print "- number of invocations:", len(invocations)
        durations = [(i.end - i.start).total_seconds() for i in invocations if i.end]
        print "- max duration:", max(durations), "s"
        print "- avg duration:", np.mean(durations), "s"
        print "- min duration:", min(durations), "s"
        print "- total duration:", sum(durations), "s"
        print

        print "### Input"
        for parameter in invocations[0].parameters:
            ptypes = sorted({str(p.ptype) for i in invocations for p in i.parameters if p.name == parameter.name})
            print "- **%s** `%s`: *%s*" % (parameter.name, ptypes, summary_unpickle(parameter.value))
        print

        for df_parameter in [p for p in invocations[0].parameters
                             if p.ptype == "<class 'pandas.core.frame.DataFrame'>"]:
            print "%s:" % df_parameter.name
            print pickle.loads(df_parameter.value).describe()
        print

        print "### Output"
        print "- `%s`: %s" % (sorted(str(i.rtype) for i in invocations), summary_unpickle(invocations[0].result))
        if invocations[0].rtype == "<class 'pandas.core.frame.DataFrame'>":
            print pickle.loads(df_parameter.value).describe()
        print


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


if __name__ == '__main__':
    main()

