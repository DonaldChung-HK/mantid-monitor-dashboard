from ensurepip import bootstrap

from collections import OrderedDict
import argparse
from pathlib import Path
from shutil import copyfile

from jinja2 import Template
from datetime import datetime

#from traverse_data import traverse_data_local
from datatable_helper import fail_test_table_data_gen, LTS_Problem_test_display
from chart_helper import get_chart_DF, plot_line_chart_plotly
from data_collector import Remote_source, File_object, traverse_data_remote

import jsonpickle

class data_name_visual():
    """store the data name and the visual
    """
    def __init__(
        self,
        entry_name,
        bootstrap_style = "primary",
        css_color_style = "blue",
        marker_shape = "circle"
    ) -> None:
        """storage container for visual style

        Args:
            entry_name (str): name of the data type
            bootstrap_style (str, optional): bootstrap style string https://getbootstrap.com/docs/5.2/components/card/#about . Defaults to "primary".
            css_color_style (str, optional): css color string https://www.w3schools.com/cssref/css_colors.asp . Defaults to "blue".
            marker_shape (str, optional): marker shape from https://plotly.com/python/marker-style/ . Defaults to "circle".
        """
        self.entry_name = entry_name
        self.bootstrap_style = bootstrap_style
        self.css_color_style = css_color_style
        self.marker_shape = marker_shape
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Produce a dashboard to monitor mantid unit test !!!edit the `agent_keys_list` and `file_names_list` as well for temporory fix')
    parser.add_argument('-u','--jenkins_url', 
                        type=str,
                        help='url to your jenkins project',
                        dest="jenkins_url",
                        required=True)
    parser.add_argument('-p', '--pipeline_name', 
                        type=str,
                        nargs='+',
                        help='the pipeline names to monitor',
                        dest = "pipeline_names",
                        required=True)
    parser.add_argument('-n', '--num_past_build', 
                        type=int,
                        help='number of past build to monitor',
                        dest = "num_past_build",
                        required=True)
    parser.add_argument('-a', '--auth', 
                        type=str,
                        help='authentication for HTTP API if needed, it is parsed as {username} {password}',
                        dest = "auth",
                        nargs = 2,
                        default = None,
                        required = False)
    parser.add_argument('-t', '--target', 
                        type=str,
                        help='The list of target name to parse the number of this argument must match the number of pipeline name and the order',
                        dest = "agent_keys_list",
                        nargs='+',
                        action='append',
                        default = None,
                        required = True)                 
    parser.add_argument('-f', '--file_name', 
                        type=str,
                        help='The list of file name to parse the number of this argument must match the number of pipeline name and the order',
                        dest = "file_names_list",
                        nargs='+',
                        action='append',
                        default = None,
                        required = True)      
    args = parser.parse_args()

    
    # environment variable############################
    
    now = datetime.now()
    ## Data
    data_name_style = OrderedDict()
    data_name_style["Build"] = data_name_visual(
        "Build",
        "light",
        "white",
        "triangle-up"
    )
    data_name_style["Tested"] = data_name_visual(
        "Tested",
        "primary",
        "LightBlue",
        "cross"
    )
    data_name_style["Passed"] = data_name_visual(
        "Passed",
        "success",
        "LightGreen",
        "star"
    )
    data_name_style["Flake"] = data_name_visual(
        "Flake",
        "secondary",
        "DarkSlateGrey",
        "circle"
    )
    data_name_style["Failed"] = data_name_visual(
        "Failed",
        "danger",
        "Red",
        "x"
    )
    data_name_style["Timeout"] = data_name_visual(
        "Timeout",
        "warning",
        "DarkGoldenRod",
        "hourglass"
    )
    missing_key = "Missing"
    data_name_style[missing_key] = data_name_visual(
        missing_key,
        "info",
        "Black",
        "x"
    )
    ## Parsing
    columns = ["Build", "Tested", "Passed", "Flake", "Failed", "Timeout"]
    grok_pattern = '[0-9\/]*Test[ ]*\#%{POSINT:test_num}\: (?<test_name>[^ ]*) [.]*[\* ]{3}%{WORD:outcome}[ ]*%{BASE10NUM:test_time} sec'
    overall_key = 'Overall'
    ## Plotting
    x_column = "Build"
    y_columns = ["Flake" ,"Failed", "Timeout"]
    x_axis = 'Build Number'
    y_axis = 'Count'
    legend_title = 'Outcome'
    ## Data location
    ###assets
    assets = Path("assets")
    ## table data dir for fail count table
    website_data_dir = assets / "data" 
    website_data_dir.mkdir(exist_ok=True)
    website_data_dir_combined = website_data_dir / "combine"
    website_data_dir_combined.mkdir(exist_ok=True)
    ###dist
    dist = Path("dist")
    dist.mkdir(exist_ok=True)
    dist_combined = dist / "combined"
    dist_combined.mkdir(exist_ok=True)
    dist_asset = dist / "assets"
    dist_asset.mkdir(exist_ok=True)
    dist_src = dist_asset / "src"
    dist_src.mkdir(exist_ok=True)
    dist_data = dist / "data" # if you change this you will also change the table.html.j2
    dist_data.mkdir(exist_ok=True)
    dist_data_combined = dist_data / "combined" # if you change this you will also change the table.html.j2
    dist_data_combined.mkdir(exist_ok=True)
    ##historical data path
    history_path = Path("history")
    history_path.mkdir(exist_ok=True)
    ####logo
    logo_path = assets / "logo.png"
    copyfile(logo_path, dist_asset / logo_path.name)
    ####CSS and JS
    src_path = assets / "src"
    bootstrap_css_file = src_path / "bootstrap.min.css"
    copyfile(bootstrap_css_file, dist_src / bootstrap_css_file.name)
    bootstrap_js_file = src_path / "bootstrap.bundle.min.js"
    copyfile(bootstrap_js_file, dist_src / bootstrap_js_file.name)
    plotly_js_file = src_path / "plotly-2.14.0.min.js"
    copyfile(plotly_js_file, dist_src / plotly_js_file.name)
    
    
    # range of data
    # !!! edit here to create a list of target that matches the order of pipeline that you specified in input
    # agent_keys_list = [
    #     ["Mac", "Linux", "Windows"], 
    #     ["Linux"]
    # ]
    # the file_name_list should have a list of file name matching to the os target in agent_keys_list
    
    # file_names_list = [
    #     ["darwin17.log", "linux-gnu.log", "msys.log"],
    #     ["linux-gnu.log"]
    # ]
    

    # name for testing system
    # file_names_list = [
    #     ["osx-64-ci.log", "linux-64-ci.log", "windows-64-ci.log"],
    #     ["linux-64-ci.log"]
    # ]

    ###############################################################
    agent_keys_list = args.agent_keys_list
    file_names_list = args.file_names_list
    pipeline_names = args.pipeline_names
    pipeline_links = {}

    combined_agent_keys_list = []

    combined_result_path = history_path / "combined_result"
    combined_result_path.mkdir(exist_ok=True)

    combined_by_testname_histroy_path = combined_result_path / "combined_by_name_fail"

    combined_result_json = combined_result_path / "combined_failed_detail_store.json"
    combined_result_jsonpickle = combined_result_path / "combined_failed_detail_store_pickle.json"
    if args.auth != None:
        auth = (args.auth[0], args.auth[1])
    else:
        auth = None


    for i in range(len(pipeline_names)):
        #temp fix for controlling files to parse if you don't edit
        pipeline_name = pipeline_names[i]
        agent_keys = agent_keys_list[i]
        file_names = file_names_list[i]

        remote_source = Remote_source(args.jenkins_url, pipeline_name, auth=auth)
        num_past_build = args.num_past_build    
        build_keys = list(remote_source.get_list_of_build_range(num_past_build))
        build_keys = [str(i) for i in build_keys]
        build_keys.sort(key=int, reverse=True)
        file_list = [
            File_object(agent_keys[i], file_names[i]) for i in range(len(file_names))
        ]
        current_pipeline_hist = history_path / pipeline_name
        current_pipeline_hist.mkdir(exist_ok=True)
        history_json = current_pipeline_hist / f"{pipeline_name}_by_build_fail.json"
        history_json_pickle = current_pipeline_hist / f"{pipeline_name}_by_build_fail_pickle.json"
        by_testname_histroy_path = current_pipeline_hist / f"{pipeline_name}_by_name_fail"
        by_testname_histroy_path.mkdir(exist_ok=True)

        if history_json_pickle.exists():
            with open(history_json_pickle, 'r') as f:
                string = f.read()
                old_data = jsonpickle.decode(string)
        else:
            old_data = None

        build_collection_data = traverse_data_remote(
            remote_source, 
            file_list,
            build_keys,
            cached_object=old_data,
            columns=columns,
            grok_pattern=grok_pattern,)
        build_collection_data.toJson_file(history_json, False)
        build_collection_data.toJson_file(history_json_pickle, True)
        

        aggregate = get_chart_DF(build_collection_data, build_keys, agent_keys=agent_keys)
        #create aggregate data table
        with (assets / "agg_table.html.j2").open("r") as f:
            agg_table_template = Template(f.read())
        agg_table_html_code = {}

        for item in aggregate.keys():
            aggregate_json_filename = f"{pipeline_name}_{item}_aggregate_table.json" 
            aggregate_dir = website_data_dir / aggregate_json_filename
            aggregate[item].fillna(missing_key).to_json(path_or_buf = aggregate_dir, orient = "split", index=False)
            copyfile((website_data_dir / aggregate_json_filename), (dist_data / aggregate_json_filename))
            agg_data_table_template_data = {
                "agent_name": item,
                "json_file_name": aggregate_json_filename,
                "missing_key": missing_key,
            }
            agg_data_table_output = agg_table_template.render(**agg_data_table_template_data)
            agg_table_html_code[item] = agg_data_table_output

        overall_agg_table_html_code = agg_table_html_code[overall_key]
        # create chart
        overall_chart_html_code = plot_line_chart_plotly(
            data=aggregate[overall_key], # getting the dataframe
            x_column = x_column, 
            y_columns = y_columns, 
            title = 'Failed, Timeout and Flake Count VS Build Number (Overall)', 
            labels = y_columns, 
            color = [data_name_style[item].css_color_style for item in y_columns],
            marker = [data_name_style[item].marker_shape for item in y_columns],   
            x_axis = x_axis, 
            y_axis = y_axis,
            legend_title = legend_title
        )

        # plot by os
        by_os_chart_html_code = {}
        for agent_key in agent_keys:
            current_plot = plot_line_chart_plotly(
                data=aggregate[agent_key], # getting the dataframe
                x_column = x_column, 
                y_columns = y_columns, 
                title = f'Failed, Timeout and Flake Count VS Build Number ({agent_key})', 
                labels = y_columns, 
                color = [data_name_style[item].css_color_style for item in y_columns],
                marker = [data_name_style[item].marker_shape for item in y_columns],   
                x_axis = x_axis, 
                y_axis = y_axis,
                legend_title = legend_title
            )
            by_os_chart_html_code[agent_key] = current_plot
        
        #create data table
        with (assets / "test_detail_table.html.j2").open("r") as f:
            table_template = Template(f.read())
        table_html_code = {}
        for agent_key in agent_keys:
            json_file_name = f"{pipeline_name}_{agent_key}_failed_detail.json"
            lts_file_name = f"{pipeline_name}_{agent_key}_failed_detail_store.json"
            lts_pickle_file_name = f"{pipeline_name}_{agent_key}_failed_detail_store_pickle.json"
            combined_result_json = combined_result_path / f"{agent_key}_combined_failed_detail_store.json"
            combined_result_jsonpickle = combined_result_path / f"{agent_key}_combined_failed_detail_store_pickle.json"
            # generate json file
            fail_test_table_data_gen(
                    path=website_data_dir / json_file_name,
                    build_collection = build_collection_data,
                    build_keys = build_keys,
                    agent = agent_key,
                    pipeline_name = pipeline_name,
                    lts_path_json = by_testname_histroy_path / lts_file_name,
                    lts_path_jsonpickle = by_testname_histroy_path / lts_pickle_file_name,
                    combined_path_json = combined_result_json,
                    combined_path_jsonpickle = combined_result_jsonpickle,
                    passed_key = "Passed",
                    not_found_key = "None",
                    stacktrace_excluded_outcome = ["Passed"]
                )
            # copy json file to dist
            copyfile((website_data_dir / json_file_name), (dist_data / json_file_name))

            data_table_template_data = {
                "agent_name": agent_key,
                "json_file_name": json_file_name
            }
            data_table_output = table_template.render(**data_table_template_data)
            table_html_code[agent_key] = data_table_output

            #add the key to combined result if it is not in there
            if agent_key not in combined_agent_keys_list:
                combined_agent_keys_list.append(agent_key)
            

        with (assets / "content.html.j2").open("r") as f:
            template = Template(f.read())

        template_data = {
            "jenkins_pipeline_name": remote_source.pipeline_name,
            "jenkins_pipeline_url": remote_source.pipeline_url,
            "agg_table_html_code": agg_table_html_code,
            "overall_agg_table_html_code": overall_agg_table_html_code,
            "current_datetime": now.strftime("%B %d, %Y %H:%M"),
            "logo": logo_path.name,
            "bootstrap_css_file": bootstrap_css_file.name,
            "bootstrap_js_file": bootstrap_js_file.name,
            "plotly_js_file": plotly_js_file.name,
            "aggregate_test_data": aggregate,
            "aggregate_columns_key": columns,
            "overall_chart_html_code": overall_chart_html_code,
            "by_os_chart_html_code": by_os_chart_html_code,
            "os_keys": agent_keys,
            "overall_key": overall_key,
            "build_keys": build_keys,
            "data_name_style": data_name_style,
            "table_html_code": table_html_code,
        }
        output = template.render(**template_data)
        content_path = dist / f"{pipeline_name}.html"
        content_path.write_text(output)
        pipeline_links[pipeline_name] = content_path.name

    with (assets / "combined_content.html.j2").open("r") as f:
        combined_page_template = Template(f.read())

    combined_html = {}
    #combined table since result need to be aggregated from multiple dable
    for agent_key in combined_agent_keys_list:
        file_name = f"{agent_key}_combined_failed_detail_store_pickle.json"
        display_file_name = f"{agent_key}_combined_failed_detail_display.json"
        combined_result_jsonpickle = combined_result_path / file_name
        with (combined_result_jsonpickle).open("r") as f:
            string = f.read()
            combined_result = jsonpickle.decode(string)
        combined_result_container = []
        for key in combined_result.data.keys():
            current_entry = {}
            current_entry["test_name"] = combined_result.data[key].test_name
            current_entry["past_failed_outcome"] = combined_result.data[key].past_failed_outcome
            #this is to accomodate older data before the last fail date was implemented
            try:
                current_entry["last_fail_detected"] = combined_result.data[key].last_fail_detected
            except:
                current_entry["last_fail_detected"] = "1990-01-01" #place holder for older data
            combined_result_container.append(current_entry)

        combined_result_display_object = LTS_Problem_test_display(combined_result_container)
        combined_result_display_object.toJson_file(website_data_dir_combined / display_file_name, unpickleable=False)

        # copy json file to dist
        copyfile((website_data_dir_combined / display_file_name), (dist_data_combined / display_file_name))

        template_data = {
            "agent_name": agent_key,
            "logo": logo_path.name,
            "current_datetime": now.strftime("%B %d, %Y %H:%M"),
            "json_file_name": display_file_name, 
            "bootstrap_css_file": bootstrap_css_file.name,
            "bootstrap_js_file": bootstrap_js_file.name,
        }
        combined_html_name = "combined_"+ agent_key +".html"
        output = combined_page_template.render(**template_data)
        dist_combined_path = dist_combined / combined_html_name
        dist_combined_path.write_text(output)
        combined_html[agent_key] = combined_html_name




    with (assets / "index.html.j2").open("r") as f:
        index_template = Template(f.read())

    template_data = {
        "jenkins_pipeline_name": remote_source.pipeline_name,
        "jenkins_url": remote_source.pipeline_url,
        "logo": logo_path.name,
        "current_datetime": now.strftime("%B %d, %Y %H:%M"),
        "pipeline_links": pipeline_links,
        "bootstrap_css_file": bootstrap_css_file.name,
        "bootstrap_js_file": bootstrap_js_file.name,
        "combined_html": combined_html,
    }

    output = index_template.render(**template_data)
    index_path = dist / "index.html"
    index_path.write_text(output)
    


