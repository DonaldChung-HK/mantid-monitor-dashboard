import pandas as pd

from pathlib import Path
from collections import OrderedDict
from data_object import Builds_collection, Build, Ctest_run
import jsonpickle

def get_local_build_num_range(
        data_path,
        num_past_build 
    ):
    build_keys = list(int(d.name) for d in data_path.iterdir())
    latest_build = max(build_keys)
    return list(range(latest_build, max(1, latest_build-num_past_build) - 1, -1))

def traverse_data_local(
    data_path, 
    run_keys,
    build_keys,
    log_sub_filename = '.log',
    columns=["Build","Test_ran", "Passed","Flake","Failed","Timeout"], 
    grok_pattern = '[0-9\/]*Test[ ]*\#%{POSINT:test_num}\: (?<test_name>[^ ]*) [.]*[\* ]{3}%{WORD:outcome}[ ]*%{BASE10NUM:test_time} sec',
    passed_string = "Passed",
    failed_string = "Failed",
    timeout_string = "Timeout",
    ):
    """traverse data in the data path

    Args:
        data_path (Pathlib.Path): path to folder containing data organized by /data_path/build_env/build_num.log
        run_keys: list of system to parse.
        build_keys: list of build number to parse.
        columns (list, optional): columns of dataframe of aggregate data. Defaults to ["Build","Test_ran", "Passed","Flake","Failed","Timeout"].
        grok_pattern (str, optional): grok pattern to parse log. Defaults to '[0-9\/]*Test[ ]*\#%{POSINT:test_num}\: (?<test_name>[^ ]*) [.]*[\* ]{3}%{WORD:outcome}[ ]*%{BASE10NUM:test_time} sec'.
        passed_string (str, optional): in grok pattern %{WORD:outcome} for passed. Defaults to "Passed".
        failed_string (str, optional): in grok pattern %{WORD:outcome} for failed. Defaults to "Failed".
        timeout_string (str, optional): in grok pattern %{WORD:outcome} for timeout. Defaults to "Timeout".
        overall_key (str, optional): key for dict that indicates overall data. Defaults to 'overall'.

    Returns:
        Tuple: 
            aggregate (dict(pandas.dataFrame, ...)): aggregate test result data for each os and overeall in the key
            stack_trace (dict(dict(grok_parser.ctest_test))): stack trace dict organized by os/build_num/stacktrace
    """
    builds_data = OrderedDict()
    for build in build_keys:
        build_path = data_path / str(build)
        ctest_runs = {}
        for run in run_keys:
            run_path = build_path / (run + log_sub_filename)
            if run_path.exists():
                f = run_path.open()
                lines = f.readlines()
                f.close()
                log_is_not_found = False
            else: 
                lines = []
                log_is_not_found = True
            current_run = Ctest_run(
                log_is_not_found=log_is_not_found, 
                lines=lines, 
                run_name=run,
                aggregate_data_key=columns[1:], 
                grok_pattern=grok_pattern,
                passed_string=passed_string,
                failed_string=failed_string,
                timeout_string=timeout_string
            )
            #print(current_run)
            ctest_runs[run] = current_run
            #print(ctest_runs.keys())
        current_build = Build(build, ctest_runs)
        builds_data[build] = current_build
    result = Builds_collection(builds_data)
    return result  


    # stack_trace = {}
    # aggregate = {}
    # aggregate[overall_key] = pd.DataFrame(columns=columns)
    # for os_key in os_keys:
    #     stack_trace[os_key] = {}
    #     aggregate[os_key] = pd.DataFrame(columns=columns)
    #     aggregate[os_key].set_index(columns[0])
    #     os_path = data_path / os_key
    #     for build_key in build_keys:
    #         build_log_path = os_path / (str(build_key) + log_sub_filename)
    #         if build_log_path.exists():
    #             f = build_log_path.open()
    #             lines = f.readlines()
    #             f.close()
    #         else: 
    #             lines = []
    #         overall_result, organized_stacktrace = grok_parser(
    #             lines, 
    #             aggregate_data_key=columns[1:], 
    #             grok_pattern=grok_pattern,
    #             passed_string=passed_string,
    #             failed_string=failed_string,
    #             timeout_string=timeout_string
    #         )
    #         build_num = int(build_log_path.name.split('.')[0])
    #         overall_result[columns[0]] = int(build_num)
    #         aggregate_row = pd.DataFrame(overall_result, index=[build_num])
    #         aggregate[os_key] = pd.concat([aggregate[os_key],aggregate_row])
    #         stack_trace[os_key][build_num] = organized_stacktrace

    #     aggregate[os_key] = aggregate[os_key].astype(int).sort_values(columns[0])
    #     aggregate[overall_key][columns[1:]] = aggregate[overall_key][columns[1:]].add(aggregate[os_key][columns[1:]], fill_value=0)  
    # aggregate[overall_key][columns[0]] =  aggregate[overall_key].index

if __name__ == '__main__':
    data_path = Path("sample_data")
    run_keys = ["darwin17", "linux-gnu", "msys"]
    build_keys = get_local_build_num_range(data_path, 10)
    columns = ["Build", "Tested", "Passed", "Flake", "Failed", "Timeout"]
    build_collection = traverse_data_local(
        data_path, 
        run_keys,
        build_keys,
        columns=columns
    )
    #print(build_collection)
    build_collection.toJson_file('sandbox/build_collection.json', unpickleable=True)
    build_collection.toJson_file('sandbox/build_collection_pretty.json', unpickleable=False)
    with open('sandbox/build_collection.json', 'r') as f:
        string = f.read()
        load = jsonpickle.decode(string)

    print(load.toJson_string(unpickleable=False))