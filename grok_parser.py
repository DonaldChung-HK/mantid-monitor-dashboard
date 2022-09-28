from pygrok import Grok
import pandas as pd
import numpy as np
from collections import OrderedDict
import html
from data_object import ctest_run, ctest_test, ctest_test_trial

import json
import pprint
import jsonpickle

# this is to disable pandas future warning for bool dtype deprecation see 1.5.0 notes
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def grok_parser(
    lines,
    run_name,
    grok_pattern = '[0-9\/]*Test[ ]*\#%{POSINT:test_num}\: (?<test_name>[^ ]*) [.]*[\* ]{3}%{WORD:outcome}[ ]*%{BASE10NUM:test_time} sec', #Default pattern for ctest unit test
    passed_string = "Passed",
    failed_string = "Failed",
    timeout_string = "Timeout",
    aggregate_data_key = ["Tested", "Passed", "Flake", "Failed","Timeout"],
    ):
    """Parse a list of logs line from a ctest run to organized data

    Args:
        lines (list(str)): log lines
        grok_pattern (str, optional): grok pattern for log result. Defaults to '[0-9\/]*Test[ ]*\#%{POSINT:test_num}\: (?<test_name>[^ ]*) [.]*[\* ]{3}%{WORD:outcome}[ ]*%{BASE10NUM:test_time} sec'.
        failed_string (str, optional): String to look for in log when test fail. Defaults to "Failed".
        timeout_string (str, optional): String to look for in log when test timeout. Defaults to "Timeout".
        aggregate_data_key (list, optional): dict keys for test aggregate data. Defaults to ["Tested", "Passed", "Flake","Fail", "Timeout"].

    Returns:
        tuple:
            overall_result(dict): dictionary of overall result with keys based on aggregate_data_key
            organized_stacktrace(dict(list(grok_parser.ctest_test(grok_parser.ctest_test_trial)))): stack traces from current build
    """
    test_result_df = pd.DataFrame(columns=["test_number", "test_name", "trial", "result", "test_time","flake","stack_trace"])
    test_result_grok = Grok(grok_pattern)
    i = 0 #pointer
    while i < len(lines):
        line = lines[i]
        #print(line)
        grokked = test_result_grok.match(line)
        current_is_flake = False
        #print(grokked)
        if grokked != None:
            previous_result = test_result_df.loc[test_result_df["test_number"] == grokked["test_num"]]
            #print(previous_result)
            trial = len(previous_result) + 1
            # is failed
            # entry_is_failed = True if grokked["outcome"] != passed_string else False
            # if flake
            if len(previous_result.loc[previous_result["result"] != passed_string]) > 0 and grokked["outcome"] == passed_string:
                test_result_df.loc[test_result_df["test_number"] == grokked["test_num"], "flake"] = True
                current_is_flake = True
            i += 1

            # is failed get stacktrace
            stack_traces = ""
            if grokked["outcome"] != passed_string:
                while i < len(lines):
                    stack_trace_line = lines[i]
                    #print(stack_trace_line)
                    stack_trace_grokked = test_result_grok.match(stack_trace_line)
                    #print(stack_trace_grokked)
                    if stack_trace_grokked == None:
                        if not stack_trace_line.endswith('\n'):
                            stack_trace_line += '\n'
                        stack_traces += stack_trace_line
                        i += 1
                        #print(stack_traces)
                    else:
                        break
        
            row ={
                    "test_number": grokked["test_num"], 
                    "test_name": grokked["test_name"], 
                    "trial": trial ,
                    "result": grokked["outcome"], 
                    "test_time": grokked["test_time"], 
                    "flake": current_is_flake,
                    "stack_trace": stack_traces,
                }
            new_row_df = pd.DataFrame(row, index=[0])
            test_result_df = pd.concat([test_result_df.loc[:],new_row_df]).reset_index(drop=True)
        else:
            i += 1


    outcome_count = {
        aggregate_data_key[0]: test_result_df["test_name"].nunique(),
        aggregate_data_key[1]: test_result_df.loc[(test_result_df["result"] == passed_string) & (test_result_df["flake"] == False), "test_name"].nunique(),
        aggregate_data_key[2]: test_result_df.loc[((test_result_df["result"] == failed_string) | (test_result_df["result"] == timeout_string)) & (test_result_df["flake"] == True), "test_name"].nunique(),
        aggregate_data_key[3]: test_result_df.loc[(test_result_df["result"] == failed_string) & (test_result_df["flake"] == False), "test_name"].nunique(),
        aggregate_data_key[4]: test_result_df.loc[(test_result_df["result"] == timeout_string) & (test_result_df["flake"] == False), "test_name"].nunique(),
    }

    organized_stacktrace_test_name = {
        aggregate_data_key[2]: np.sort(test_result_df.loc[((test_result_df["result"] == failed_string) | (test_result_df["result"] == timeout_string)) & (test_result_df["flake"] == True), "test_name"].unique().astype(str)),
        aggregate_data_key[3]: np.sort(test_result_df.loc[(test_result_df["result"] == failed_string) & (test_result_df["flake"] == False), "test_name"].unique().astype(str)),
        aggregate_data_key[4]: np.sort(test_result_df.loc[(test_result_df["result"] == timeout_string) & (test_result_df["flake"] == False), "test_name"].unique().astype(str)),
    }

    outcome_groups = {}
    for key in organized_stacktrace_test_name:
        test_name_list = organized_stacktrace_test_name[key]
        outcome_groups[key] = []
        if len(test_name_list) <= 0:
            continue
        for test_name in test_name_list:
            test_name_result_df = test_result_df.loc[test_result_df["test_name"] == str(test_name)]
            #make sure html safe
            current_test = ctest_test(html.escape(test_name)) 
            for i in test_name_result_df.index:
                trial = ctest_test_trial(
                    test_name_result_df['trial'][i],
                    test_name_result_df['result'][i],
                    test_name_result_df['test_time'][i],
                    html.escape(test_name_result_df['stack_trace'][i])
                )
                current_test.add_trial(trial)
            outcome_groups[key].append(current_test)
    result = ctest_run(run_name, outcome_count, outcome_groups)
    return result

if __name__ == '__main__':
    f = open("sample_data/34/msys.log", "r")
    lines  = f.readlines()
    f.close()
    result = grok_parser(lines, 'linux')
    print(jsonpickle.encode(result, indent=4))
    with open('sandbox/data.json', 'w') as f:
        f.write(jsonpickle.encode(result, indent=4))