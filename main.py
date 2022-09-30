from ensurepip import bootstrap
import sys
import json
import os
from itertools import groupby, product
from collections import defaultdict, OrderedDict
import argparse
from pathlib import Path
from shutil import copyfile

from jinja2 import Template
from github import Github
from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt
import pandas as pd

from traverse_data import traverse_data_local
from datatable_helper import fail_test_table_data_gen
from chart_helper import get_chart_DF, plot_line_chart, plot_line_chart_plotly

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
        

def get_local_build_num_range(
        data_path,
        num_pass_build 
    ):
    build_keys = list(int(d.name) for d in data_path.iterdir())
    latest_build = max(build_keys)
    return list(range(latest_build, max(1, latest_build-num_pass_build) - 1, -1))



if __name__ == "__main__":
    # environmental variable############################
    jenkins_pipeline_name = "Testing Pipeline"
    jenkins_pipeline_url = "#"
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
    agent_keys = ["darwin17", "linux-gnu", "msys"]
    build_keys = get_local_build_num_range(local_sample_data_path, 10)
    ###############################################################


    

    build_collection_data = traverse_data_local(
        local_sample_data_path, 
        agent_keys,
        build_keys,
        columns=columns, 
        grok_pattern=grok_pattern)

    aggregate = get_chart_DF(build_collection_data)

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
        # generate json file
        fail_test_table_data_gen(
                path=website_data_dir / json_file_name,
                build_collection = build_collection_data,
                build_keys = build_keys,
                agent = agent_key,
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
        "jenkins_pipeline_name": jenkins_pipeline_name,
        "jenkins_pipeline_url": jenkins_pipeline_url,
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

