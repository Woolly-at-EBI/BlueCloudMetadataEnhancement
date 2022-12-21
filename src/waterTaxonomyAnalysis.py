"""Script of waterTaxonomyAnalysis.py is to


___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2022-12-21
__docformat___ = 'reStructuredText'

"""
from get_directory_paths import get_directory_paths
import pandas as pd
from icecream import ic

import matplotlib.pyplot as plt

import argparse

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

def getTaxonomyInfo(taxonomy_dir):
    """ getTaxonomyInfo
     read in the relevant marine taxonomic terms.
    These cam from Stephane Pesant
        __params__:
             taxonomy_dir
        __returns__:
                df_metag_tax, df_tax2env
    """
    ic()

    metagenomes_file = taxonomy_dir + "NCBI-metagenomes-to-environment.csv"
    df_metag_tax = pd.read_csv(metagenomes_file)
    ic(df_metag_tax.head(10))

    taxa_env_file = taxonomy_dir  + "NCBI-taxa-to-environment.csv"
    df_tax2env = pd.read_csv(taxa_env_file)
    ic(df_tax2env.head(10))
   
    return (taxonomy_dir, df_metag_tax, df_tax2env)


def main(passed_args):
    """ main
        __params__:
               passed_args
    """
    ic()
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir,  taxonomy_dir) = get_directory_paths()
    ic(taxonomy_dir)

    (taxonomy_dir, df_metag_tax, df_tax2env) = getTaxonomyInfo(taxonomy_dir)
    merged_all_categories_file = analysis_dir + "merged_all_categories.tsv"
    df_merged_all_categories = pd.read_csv(merged_all_categories_file, sep = "\t")
    ic(df_merged_all_categories.head(3))
    return ()


if __name__ == '__main__':
    ic()
    # Read arguments from command line
    prog_des = "Script to get the marine zone classification for a set of longitude and latitude coordinates"
    parser = argparse.ArgumentParser(description = prog_des)

    # Adding optional argument, n.b. in debugging mode in IDE, had to turn required to false.
    parser.add_argument("-v", "--verbosity", type = int, help = "increase output verbosity", required = False)
    parser.add_argument("-o", "--outfile", help = "Output file", required = False)

    parser.parse_args()
    args = parser.parse_args()
    ic(args)
    print(args)
    if args.verbosity:
        print("verbosity turned on")


    main(args)
