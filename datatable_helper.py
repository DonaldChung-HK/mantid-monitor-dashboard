import jsonpickle
from data_object import Data_object

class Problem_test_trial(Data_object):
    """store stack_trace for problem test
    """
    def __init__(
        self,
        test_name, 
        build,
        agent_name='',
        trial=0,
        outcome = '',
        test_time = 0.0,
        stack_trace = '' 
        ) -> None:
        """store a problem test trial entry

        Args:
            build (int or str): build ID of the problem test
            agent_name (str, optional): agent_name usually OS env name. Defaults to ''.
            trial (int, optional): trial number for repeat until pass. Defaults to 0.
            outcome (str, optional): outcome of the trial. Defaults to ''.
            test_time (float, optional): time taken. Defaults to 0.0.
            stacktrace (str, optional): stack trace of the test. Defaults to ''.
        """
        self.test_name = test_name
        self.build = build
        self.agent_name = agent_name
        self.trial = trial
        self.outcome = outcome
        self.test_time = test_time
        self.stacktrace = stack_trace       

class Problem_test_entry(Data_object):
    """
    store the last failed trial of a system/ctest run
    """
    
    def __init__(
        self, 
        test_name, 
        latest_failed_build,
        last_failed_outcome, 
        build_collection, 
        agent_name, 
        build_keys, 
        passed_key = "Passed", 
        not_found_key = "None", 
        stacktrace_excluded_outcome = ['Passed']):
        """Initialise a container for a fail test entry

        Args:
            test_name (str): Failed test name
            latest_failed_build (str): last failed build name
            last_failed_outcome (_type_): outcome of the test in the last failed build
            build_collection (_type_): _description_
            agent_name (_type_): _description_
            build_keys (_type_): _description_
            passed_key (str, optional): _description_. Defaults to "Passed".
            not_found_key (str, optional): _description_. Defaults to "None".
            stacktrace_excluded_outcome (list, optional): _description_. Defaults to ['Passed'].
        """
        self.test_name = test_name
        self.latest_failed_build = latest_failed_build
        self.agent_name = agent_name
        self.last_failed_outcome = last_failed_outcome
         
        past_outcome_list, self.problem_count = self.get_past_outcome_list_single_env(build_collection, build_keys, passed_key, not_found_key)

        self.past_outcome = {
            "build_keys":build_keys,
            "past_outcome_list":past_outcome_list, 
        }
        self.last_stack_traces = self.get_last_stack_trace(build_collection, stacktrace_excluded_outcome)

    def get_past_outcome_list_single_env(self, build_collection, build_keys, passed_key, not_found_key):
        """Populate the outcome list

        Args:
            build_collection (data_object.Builds_collection): test data container
            build_keys (list(str)): List of build id to search
            passed_key (str): Key for passed test since passed test is not included in test data container
            not_found_key (str): Key for log not found test.

        Returns:
            tuple: 
                past_outcome_list_result(list(str)): Outcome of test result
                problem_count(int): count of problem
        """
        past_outcome_list_result = []
        problem_count = 0
        for build in build_keys:
            if build_collection.data[build].ctest_runs[self.agent_name].is_not_found:
                past_outcome_list_result.append(not_found_key)
            else:
                for outcome in build_collection.data[build].ctest_runs[self.agent_name].outcome_groups.keys():
                    failed_test = build_collection.data[build].ctest_runs[self.agent_name].outcome_groups[outcome]
                    if self.test_name in failed_test.keys():
                        #print(self.test_name, failed_test.keys())
                        past_outcome_list_result.append(outcome)
                        problem_count += 1
                        break
                else:
                    past_outcome_list_result.append(passed_key)
        return past_outcome_list_result, problem_count
        
    def get_last_stack_trace(self, build_collection, stacktrace_excluded_outcome):
        """_summary_

        Args:
            build_collection (data_object.Builds_collection): test data container
            stacktrace_excluded_outcome (list(str)): key of test result to exclude such as excluding the passed test in flaky test

        Returns:
            Problem_test_trial: the stack trace information object to populate the stack trace card in DataTable JS.
        """
        failed_test_trials = build_collection.data[self.latest_failed_build].ctest_runs[self.agent_name].outcome_groups[self.last_failed_outcome][self.test_name].trials
        for failed_test_trial_i in range(len(failed_test_trials) - 1 , 0 - 1, -1):
            #print(failed_test_trials[failed_test_trial_i].trial_num)
            if failed_test_trials[failed_test_trial_i].outcome not in stacktrace_excluded_outcome: # exclude the flaky pass
                return Problem_test_trial(
                    test_name = self.test_name,
                    build = self.latest_failed_build,
                    agent_name = self.agent_name,
                    trial = failed_test_trials[failed_test_trial_i].trial_num,
                    outcome = failed_test_trials[failed_test_trial_i].outcome,
                    test_time = failed_test_trials[failed_test_trial_i].test_time,
                    stack_trace = failed_test_trials[failed_test_trial_i].stack_trace
                )

            
                

class Problem_test_table_collection(Data_object):
    """store the latest fail information
    """
    def __init__(
        self, 
        build_collection,
        build_keys,
        agent,
        passed_key = "Passed",
        not_found_key = "None",
        stacktrace_excluded_outcome = ["Passed"]) -> None:
        """store for jQuerry datatable 
        jQUerry data table forces data to be encoded in a list named data.

        Args:
            build_collection (data_object.Builds_collection): Build container for extracted test data
            build_keys (list(int or str)): the key of build data to explore
            agent (str): The agent to parse
            passed_key (str, optional): Key name for passed result. Defaults to "Passed".
            not_found_key (str, optional): Key Name for not found . Defaults to "None".
            stacktrace_excluded_outcome (list, optional): excluded outcomes key for getting latest stacktrace. Defaults to ["Passed"].
        """
        recent_fail_list = []
        result_object_list = []
        for build in build_keys:
                failed_outcomes = build_collection.data[build].ctest_runs[agent].outcome_groups
                for outcome_group in failed_outcomes.keys():
                    for item in failed_outcomes[outcome_group].keys():
                        if item not in recent_fail_list:
                            recent_fail_list.append(item)
                            result_object_list.append(Problem_test_entry(
                                    test_name = failed_outcomes[outcome_group][item].test_name,
                                    latest_failed_build=build,
                                    last_failed_outcome = outcome_group,
                                    agent_name=agent,
                                    build_keys=build_keys,
                                    build_collection=build_collection,
                                    passed_key=passed_key,
                                    not_found_key=not_found_key,
                                    stacktrace_excluded_outcome = stacktrace_excluded_outcome
                                ))

        self.data = result_object_list

def fail_test_table_data_gen(
    path,
    build_collection,
    build_keys,
    agent,
    passed_key = "Passed",
    not_found_key = "None",
    stacktrace_excluded_outcome = ["Passed"]
    ):
    """Generate a JSON file to pass into DataTable

    Args:
        path (pathlib.Path): Path to the JSON file
        build_collection (data_object.Build_collection): container for test data
        build_keys (list(str)): builds to perform search
        agent (str): agent type to construct the report
        passed_key (str, optional): Key name for passed result since passed test is excluded. Defaults to "Passed".
        not_found_key (str, optional): Key Name for not found. Defaults to "None".
        stacktrace_excluded_outcome (list, optional): excluded outcomes key for getting latest stacktrace. Defaults to ["Passed"].
    """
    data = Problem_test_table_collection(
        build_collection=build_collection, 
        build_keys=build_keys, 
        agent=agent,
        passed_key=passed_key,
        not_found_key=not_found_key,
        stacktrace_excluded_outcome=stacktrace_excluded_outcome
        )
    data.toJson_file(path, unpickleable=False)

if __name__ == '__main__':
    with open('sandbox/build_collection.json', 'r') as f:
        string = f.read()
        load = jsonpickle.decode(string)

    data = Problem_test_table_collection(load, list(range(35, 35-10-1, -1)), "msys")
    data.toJson_file('sandbox/problem_test_pretty_msys.json', unpickleable=False)