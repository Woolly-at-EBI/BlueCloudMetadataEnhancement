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
   
    return (df_metag_tax, df_tax2env)

def get_ena_detailed_sample_info(sample_dir):
    """ get_ena_detailed_sample_info
        __params__:
               passed_args:
                  sample_dir
        __return__:
            df_ena_sample_detail
    """
    ic()
    infile = sample_dir + "sample_much_lat_filtered.tsv"
    df_ena_sample_detail = pd.read_csv(infile, sep = "\t", nrows=100000000)
    ic(df_ena_sample_detail.head())

    return df_ena_sample_detail

def taxa_with_ena_coords(df_ena_sample_detail, df_metag_tax, df_tax2env, analysis_dir):
    """ taxa_with_ena_coords
    NCBI Taxa from samples that have at least 1 coordinate at ENA.

    For each taxon, please inform the following fields:

    NCBI taxID
    #samples in sea, sea & land, land
    #of associated runs in sea, sea & land, land (if possible, to assess relevance/importance)


        __params__:
               passed_args
               df_ena_sample_detail, df_metag_tax, df_tax2env
        __return__:
    """
    ic(len(df_ena_sample_detail))
    df_merged_ena_metag_tax = pd.merge(df_ena_sample_detail, df_metag_tax, how='inner',left_on=['tax_id'],
                                right_on=['NCBI:taxid'])
    ic(df_merged_ena_metag_tax.head())
    ic(len(df_merged_ena_metag_tax))

    df_tax2env = df_tax2env.rename({'NCBI taxID': "NCBI:taxid", "NCBI taxID Name": "NCBI term"})
    df_merged_ena_tax2env = pd.merge(df_ena_sample_detail, df_metag_tax, how='inner',left_on=['tax_id'],
                                right_on=['NCBI:taxid'])
    ic(df_merged_ena_tax2env.head())
    ic(len(df_merged_ena_tax2env))

    """ metag get counts of sample rows by NCBI taxid"""
    out_file = analysis_dir + 'tax_metag_sample_counts.tsv'
    df2 = df_merged_ena_metag_tax[["NCBI:taxid", "accession", "NCBI term"]]
    df3 = df2.groupby(["NCBI:taxid", "NCBI term"]).size().to_frame('count')
    ic(df3.head(2))
    ic(out_file)
    df3.to_csv(out_file, sep = '\t')

    out_file = analysis_dir + 'tax_metag_lat_lon_counts.tsv'
    df2 = df_merged_ena_metag_tax[["NCBI:taxid",  "NCBI term", 'lat', 'lon']].drop_duplicates()
    ic(df2.head(2))
    df3 = df2.groupby(["NCBI:taxid", "NCBI term"]).size().to_frame('count')
    ic(df3.head(2))
    ic(out_file)
    df3.to_csv(out_file, sep = '\t')

    """ tax2env get counts of sample rows by NCBI taxid"""
    out_file = analysis_dir + 'tax2env_sample_counts.tsv'
    df2 = df_merged_ena_tax2env[["NCBI:taxid", "accession", "NCBI term"]]
    df3 = df2.groupby(["NCBI:taxid", "NCBI term"]).size().to_frame('count')
    ic(df3.head(2))
    ic(out_file)
    df3.to_csv(out_file, sep = '\t')

    out_file = analysis_dir + 'tax2env__lat_lon_counts.tsv'
    df2 = df_merged_ena_tax2env[["NCBI:taxid",  "NCBI term", 'lat', 'lon']].drop_duplicates()
    ic(df2.head(2))
    df3 = df2.groupby(["NCBI:taxid", "NCBI term"]).size().to_frame('count')
    ic(df3.head(2))
    ic(out_file)
    df3.to_csv(out_file, sep = '\t')

    return


def main(passed_args):
    """ main
        __params__:
               passed_args
    """
    ic()
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir,  taxonomy_dir) = get_directory_paths()
    ic(taxonomy_dir)

    df_ena_sample_detail = get_ena_detailed_sample_info(sample_dir)
    df_ena_sample_detail = df_ena_sample_detail.drop(columns=['altitude', 'elevation', 'checklist', 'collection_date',
            'collection_date_submitted', 'country', 'taxonomic_classification', 'salinity', 'depth',
            'environment_biome', 'environment_feature'])

    (df_metag_tax, df_tax2env) = getTaxonomyInfo(taxonomy_dir)
    merged_all_categories_file = analysis_dir + "merged_all_categories.tsv"
    df_merged_all_categories = pd.read_csv(merged_all_categories_file, sep = "\t")
    ic(df_merged_all_categories.head(3))

    taxa_with_ena_coords(df_ena_sample_detail, df_metag_tax, df_tax2env,analysis_dir)


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
