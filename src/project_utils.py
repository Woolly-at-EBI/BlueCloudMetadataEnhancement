""" project_utils
     some utilities needed in several projects

 ___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-17
__docformat___ = 'reStructuredText'

"""

import os.path
import pandas as pd
import sys
import pickle
from icecream import ic
import plotly.express as px
import plotly
import plotly.io as pio
pio.renderers.default = "browser"

def put_pickleObj2File(obj, pickle_file, verbose):
    """

    :param obj:
    :param pickle_file
    :param verbose
    :return: nowt
    """
    if verbose:
        ic(f"writing {pickle_file}")
    with open(pickle_file, 'wb') as handle:
        pickle.dump(obj, handle, protocol = pickle.HIGHEST_PROTOCOL)

def get_pickleObj(pickle_file):
    """

    :param pickle_file:
    :return:
    """
    if os.path.isfile(pickle_file):
        ic(pickle_file + " exists, so using it")
        with open(pickle_file, 'rb') as handle:
            obj = pickle.load(handle)
    else:
        ic(pickle_file + " does not exist")
    return obj

def obj_size_fmt(num):
    """

    :param num:
    :return: object size with units
    """
    if num < 10**3:
        return "{:.2f}{}".format(num, "B")
    elif ((num>=10**3)&(num<10**6)):
        return "{:.2f}{}".format(num/(1.024*10**3), "KB")
    elif ((num>=10**6)&(num<10**9)):
        return "{:.2f}{}".format(num/(1.024*10**6), "MB")
    else:
        return "{:.2f}{}".format(num/(1.024*10**9), "GB")

def memory_usage():
    """

    :return: memory_usage_by_variable
    """
    memory_usage_by_variable= pd.DataFrame({k:sys.getsizeof(v)\
    for (k,v) in globals().items()}, index=['Size'])
    memory_usage_by_variable = memory_usage_by_variable.T
    memory_usage_by_variable = memory_usage_by_variable.sort_values(by='Size', ascending=False).head(10)
    memory_usage_by_variable['Size'] = memory_usage_by_variable['Size'].apply(lambda x: obj_size_fmt(x))
    return memory_usage_by_variable

def u_plot_hist(df, cat, color, title, log_y, out_graph_file, width, format, other_params):
    """

    :param df:
    :param cat: - the category (column) to focus on
    :param color: #factor to colour the histograms by - can be the same as category
    :param title:
    :param log_y: bool
    :param out_graph_file:
    :param format:
    :param other_params:  miscellaneous optional parameters passed in as dict - future proofing
    :return: fig
    """
    fig = px.histogram(df, title = title, x = cat,
                       width = width, color = color, log_y = log_y)
    fig.update_xaxes(categoryorder = "total descending")
    fig.update_xaxes(tickangle = 60, tickfont = dict(size = 12))
    # fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = format)
    #fig.show()
    return fig

def u_plot_pie(df, cat, value_column, title, value_type, out_file, other_params):
    """

    :param df:
    :param cat:
    :param value_column:
    :param type:  is value or percent or 'value+percent'
    :param out_file:
    :param other_params:
    :return: fig
    """
    textinfo = value_type
    if '+' in textinfo:
        ic("found: +")
        textinfo = 'value+percent'
    ic(other_params)

    if len(other_params) ==0:
        ic("no params")
        fig = px.pie(df,
                 values = value_column,
                 names = df[cat], title = title)
    else:
        if "color_discrete_map" in other_params:
            ic("adding: color_discrete_map params")
            fig = px.pie(df,
                         values = value_column,
                         names = df[cat],
                         color = df[cat],
                         title = title,
                         color_discrete_map = other_params["color_discrete_map"])
    fig.update_traces(hoverinfo = 'label+percent', textinfo = textinfo)
    fig.update_layout(title_text = title, title_x = 0.5)
    fig.update_layout(legend = dict(yanchor = "top", y = 0.9, xanchor = "left", x = 0.5))
    ic(out_file)
    fig.write_image(out_file)
    # fig.show()
    return fig
