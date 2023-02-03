"""Script of analysis_count_stats.py is to analsis the combined output count file from the waterTaxonomyAnalyis.py
 It is doing some basic stats and comparisions.

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-02
__docformat___ = 'reStructuredText'

"""


from icecream import ic
#from IPython.display import display
from tabulate import tabulate
import numpy as np
import pandas as pd
import plotly
import plotly.express as px
import plotly.io as pio
pio.renderers.default = "browser"
pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)


def focus(df):
    """ focus

    :param df:
    :return:
    """
    # df['tax_id'] = df['tax_id'].to_string()
    df_filtered = df.query('(`NCBI term` == "marine metagenome") or (`NCBI term` == "Saccharomyces cerevisiae") or (`NCBI term` == "Piscirickettsia salmonis")')
    #display(df_filtered.head())
    ic(df_filtered.columns)
    ic(df_filtered)
    df_filtered = df.query('`marine (ocean connected)` == True')
    df_tmp = df_filtered.loc[:, ~df_filtered.columns.isin(['tax_id', 'NCBI term taxonomy_type', 'marine (ocean connected)',  'freshwater (land enclosed)'])]

    corr_matrix = df_tmp.corr()
    fig = px.imshow(corr_matrix)
    fig.show()


    fig.show()


def combinations(df):
    """ combinations of some pairs of columns

    :param df:
    :return:
    """
    pairs = {}
    count_fields = ['lat_lon_marine_counts', 'lat_lon_terrestrial_counts', 'lat_lon_terrestrial_counts', 'lat_lon_marine_and_terrestrial_counts', 'lat_lon_not_marine_or_terrestrial_counts', 'not_lat_lon_counts', 'all_ena_counts']
    pairs["marine (ocean connected)"] = count_fields
    pairs['freshwater (land enclosed)'] = count_fields

    ic("These figures are the number of rows(=taxa) that the match the following logic: ")

    for x in pairs:
        ic(x)
        for y in pairs[x]:
            df_res = df.query(f"`{x}` == True").query(f"`{y}` > 0")
            ic(f"==True " + f"`{y}`  > 0" + ": " + str(df_res.shape[0]))
            df_res = df.query(f"`{x}` == True").query(f"`{y}` == 0")
            ic(f"==True " + f"`{y}` == 0" + ": " + str(df_res.shape[0]))
            df_res = df.query(f"`{x}` == False").query(f"`{y}` > 0")
            ic(f"==False" + f"`{y}`  > 0" + ": " + str(df_res.shape[0]))
            df_res = df.query(f"`{x}` == False").query(f"`{y}` == 0")
            ic(f"==False" + f"`{y}` == 0" + ": " + str(df_res.shape[0]))


def basic(df):
    """ basic statistics of the columns.

    :param df:
    :return:
    """
    ic(df.describe(include=[object]))
    ic(df['taxonomy_type'].value_counts())
    ic(df.describe(include=[bool]))
    ic(df['marine (ocean connected)'].value_counts())
    ic(df['freshwater (land enclosed)'].value_counts())
    ic(df.eval("`marine (ocean connected)` == `freshwater (land enclosed)`").all())
    ic(df.describe(include =[np.number]))

def analysis_count(analysis_count_file):
    """analysis_count routine that controls

    :param analysis_count_file:
    :return:
    """
    ic()
    ic(analysis_count_file)
    df = pd.read_csv(analysis_count_file, sep = "\t", index_col=None)
    df['tax_id_index'] = df['tax_id']
    df = df.set_index('tax_id_index')
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    ic(df.head(10))

    #basic(df)
    #combinations(df)
    focus(df)

def main():
    analysis_count_file = "/Users/woollard/projects/bluecloud/analysis/merge_tax_combined_all_sample_counts.tsv"
    analysis_count(analysis_count_file)


if __name__ == '__main__':
    ic()
    main()
