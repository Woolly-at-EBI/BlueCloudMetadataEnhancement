"""Script of waterTaxonomyAnalysis.py is to take the taxonomy environment assignments
   and combine them with the output from analyseHits.py
   to allow one to get analysis of what is marine or terrestrial/freshwater from different methods

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2022-12-21
__docformat___ = 'reStructuredText'

"""
from get_directory_paths import get_directory_paths
import pandas as pd
from icecream import ic

import plotly.express as px
import plotly

import argparse
import warnings
import numpy as np

import matplotlib.pyplot as plt
from wordcloud import WordCloud

# from matplotlib_venn import venn2

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def get_taxonomy_info(taxonomy_dir):
    """ get_taxonomy_info
     read in the relevant marine taxonomic terms.
    These came from Stephane Pesant
        __params__:
             taxonomy_dir
        __returns__:
                df_metag_tax, df_tax2env
    """
    ic()

    metagenomes_file: str = taxonomy_dir + "NCBI-metagenomes-to-environment.csv"
    df_metag_tax = pd.read_csv(metagenomes_file)
    df_metag_tax = clean_up_df_metag_tax(df_metag_tax)
    ic(df_metag_tax.head(10))

    taxa_env_file = taxonomy_dir + "NCBI-taxa-to-environment.csv"
    df_tax2env = pd.read_csv(taxa_env_file)
    df_tax2env = clean_up_df_tax2env(df_tax2env)
    ic(df_tax2env.head(10))

    return df_metag_tax, df_tax2env


def get_ena_detailed_sample_info(sample_dir):
    """ get_ena_detailed_sample_info
        This is filtered for just those with lat anlons
        __params__:
               passed_args:
                  sample_dir
        __return__:
            df_ena_sample_detail
    """
    ic()
    infile = sample_dir + "sample_much_lat_filtered.tsv"
    df_ena_sample_detail = pd.read_csv(infile, sep = "\t", nrows = 1000000000)
    ic(df_ena_sample_detail.head())

    return df_ena_sample_detail

def get_ena_species_info(sample_dir):
    """ get_ena_species_info
          just the species tax_id and scientific name
        __params__:
               passed_args:
                  sample_dir
        __return__:
            df_ena_species
    """
    infile = sample_dir + "ena_sample_species.txt"
    df_ena_species = pd.read_csv(infile, sep = "\t")
    ic(df_ena_species.head())
    return df_ena_species

def clean_up_df_metag_tax(df):
    """ clean_up_df_metag_tax
        mapping 1's to True and 0's to False

        __params__:
               passed_args: df

        __return__: df
        """
    # N.B. changed all NaN's to 0. Mapping 1's to True and 0's to False
    warnings.simplefilter('ignore')
    df["marine (ocean connected)"] = df["marine (ocean connected)"].replace(np.nan, 0).astype(bool)
    df["freshwater (land enclosed)"] = df["freshwater (land enclosed)"].replace(np.nan, 0).astype(bool)
    df["taxonomic_source"] = 'metagenome'
    warnings.resetwarnings()

    return df


def clean_up_df_tax2env(df):
    """ clean_up_df_tax2env
       For NCBI-to-terrestrial.1 NCBI-to-marine.1" columns apping 1's to True and 0's to False
       make the key column names  the same as the metag one
       N.B. also ensures that every row has at least one true water species (marine or terrestrial freshwate)

        __params__:
               passed_args: df_tax2env

        __return__: df_tax2env

    """
    # N.B. changed all NaN's to 0. Mapping 1's to True and 0's to False
    warnings.simplefilter('ignore')
    df["NCBI-to-terrestrial.1"] = df["NCBI-to-terrestrial.1"].replace(np.nan, 0).astype(bool)
    df["NCBI-to-marine.1"] = df["NCBI-to-marine.1"].replace(np.nan, 0).astype(bool)
    warnings.resetwarnings()

    # get all those where it is water based and marine inclusive OR  terrestrial
    df = df.loc[(df["NCBI-to-marine.1"] | df["NCBI-to-terrestrial.1"])]

    # make the key column names  the same as the metag one
    df = df.rename(columns = {'NCBI taxID': "NCBI:taxid", "NCBI taxID Name": "NCBI term"})

    # also copy these to increase compatability with further key columns
    df["marine (ocean connected)"] = df["NCBI-to-marine.1"]
    df["freshwater (land enclosed)"] = df["NCBI-to-terrestrial.1"]
    df["taxonomic_source"] = 'environment'

    return df


def analyse_all_ena_all_tax2env(plot_dir, stats_dict, df_all_ena_sample_detail, df_tax2env):
    """ analyse_all_ena_all_tax2env
           analyse the taxonomy WRT the GPS coordinates
        __params__:
               passed_args: plot_dir,df_all_ena_sample_detail, df_tax2env

        __return__: stats_dict, df_merged

    """

    ic()
    ic(plot_dir)
    ic(df_all_ena_sample_detail.shape[0])
    ic(df_tax2env.shape[0])

    df_tax2env = df_tax2env.rename(columns = {'NCBI taxID': "NCBI:taxid", "NCBI taxID Name": "NCBI term"})
    ic(df_tax2env.head())
    df_merged_ena_tax2env = pd.merge(df_all_ena_sample_detail, df_tax2env, how = 'inner', left_on = ['tax_id'],
                                     right_on = ['NCBI:taxid'])

    stats_dict["env_tax_ids_in_ena_count"] = df_merged_ena_tax2env["NCBI:taxid"].nunique()
    stats_dict["env_tax_not_in_ena_count"] = stats_dict["_input_env_tax_id_count"] - stats_dict[
        "env_tax_ids_in_ena_count"]
    stats_dict["env_tax_in_ena_sample_count"] = df_merged_ena_tax2env.shape[0]

    print(f"total ENA samples={len(df_all_ena_sample_detail)}")
    print(f"total Taxonomic entries={len(df_tax2env)}")

    samples_with_marine_tax = stats_dict["env_tax_in_ena_sample_count"]
    samples_without_marine_tax = df_all_ena_sample_detail.shape[0] - samples_with_marine_tax
    print(
        f"total ENA samples with a marine or freshwater tax_id={samples_with_marine_tax} "
        f"percentage= {(samples_with_marine_tax * 100) / len(df_all_ena_sample_detail):.2f} %")
    print(
        f"total ENA samples without a marine or freshwater tax_id={samples_without_marine_tax} "
        f"percentage= {(samples_without_marine_tax * 100) / len(df_all_ena_sample_detail):.2f} %")

    # reduce the columns dowm to make it easier to debug (not reused elsewere_
    df = df_merged_ena_tax2env[
        ["accession", "NCBI-to-marine.1", "NCBI-to-terrestrial.1", "NCBI:taxid", "NCBI taxID Type", "NCBI taxID rank",
         "NCBI term"]]

    # ic(df.head())
    ic(df["NCBI-to-terrestrial.1"].value_counts())
    ic(df["NCBI-to-marine.1"].value_counts())
    both_true_total = len(df.loc[(df["NCBI-to-marine.1"] & df["NCBI-to-terrestrial.1"])])
    print(f"NCBI-to-marine.1 and NCBI-to-terrestrial.1 ={both_true_total}")
    just_marine_true_total = len(df.loc[(df["NCBI-to-marine.1"] & ~df["NCBI-to-terrestrial.1"])])
    print(f"NCBI-to-marine.1 and not NCBI-to-terrestrial.1 ={just_marine_true_total}")
    just_terr_true_total = len(df.loc[(~df["NCBI-to-marine.1"] & df["NCBI-to-terrestrial.1"])])
    print(f"not NCBI-to-marine.1 and  NCBI-to-terrestrial.1 ={just_terr_true_total}")
    non_true_total = len(df.loc[(~df["NCBI-to-marine.1"] & ~df["NCBI-to-terrestrial.1"])])
    print(f"not NCBI-to-marine.1 and not NCBI-to-terrestrial.1 ={non_true_total}")

    non_true = df.loc[(~df["NCBI-to-marine.1"] & ~df["NCBI-to-terrestrial.1"])]
    ic(non_true.head())

    # stats_dict = metag_taxa_with_ena_coords(stats_dict, df_ena_sample_detail, df_merged_ena_tax2env, analysis_dir):

    # Use the venn2 function
    # ic("plotting as venn")
    # # venn2(subsets = (10, 5, 2), set_labels = ('Group A', 'Group B'))
    # venn2(subsets = (just_terr_true_total, both_true_total, just_terr_true_total),
    # set_labels = ('Marine', 'Terrestrial'))
    # plt.title("ENA marine and terrestrial water taxon counts")
    # plt.show()
    # plotfile=plot_dir + 'ENA_marine_terristrial_water_tax_counts.pdf'
    # ic(plotfile)
    # plt.savefig(plotfile)

    return stats_dict, df


def get_all_ena_detailed_sample_info(sample_dir):
    """ get_all_ena_detailed_sample_info
         This is using ALL ENA samples whether they have GPS coordinates (lat lons) or not.
         It contains many, but not all columns of sample metadata
        __params__:
               passed_args:
                  sample_dir
        __return__:
            df_all_ena_sample_detail
    """

    infile = sample_dir + "sample_much_raw.tsv"
    ic(infile)
    # df = pd.read_csv(infile, sep = "\t", nrows = 100000)
    df = pd.read_csv(infile, sep = "\t")
    ic(df.head())

    return df


def taxa_notin_ena_coords(df_ena_sample_detail, df_metag_tax, df_tax2env, analysis_dir):
    """ taxa_notin_ena_coords  - DEPRECATED
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
    ic(df_tax2env.head(1))
    df_metag_not_in_ena_latlon = df_metag_tax[~df_metag_tax['NCBI:taxid'].isin(df_ena_sample_detail['tax_id'])]
    ic(df_metag_not_in_ena_latlon.head(10))
    ic(len(df_metag_tax))
    ic(len(df_metag_not_in_ena_latlon))
    out_file = analysis_dir + 'tax_metag_notin_ena_latlon.tsv'
    ic(out_file)
    df_metag_not_in_ena_latlon.to_csv(out_file, sep = '\t')

    df_metag_is_in_ena_latlon = df_metag_tax[df_metag_tax['NCBI:taxid'].isin(df_ena_sample_detail['tax_id'])]
    ic(df_metag_is_in_ena_latlon.head(2))
    ic(len(df_metag_tax))
    ic(len(df_metag_is_in_ena_latlon))
    out_file = analysis_dir + 'tax_metag_is_in_ena_latlon.tsv'
    ic(out_file)
    df_metag_is_in_ena_latlon.to_csv(out_file, sep = '\t')

    # how many runs are for these samples
    sample_acc = ["SAMN18146923", "SAMN18146924", "SAMN18146925", "SAMN18146926", "SAMN18146927", "SAMN18146928",
                  "SAMN18146929", "SAMN18146930", "SAMN18146931", "SAMN18146932", "SAMN18146933", "SAMN18146934",
                  "SAMN18146935", "SAMN18146936", "SAMN18146937", "SAMN18146938", "SAMN18146939", "SAMN18146940",
                  "SAMN18146941", "SAMN18146942", "SAMN18146943", "SAMN18146944", "SAMN18146945", "SAMN18146946",
                  "SAMN18146947", "SAMN18146948", "SAMN18146949", "SAMN18146950", "SAMN18146951", "SAMN18146952",
                  "SAMN18146953", "SAMN18146954", "SAMN18146955", "SAMN18146956", "SAMN18146957", "SAMN18146958",
                  "SAMN18146959", "SAMN18146960", "SAMN18146961", "SAMN18146962", "SAMN18146963", "SAMN18146964",
                  "SAMN18146965", "SAMN18146966", "SAMN18146967", "SAMN18146968", "SAMN18146969", "SAMN18146970",
                  "SAMN18146971", "SAMN18146972", "SAMN18146973", "SAMN18146974", "SAMN18146975", "SAMN18146976",
                  "SAMN21876556"]
    ic(len(sample_acc))

    return


def metag_taxa_with_ena_coords(stats_dict, df_ena_sample_detail, df_metag_tax, analysis_dir):
    """ taxa_with_ena_coords
    NCBI Taxa from samples that have at least 1 coordinate at ENA.
    Only implemented with metagenomes!

    For each taxon, please inform the following fields:

    NCBI taxID
    #samples in sea, sea & land, land
    #of associated runs in sea, sea & land, land (if possible, to assess relevance/importance)

        __params__:
               passed_args
               stats_dict
               df_ena_sample_detail,
                df_metag_tax,
        __return__:
          stats_dict, df_merged_ena_metag_tax
    """
    ic()
    ic(analysis_dir)
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()

    # ic(df_metag_tax.head())
    # ic(df_ena_sample_detail.head())
    # ic(df_ena_sample_detail.shape[0])
    df_merged_ena_metag_tax = pd.merge(df_ena_sample_detail, df_metag_tax, how = 'inner', left_on = ['tax_id'],
                                       right_on = ['NCBI:taxid'])
    # ic(df_merged_ena_metag_tax.head(5))
    # ic(df_merged_ena_metag_tax.shape[0])

    # how many taxonomies did we and did not find? (in all not just GPS)
    stats_dict["metag_tax_ids_in_ena_count"] = df_merged_ena_metag_tax["NCBI:taxid"].nunique()
    stats_dict["metag_tax_in_ena_sample_count"] = df_merged_ena_metag_tax.shape[0]
    stats_dict["metag_tax_not_in_ena_count"] = stats_dict["_input_metag_tax_id_count"] - stats_dict[
        "metag_tax_ids_in_ena_count"]

    """ metag get counts of sample rows by NCBI taxid" for simple plotting """
    ic(" metag get counts of sample rows by NCBI taxid")
    out_file = analysis_dir + 'tax_metag_sample_counts.tsv'
    # df2 = df_merged_ena_metag_tax[["NCBI:taxid", "accession", "NCBI term", "marine (ocean connected)",
    # "freshwater (land enclosed)"]]
    df3 = df_merged_ena_metag_tax.groupby(
        ["NCBI:taxid", "NCBI term", "NCBI metagenome category", "marine (ocean connected)",
         "freshwater (land enclosed)"]).size().to_frame('count').reset_index()
    ic(df3.head(2))
    ic(out_file)
    df3.to_csv(out_file, sep = '\t')
    ic(df3.head())

    out_file = analysis_dir + 'tax_metag_lat_lon_counts.tsv'
    df2 = df_merged_ena_metag_tax[["NCBI:taxid", "NCBI term", 'lat', 'lon']].drop_duplicates()
    ic(df2.head(2))
    df3 = df2.groupby(["NCBI:taxid", "NCBI term"]).size().to_frame('count')
    ic(df3.head(2))
    ic(out_file)
    df3.to_csv(out_file, sep = '\t')

    """ want to get samples in sea, sea & land, land"""
    ic(df_merged_ena_metag_tax.head(2))
    # this file comes from analyseHits.py
    merged_all_categories_file = analysis_dir + "merged_all_categories.tsv"
    df_merged_all_categories = pd.read_csv(merged_all_categories_file, sep = "\t")

    ic(df_merged_all_categories.head(2))
    df_mega = pd.merge(df_merged_ena_metag_tax, df_merged_all_categories, how = 'inner', left_on = ['lat', 'lon'],
                       right_on = ['lat', 'lon'])
    ic(df_mega.head(2))
    ic(df_mega.columns)
    ic(df_mega.shape[0])
    out_file = analysis_dir + 'tax_metag_sample_land_sea_counts.tsv'
    df3 = df_mega.groupby(
        ["NCBI:taxid", "NCBI term", 'location_designation', "NCBI metagenome category", "marine (ocean connected)",
         "freshwater (land enclosed)"]).size().to_frame('count').reset_index()

    ic(df3.head())

    stats_dict["metag_tax_and_GPS_location_sample_count"] = df_mega.shape[0]
    stats_dict["metag_tax_andnot_GPS_location_sample_count"] = stats_dict['metag_tax_in_ena_sample_count'] - stats_dict[
        "metag_tax_and_GPS_location_sample_count"]

    ic(out_file)
    df3.to_csv(out_file, sep = '\t')
    # df_tax_metag_sample_land_sea_counts = df3

    # only commented out plotting whilst debugging
    # plotting_metag(plot_dir,df_tax_metag_sample_land_sea_counts )

    # """ tax2env get counts of sample rows by NCBI taxid"""
    # out_file = analysis_dir + 'tax2env_sample_counts.tsv'
    # df2 = df_merged_ena_tax2env[["NCBI:taxid", "accession", "NCBI term"]]
    # df3 = df2.groupby(["NCBI:taxid", "NCBI term"]).size().to_frame('count')
    # ic(df3.head(2))
    # ic(out_file)
    # df3.to_csv(out_file, sep = '\t')
    #
    # out_file = analysis_dir + 'tax2env__lat_lon_counts.tsv'
    # df2 = df_merged_ena_tax2env[["NCBI:taxid",  "NCBI term", 'lat', 'lon']].drop_duplicates()
    # ic(df2.head(2))
    # df3 = df2.groupby(["NCBI:taxid", "NCBI term"]).size().to_frame('count')
    # ic(df3.head(2))
    # ic(out_file)
    # df3.to_csv(out_file, sep = '\t')

    return stats_dict, df_merged_ena_metag_tax


def plotting_metag(plot_dir, df_merged_cats_metag_land_sea_counts):
    """ plotting_metag
        __params__:
               passed_args
               df_merged_cats_metag_land_sea_counts
    """
    ic()
    ic(df_merged_cats_metag_land_sea_counts.head())
    df = df_merged_cats_metag_land_sea_counts
    df['fraction'] = df['count'] / df.groupby(["NCBI:taxid"])['count'].transform('sum')
    ic()
    ic(df.head(5))

    ic(df.columns)
    title_string = "Marine and Aqua metagenome Counts in ENA having GPS coordinates"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_counts.pdf'
    color_value = 'location_designation'
    fig = px.histogram(df, x = "NCBI term", y = "count", color = color_value, title = title_string)
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    title_string = "Marine and Aqua metagenome log(Counts) in ENA having GPS coordinates"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_log_counts.pdf'
    color_value = 'location_designation'
    fig = px.histogram(df, x = "NCBI term", y = "count", log_y = True, color = color_value, title = title_string)
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    title_string = "Marine and Aqua metagenome counts in ENA having GPS coordinates - stacked"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_stacked_counts.pdf'
    color_value = 'location_designation'
    fig = px.bar(df, x = "NCBI term", y = "fraction", color = color_value, title = title_string, barmode = "stack")
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    """change the location_designation to a more sensible order """
    category_order = ['sea', 'sea and land', 'land']
    df["location_designation"] = pd.Categorical(df["location_designation"], category_order)
    df = df.sort_values(["location_designation", "fraction"], ascending = [True, False])
    ic(df.head(20))

    # title_string = "Marine and Aqua metagenome counts in ENA having GPS coordinates - stacked ordered"
    # out_graph_file = plot_dir + 'merged_cats_metag_land_sea_stacked_counts_ordered.pdf'
    # color_value = 'location_designation'
    # fig = px.bar(df, x = "NCBI term", y = "fraction", color = color_value, title = title_string, barmode = "stack")
    # ic(out_graph_file)

    """ creating a single column summary for the taxonomic geographic assignments"""

    def categorise_df(df):
        if df["marine (ocean connected)"] and df["freshwater (land enclosed)"]:
            return "tax:marine and freshwater"
        elif df["marine (ocean connected)"] and not df["freshwater (land enclosed)"]:
            return "tax:marine (ocean connected)"
        elif not df["marine (ocean connected)"] and df["freshwater (land enclosed)"]:
            return "tax:freshwater (land enclosed)"

    df["marine_freshwater_by_tax"] = df.apply(categorise_df, axis = 1)
    category_order = ['sea', 'sea and land', 'land']
    df["location_designation"] = pd.Categorical(df["location_designation"], category_order)
    df = df.sort_values(["location_designation", "fraction"], ascending = [True, False])

    ic(df.head(20))
    title_string = "Marine and Aqua metagenome sample counts in ENA having GPS coordinates + taxonomic categorisation" \
                   + "<br><sup>stacked and ordered by the GPS location_designations - " \
                   + "the taxonomic cat are in the patterns</sup>" \
                   + "<br><sup>the numbers are sample counts foreach of the GPS location_designations</sup>"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_tax_cat_stacked_counts_ordered.pdf'
    color_value = 'location_designation'
    fig = px.bar(df, x = "NCBI term", y = "fraction", color = color_value, title = title_string, barmode = "stack",
                 text = "count", pattern_shape = "marine_freshwater_by_tax")
    # fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    title_string = "Marine and Aqua metagenome sample counts in ENA having GPS coordinates + taxonomic categorisation" \
                   + "<br><sup>stacked and ordered by the GPS location_designations - " \
                   + "the taxonomic cat are in the patterns</sup>" \
                   + "<br><sup>the numbers are sample counts foreach of the GPS location_designations</sup>"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_tax_cat_stacked_counts_ordered_facet.pdf'
    color_value = 'location_designation'
    fig = px.bar(df, x = "NCBI term", y = "fraction", color = color_value, title = title_string, barmode = "stack",
                 text = "count", pattern_shape = "marine_freshwater_by_tax", facet_row = "NCBI metagenome category")
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    df = df.sort_values(["marine (ocean connected)", "freshwater (land enclosed)"])
    ic(df.head(20))
    title_string = "Marine and Aqua metagenome sample counts in ENA having GPS coordinates + taxonomic categorisation" \
                   + "<br><sup>stacked and ordered by the taxonomic geography</sup>" \
                   + "<br><sup>the numbers are sample counts foreach of the GPS location_designations </sup>"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_tax_cat_stacked_counts_ordered_by_tax_cat.pdf'
    color_value = 'location_designation'
    fig = px.bar(df, x = "NCBI term", y = "fraction", color = color_value, title = title_string, barmode = "stack",
                 text = "count", pattern_shape = "marine_freshwater_by_tax")
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_tax_cat_stacked_counts_ordered_by_tax_cat_facet.pdf'
    fig = px.bar(df, x = "NCBI term", y = "fraction", color = color_value, title = title_string, barmode = "stack",
                 text = "count", facet_row = "marine_freshwater_by_tax")
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    title_string = "Marine and Aqua metagenome sample counts in ENA having GPS coordinates + taxonomic categorisation" \
                   + "<br><sup>Is an overall (sunburst plot)</sup>"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_tax_cat_sunburst_LOOKATTHISONE.pdf'
    fig = px.sunburst(
        df,
        title = title_string,
        path = ['marine_freshwater_by_tax', 'location_designation', 'NCBI term'],
        values = 'count',
    )
    # fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_tax_cat_sunburst.html'
    ic(out_graph_file)
    fig.write_html(out_graph_file)

    title_string = "Marine and Aqua metagenome sample counts in ENA having GPS coordinates + taxonomic categorisation" \
                   + "<br><sup>Is an overall (sunburst plot)</sup>" \
                   + "<br><sup>Excluding the land/sea from GPS from plot</sup>"
    out_graph_file = plot_dir + 'merged_cats_metag_tax_cat_exclusive_sunburst.pdf'
    fig = px.sunburst(
        df,
        title = title_string,
        path = ['marine_freshwater_by_tax', 'NCBI term'],
        values = 'count',
    )
    # fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_tax_cat_exclusive_sunburst.html'
    ic(out_graph_file)
    fig.write_html(out_graph_file)


def analyse_all_ena_just_metag(plot_dir, analysis_dir, stats_dict, df_all_ena_sample_detail, df_metag_tax):
    """ analyse_all_ena_just_metag
        __params__: plot_dir, analysis_dir, stats_dict, df_all_ena_sample_detail, df_metag_tax
               passed_args
               stats_dict, df_merged_all_categories
    """
    ic()
    ic(plot_dir)
    df_ena_sample_detail = df_all_ena_sample_detail.drop(
        columns = ['altitude', 'elevation', 'checklist', 'collection_date',
                   'collection_date_submitted', 'country', 'taxonomic_classification', 'salinity', 'depth',
                   'environment_biome', 'environment_feature'])

    stats_dict, df_merged_all_categories = metag_taxa_with_ena_coords(stats_dict, df_ena_sample_detail, df_metag_tax,
                                                                      analysis_dir)
    # taxa_notin_ena_coords(df_ena_sample_detail, df_metag_tax, df_tax2env, analysis_dir)

    return stats_dict, df_merged_all_categories


def taxonomic_environment_assignment(df_mega):
    """ taxonomic_environment_assignment"""
    ic()
    # "marine (ocean connected)",
    # "freshwater (land enclosed)"

    conditions = [
         ((df_mega["marine (ocean connected)"]) & (df_mega["freshwater (land enclosed)"])),
         ((df_mega["marine (ocean connected)"]) & (df_mega["freshwater (land enclosed)"] == False)),
         ((df_mega["marine (ocean connected)"] == False) & (df_mega["freshwater (land enclosed)"])),
         ((df_mega["marine (ocean connected)"] == False) & (df_mega["freshwater (land enclosed)"] == False))
    ]

    values =["marine and freshwater", "marine (ocean connected)", "freshwater (land enclosed)", "undetermined"]
    df_mega['taxonomic_environment'] = np.select(conditions, values, default = "undetermined")
    ic(df_mega['taxonomic_environment'].value_counts())

    return df_mega


def investigate_gps_tax(df_mega, stats_dict):

    """ investigate_gps_tax
        __params__:
            passed_args
        stats_dict, df_merged_ena_combined_tax 
    """
    ic()
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()

    df_mega = df_mega[
        (df_mega["location_designation"] != "no_gps") | (df_mega["taxonomic_environment"] != "undetermined")]

    """ Want to investigate where sea from GPS but no marine species """
    df_sea_notax = df_mega.query("location_designation == 'sea' and taxonomic_environment == 'undetermined'")

    df_ena_species = get_ena_species_info(sample_dir)
    df_sea_notax = pd.merge(df_sea_notax, df_ena_species, how = 'inner', on = 'tax_id')
    ic(df_sea_notax.shape[0])
    ic(df_sea_notax.head())

    df = df_sea_notax.groupby(
        ["tax_id", 'scientific_name']).size().to_frame('count').reset_index().sort_values("count", ascending = False)
    ic(df.head(20))
    outfile = analysis_dir + 'sea_no-marine-tax_species_sample_count.tsv'
    ic(outfile)
    df.to_csv(outfile, sep = "\t")

    df_wordc = df_sea_notax["scientific_name"]
    title = "Species observed where: Sea (From GPS), but no-marine-tax-defined"
    my_wordc(df_wordc, title, plot_dir + 'Sea_no-marine-tax-defined-World_Cloud.png')

    return stats_dict

def my_wordc(df_wordc,title,outfile):
    """my_wordc
    providing a dataframe with just one column, it automatically generates counts.
    """
    plt.subplots(figsize = (8, 8))
    warnings.simplefilter('ignore')
    wordcloud = WordCloud(
        background_color = 'white',
        width = 512,
        height = 384
    ).generate(' '.join(df_wordc))
    warnings.resetwarnings()
    plt.imshow(wordcloud)  # image show
    plt.axis('off')  # to off the axis of x and y
    plt.title(title)
    ic(outfile)
    plt.savefig(outfile)
    plt.show()

def combine_analysis_all_tax(analysis_dir, plot_dir, stats_dict, df_all_ena_sample_detail, df_metag_tax, df_tax2env):
    """ combine_analysis_all_tax
        __params__:
               passed_args
               stats_dict, df_merged_ena_combined_tax
    """
    ic()
    ic(df_metag_tax.shape[0])
    ic(df_tax2env.shape[0])
    df = pd.concat([df_metag_tax, df_tax2env])
    ic(df.shape[0])
    ic(df.head())

    # doing a left join, so all ENA samples represented.
    df_merged_ena_combined_tax = pd.merge(df_all_ena_sample_detail, df, how = 'left', left_on = ['tax_id'],
                                          right_on = ['NCBI:taxid'])
    ic(df_merged_ena_combined_tax.head(5))
    ic(df_merged_ena_combined_tax.shape[0])
    df = df_merged_ena_combined_tax

    stats_dict["_global_total_samples_with_gps"] = df["lat"].count()
    stats_dict["_global_total_samples_with_watertax"] = df["NCBI:taxid"].count()
    stats_dict["_global_total_samples_with_watertax_and_gps"] = 0
    """ comparing a column to itself gets rid of NaN"""
    df["NCBI_taxid"] = df["NCBI:taxid"]
    df_tmp = df.query('lat == lat')
    ic(df_tmp.shape[0])
    df_tmp = df_tmp.query('NCBI_taxid == NCBI_taxid')
    ic(df_tmp.shape[0])
    stats_dict["_global_total_samples_with_watertax_and_gps"] = df_tmp.shape[0]

    merged_all_categories_file = analysis_dir + "merged_all_categories.tsv"
    df_merged_all_categories = pd.read_csv(merged_all_categories_file, sep = "\t")

    ic(df_merged_all_categories.head(2))
    ic(df_merged_all_categories.shape[0])
    ic(df_merged_ena_combined_tax.shape[0])
    df_mega = pd.merge(df_merged_ena_combined_tax, df_merged_all_categories, how = 'left', left_on = ['lat', 'lon'],
                       right_on = ['lat', 'lon'])

    df_mega["location_designation"] = df_mega["location_designation"].fillna("no_gps")
    df_mega["NCBI:taxid"] = df_mega["NCBI:taxid"].fillna("undetermined")
    df_mega["NCBI term"] = df_mega["NCBI term"].fillna("undetermined")

    # "marine (ocean connected)",
    # "freshwater (land enclosed)
    df_mega = taxonomic_environment_assignment(df_mega)
    ic(df_mega["location_designation"].value_counts())
    ic(df_mega.head())
    ic(df_mega.shape[0])
    out_file = analysis_dir + "all_ena_gps_tax_combined.tsv"
    ic(out_file)
    df_mega.to_csv(out_file, sep = '\t')

    stats_dict = plot_combined_analysis(plot_dir, df_mega, stats_dict)
    investigate_gps_tax(df_mega,stats_dict)

    return stats_dict, df_mega

def plot_combined_analysis(plot_dir,df_mega, stats_dict):
    """plot_combined_analysis

    """
    """rm the rows where no_gps AND taxonomic_environment is no undetermined - reduce clutter"""
    #df_mega = df_mega[(df_mega["location_designation"] != "no_gps")]
    df_mega = df_mega[(df_mega["location_designation"] != "no_gps") | (df_mega["taxonomic_environment"] != "undetermined")]

    df3 = df_mega.groupby(
        ["NCBI:taxid", "NCBI term", 'location_designation',
         "taxonomic_environment"]).size().to_frame('count').reset_index()
    ic(df3.shape[0])
    ic(df3.head())
    ic(stats_dict)

    """Plotting start"""
    title_string = "All ENA - incorporates Marine and Aqua metagenome, GPS coordinates + taxonomic categorisation" \
                   + "<br><sup>Is an overall (sunburst plot)</sup>" \
                   + "<br><sup>This should be all of ENA samples!</sup>"
    out_graph_file = plot_dir + 'all_ena_gps_tax_combined_sunburst.html'
    fig = px.sunburst(
        df3,
        title = title_string,
        path = ['location_designation', 'taxonomic_environment', 'NCBI term'],
        values = 'count',
    )
    # fig.show()
    ic(out_graph_file)
    fig.write_html(out_graph_file)
    out_graph_file = plot_dir + 'all_ena_gps_tax_combined_sunburst.pdf'
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')
    """Plotting end"""

    return stats_dict


def investigate_a_tax():
    """ investigate_a_tax
    cut -f2- all_ena_gps_tax_combined.tsv | egrep -e '(^accession|410658)'  | cut -f 3,7,8,9,16-18,22,49,50 > 410658.tsv
    """
    infile = "/Users/woollard/projects/bluecloud/analysis/410658.tsv"
    ic(infile)
    df = pd.read_csv(infile, sep = "\t")
    ic(df.head())
    ic(df["location_designation"].value_counts())
    ic(df["taxonomic_environment"].value_counts())
    df_sea_undetermined = df.query("location_designation == 'sea' and taxonomic_environment == 'undetermined'")
    ic(df_sea_undetermined.shape[0])
    ic(df_sea_undetermined["environment_biome"].value_counts())
    ic(df_sea_undetermined["environment_feature"].value_counts())
    ic(df_sea_undetermined["environment_material"].value_counts())

def main():
    """ main
        __params__:
               passed_args
    """
    stats_dict = {}
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    ic(analysis_dir)
    ic(plot_dir)

    """ This section can be deleted, plotting called elsewhere - is here as to allow plotting without 
    re-running everything"""
    # infile = analysis_dir + 'tax_metag_sample_land_sea_counts.tsv'
    # df_merged_cats_metag_land_sea_counts = pd.read_csv(infile, sep = "\t")
    # plotting_metag(plot_dir, df_merged_cats_metag_land_sea_counts)
    #
    # quit()

    """ The section above can be deleted, plotting called else"""

    (df_metag_tax, df_tax2env) = get_taxonomy_info(taxonomy_dir)
    investigate_a_tax()

    quit()

    # gets all sample data rows in ENA(with or without GPS coords), and a rich but limited selection of metadata files
    df_all_ena_sample_detail = get_all_ena_detailed_sample_info(sample_dir)

    stats_dict["_input_ena_sample_total_count"] = df_all_ena_sample_detail.shape[0]
    stats_dict["_input_metag_tax_id_count"] = df_metag_tax["NCBI:taxid"].nunique()
    stats_dict["_input_env_tax_id_count"] = df_tax2env["NCBI:taxid"].nunique()
    stats_dict["_input_total_tax_id_count"] = stats_dict["_input_metag_tax_id_count"] + stats_dict[
        "_input_env_tax_id_count"]

    stats_dict, df_merged_ena_combined_tax = combine_analysis_all_tax(analysis_dir, plot_dir, stats_dict,
                                                                      df_all_ena_sample_detail, df_metag_tax,
                                                                      df_tax2env)
    quit()
    stats_dict, df_merge_tax2env = analyse_all_ena_all_tax2env(plot_dir, stats_dict, df_all_ena_sample_detail,
                                                               df_tax2env)
    stats_dict, df_merge_metag = analyse_all_ena_just_metag(plot_dir, analysis_dir, stats_dict,
                                                            df_all_ena_sample_detail, df_metag_tax)


    ic(stats_dict)
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

    main()
