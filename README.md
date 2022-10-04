# Mantid-monitor-dashboard
A dashboard design to monitor unit test for mantid

## To build
Run
```
pip install -r requirements.txt
python main.py -u 'https://builds.mantidproject.org/' -p 'build_packages_from_branch' -n 15
```
| argument  | description | Example
| ------------- | ------------- |-----------------|
| `-u`, `--jenkins_url` | url to your jenkins project you have to include the ending `/` | `https://builds.mantidproject.org/` |
| `-p`, `--pipeline_name`  | the pipeline name to monitor  | `build_packages_from_branch` |
|  `-u`, `--jenkins_url`  | the number of builds from latest to parse  | `15` |

The webpage should be in `dist/index.html`
## Process
The main.py does the following
1. gather the argument for argparse
2. set the general settings in the environment variable section
3. copy the resources such as logos and bootstrap and plottyJS from `assets` to `dist/assets`
4. load the JSON pickle from `history/history_fail_test_data_pickle.json` if exist
5. update the object by looking at the builds in build range
6. save the new object to `history/history_fail_test_data_pickle.json` (allow object operation) and `history/history_fail_test_data.json` (easier to read version)
7. generate the `pandas.DataFrame` for the chart data with `chart_helper.get_chart_DF`
8. generate the HTML code for the plotty line chart using `chart_helper.plot_line_chart_plotly`
9. create and copy the json for the data table using `datatable_helper.fail_test_table_data_gen` 
10. generate the HTML code for failed test dataTable with `jinja2` and `assets/table.html.j2` not that you will have to add the helper functions to the header of `assets/index.html.j2`
11. generate the HTML code for the page using `jinja2` and `assets/index.html.j2` 
## Github page
This repo is deploy using the legacy github page mode, you have to enable the github page in the `repo settings -> pages`
set source to `deploy from a branch` and point to the `gh-pages` Branch
## Github action
The update action will run daily at `14:00 UTC` you can also manually run the github action in `Actions - Build webpage` workflow. 