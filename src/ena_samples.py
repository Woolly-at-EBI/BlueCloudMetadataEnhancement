
""" ena_samples.py
 a bunch of ena_sample related methods
 - get_all_ena_detailed_sample_info
 - get_ena_species_count
 - get_ena_species_info

 ___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-14
__docformat___ = 'reStructuredText'

"""

import pandas as pd
import pyarrow as pa
from pyarrow import parquet as pq
from pyarrow.parquet import ParquetFile
from icecream import ic

MyDataStuctures = {}

from get_directory_paths import get_directory_paths

def get_all_ena_detailed_sample_info(test_bool):
    """ get_all_ena_detailed_sample_info
         This is using ALL ENA samples whether they have GPS coordinates (lat lons) or not.
         It contains many, but not all columns of sample metadata
         refactored to both use a parquet and to check if this df has already be called and to reuse that
        __params__:
               passed_args:
                  test_bool
        __return__:
            df_all_ena_sample_detail
    """
    ic()
    key_name = 'df_all_ena_detailed_sample_info'
    if key_name in MyDataStuctures:
        df = MyDataStuctures[key_name]
        ic("yes! can reuse")
    else:
        ic("have to generate the dataframe")

        (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()

        infile = sample_dir + "sample_much_raw.pa"
        ic(infile)
        # df = pd.read_csv(infile, sep = "\t", nrows = 100000)
        # df = pd.read_csv(infile, sep = "\t")

        pf = ParquetFile(infile)
        specific_columns_needed = ["accession", "tax_id", "scientific_name", "lat", "lon", "environment_biome"]

        # was useful to limit number of rows, and alternatively focus on specific species
        if test_bool:
            nrows = 100000
            first_nrows = next(pf.iter_batches(batch_size = nrows))
            df = pa.Table.from_batches([first_nrows]).to_pandas()
            ic(df.head())
            df = df[specific_columns_needed]
            del first_nrows
        else:
            table = pq.read_table(infile, columns=specific_columns_needed)
            df = table.to_pandas()
            # df = df.query('(scientific_name == "marine metagenome") or (scientific_name == "Saccharomyces cerevisiae") or (scientific_name == "Piscirickettsia salmonis")')
            # df = df.query('(scientific_name == "Piscirickettsia salmonis")')
            del table

        #reduce memory
        df["tax_id"] = df["tax_id"].astype(int)
        #df["lat"] = df["lat"].astype(np.float32)
        #df["lon"] = df["lon"].astype(np.float32)

        #df = df.query(
        #   '(scientific_name == "marine metagenome") or (scientific_name == "Saccharomyces cerevisiae") or (scientific_name == "Piscirickettsia salmonis") or (scientific_name == "Equisetum")')

        MyDataStuctures[key_name] = df

    ic(df.head())
    ic(df.shape)
    ic()
    return df

def get_ena_species_count(sample_dir):
    """ get_ena_species_count
           returns a df indexed by tax_id, scientific name and count
           refactored to reuse the master ena_all
        __params__:
               passed_args:
                  sample_dir
        __return__:
            df_all_ena_species_count
    """
    ic()
    # infile = sample_dir + "ena_tax.tsv"
    # df_ena_species = pd.read_csv(infile, sep = "\t")
    # ic(df_ena_species.head())
    # df_ena_all_species_count = df_ena_species.groupby(["tax_id", "scientific_name"]).size().to_frame('count')

    df = get_all_ena_detailed_sample_info(False)
    df_ena_species = df[["tax_id", "scientific_name"]]

    df_ena_all_species_count = df_ena_species.groupby(["tax_id", "scientific_name"]).size().to_frame('count')
    ic(df_ena_all_species_count.head())
    ic(df_ena_all_species_count.shape[0])
    return df_ena_all_species_count


def get_ena_species_info(sample_dir):
    """ get_ena_species_info
          just the species tax_id and scientific name
          refactored so it using this from a probably already parsed in version
        __params__:
               passed_args:
                  sample_dir
        __return__:
            df_ena_species
    """
    ic()
    # infile = sample_dir + "ena_sample_species.txt"
    # df_ena_species = pd.read_csv(infile, sep = "\t")
    # ic(df_ena_species.head())
    df_ena_species = get_all_ena_detailed_sample_info(False)
    ic(df_ena_species.columns)
    df_ena_species = df_ena_species[["tax_id", "scientific_name"]]
    ic()
    return df_ena_species