#!/usr/bin/env python3
"""Script of get_high_seas_info_4_specific.py is to get_high_seas_info_4_specific
to answer a request to get the high seas info for sample accessions that Vishnu had already found

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2025-05-20
__docformat___ = 'reStructuredText'

"""
import sys

import pandas as pd
import logging
logger = logging.getLogger(__name__)
import argparse

def get_vishnus_sample_ids():
    infile = 'target_sample_accession_ids.txt'
    df = pd.read_csv(infile, header=None)
    df.columns = ['accession']
    logger.info(df.head())
    return df

def merge_dfs(df_sample, df_sea_info, df_target_accessions):
    """

    :param df_sample:
    :param df_sea_info:
    :param df_target_accessions:
    :return:
    """
    first2_df = pd.merge(
     left=df_sample,
     right=df_sea_info,
     how='inner', #only want all matches
     left_on=['lat', 'lon'],
     right_on=['lat', 'lon'],
    )
    logger.info(f"FIRST Merge complete: {len(first2_df)}")
    logger.info(first2_df)

    df_all3 = pd.merge(
     left=first2_df,
     right=df_target_accessions,
     how='inner',  #only want all matches
     left_on=['accession'],
     right_on=['accession'],
    )
    logger.info(f"second merge complete: {len(df_all3)}")
    logger.info(df_all3)

    # df_tmp = df_all3.head(10)
    # logger.info(df_tmp.pivot_table(columns=None))

    return df_all3

def get_sea_info():
    """

    :return:
    """
    infile = "/Users/woollard/projects/bluecloud/data/hits/merged_sea.tsv"
    df = pd.read_csv(infile, sep="\t")
    logger.info(f"Number of samples: {len(df)}")
    logger.info(df.head(10))
    print()
    return df

def get_sample_lat_lon():
    """"""
    infile = "all_samples_with_lat_lon.tsv"

    # df = pd.read_csv(infile, sep="\t", nrows=100)
    df = pd.read_csv(infile, sep = "\t")
    logger.info(f"Number of samples: {len(df)}")
    logger.info(df.head(10))
    print()
    return df

def analysis():
    infile = "target_samples_sea_area_just_iho.tsv"
    df = pd.read_csv(infile, sep = "\t")
    logger.info(f"Number of samples: {len(df)}")
    logger.info(df.head(10))

    df_new = df[['accession','eez_iho_intersect_category']]
    df_new = df_new[df_new['eez_iho_intersect_category'].]
    logger.info(f"ddd: {df_new.head(5)}")

def main():
    analysis()
    sys.exit("FFFFF")

    df_target_accessions = get_vishnus_sample_ids()

    df_sample = get_sample_lat_lon()
    df_sea_info = get_sea_info()
    df_all3 = merge_dfs(df_sample, df_sea_info, df_target_accessions)
    outfile = "target_samples_sea_area.tsv"
    logger.info(f"Writing to {outfile}")
    df_all3.to_csv(outfile, sep="\t", index=False)
    # cut -f 1,2,3,5,9,10,38,42 target_samples_sea_area.tsv > target_samples_sea_area_just_iho.tsv

if __name__ == '__main__':
    logging.basicConfig(level = logging.DEBUG, format = '%(levelname)s - %(message)s')
    main()
