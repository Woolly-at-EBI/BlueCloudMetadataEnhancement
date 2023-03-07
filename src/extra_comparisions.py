"""Script of extra_comparisions.py is to


___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-03-07
__docformat___ = 'reStructuredText'

"""


from icecream import ic

import matplotlib.pyplot as plt
import pandas as pd
from ena_samples import *
from categorise_environment import process_environment_biome
from project_utils import *

import argparse

def first_func():
    """"""
    ic()
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    #cut -f 3,6,7,45 merge_combined_tax_all_with_confidence_complete.tsv | awk '{if ($4) print $0;}'   > acc_combined_acc.tsv
    combined_dom_file = analysis_dir + "acc_combined_acc.tsv"
    df_combined_dom = pd.read_csv(combined_dom_file, sep = "\t")
    ic(df_combined_dom.head())
    ic(df_combined_dom.shape)

    merged_cats_file = analysis_dir + "merged_all_categories.tsv"
    df_merged_cats = pd.read_csv(merged_cats_file, sep = "\t")
    ic(df_merged_cats.head())
    df_merged_cats = df_merged_cats.loc[:, ~df_merged_cats.columns.str.contains('^Unnamed')]
    df_merged_cats = df_merged_cats.drop_duplicates()
    ic(df_merged_cats.head())
    ic(df_merged_cats.head())

    df_all_merged = pd.merge(df_combined_dom,df_merged_cats, on=["lat", "lon"], how = "left")
    ic(df_all_merged.sample(n=20))
    ic(df_all_merged.shape)

    return


def main():
    first_func()

if __name__ == '__main__':
    ic()
    main()


