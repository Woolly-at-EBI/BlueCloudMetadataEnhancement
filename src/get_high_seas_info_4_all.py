#!/usr/bin/env python3
"""

Script of get_high_seas_info_4_all.py is
to answer a request to get the high seas info

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2025-08-18
__docformat___ = 'reStructuredText'

"""
import sys

import pandas as pd
import numpy as np
import logging
logger = logging.getLogger(__name__)
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

hit_dir = "/Users/woollard/projects/bluecloud/data/hits"
sample_data_dir = "/Users/woollard/projects/bluecloud/data/samples"



def merge_dfs(df_sample, df_sea_info):
    """
    Merge sample and sea-info dataframes on latitude/longitude columns.

    This function performs an inner join between df_sample and df_sea_info
    on the columns ['lat', 'lon'] to retain only rows that match in both
    dataframes.

    :param df_sample: pandas.DataFrame containing at least columns ['lat', 'lon'] and sample attributes
    :param df_sea_info: pandas.DataFrame containing at least columns ['lat', 'lon'] and sea/intersection attributes
    :return: pandas.DataFrame resulting from the inner merge
    """

    first2_df = pd.merge(
     left=df_sample,
     right=df_sea_info,
     how='inner', #only want matches
     left_on=['lat', 'lon'],
     right_on=['lat', 'lon'],
    )
    logger.info(f"merge_dfs len: {len(first2_df)}")
    #logger.info(first2_df.head())

    return first2_df

def get_sea_info():
    """
    Load the merged sea file created by analyseHits.py.

    Reads a tab-separated file containing sea region annotations for
    coordinates and returns it as a pandas DataFrame.

    :return: pandas.DataFrame of merged sea annotations
    """
    logger.debug("in get_sea_info")
    infile = f"{hit_dir}/merged_sea.tsv"
    df_sea_info = pd.read_csv(infile, sep="\t")
    logger.info(f"sea_info {infile}: {len(df_sea_info)}")
    logger.debug(df_sea_info.head(10))
    return df_sea_info

def get_sample_lat_lon():
    """
    Load sample data (filtered) with latitude/longitude coordinates.

    The function currently reads a parquet file with pre-filtered samples
    and returns it as a pandas DataFrame.

    :return: pandas.DataFrame of samples with lat/lon
    """
    logger.debug("in get_sample_lat_lon")
    infile = "all_samples_with_lat_lon.tsv"
    infile = f"{sample_data_dir}/all_sample_lat_longs_present_uniq.tsv"
    infile = f"{sample_data_dir}/sample_much_filtered_lat_lon.pa"

    logger.info(f"Reading {infile}")
    df = pd.read_parquet(infile, engine = 'pyarrow')

    # df = pd.read_csv(infile, sep="\t", nrows=100)
    # df = pd.read_csv(infile, sep = "\t")
    logger.info(f"Number of samples (lat/lon): {len(df)}")

    return df

def determine_high_seas(df):
    """
    Adds a new column `hs_or_eez` to the provided dataframe based on whether the
    values in the `eez_iho_intersect_category` column start with "High Seas", and
    logs the counts of each category along with a sample of the resulting dataframe.

    :param df: pandas.DataFrame
        The input dataframe containing the column `eez_iho_intersect_category`.

    :return: pandas.DataFrame
        The modified dataframe with an added column `hs_or_eez` indicating "High Seas"
        or "EEZ" based on the values in `eez_iho_intersect_category`.
    """
    logger.debug("in determine_high_seas")
    # Add 'hs_or_eez' based on eez_iho_intersect_category starting with 'High Seas'
    df['hs_or_eez'] = np.where(
        df['eez_iho_intersect_category'].str.startswith("High Seas", na = False),
        "High Seas",
        "EEZ"
    )
    logger.info(f"hs_or_eez counts: {df['hs_or_eez'].value_counts().to_dict()}")
    logger.debug(df[['eez_iho_intersect_category', 'hs_or_eez']].sample(10).to_markdown())
    return df

def analysis(df_sample, df_sea_info):
    """
    Perform exploratory analysis

    - Loads a subset of target_samples_sea_area.tsv for inspection
    - Logs column summaries and value counts
    - Adds a new column 'hs_or_eez' with values:
        * 'High Seas' if eez_iho_intersect_category starts with 'High Seas'
        * 'EEZ' otherwise (including NaN or non-matching strings)
    - Splits the dataframe for quick sanity checks
    """
    df = merge_dfs(df_sample, df_sea_info)
    outfile = f"{sample_data_dir}/target_samples_sea_area.tsv"
    # logger.info(f"Writing to {outfile} row_total={len(df)}")
    # df.to_csv(outfile, sep = "\t", index = False)
    df = determine_high_seas(df)

    logger.info(f"Number of samples: {len(df)}")
    logger.info(df.sample(5).to_markdown())

    logger.info(f"columns={df.columns}")

    for my_col in sorted(df.columns):
        if "intersect" in my_col:
            print(my_col)

    logger.info(f"eez_iho_intersect_category: {df['eez_iho_intersect_category'].value_counts()}")
    logger.info(f"eez_category {df['eez_category'].value_counts()}")
    logger.debug(f"High Seas: total={len(df.query('hs_or_eez == "High Seas"'))}  examples {df.query('hs_or_eez == "High Seas"').head(3)}")
    logger.debug(f"EEZ: total={len(df.query('hs_or_eez == "EEZ"'))}  examples {df.query('hs_or_eez == "EEZ"').head(3)}")



def get_minimal_high_seas_df(df_sample, df_sea_info):
    """
    Get the minimal high seas DataFrame based on the provided sample and sea info DataFrames.

    This function processes the input sample and sea info DataFrames, merging them and
    filtering down to a minimal structure containing specific columns: `accession`,
    `hs_or_eez`, and `eez_iho_intersect_category`.

    :param df_sample: The sample DataFrame to be processed.
    :type df_sample: pandas.DataFrame
    :param df_sea_info: The sea information DataFrame to be used for merging.
    :type df_sea_info: pandas.DataFrame
    :return: A filtered DataFrame containing only the `accession`, `hs_or_eez`,
        and `eez_iho_intersect_category` columns.
    :rtype: pandas.DataFrame
    """
    df = merge_dfs(df_sample, df_sea_info)
    outfile = f"{sample_data_dir}/target_samples_sea_area.tsv"
    # logger.info(f"Writing to {outfile} row_total={len(df)}")
    # df.to_csv(outfile, sep = "\t", index = False)
    df = determine_high_seas(df)

    # df_minimal = df[['accession', 'hs_or_eez', 'eez_iho_intersect_category']]
    df_minimal = df[['accession', 'hs_or_eez', 'lat', 'lon']]
    return df_minimal


def main():
    """
    Entrypoint for this script.

    Currently runs the analysis() function for exploratory inspection.
    When enabled (after removing the early exit), it:
      - Loads sample and sea-info data
      - Merges them on lat/lon
      - Writes a combined TSV to sample_data_dir
    """
    df_sample = get_sample_lat_lon()
    df_sea_info = get_sea_info()

    df_minimal = get_minimal_high_seas_df(df_sample, df_sea_info)
    out_file_name = f"{sample_data_dir}/samples_sea_area_minimal.tsv"
    logger.info(f"Write_minimal_high_seas_info writing to {out_file_name} row_total={len(df_minimal)}")
    df_minimal.to_csv(out_file_name, sep = "\t", index = False)

    # analysis(df_sample, df_sea_info)


if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO, format = '%(levelname)s - %(message)s')
    main()
