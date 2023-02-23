"""Script of get_geo_props_using_dates.py is to


___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-23
__docformat___ = 'reStructuredText'

"""


from icecream import ic

import matplotlib.pyplot as plt

import argparse
import pandas as pd
pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)

from ena_samples import get_all_ena_detailed_sample_info
from get_directory_paths import get_directory_paths

def merge_sea_ena(hit_dir,df_ena_detail):
    """merge_sea_ena
        merge the sea hits from the shape files with ENA
        only selecting those ENA samples that intersect with EEZ
    :param hit_dir:
    :return: df_merge_sea_ena
    """

    df_sea_hits = pd.read_csv(hit_dir + "merged_sea.tsv", sep='\t')
    for mrg in ['MRGID', 'MRGID_TER1', 'MRGID_TER2', 'MRGID_SOV1', 'MRGID_SOV2']:
        df_sea_hits[mrg] = df_sea_hits[mrg].fillna(0).astype(int)
    df_merge_sea_ena = pd.merge(df_ena_detail,df_sea_hits, on=["lat", "lon"], how="inner")

    return df_merge_sea_ena


def get_df_4_collection_date(hit_dir):
    """"""
    test_status = True
    df_ena_detail = get_all_ena_detailed_sample_info(test_status)
    df_ena_detail = df_ena_detail[~df_ena_detail['collection_date'].isna()]
    ic(df_ena_detail.sample(n=10))

    #merge_sea_ena(hit_dir, df_ena_detail):

    ic()

def main():
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    get_df_4_collection_date(hit_dir)


if __name__ == '__main__':
    main()
    ic()


