import requests
from collections import OrderedDict
from data_object import Builds_collection, Build, Ctest_run
import jsonpickle
class Remote_source():
    """remote pipeline source
    """
    def __init__(
        self,
        jenkins_url = "https://builds.mantidproject.org/",
        pipeline_name = "build_packages_from_branch",
        auth=None) -> None:
        self.jenkins_url = jenkins_url
        self.pipeline_name = pipeline_name
        self.auth = auth
        self.pipeline_url = self.jenkins_url + "job/" + self.pipeline_name
        self.job_api = self.jenkins_url + "job/" + self.pipeline_name + "/api/json"
        self.build_url_dict = self.get_build_url()
        

    def get_build_url(self):
        job_api = self.job_api
        data = requests.get(job_api, auth=self.auth).json()['builds']
        build_url_dict = OrderedDict()
        for item in data:
            build_url_dict[str(item['number'])] = item['url']
        return build_url_dict

    def get_latest_build_id(self):
        job_api = self.job_api
        data = requests.get(job_api, auth=self.auth).json()['lastBuild']
        #print(data)
        latest_build = data['number']
        return latest_build

    def get_list_of_build_range(self, quantity):
        job_api = self.job_api
        data = requests.get(job_api, auth=self.auth).json()['builds']
        build_url_dict = []
        for i in range(min(quantity, len(data))):
            build_url_dict.append(data[i]['number'])

    def get_log_artifacts_for_build(self, build, file_names):
        build_api = self.build_url_dict[build] + 'api/json'
        data = requests.get(build_api, auth=self.auth).json()
        artifacts = data['artifacts']
        log_files = {}
        artifacts_list = []
        for item in artifacts:
            artifacts_list.append(item['fileName'])
            if item['fileName'] in file_names:
                file_url = self.build_url_dict[build] + 'artifact/' + item['relativePath']
                file_requset = requests.get(file_url, auth=self.auth)
                content = file_requset.text
                log_files[item['fileName']] = {
                    "content": content,
                    "url" : file_url
                }
        for file in file_names:
            if file not in artifacts_list:
                log_files[file] = {
                    "content": None,
                    "url" : None,
                }
        #print (artifacts_list)
        #print(log_files.keys())
        return log_files

class file_object():
    def __init__(self, agent_key, file_name) -> None:
        self.file_name = file_name
        self.agent_key = agent_key

def traverse_data_remote(
    remote_source, 
    file_list,
    build_search_range,
    cached_object = None,
    columns=["Build","Tested", "Passed","Flake","Failed","Timeout"], 
    grok_pattern = '[0-9\/]*Test[ ]*\#%{POSINT:test_num}\: (?<test_name>[^ ]*) [.]*[\* ]{3}%{WORD:outcome}[ ]*%{BASE10NUM:test_time} sec',
    passed_string = "Passed",
    failed_string = "Failed",
    timeout_string = "Timeout",):
    existing_completed = set()
    if cached_object != None:
        for build in cached_object.data.keys():
            if cached_object.data[build].is_completed:
                existing_completed.add(build)
    else:
        cached_object = Builds_collection({})
    print(existing_completed)
    targets = list(set(build_search_range) - existing_completed)
    print(targets)
    for build in targets:
        log_data = remote_source.get_log_artifacts_for_build(build, [f.file_name for f in file_list])
        #print(log_data)
        ctest_agents = {}
        for i in range(len(file_list)):
            print(build, file_list[i].file_name, log_data.keys())
            if log_data[file_list[i].file_name]['content'] != None:
                lines = log_data[file_list[i].file_name]['content'].split('\n')
                is_not_found = False
            else: 
                lines = []
                is_not_found = True
            current_agent = Ctest_run(
                is_not_found=is_not_found, 
                lines=lines, 
                agent_name=file_list[i].agent_key,
                aggregate_data_key=columns[1:], 
                grok_pattern=grok_pattern,
                passed_string=passed_string,
                failed_string=failed_string,
                timeout_string=timeout_string
            )
            #print(current_agent)
            ctest_agents[file_list[i].agent_key] = current_agent
            #print(ctest_agents.keys())
        current_build = Build(build, ctest_agents)
        cached_object.data[build] = current_build
    
    cached_object.sort()
    
    return cached_object
    


    
    


    
    
if __name__ == '__main__':
    remote_source_test = Remote_source()
    num_past_build = 10
    print(type(remote_source_test.get_latest_build_id()))
    build_range = list(range(remote_source_test.get_latest_build_id(), max(1, remote_source_test.get_latest_build_id()-num_past_build) - 1, -1))
    build_range = [str(i) for i in build_range]
    print(build_range)
    agent_keys = ["darwin17", "linux-gnu", "msys"]
    file_names = ["darwin17.log", "linux-gnu.log", "msys.log"]
    file_list = [
        file_object(agent_keys[i], file_names[i]) for i in range(len(file_names))
    ]

    with open('sandbox/testing_pickle', 'r') as f:
        string = f.read()
        load = jsonpickle.decode(string)

    data = traverse_data_remote(remote_source_test, file_list,build_range,cached_object=load)
    data.toJson_file('sandbox/testing', False)
    data.toJson_file('sandbox/testing_pickle', True)