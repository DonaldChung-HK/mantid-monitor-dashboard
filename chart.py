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