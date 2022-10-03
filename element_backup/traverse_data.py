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
    agent_keys,
    build_keys,
    log_sub_filename = '.log',
    columns=["Build","Tested", "Passed","Flake","Failed","Timeout"], 
    grok_pattern = '[0-9\/]*Test[ ]*\#%{POSINT:test_num}\: (?<test_name>[^ ]*) [.]*[\* ]{3}%{WORD:outcome}[ ]*%{BASE10NUM:test_time} sec',
    passed_string = "Passed",
    failed_string = "Failed",
    timeout_string = "Timeout",
    ):
    """traverse data in the data path

    Args:
        data_path (Pathlib.Path): path to folder containing data organized by /data_path/build_env/build_num.log
        agent_keys: list of system to parse.
        build_keys: list of build number to parse.
        columns (list, optional): columns of dataframe of aggregate data. Defaults to ["Build","Tested", "Passed","Flake","Failed","Timeout"].
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
    builds_data = dict()
    for build in build_keys:
        build_path = data_path / str(build)
        ctest_agents = {}
        for agent in agent_keys:
            agent_path = build_path / (agent + log_sub_filename)
            if agent_path.exists():
                f = agent_path.open()
                lines = f.readlines()
                f.close()
                is_not_found = False
            else: 
                lines = []
                is_not_found = True
            current_agent = Ctest_run(
                is_not_found=is_not_found, 
                lines=lines, 
                agent_name=agent,
                aggregate_data_key=columns[1:], 
                grok_pattern=grok_pattern,
                passed_string=passed_string,
                failed_string=failed_string,
                timeout_string=timeout_string
            )
            #print(current_agent)
            ctest_agents[agent] = current_agent
            #print(ctest_agents.keys())
        current_build = Build(build, ctest_agents)
        builds_data[build] = current_build
    result = Builds_collection(builds_data)
    return result  

if __name__ == '__main__':
    data_path = Path("sample_data")
    agent_keys = ["darwin17", "linux-gnu", "msys"]
    build_keys = get_local_build_num_range(data_path, 10)
    columns = ["Build", "Tested", "Passed", "Flake", "Failed", "Timeout"]
    build_collection = traverse_data_local(
        data_path, 
        agent_keys,
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