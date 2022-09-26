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

from grok_parser import grok_parser
from chart import plot_line_chart, plot_line_chart_plotly

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
        

def traverse_data(
    data_path, 
    os_keys,
    build_keys,
    log_sub_filename = '.log',
    columns=["Build","Test_ran", "Passed","Flake","Failed","Timeout"], 
    grok_pattern = '[0-9\/]*Test[ ]*\#%{POSINT:test_num}\: (?<test_name>[^ ]*) [.]*[\* ]{3}%{WORD:outcome}[ ]*%{BASE10NUM:test_time} sec',
    passed_string = "Passed",
    failed_string = "Failed",
    timeout_string = "Timeout",
    overall_key = 'overall'):
    """traverse data in the data path

    Args:
        data_path (Pathlib.Path): path to folder containing data organized by /data_path/build_env/build_num.log
        os_keys: list of system to parse.
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

    stack_trace = {}
    aggregate = {}
    aggregate[overall_key] = pd.DataFrame(columns=columns)
    for os_key in os_keys:
        stack_trace[os_key] = {}
        aggregate[os_key] = pd.DataFrame(columns=columns)
        aggregate[os_key].set_index(columns[0])
        os_path = data_path / os_key
        for build_key in build_keys:
            build_log_path = os_path / (str(build_key) + log_sub_filename)
            if build_log_path.exists():
                f = build_log_path.open()
                lines = f.readlines()
                f.close()
            else: 
                lines = []
            overall_result, organized_stacktrace = grok_parser(
                lines, 
                aggregate_data_key=columns[1:], 
                grok_pattern=grok_pattern,
                passed_string=passed_string,
                failed_string=failed_string,
                timeout_string=timeout_string
            )
            build_num = int(build_log_path.name.split('.')[0])
            overall_result[columns[0]] = int(build_num)
            aggregate_row = pd.DataFrame(overall_result, index=[build_num])
            aggregate[os_key] = pd.concat([aggregate[os_key],aggregate_row])
            stack_trace[os_key][build_num] = organized_stacktrace

        aggregate[os_key] = aggregate[os_key].astype(int).sort_values(columns[0])
        aggregate[overall_key][columns[1:]] = aggregate[overall_key][columns[1:]].add(aggregate[os_key][columns[1:]], fill_value=0)  
    aggregate[overall_key][columns[0]] =  aggregate[overall_key].index
    
    return aggregate, stack_trace

def get_local_build_num_range(
        data_path,
        os_keys,
        num_pass_build 
    ):
    build_keys = {}
    max_build_num = 0
    for os_env in os_keys:
        build_log_path = data_path / os_env
        build_keys[os_env] = list(int(d.name.split('.')[0]) for d in build_log_path.iterdir())
        max_build_num = max(max(build_keys[os_env]), max_build_num)
    return list(range(max_build_num, max(1, max_build_num-num_pass_build) - 1, -1))

    


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
    ## Parsing
    columns = ["Build", "Tested", "Passed", "Flake", "Failed", "Timeout"]
    grok_pattern = '[0-9\/]*Test[ ]*\#%{POSINT:test_num}\: (?<test_name>[^ ]*) [.]*[\* ]{3}%{WORD:outcome}[ ]*%{BASE10NUM:test_time} sec'
    overall_key = 'overall'
    ## Plotting
    x_column = "Build"
    y_columns = ["Flake" ,"Failed", "Timeout"]
    x_axis = 'Build Number'
    y_axis = 'Count'
    legend_title = 'Outcome'
    ## Data location
    ###assets
    assets = Path("assets")
    ###dist
    dist = Path("dist")
    dist.mkdir(exist_ok=True)
    dist_asset = dist / "assets"
    dist_asset.mkdir(exist_ok=True)
    dist_src = dist_asset / "src"
    dist_src.mkdir(exist_ok=True)
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
    ###data_dir and range
    data_path = Path("data")
    os_keys = list(d.name for d in data_path.iterdir())
    
    build_keys = get_local_build_num_range(
        data_path,
        os_keys,
        10
    )
    ###############################################################


    

    aggregate, stack_trace = traverse_data(
        data_path, 
        os_keys,
        build_keys,
        columns=columns, 
        grok_pattern=grok_pattern)


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
    for os_key in os_keys:
        current_plot = plot_line_chart_plotly(
            data=aggregate[os_key], # getting the dataframe
            x_column = x_column, 
            y_columns = y_columns, 
            title = f'Failed, Timeout and Flake Count VS Build Number ({os_key})', 
            labels = y_columns, 
            color = [data_name_style[item].css_color_style for item in y_columns],
            marker = [data_name_style[item].marker_shape for item in y_columns],   
            x_axis = x_axis, 
            y_axis = y_axis,
            legend_title = legend_title
        )
        by_os_chart_html_code[os_key] = current_plot
    
    with (assets / "index.html.j2").open("r") as f:
        template = Template(f.read())
    # organize 
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
        "stack_trace_columns": y_columns,
        "stack_trace": stack_trace,
        "overall_chart_html_code": overall_chart_html_code,
        "by_os_chart_html_code": by_os_chart_html_code,
        "os_keys": os_keys,
        "overall_key": overall_key,
        "build_keys": build_keys,
        "data_name_style": data_name_style,
    }
    output = template.render(**template_data)
    index_path = dist / "index.html"
    index_path.write_text(output)
    # move assets to dist
    
    #copyfile(cache, dist_asset / cache.name)

