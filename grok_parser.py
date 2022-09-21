from pygrok import Grok
import pandas as pd

def grok_parser(
    lines,
    grok_pattern = '[0-9\/]*Test[ ]*\#%{POSINT:test_num}\: (?<test_name>[^ ]*) [.]*[\* ]{3}%{WORD:outcome}[ ]*%{BASE10NUM:test_time} sec', #Default pattern for ctest unit test
    passed_string = "Passed",
    failed_string = "Failed",
    timeout_string = "Timeout"
):
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
            entry_is_failed = True if grokked["outcome"] != passed_string else False
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


    overall_result = {
        "num_unique_test_run": test_result_df["test_name"].nunique(),
        "num_fail": test_result_df.loc[(test_result_df["result"] == failed_string) & (test_result_df["flake"] == False), "test_number"].nunique(),
        "num_timeout": test_result_df.loc[(test_result_df["result"] == timeout_string) & (test_result_df["flake"] == False), "test_number"].nunique(),
        "num_flake": test_result_df.loc[(test_result_df["result"] == passed_string) & (test_result_df["flake"] == True), "test_number"].nunique(),
    }
    failed_test_result_df = test_result_df.loc[(test_result_df["result"] == failed_string) | (test_result_df["result"] == timeout_string)]

    parsed = {
        "overall": overall_result,
        "failed_test_detail": failed_test_result_df
    }
    return parsed

if __name__ == '__main__':
    f = open("flake-64-ci.log", "r")
    lines  = f.readlines()
    f.close()
    result = grok_parser(lines)
    print(result)