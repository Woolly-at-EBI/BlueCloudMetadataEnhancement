"""Script of extra_comparisions.py is to


___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-03-07
__docformat___ = 'reStructuredText'

"""
import numpy as np
from icecream import ic

import matplotlib.pyplot as plt
import pandas as pd
from ena_samples import *
from categorise_environment import process_environment_biome
from project_utils import *

import argparse

def merged_plots(df):
    ic()
    # ic| df_all_merged.sample(n=20):               accession        lat         lon combined_location_designation
    # coords ena_country ena_region eez_category longhurst_category         IHO_category sea_category
    # eez_iho_intersect_category land_category                         worldAdmin_category feow_category ena_category
    # sea_total  land_total location_designation_marine location_designation_terrestrial location_designation_other
    # location_designation
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    ic(df.head())

    cats = ["longhurst_category", "IHO_category", "eez_iho_intersect_category", "sea_category", "land_category",\
            "worldAdmin_category", "feow_category", "ena_category", "sea_total","land_total"]

    df_combined = pd.DataFrame()
    fori=0
    for cat in cats:
        ic(cat)
        df_groupby = df.groupby(["combined_location_designation", cat]).size().to_frame('count').reset_index()
        #ic(df_groupby)
        color = "combined_location_designation"
        other_params = {}
        title = cat + " " + color
        format = "png"
        out_graph_file = plot_dir + cat + "_" + color + "." + format
        log_y = False
        width = 1500
        #u_plot_hist(df, cat, color, title, log_y, out_graph_file, width, format, other_params)
        df_tmp = df
        #ic(df_tmp.head())
        df_tmp.loc[df_tmp[cat] == 0, cat] = np.NaN

        df_tmp[cat] = True

        df_tmp = df_tmp[~df_tmp[cat].isna()]

        #df_tmp.loc[len(df_tmp[cat]) > 1, "hit_found"] = 1

        df_groupby = df_tmp.groupby(["combined_location_designation", cat]).size().to_frame('count').reset_index()
        ic("final-",df_groupby)
        # type = "percent"
        # out_graph_file = plot_dir + cat + "_" + color + "pie" + type +  "." + format
        # u_plot_pie(df_groupby, "combined_location_designation", 'count', title, type, out_graph_file)
        #
        # type = "value"
        # out_graph_file = plot_dir + cat + "_" + color + "pie" + type + "." + format
        # u_plot_pie(df_groupby, "combined_location_designation", 'count', title, type, out_graph_file)

        df_groupby = df_groupby.drop(cat, axis=1)
        df_groupby = df_groupby.rename(columns = {"count": cat})
        df_groupby = df_groupby[df_groupby[cat].notna()]
        if fori == 0:
            df_combined = df_groupby
        else:
            df_combined = pd.merge(df_combined, df_groupby, on = ["combined_location_designation"])


        fori += 1
        ic(df_combined)
        




def merge_comb_calls_plus_cat_dfs():
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

    return df_all_merged


def main():
    df = merge_comb_calls_plus_cat_dfs()
    merged_plots(df)

if __name__ == '__main__':
    ic()
    main()


