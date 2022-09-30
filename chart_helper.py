import mpld3
from mpld3 import plugins
from mpld3.utils import get_id
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import jsonpickle

def get_chart_DF(
    Builds_collection, 
    overall_name = 'Overall', 
    agent_keys = ["darwin17", "linux-gnu", "msys"],
    columns = ["Build", "Tested", "Passed", "Flake", "Failed", "Timeout"]):
    """collect data from Builds_collection to form a dict of pandas DF for plotting chart
    I it is like a SQL groupBy for build
    Args:
        Builds_collection (data_object): Collection of build result
        overall_name(str): name of the overall entry
        agent_keys(list(str)): your agent keys
        columns(list(str)): columns for pandas frame starting with build number. Default to ["Build", "Tested", "Passed", "Flake", "Failed", "Timeout"]
    """
    
    
    # initialising container
    holder = {
        overall_name: [],
    }
    for agent_key in agent_keys:
        holder[agent_key] = []
    # traverse JSON dict type container
    build_nums = list(Builds_collection.data.keys())
    build_nums.sort(reverse=True)


    def populate_row(build_num, data_dict, columns):
        current_row = [build_num]
        for item in columns[1:]:
            current_row.append(data_dict[item])
        return current_row

    for build_num in build_nums:
        overall_data_dict = Builds_collection.data[build_num].aggregate
        holder[overall_name].append(populate_row(build_num, overall_data_dict, columns))
        for agent_key in agent_keys:
            agent_data_dict = Builds_collection.data[build_num].ctest_runs[agent_key].outcome_count
            holder[agent_key].append(populate_row(build_num, agent_data_dict, columns))

    result = {}
    for key in holder.keys():
        result[key] = pd.DataFrame(holder[key], columns=columns)
    return result

def plot_line_chart(
    data,
    x_column = "Build", 
    y_columns = ["Fail", "Timeout", "Flake"], 
    title = 'Fail, Timeout and Flake Count VS Build Number', 
    labels = ["Fail", "Timeout", "Flake"], 
    color = ["r", "y", "k"],
    marker = ['x', 'v', '.'],   
    x_axis = 'Build Number', 
    y_axis = 'Count'):
    """
    Plot the graph using mpld3 to html code

    Args:
        data (pandas.DataFrame): DataFrame to plot
        x_column (str, optional): label to select column for x-axis. Defaults to "Build".
        y_columns (list, optional): label to select column for y-axis. Defaults to ["Fail", "Timeout", "Flake"].
        title (str, optional): chart title. Defaults to 'Fail, Timeout and Flake Count VS Build Number'.
        labels (list(str), optional): label list for each series. Defaults to ["Fail", "Timeout", "Flake"].
        color (list(str), optional): list of string of matplotlib color for each series. Defaults to ["r", "y", "k"].
        marker (list, optional): list of string of matplotlib marker for each series. Defaults to ['x', 'v', '.'].
        x_axis (str, optional): label for x_axis. Defaults to 'Build Number'.
        y_axis (str, optional): label for y_axis. Defaults to 'Count'.

    Returns:
        str: HTML string to be inserted via jinja2
    """
    fig, ax = plt.subplots()
    line_collections = ax.plot(data[x_column], data[y_columns], lw=4, alpha=0.4, ms=8, mew=2)
    #print(data[x_column])
    #print(data[y_columns])
    ax.set_title(title)
    ax.set_xlabel(x_axis)
    ax.set_ylabel(y_axis)
    for i in range(len(y_columns)):
        ax.get_lines()[i].set_color(color[i])
        ax.get_lines()[i].set_marker(marker[i])
    ax.set_xticks(data[x_column])
    #plt.show()
    interactive_legend = plugins.InteractiveLegendPlugin(line_collections, labels)
    plugins.connect(fig, interactive_legend)
    #plt.show()
    reresult_html_str =  mpld3.fig_to_html(fig)
    return reresult_html_str

def plot_line_chart_plotly(
    data,
    x_column = "Build", 
    y_columns = ["Fail", "Timeout", "Flake"], 
    title = 'Fail, Timeout and Flake Count VS Build Number', 
    labels = ["Fail", "Timeout", "Flake"], 
    color = ["red", "gold", "black"],
    marker = ['x', 'hourglass', 'circle'],   
    x_axis = 'Build Number', 
    y_axis = 'Count',
    legend_title = 'Outcome'):
    """Plot the graph using plotly to html code. Note that this doesn't include the JS component and must be inserted inthe the Jinja template

    Args:
        data (pandas.DataFrame): DataFrame to plot
        x_column (str, optional): label to select column for x-axis. Defaults to "Build".
        y_columns (list, optional): label to select column for y-axis. Defaults to ["Fail", "Timeout", "Flake"].
        title (str, optional): chart title. Defaults to 'Fail, Timeout and Flake Count VS Build Number'.
        labels (list, optional): label list for each series. Defaults to ["Fail", "Timeout", "Flake"].
        color (list, optional): list of string of CSS color for each series. Defaults to ["red", "gold", "black"].
        marker (list, optional): list of string of Plotly marker for each series. Defaults to ['x', 'hourglass', 'circle'].
        x_axis (str, optional): label for x_axis. Defaults to 'Build Number'.
        y_axis (str, optional): label for y_axis. Defaults to 'Count'.
        legend_title (str, optional): label for legend. Defaults to 'Outcome'.

    Returns:
        str: HTML string to be inserted via jinja2
    """   
    fig = go.Figure()

    for i in range(len(y_columns)):
        fig.add_trace(go.Scatter(
            x=data[x_column], 
            y=data[y_columns[i]].fillna(0), 
            name=y_columns[i],
            marker_symbol=marker[i],
            marker_size=10,
            hovertemplate="<br>".join([
                "<b>"+ y_columns[i] +"</b>",
                x_axis + ": %{x}",
                y_axis + ": %{y}",
                #remove the extra tag
                "<extra></extra>"
            ]),
            line=dict(color=color[i])))

    fig.update_layout(
        title=title,
        xaxis_title=x_axis,
        yaxis_title=y_axis,
        legend_title=legend_title)
    
    return fig.to_html(include_plotlyjs=False, full_html=False)


if __name__ == '__main__':
    with open('sandbox/build_collection.json', 'r') as f:
        string = f.read()
        load = jsonpickle.decode(string)

    test_df = get_chart_DF(load)
    print(test_df)