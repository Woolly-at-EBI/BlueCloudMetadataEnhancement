""" ena_samples.py
 a bunch of ena_sample related methods
 - get_all_ena_detailed_sample_info
 - get_ena_species_count
 - get_ena_species_info

    It is using already downloaded files. This will need to be periodically updated, by running get_ena_ws_data.sh
 ___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-14
__docformat___ = 'reStructuredText'

"""

import pandas as pd
import numpy as np
import pyarrow as pa
from pyarrow import parquet as pq
from pyarrow.parquet import ParquetFile
from icecream import ic
from get_directory_paths import get_directory_paths
from pathlib import Path
import sys

MyDataStuctures = {}

def exit_if_file_not_found(my_file):
    """
    Checks if the file exists and if it does not exists
    :param my_file:
    :return: path_file
    """
    path_file = Path(my_file)
    if not path_file:
        ic(f"{my_file} does not exist")
        sys.exit(f"{my_file} does not exist")
    return path_file

def get_all_ena_detailed_sample_info(debug_status, optional_nrows):
    """ get_all_ena_detailed_sample_info
         This is using ALL ENA samples whether they have GPS coordinates (lat lons) or not.
         It contains many, but not all columns of sample metadata
         refactored to both use a parquet and to check if this df has already been called and to reuse that

         It is using an already downloaded file. This will need to be periodically updated.
        __params__:
               passed_args:
                  debug_status=test_bool
                  optional_nrows=integer based max num of rows to retrieve: only works in debug mode

        __return__:
            df_all_ena_sample_detail
    """
    ic()
    """    ic(f"debug_status={debug_status}") """
    key_name = 'df_all_ena_detailed_sample_info'
    if key_name in MyDataStuctures:
        df = MyDataStuctures[key_name]
        # ic("yes! can reuse")
    else:
        """ ic("have to generate the dataframe") """
        (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
        infile = sample_dir + "sample_much_raw.pa"
        ic(infile)
        exit_if_file_not_found(infile)
        pf = ParquetFile(infile)

        # specific_columns_needed = ["accession", "tax_id", "scientific_name", "lat", "lon", "collection_date",
        # "environment_biome"]
        specific_columns_needed = ["accession", "tax_id", "lat", "lon", "collection_date", "environment_biome"]

        # was useful to limit number of rows, and alternatively focus on specific species
        if debug_status:
            if optional_nrows != 0:
                nrows = optional_nrows
            else:
                nrows = 50000
            ic(f"restricted to {nrows}")
            first_nrows = next(pf.iter_batches(batch_size = nrows))
            df = pa.Table.from_batches([first_nrows]).to_pandas()
            ic(df.head())
            ic(df.columns)
            df = df[specific_columns_needed]
            del first_nrows
        else:
            ic("all ENA")
            exit_if_file_not_found(infile)
            table = pq.read_table(infile, columns = specific_columns_needed)
            df = table.to_pandas()
            # df = df.query('(scientific_name == "marine metagenome") or (scientific_name == "Saccharomyces
            # cerevisiae") or (scientific_name == "Piscirickettsia salmonis")') df = df.query('(scientific_name ==
            # "Piscirickettsia salmonis")')
            del table
        ic(df.columns)

        # reduce memory
        df["tax_id"] = df["tax_id"].astype(np.int32)
        df["collection_date"] = pd.to_datetime(df['collection_date'], errors = 'coerce')
        # for cat in ["scientific_name", "environment_biome"]:
        for cat in ["environment_biome"]:
            df[cat] = df[cat].astype('category')

        # df = df.query( '(scientific_name == "marine metagenome") or (scientific_name == "Saccharomyces cerevisiae")
        # or (scientific_name == "Piscirickettsia salmonis") or (scientific_name == "Equisetum")') ic(df.head(3))

        MyDataStuctures[key_name] = df

    # ic(df.head())
    ic(df.shape)
    # ic()
    return df


def get_ena_species_count():
    """ get_ena_species_count
           returns a df indexed by tax_id, scientific name and count
           refactored to reuse the master ena_all
        __params__:

        __return__:
            df_all_ena_species_count
    """
    ic()

    df = get_all_ena_detailed_sample_info(False, 0)
    df_ena_species = df[["tax_id", "scientific_name"]]

    df_ena_all_species_count = df_ena_species.groupby(["tax_id", "scientific_name"]).size().to_frame('count')
    ic(df_ena_all_species_count.head())
    ic(df_ena_all_species_count.shape[0])
    return df_ena_all_species_count


def get_ena_species_info():
    """ get_ena_species_info
          just the species tax_id and scientific name
          refactored so is using this from a probably already parsed in version
        __params__:
               passed_args:
                  sample_dir
        __return__:
            df_ena_species
    """
    ic()
    df_ena_species = get_all_ena_detailed_sample_info(False, 0)
    ic(df_ena_species.columns)
    df_ena_species = df_ena_species[["tax_id", "scientific_name"]]
    ic()
    return df_ena_species


def get_ena_total_sample_count(sample_dir):
    """ get_ena_total_sample_count
        __params__:
               passed_args: sample_dir
        rtn: integer line count
    """
    sample_file = sample_dir + 'sample_much_raw.tsv'
    exit_if_file_not_found(sample_file)
    num_lines = sum(1 for _ in open(sample_file))

    return num_lines
