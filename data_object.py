import jsonpickle
from pygrok import Grok
import pandas as pd
import numpy as np
import html
from collections import OrderedDict

import jsonpickle.ext.numpy as jsonpickle_numpy
import jsonpickle.ext.pandas as jsonpickle_pandas

# this is to disable pandas future warning for bool dtype deprecation see 1.5.0 notes
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

class Data_object():
    """base class for JSON storage
    """
    def __init__(self) -> None:
        pass

    def __str__(self):
        return str(vars(self))

    def toJson_file(self, path, unpickleable = True):
        """write the object to a JSON File overwrite existing file
        

        Args:
            path (str): location of file
            unpickleable (bool, optional): wheather it will add the "py/object" attribute to allow unpickling of object. Defaults to True.
        """
        jsonpickle_numpy.register_handlers()
        with open(path, 'w') as f:
            f.write(jsonpickle.encode(self, unpicklable=unpickleable, indent=4))
    
    def toJson_string(self, unpickleable = True):
        jsonpickle_numpy.register_handlers()
        return jsonpickle.encode(self, unpicklable=unpickleable, indent=4)
        

class Data_table_helper(Data_object):
    """Initialize a container object with data as key for jQuery Datatable to parse
    """
    def __init__(self, data) -> None:
        """data to store

        Args:
            data (any): data to store
        """
        self.data = data

class Builds_collection(Data_object):
    """result container that contain the "build_number":data_object.build"""
    def __init__(self, data_collection) -> None:
        """_summary_

        Args:
            data_collection (OrderedDict(Build)): Ordered dict collection of Build
        """
        self.data = data_collection

    def keep_only_range(self, build_num_range):
        """
        Drop data outside of key range make sure you have the correct key
        """
        print(build_num_range)
        build_num_range = list(set(build_num_range))
        build_num_range.sort(reverse=True)
        print(f"build_num_range: {build_num_range}")
        new_dict = OrderedDict()
        for build_num in build_num_range:
            new_dict[build_num] = self.data[build_num]
        self.data = new_dict


class Build(Data_object):
    """Store a dict of OS agent for a build
    """
    def __init__(self, build_name, ctest_runs) -> None:
        """group of test with the same OS agent

        Args:
            agent_name (str): name of the agent
            aggreagte (dict(int)): result of aggregate data 
            ctest_agents (dict(ctest_run)): dict that contains the a set of ctest_agent 
        """
        self.build_name = build_name
        is_completed = True
        for agent in ctest_runs.keys():
            if ctest_runs[agent].is_not_found:
                is_completed = False

        aggregate = {}
        for agent in ctest_runs.keys():
            for result in ctest_runs[agent].outcome_count.keys():
                if result not in aggregate:
                    aggregate[result] = ctest_runs[agent].outcome_count[result]
                else:
                    # only add if both is not None
                    if ctest_runs[agent].outcome_count[result] != None and aggregate[result] != None:
                        aggregate[result] += ctest_runs[agent].outcome_count[result]
                    elif ctest_runs[agent].outcome_count[result] != None and aggregate[result] == None:
                        aggregate[result] = ctest_runs[agent].outcome_count[result]
                    elif ctest_runs[agent].outcome_count[result] == None and aggregate[result] != None:
                        pass
        self.is_completed = is_completed
        self.aggregate = aggregate
        self.ctest_runs = ctest_runs
        

class Ctest_run(Data_object):
    """Store a dict of outcome_group for a OS run usually from a single log file
    """
    def __init__(
        self,
        is_not_found = True,
        lines = [],
        agent_name = '',
        grok_pattern = '[0-9\/]*Test[ ]*\#%{POSINT:test_num}\: (?<test_name>[^ ]*) [.]*[\* ]{3}%{WORD:outcome}[ ]*%{BASE10NUM:test_time} sec', #Default pattern for ctest unit test
        passed_string = "Passed",
        failed_string = "Failed",
        timeout_string = "Timeout",
        aggregate_data_key = ["Tested", "Passed", "Flake", "Failed","Timeout"],
        ) -> None:
        """Parse a list of logs line from a ctest run to organized data

        Args:
            is_not_found(Bool): a flag for not found log
            lines (list(str)): log lines
            agent_name(str): the name of the agent usually the agent or environment name
            grok_pattern (str, optional): grok pattern for log result. Defaults to '[0-9\/]*Test[ ]*\#%{POSINT:test_num}\: (?<test_name>[^ ]*) [.]*[\* ]{3}%{WORD:outcome}[ ]*%{BASE10NUM:test_time} sec'.
            failed_string (str, optional): String to look for in log when test fail. Defaults to "Failed".
            timeout_string (str, optional): String to look for in log when test timeout. Defaults to "Timeout".
            aggregate_data_key (list, optional): dict keys for test aggregate data. Defaults to ["Tested", "Passed", "Flake","Fail", "Timeout"].

        Returns:
            tuple:
                overall_result(dict): dictionary of overall result with keys based on aggregate_data_key
                organized_stacktrace(dict(list(grok_parser.ctest_test(grok_parser.ctest_test_trial)))): stack traces from current build
        """
        if is_not_found == False:
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
                outcome_groups[key] = {}
                if len(test_name_list) <= 0:
                    continue
                for test_name in test_name_list:
                    test_name_result_df = test_result_df.loc[test_result_df["test_name"] == str(test_name)]
                    #make sure html safe
                    test_name = html.escape(test_name)
                    current_test = Ctest_test(test_name) 
                    for i in test_name_result_df.index:
                        trial = Ctest_test_trial(
                            test_name_result_df['trial'][i],
                            test_name_result_df['result'][i],
                            test_name_result_df['test_time'][i],
                            html.escape(test_name_result_df['stack_trace'][i])
                        )
                        current_test.add_trial(trial)
                    outcome_groups[key][test_name] = (current_test)
        else:
            outcome_count = {
                aggregate_data_key[0]: None,
                aggregate_data_key[1]: None,
                aggregate_data_key[2]: None,
                aggregate_data_key[3]: None,
                aggregate_data_key[4]: None,
            }
            outcome_groups = {}
                
        self.agent_name = agent_name
        self.is_not_found = is_not_found
        self.outcome_count = outcome_count
        self.outcome_groups = outcome_groups

# class Outcome_group(Data_object):
#     """Store a list of stacktrace for a outcome
#     """
#     def __init__(self, outcome, ctest_dict) -> None:
#         """group of test with an outcome  

#         Args:
#             outcome (str): name of the outcome
#             ctest_list (dict(ctest_test)): list of ctest item with this outcome
#         """
#         self.outcome = outcome
#         self.ctest_dict = ctest_dict


class Ctest_test(Data_object):
    """
    Store the result of a test collection of trials
    """
    def __init__(self, test_name=''):
        """Initialize a container to store result from multiple trial fo a single test

        Args:
            test_num (int): = The number of the test by ctest
            test_name (str, optional): The name of the test. Defaults to ''.
        """
        self.test_name = test_name
        self.trials = []
    
    def add_trial(self, entry):
        """add a result of a trial to a test

        Args:
            entry (ctest_test_trial): _description_
        """
        self.trials.append(entry)

class Ctest_test_trial(Data_object):
    """
    Store the trial and its informatieon 
    """
    def __init__(self, trial_num, outcome='', test_time=0.0,stack_trace=''):
        """Create a container for a storing a trial

        Args:
            trial_num (int): trial number
            outcome (str, optional): outcome string of a test. Defaults to ''.
            test_time (float, optional): time of test. Defaults to 0.0 .
            stack_trace (str, optional): stack_trace_string. Defaults to ''.
        """
        self.trial_num = trial_num
        self.outcome = outcome
        self.test_time = test_time
        self.stack_trace = stack_trace


if __name__ == '__main__':
    f = open("sample_data/34/msys.log", "r")
    lines  = f.readlines()
    f.close()
    result = Ctest_run(False ,lines, 'linux')
    print(result.toJson_string(unpickleable=False))
    # with open('sandbox/data.json', 'w') as f:
    #     f.write(jsonpickle.encode(result, indent=4))