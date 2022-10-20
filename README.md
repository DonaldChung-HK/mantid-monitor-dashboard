# Mantid-monitor-dashboard
A dashboard design to monitor unit test for mantid

## Link to dashboard
[Mantid Unit Test Dashboard](https://mantidproject.github.io/mantid-monitor-dashboard/index.html)

## To build
Run
```
pip install -r requirements.txt
python main.py -u 'https://builds.mantidproject.org/' -p 'build_packages_from_branch' 'main_nightly_deployment_prototype' -n 30
```
| argument  | description | Example
| ------------- | ------------- |-----------------|
| `-u`, `--jenkins_url` | url to your jenkins project you have to include the ending `/` | `https://builds.mantidproject.org/` |
| `-p`, `--pipeline_name`  | list of pipeline name to monitor (past multiple string as list) | `build_packages_from_branch` |
|  `-u`, `--jenkins_url`  | the number of builds from latest to parse  | `15` |

The webpage should be in `dist/index.html`
## Process
The main.py does the following
1. gather the argument for argparse
2. set the general settings in the environment variable section
3. copy the resources such as logos and bootstrap and plottyJS from `assets` to `dist/assets`
4. load the JSON pickle from `history/{pipeline_name}/{pipeline_name}_by_build_fail_pickle` if exist
5. update the object by looking at the builds in build range
6. save the new object to `history/{pipeline_name}/{pipeline_name}_by_build_fail_pickle` (allow object operation) and `history/{pipeline_name}/{pipeline_name}_by_build_fail.json` (easier to read version)
7. generate the `pandas.DataFrame` for the chart data with `chart_helper.get_chart_DF`
8. generate the HTML code for the plotty line chart using `chart_helper.plot_line_chart_plotly`
9. create json_file for aggregate data table and copy it
10. create and copy the json for the data table using `datatable_helper.fail_test_table_data_gen`. This also save tabulated fail test result in `history/{pipeline_name}/{pipeline_name}_by_name_fail/{pipeline_name}_{agent_key}_failed_detail_store.json`(easier to read version) and `history/{pipeline_name}/{pipeline_name}_by_name_fail/{pipeline_name}_{agent_key}_failed_detail_store_pickle.json`(allow object operation). This will also update the combined data store in `history/combined_result/combined_by_name_fail/` that aggregate fail builds across pipeline with the same platform.
11. generate the HTML code for failed test dataTable with `jinja2` and `assets/table.html.j2` note that you will have to add the helper functions to the header of `assets/content.html.j2`
12. generate the HTML code for the page using `jinja2` and `assets/content.html.j2` 
13. This is repeated for every pipeline
14. An index page is generated using `jinja2` and `assets/index.html.j2` that contains links to all pipeline dashboard
## Github page
This repo is deploy using the legacy github page mode, you have to enable the github page in the `repo settings -> pages`
set source to `deploy from a branch` and point to the `gh-pages` Branch
## Github action
The update action will run daily at `14:00 UTC` you can also manually run the github action in `Actions - Build webpage` workflow. 
## Potential Issue
- Delete the `History` when you change to monitor another pipeline which change the build number series to avoid any issues.
- Change the `data_collector.File_object` if the name of the log file changes in the future because the log file name is based on the environmental variables on the build machine
- The format of the Jenkins url can also change in the future so modify `data_collector.Remote_source` to change the logic of how to build the url