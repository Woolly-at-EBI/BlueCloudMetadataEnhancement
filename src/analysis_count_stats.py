"""Script of analysis_count_stats.py is to analsis the combined output count file from the waterTaxonomyAnalyis.py
 It is doing some basic stats and comparisions.

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-02
__docformat___ = 'reStructuredText'

"""


from icecream import ic
import numpy as np
import pandas as pd
pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)

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
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    ic(df.head(10))
    df['tax_id'] = df['tax_id'].to_string()
    basic(df)
    combinations(df)

def main():
    analysis_count_file = "/Users/woollard/projects/bluecloud/analysis/merge_tax_combined_all_sample_counts.tsv"
    analysis_count(analysis_count_file)


if __name__ == '__main__':
    ic()
    main()
