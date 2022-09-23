import sys
import json
import os
from itertools import groupby, product
from collections import defaultdict
import argparse
from pathlib import Path
from collections import defaultdict
from shutil import copyfile

from jinja2 import Template
from github import Github
from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt
import pandas as pd

from grok_parser import grok_parser
from chart import plot_line_chart, plot_line_chart_plotly

def traverse_data(
    data_path, 
    columns=["Build","Test_ran", "Passed","Flake","Fail","Timeout"], 
    grok_pattern = '[0-9\/]*Test[ ]*\#%{POSINT:test_num}\: (?<test_name>[^ ]*) [.]*[\* ]{3}%{WORD:outcome}[ ]*%{BASE10NUM:test_time} sec',
    passed_string = "Passed",
    failed_string = "Failed",
    timeout_string = "Timeout",):
    stack_trace = {}
    aggregate = {}
    aggregate['overall'] = pd.DataFrame(columns=columns)
    #aggregate['overall'].set_index("Build")
    for os_env_path in data_path.iterdir():
        stack_trace[os_env_path.name] = {}
        aggregate[os_env_path.name] = pd.DataFrame(columns=columns)
        aggregate[os_env_path.name].set_index(columns[0])
        for build_log_path in os_env_path.iterdir():
            f = build_log_path.open()
            lines = f.readlines()
            f.close()
            file_result = grok_parser(
                lines, 
                aggregate_data_key=columns[1:], 
                grok_pattern=grok_pattern,
                passed_string=passed_string,
                failed_string=failed_string,
                timeout_string=timeout_string
            )
            build_num = int(build_log_path.name.split('.')[0])
            file_result['overall']['Build'] = int(build_num)
            aggregate_row = pd.DataFrame(file_result['overall'], index=[build_num])
            aggregate[os_env_path.name] = pd.concat([aggregate[os_env_path.name],aggregate_row])
            stack_trace[os_env_path.name][build_num] = file_result['failed_test_detail']

        aggregate[os_env_path.name] = aggregate[os_env_path.name].astype(int)
        aggregate['overall'][columns[1:]] = aggregate['overall'][columns[1:]].add(aggregate[os_env_path.name][columns[1:]], fill_value=0)  
    aggregate['overall'][columns[0]] =  aggregate['overall'].index
    
    return aggregate, stack_trace


    


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     "jenkins-pipeline-url", 
    #     help="url to jenkins pipeline", 
    #     type=str
    # )
    # parser.add_argument(
    #     "--grok-pattern", 
    #     help="grok pattern for test log", 
    #     type=str, 
    #     default='[0-9\/]*Test[ ]*\#%{POSINT:test_num}\: (?<test_name>[^ ]*) [.]*[\* ]{3}%{WORD:outcome}[ ]*%{BASE10NUM:test_time} sec'
    # )
    
    # args = parser.parse_args()
    # environmental variable
    columns = ["Build","Tested", "Passed", "Flake", "Failed","Timeout"]
    grok_pattern = '[0-9\/]*Test[ ]*\#%{POSINT:test_num}\: (?<test_name>[^ ]*) [.]*[\* ]{3}%{WORD:outcome}[ ]*%{BASE10NUM:test_time} sec'
    jenkins_pipeline_name = "Testing Pipeline"
    os_keys = ["Windows", "Linux", "MacOS"]
    overall_key = 'overall'
    color_scheme = {
        "Tested": "primary",
        "Passed": "success", 
        "Flake": "secondary",
        "Failed": "danger",
        "Timeout": "warning"
    }
    stack_trace_key = [
        "test_number", 
        "test_name", 
        "trial" ,
        "result", 
        "test_time", 
        "flake",
        "stack_trace",
    ]

    assets = Path("assets")
    logo_path = assets / "logo.png"

    dist = Path("dist")
    dist.mkdir(exist_ok=True)

    data_path = Path("data")

    dist_asset = dist / "assets"
    dist_asset.mkdir(exist_ok=True)

    parsed_data = traverse_data(data_path, columns=columns, grok_pattern=grok_pattern)
    #print(parsed_data[0])

    now = datetime.now()

    overall_chart_html_code = plot_line_chart_plotly(
        data=parsed_data[0]['overall'], # getting the dataframe
        x_column = "Build", 
        y_columns = ["Failed", "Timeout", "Flake"], 
        title = 'Failed, Timeout and Flake Count VS Build Number (Overall)', 
        labels = ["Failed", "Timeout", "Flake"], 
        color = ["red", "DarkGoldenRod", "black"],
        marker = ['x', 'hourglass', 'circle'],   
        x_axis = 'Build Number', 
        y_axis = 'Count',
        legend_title = 'Outcome'
    )

    # plot by os
    by_os_chart_html_code = {}
    for os_key in os_keys:
        # print(os_key)
        # print(parsed_data[0][os_key])
        current_plot = plot_line_chart_plotly(
            data=parsed_data[0][os_key], # getting the dataframe
            x_column = "Build", 
            y_columns = ["Failed", "Timeout", "Flake"], 
            title = f'Failed, Timeout and Flake Count VS Build Number ({os_key})', 
            labels = ["Failed", "Timeout", "Flake"], 
            color = ["red", "DarkGoldenRod", "black"],
            marker = ['x', 'hourglass', 'circle'],   
            x_axis = 'Build Number', 
            y_axis = 'Count',
            legend_title = 'Outcome'
        )
        by_os_chart_html_code[os_key] = current_plot
    # print(parsed_data[0][os_keys[0]].dtypes)
    # a = plot_line_chart(
    #         data=parsed_data[0][os_keys[0]], # getting the dataframe
    #         x_column = "Build", 
    #         y_columns = ["Fail", "Timeout", "Flake"], 
    #         title = f'Fail, Timeout and Flake Count VS Build Number ({os_keys[0]})', 
    #         labels = ["Fail", "Timeout", "Flake"], 
    #         color = ["r", "y", "k"],
    #         marker = ['x', 'v', '.'],   
    #         x_axis = 'Build Number', 
    #         y_axis = 'Count'
    #     )

    # print(parsed_data)
    with (assets / "index.html.j2").open("r") as f:
        template = Template(f.read())
    # organize 
    template_data = {
        "jenkins_pipeline_name": jenkins_pipeline_name,
        "current_datetime": now.strftime("%B %d, %Y %H:%M"),
        "logo": logo_path.name,
        "aggregate_test_data": parsed_data[0],
        "aggregate_columns_key": columns,
        "stack_trace": parsed_data[1],
        "overall_chart_html_code": overall_chart_html_code,
        "by_os_chart_html_code": by_os_chart_html_code,
        "os_keys": os_keys,
        "overall_key": overall_key,
        "builds_key": list(parsed_data[0][overall_key][columns[0]].sort_values(ascending=True)),
        "color_scheme": color_scheme,
    }


    output = template.render(**template_data)
    index_path = dist / "index.html"
    index_path.write_text(output)

    # move assets to dist
    copyfile(logo_path, dist_asset / logo_path.name)
    #copyfile(cache, dist_asset / cache.name)

