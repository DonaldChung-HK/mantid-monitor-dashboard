import mpld3
from mpld3 import plugins
from mpld3.utils import get_id
import numpy as np
import collections
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go

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
            y=data[y_columns[i]], 
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
    a = pd.read_csv('test.csv')
    print(plot_line_chart(a))
    print(plot_line_chart_plotly(a)(a))