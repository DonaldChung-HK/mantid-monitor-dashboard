from ensurepip import bootstrap

from collections import OrderedDict
import argparse
from pathlib import Path
from shutil import copyfile

from jinja2 import Template
from datetime import datetime

#from traverse_data import traverse_data_local
from datatable_helper import fail_test_table_data_gen
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
    parser = argparse.ArgumentParser(description='Produce a dashboard to monitor mantid unit test')
    parser.add_argument('-u','--jenkins_url', 
                        type=str,
                        help='url to your jenkins project',
                        dest="jenkins_url",
                        required=True)
    parser.add_argument('-p', '--pipeline_name', 
                        type=str,
                        help='the pipeline name to monitor',
                        dest = "pipeline_name",
                        required=True)
    parser.add_argument('-n', '--num_past_build', 
                        type=int,
                        help='number of past build to monitor',
                        dest = "num_past_build",
                        required=True)                    

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
    data_name_style["None"] = data_name_visual(
        "None",
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
    ###data_dir
    local_sample_data_path = Path("sample_data")
    ## table data dir for fail count table
    website_data_dir = assets / "data" 
    website_data_dir.mkdir(exist_ok=True)
    ###dist
    dist = Path("dist")
    dist.mkdir(exist_ok=True)
    dist_asset = dist / "assets"
    dist_asset.mkdir(exist_ok=True)
    dist_src = dist_asset / "src"
    dist_src.mkdir(exist_ok=True)
    dist_data = dist / "data" # if you change this you will also change the table.html.j2
    dist_data.mkdir(exist_ok=True)
    ##historical data path
    history_path = Path("history")
    history_path.mkdir(exist_ok=True)
    history_json = history_path / "history_fail_test_data.json"
    history_json_pickle = history_path / "history_fail_test_data_pickle.json"
    tabled_histroy_path = history_path / "tabled_fail_test"
    tabled_histroy_path.mkdir(exist_ok=True)
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
    remote_source = Remote_source(args.jenkins_url, args.pipeline_name) # set in arguments
    num_past_build = args.num_past_build    
    agent_keys = ["Mac", "Linux", "Windows"]
    file_names = ["darwin17.log", "linux-gnu.log", "msys.log"]
    build_keys = list(remote_source.get_list_of_build_range(num_past_build))
    build_keys = [str(i) for i in build_keys]
    file_list = [
        File_object(agent_keys[i], file_names[i]) for i in range(len(file_names))
    ]

    ###############################################################
    
    

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
        aggregate_json_filename = f"{item}_aggregate_table.json" 
        aggregate_dir = website_data_dir / aggregate_json_filename
        aggregate[item].fillna('Missing').to_json(path_or_buf = aggregate_dir, orient = "split", index=False)
        copyfile((website_data_dir / aggregate_json_filename), (dist_data / aggregate_json_filename))
        agg_data_table_template_data = {
            "agent_name": item,
            "json_file_name": aggregate_json_filename
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
    with (assets / "table.html.j2").open("r") as f:
        table_template = Template(f.read())
    table_html_code = {}
    for agent_key in agent_keys:
        json_file_name = "fail_test_table_" + agent_key + ".json"
        lts_file_name = "fail_test_store_" + agent_key + ".json"
        lts_pickle_file_name = "fail_test_store_" + agent_key + "_pickle.json"
        # generate json file
        fail_test_table_data_gen(
                path=website_data_dir / json_file_name,
                build_collection = build_collection_data,
                build_keys = build_keys,
                agent = agent_key,
                lts_path = tabled_histroy_path / lts_file_name,
                lts_path_pickle = tabled_histroy_path / lts_pickle_file_name,
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

    with (assets / "index.html.j2").open("r") as f:
        template = Template(f.read())
    # organize 
    # print(aggregate["msys"].set_indexT.to_json(orient="records"))
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
    index_path = dist / "index.html"
    index_path.write_text(output)
    # move assets to dist
    
    #copyfile(cache, dist_asset / cache.name)

