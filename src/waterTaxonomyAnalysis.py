"""Script of waterTaxonomyAnalysis.py is to


___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2022-12-21
__docformat___ = 'reStructuredText'

"""
import pandas as pd
from icecream import ic

import matplotlib.pyplot as plt

import argparse

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

def getTaxonomyInfo():
    """ eg
    desg
        __params__:

        __returns__:
                
    """
    ic()
    taxonomy_dir = "/Users/woollard/projects/bluecloud/data/taxonomy/"
    metagenomes_file = taxonomy_dir + "NCBI-metagenomes-to-environment.csv"
    df_metag_tax = pd.read_csv(metagenomes_file)
    ic(df_metag_tax.head(10))

    taxa_env_file = taxonomy_dir + "NCBI-taxa-to-environment.csv"
    df_tax2env = pd.read_csv(taxa_env_file)
    ic(df_tax2env.head(10))
   
    return


def main(passed_args):
    """ main
        __params__:
               passed_args
    """
    ic()
    getTaxonomyInfo()

    
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
