#!/usr/bin/env python3
"""Script of high_seas_analysis.py is to high_seas_analysis.py

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2024-04-10
__docformat___ = 'reStructuredText'
chmod a+x high_seas_analysis.py
"""
import os
import sys

from icecream import ic
# import os
# import argparse
import pandas as pd
import plotly
import plotly.express as px
import re
import json
import pickle

pd.set_option('display.max_rows', 1000);
pd.set_option('display.max_columns', 1000);
pd.set_option('display.width', 1000)

def plot_scatter(df, cat, color, y, title, plot_width, outformat, out_graph_file):
    fig = px.scatter(df, title = title, x = cat, y = y, width = plot_width,
                     color = color)
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = outformat)


def read_multi_json_file(json_file):
    """
    Read json file with multiple records in it.
    :param json_file:
    :return:
    """
    with open(json_file, 'r') as infile:
        new_data = infile.read()
        # removing newlines initially to allow some other patterns matching work
        new_data = new_data.replace('\n', '').replace('}{', '},{').replace('}\n{', '},{').replace('{"id"', '\n{"id"')
        # ic(f"before replacements: {len(new_data)}")
        start_size = len(new_data)
        # re.sub('\n{"id"[^\n]*},\n', '', new_data) remove lines that only have a partial pattern!  want to delete
        # any "line" that starts /{"id"/ and doesn't /end }/ these should not exist, but they do... after some
        # exploration it is those that have a single white space. new_data = re.sub(r'\n{"id"[^\n]+^((?!},).)\n',
        # '\n', new_data) need to remove partial records. Cause broken JSON. We think that there was possibly an
        # interruption to streaming
        new_data = re.sub('\n{"id".* \n', '\n', new_data)
        end_size = len(new_data)
        if end_size < start_size:
            ic(f"WARNING Removed some defective JSON records: went from start_len={start_size} to end_len={end_size}")

    #     ic(new_data[:100])
    # outfile = json_file + ".tmp_data"
    # ic(f"Writing {outfile}")
    # with open(outfile, 'w') as outfile:
    #     outfile.write(new_data)
    # print(f"new_data[983:986] {new_data[983:986]}")
    # print(f"new_data[950:1050] {new_data[950:1050]}")
    py_data = json.loads(f"[{new_data}]")


    df = pd.DataFrame(py_data)
    return df


def high_seas_analyse():
    """"""

    pickle_file_path = 'tmp_df.pickle'


    json_dir = '/Users/woollard/projects/bluecloud/clearinghouse/high_seas/past_curations_records/pull_all_curations_done/output/'
    json_filename = json_dir + 'cho_EEZ-IHO-intersect-name.json'
    if(os.path.exists(pickle_file_path)):
        df = pd.read_pickle(pickle_file_path)
    else:
        df = read_multi_json_file(json_filename)
        with open(pickle_file_path, 'wb') as file:
            # Serialize and write the variable to the file
            pickle.dump(df, file)
    df = df.query('suppressed == False')
    ic(df.columns)
    ic(df.head())

    df['category'] = df['valuePost']
    plot_width = 1000
    out_graph_file = 'high_seas_graph.png'
    color
    plot_scatter(df, "category", color, y, "High Seas", plot_width, 'PNG', out_graph_file):


    ic()

def main():
    high_seas_analyse()

if __name__ == '__main__':
    ic()
    main()
