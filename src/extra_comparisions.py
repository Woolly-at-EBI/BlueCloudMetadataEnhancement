"""Script of extra_comparisions.py is to


___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-03-07
__docformat___ = 'reStructuredText'

"""
import numpy as np
from icecream import ic

import matplotlib.pyplot as plt
from collections import Counter
from matplotlib_venn import venn2, venn3, venn3_unweighted

import plotly.graph_objects as go
import pandas as pd
from ena_samples import *
from categorise_environment import process_environment_biome
from project_utils import *
import sys
import argparse

def plot_venn(my_sets, designation, title):
    """

    :param my_sets:
    :return:
    """
    ic()
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    cats = ["longhurst_category","eez_iho_intersect_category", "sea_category"]
    le_overlap = my_sets["longhurst_category"] & my_sets["eez_iho_intersect_category"]
    ls_overlap = my_sets["longhurst_category"] & my_sets["sea_category"]
    es_overlap = my_sets["eez_iho_intersect_category"] & my_sets["sea_category"]
    les_overlap = my_sets["longhurst_category"] & my_sets["eez_iho_intersect_category"] & my_sets["sea_category"]
    l_rest = my_sets["longhurst_category"] - le_overlap - ls_overlap
    e_rest = my_sets["eez_iho_intersect_category"] - le_overlap - es_overlap
    s_rest = my_sets["sea_category"] - es_overlap - ls_overlap
    le_only = le_overlap - les_overlap
    ls_only = ls_overlap - les_overlap
    es_only = es_overlap - les_overlap

    sets = Counter()  # set order A, B, C
    sets['100'] = len(l_rest)  # 100 denotes A on, B off, C off
    sets['010'] = len(e_rest)      #010 denotes A off, B on, C off
    sets['001'] = len(s_rest)  # 001 denotes A off, B off, C on
    sets['110'] = len(le_only)     #110 denotes A on, B on, C off
    sets['101'] = len(ls_only)  # 101 denotes A on, B off, C on
    sets['011'] = len(es_only)     #011 denotes A off, B on, C on
    sets['111'] = len(les_overlap) #011 denotes A on, B on, C on
    labels = ("Longhurst", "EEZ_IHO", 'Sea')
    plt.figure(figsize = (7, 7))
    plt.title(title)
    ax = plt.gca()
    #venn3(subsets = sets, set_labels = labels, ax = ax, set_colors = ('darkviolet', 'deepskyblue', 'blue'), alpha = 0.7)
    venn3_unweighted(subsets = sets, set_labels = labels, ax = ax, set_colors = ('darkviolet', 'deepskyblue', 'blue'),
                    alpha=0.5)

    plt.interactive(False)
    out_graph_file = plot_dir + "merged_all_category_counts_" +  designation + "_venn.png"
    ic(out_graph_file)
    plt.savefig(out_graph_file)
    plt.show()

def get_sets(cats, df_passed, list_wants):
    """

    :param cats:
    :param df:
    :return:
    """
    ic()
    df_combined = pd.DataFrame()

    fori = 0
    my_sets = {}
    ic(df_passed.head())

    ic(cats)

    for cat in cats:
        ic(cat)
        df_tmp = df_passed.copy()
        df_groupby = df_passed.groupby(["combined_location_designation", cat]).size().to_frame('count').reset_index()
        ic(df_tmp.head())

        # ic(df_tmp.head())
        designations = df_tmp["combined_location_designation"].unique()
        for designation in designations:
            if designation not in list_wants:
                df_tmp.loc[df_tmp["combined_location_designation"] == designation, cat] = np.NaN
                ic(f"removing {designation}")
        df_tmp.loc[df_tmp[cat] == 0, cat] = np.NaN
        df_tmp = df_tmp[~df_tmp[cat].isna()]
        df_tmp[cat] = True

        df_groupby = df_tmp.groupby(["combined_location_designation", cat]).size().to_frame('count').reset_index()

        df_groupby = df_groupby.drop(cat, axis = 1)
        df_groupby = df_groupby.rename(columns = {"count": cat})
        df_groupby = df_groupby[df_groupby[cat].notna()]

        if fori == 0:
            df_combined = df_groupby
        else:
            df_combined = pd.merge(df_combined, df_groupby, on = ["combined_location_designation"])

        my_sets[cat] = set(df_tmp['accession'])
        ic(len(my_sets[cat]))
        fori += 1
        if fori >= 4:
            break

    return my_sets, df_combined


def merged_plots(df_start):
    ic()
    # ic| df_all_merged.sample(n=20):               accession        lat         lon combined_location_designation
    # coords ena_country ena_region eez_category longhurst_category         IHO_category sea_category
    # eez_iho_intersect_category land_category                         worldAdmin_category feow_category ena_category
    # sea_total  land_total location_designation_marine location_designation_terrestrial location_designation_other
    # location_designation
    ic()
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()

    ic(df_start.head())

    cats = ["longhurst_category", "IHO_category", "eez_iho_intersect_category", "sea_category", "sea_total", "land_category",\
            "worldAdmin_category", "feow_category", "land_total"]

    cats = ["sea_category", "longhurst_category", "eez_iho_intersect_category", "sea_total", "feow_category"]

    format = 'png'
    #for designation in ["marine", "marine_and_terrestrial"]:
    ic(df_start["combined_location_designation"].value_counts())

    for designation in ["marine_and_terrestrial", "terrestrial", "marine"]:
        df = df_start.copy()
        ic(designation)
        ic(df.columns)
        total = df["combined_location_designation"].value_counts()[designation]
        ic(total)
        (my_sets, df_combined) = get_sets(cats, df, [designation])
        df_combined = df_combined.set_index("combined_location_designation")
        ic(df_combined)
        df_tr = df_combined.transpose().reset_index().rename(columns={"index": "category"})
        out_graph_file = plot_dir + "merged_all_category_counts_" + designation + "_hist." + format
        ic(out_graph_file)
        fig = px.histogram(df_tr, x = "category", y=designation, color_discrete_sequence=["blue"])
        plotly.io.write_image(fig, out_graph_file, format = format)

        ic(my_sets.keys())
        title = "samples with " + designation + " (total=" + f"{total}" + " ) combined_location_designation"
        plot_venn(my_sets, designation, title)


    # for cat in cats:
    #     ic(cat)
    #     df_tmp = df[df[cat] == True]
    #     my_sets[cat] = set(df_tmp['accession'])
    #     ic(len(my_sets[cat]))



    sys.exit()








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


