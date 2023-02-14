"""Script of water_taxonomyAnalysis.py is to take the taxonomy environment assignments
   and combine them with the output from analyseHits.py
   to allow one to get analysis of what is marine or terrestrial/freshwater from different methods

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2022-12-21
__docformat___ = 'reStructuredText'

"""
from get_directory_paths import get_directory_paths
from ena_samples import *

import pandas as pd
import pyarrow as pa
from pyarrow import parquet as pq
from pyarrow.parquet import ParquetFile
from icecream import ic
import sys  #system specific parameters and names
import gc   #garbage collector interface

import plotly.express as px
import plotly
import re
from re import match

import argparse
import warnings
import numpy as np

import matplotlib.pyplot as plt
from wordcloud import WordCloud

# from matplotlib_venn import venn2

pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)

MyDataStuctures = {}

def obj_size_fmt(num):
    if num < 10**3:
        return "{:.2f}{}".format(num, "B")
    elif ((num>=10**3)&(num<10**6)):
        return "{:.2f}{}".format(num/(1.024*10**3), "KB")
    elif ((num>=10**6)&(num<10**9)):
        return "{:.2f}{}".format(num/(1.024*10**6), "MB")
    else:
        return "{:.2f}{}".format(num/(1.024*10**9), "GB")
def memory_usage():
    memory_usage_by_variable= pd.DataFrame({k:sys.getsizeof(v)\
    for (k,v) in globals().items()}, index=['Size'])
    memory_usage_by_variable = memory_usage_by_variable.T
    memory_usage_by_variable = memory_usage_by_variable.sort_values(by='Size', ascending=False).head(10)
    memory_usage_by_variable['Size'] = memory_usage_by_variable['Size'].apply(lambda x: obj_size_fmt(x))
    return memory_usage_by_variable

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
    my_dtypes = {"NCBI:taxid": int, "NCBI metagenome category": "category", "taxonomic_source": "category"}
    df_metag_tax = pd.read_csv(metagenomes_file, dtype=my_dtypes, index_col=None)
    ic(df_metag_tax.columns)
    df_metag_tax["NCBI:taxid"] = df_metag_tax["NCBI:taxid"]
    df_metag_tax = clean_up_df_metag_tax(df_metag_tax)
    ic(df_metag_tax.head(10))

    taxa_env_file = taxonomy_dir + "NCBI-taxa-to-environment.csv"
    my_dtypes = {"NCBI:taxid": int, "NCBI taxID Type": "category"}
    # 'rule set description': "category", 'taxID rank offset: NCBI rank [relation] WoRMS rank': "category", 'NCBI-to-marine': "category"
    my_cols = ["NCBI taxID Name", "NCBI taxID", "NCBI taxID Type", "NCBI-to-marine.1", "NCBI-to-terrestrial.1"]
    df_tax2env = pd.read_csv(taxa_env_file, usecols=my_cols, dtype=my_dtypes, index_col=None).reset_index()
    ic(df_tax2env.columns)
    #df_tax2env["NCBI taxID"] = df_tax2env["NCBI taxID"].astype(np.int16).abs()
    df_tax2env = clean_up_df_tax2env(df_tax2env)
    ic(df_tax2env.shape[0])
    ic(df_tax2env.head(10))

    ic(df_tax2env.query('`NCBI:taxid` == 16084'))

    return df_metag_tax, df_tax2env


# def get_ena_detailed_sample_info(sample_dir):
#     """ get_ena_detailed_sample_info
#         This is filtered for just those with lat and lons
#         __params__:
#                passed_args:
#                   sample_dir
#         __return__:
#             df_ena_sample_detail
#     """
#     ic()
#     infile = sample_dir + "sample_much_lat_filtered.tsv"
#     df_ena_sample_detail = pd.read_csv(infile, sep = "\t", nrows = 1000000000)
#     ic(df_ena_sample_detail.head())
#
#     return df_ena_sample_detail





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
       For NCBI-to-terrestrial.1 NCBI-to-marine.1" columns mapping 1's to True and 0's to False
       make the key column names  the same as the metag one
       N.B. also ensures that every row has at least one true water species (marine or terrestrial freshwater)

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
    df = df.rename(columns={"NCBI-to-marine.1": "marine (ocean connected)", "NCBI-to-terrestrial.1": "freshwater (land enclosed)"})
    df["taxonomic_source"] = 'environment'

    df_tmp = df.query('(`freshwater (land enclosed)` == True) & (`marine (ocean connected)` == False)')
    ic(df_tmp.head(10))

    return df


# def analyse_all_ena_all_tax2env(plot_dir, stats_dict, df_all_ena_sample_detail, df_tax2env):
#     """ analyse_all_ena_all_tax2env
#            analyse the taxonomy WRT the GPS coordinates
#         __params__:
#                passed_args: plot_dir,df_all_ena_sample_detail, df_tax2env
#
#         __return__: stats_dict, df_merged
#
#     """
#
#     ic()
#     ic(plot_dir)
#     ic(df_all_ena_sample_detail.shape[0])
#     ic(df_tax2env.shape[0])
#
#     df_tax2env = df_tax2env.rename(columns = {'NCBI taxID': "NCBI:taxid", "NCBI taxID Name": "NCBI term"})
#     ic(df_tax2env.head())
#     df_merged_ena_tax2env = pd.merge(df_all_ena_sample_detail, df_tax2env, how = 'inner', left_on = ['tax_id'],
#                                      right_on = ['NCBI:taxid'])
#
#     stats_dict["env_tax_ids_in_ena_count"] = df_merged_ena_tax2env["NCBI:taxid"].nunique()
#     stats_dict["env_tax_not_in_ena_count"] = stats_dict["_input_env_tax_id_count"] - stats_dict[
#         "env_tax_ids_in_ena_count"]
#     stats_dict["env_tax_in_ena_sample_count"] = df_merged_ena_tax2env.shape[0]
#
#     print(f"total ENA samples={len(df_all_ena_sample_detail)}")
#     print(f"total Taxonomic entries={len(df_tax2env)}")
#
#     samples_with_marine_tax = stats_dict["env_tax_in_ena_sample_count"]
#     samples_without_marine_tax = df_all_ena_sample_detail.shape[0] - samples_with_marine_tax
#     print(
#         f"total ENA samples with a marine or freshwater tax_id={samples_with_marine_tax} "
#         f"percentage= {(samples_with_marine_tax * 100) / len(df_all_ena_sample_detail):.2f} %")
#     print(
#         f"total ENA samples without a marine or freshwater tax_id={samples_without_marine_tax} "
#         f"percentage= {(samples_without_marine_tax * 100) / len(df_all_ena_sample_detail):.2f} %")
#
#     # reduce the columns down to make it easier to debug (not reused elsewhere_
#     df = df_merged_ena_tax2env[
#         ["accession", "NCBI-to-marine.1", "NCBI-to-terrestrial.1", "NCBI:taxid", "NCBI taxID Type", "NCBI taxID rank",
#          "NCBI term"]]
#
#     # ic(df.head())
#     ic(df["NCBI-to-terrestrial.1"].value_counts())
#     ic(df["NCBI-to-marine.1"].value_counts())
#     both_true_total = len(df.loc[(df["NCBI-to-marine.1"] & df["NCBI-to-terrestrial.1"])])
#     print(f"NCBI-to-marine.1 and NCBI-to-terrestrial.1 ={both_true_total}")
#     just_marine_true_total = len(df.loc[(df["NCBI-to-marine.1"] & ~df["NCBI-to-terrestrial.1"])])
#     print(f"NCBI-to-marine.1 and not NCBI-to-terrestrial.1 ={just_marine_true_total}")
#     just_terr_true_total = len(df.loc[(~df["NCBI-to-marine.1"] & df["NCBI-to-terrestrial.1"])])
#     print(f"not NCBI-to-marine.1 and  NCBI-to-terrestrial.1 ={just_terr_true_total}")
#     non_true_total = len(df.loc[(~df["NCBI-to-marine.1"] & ~df["NCBI-to-terrestrial.1"])])
#     print(f"not NCBI-to-marine.1 and not NCBI-to-terrestrial.1 ={non_true_total}")
#
#     non_true = df.loc[(~df["NCBI-to-marine.1"] & ~df["NCBI-to-terrestrial.1"])]
#     ic(non_true.head())
#
#     # stats_dict = metag_taxa_with_ena_coords(stats_dict, df_ena_sample_detail, df_merged_ena_tax2env, analysis_dir):
#
#     # Use the venn2 function
#     # ic("plotting as venn")
#     # # venn2(subsets = (10, 5, 2), set_labels = ('Group A', 'Group B'))
#     # venn2(subsets = (just_terr_true_total, both_true_total, just_terr_true_total),
#     # set_labels = ('Marine', 'Terrestrial'))
#     # plt.title("ENA marine and terrestrial water taxon counts")
#     # plt.show()
#     # plotfile=plot_dir + 'ENA_marine_terrestrial_water_tax_counts.pdf'
#     # ic(plotfile)
#     # plt.savefig(plotfile)
#
#     return stats_dict, df
# #

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
    ic(df_metag_not_in_ena_latlon.head(5))
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

def clean_df_mega(df_mega):
    """"clean_df_mega
         e.g. reduce the columns to just those we are using to reduce complexity
    """
    # ic(df_mega.head(10))
    # ic(df_mega.columns)

    drop_columns = ["ena_country", "ena_region","sea_total",  "land_total", 'coords']

    df_mega.drop(columns = drop_columns, inplace=True)
    df_mega['NCBI:taxid'] = df_mega['NCBI:taxid'].astype('Int64')
    ic(df_mega.shape[0])
    ic(df_mega.head(2))
    ic(df_mega.columns)
    return(df_mega)


def print_df_mega(prefix, df_mega):
    """print_df_mega
       (This is reused several times, hence the prefix. Such a bad subroutine name!)
       Does lots of taxonomy_id specific group_by's to generate counts by different criteria
        The counts are renamed with a relevant column name
        - it generates a df with a row per tax and many column counts for different criteria
       Intermediate files are printed too,
    :param prefix: this is used for the column and file naming
    :param df_mega:
    :return:

    sorry, it is a very badly named routine!
    """
    ic('=' * 100)
    ic()
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()

    ic()
    ic(df_mega["taxonomy_type"].value_counts())
    df_mega["taxonomy_type"] = df_mega["taxonomy_type"].fillna('unclassified')

    def add_in_extra_cols(df_mega_combined_counts, df_mega):
        """ add_in_extra_cols

        :param df_mega_combined_counts:
        :return: df_mega_combined_counts
        """
        #    'marine (ocean connected)', 'freshwater (land enclosed)'
        df = pd.merge(df_mega_combined_counts,
                      df_mega[['tax_id', 'marine (ocean connected)', 'freshwater (land enclosed)']], on = 'tax_id',
                      how = 'inner')
        # don't understand why this merge duplicates
        df.drop_duplicates(inplace = True)
        df.fillna(False, inplace = True)

        ic(df.head(5))
        return (df)

    def combine_count(df_mega_combined_counts, df_right, title):
        """ combine_count function to merge the counts column of df_right with the combined counts
            the title is used to give the counts column a meaningful name
        """
        df_mega_combined_counts = pd.merge(df_mega_combined_counts, df_right, how = 'left',
                                           on = 'tax_id', suffixes = ('', '_y'))
        df_mega_combined_counts.rename(columns = {'count': title}, inplace = True)
        df_mega_combined_counts[title] = df_mega_combined_counts[title].astype('Int64')
        df_mega_combined_counts[title] = df_mega_combined_counts[title].astype('Int64')
        df_mega_combined_counts.drop_duplicates(inplace = True)
        my_cols_y = [match for match in df_mega_combined_counts.columns if "_y" in match]
        df_mega_combined_counts.drop(columns=my_cols_y, inplace=True)

        return df_mega_combined_counts

    def combine_count_allspecies(df_mega_combined_counts, df_right, title):
        """ combine_count_allspecies function to merge the counts column of df_right with the combined counts
                   the title is used to give the counts column a meaningful name
            the difference from the combine_count function is that it copes with species specific aspects.
            currently it is only used once
        """

        ic()
        ic(df_mega_combined_counts.sort_values('tax_id').head(3))
        ic(df_mega_combined_counts.shape)
        ic(df_mega_combined_counts['tax_id'].dtype)
        ic(df_right.sort_values('tax_id').head(3))
        ic(df_right.shape)
        ic(df_right['tax_id'].dtype)
        #df_right.drop(columns = ["level_0", "index"])
        ic(df_right.query('scientific_name == 0').shape)
        ic(df_mega_combined_counts.query('scientific_name == 0').shape)
        df_mega_combined_counts.reset_index(inplace = True)
        df_mega_combined_counts = pd.merge(df_right, df_mega_combined_counts, how = 'left',
                                           on = ['tax_id'], suffixes = ('', '_y'))
        ic('after merge',df_mega_combined_counts.shape)
        ic(df_mega_combined_counts.sort_values('tax_id').head(20))

        #df_mega_combined_counts.reset_index(inplace = True)
        df_mega_combined_counts.drop_duplicates(inplace = True)
        ic(df_mega_combined_counts.sort_values('tax_id').head(3))

        my_cols_y = [match for match in df_mega_combined_counts.columns if "_y" in match]
        for my_y_col in my_cols_y:
            my_x_col = my_y_col[:-2]
            ic(my_x_col, my_y_col)
            df_mega_combined_counts[my_x_col] = df_mega_combined_counts[my_x_col].fillna(
                df_mega_combined_counts[my_y_col])
        ic(df_mega_combined_counts.sort_values('tax_id').head(3))
        df_mega_combined_counts.drop(columns=my_cols_y, inplace=True)
        ic(df_mega_combined_counts.sort_values('tax_id').head(3))
        df_mega_combined_counts["taxonomy_type"].fillna("unclassified", inplace=True)
        ic(df_mega_combined_counts.sort_values('tax_id').head(3))
        df_mega_combined_counts["NCBI term"] = df_mega_combined_counts["NCBI term"].fillna(
            df_mega_combined_counts["scientific_name"], inplace = True)
        ic(df_mega_combined_counts.sort_values('tax_id').head(3))
        df_mega_combined_counts["scientific_name"] = df_mega_combined_counts["scientific_name"].fillna(
            df_mega_combined_counts["NCBI term"])
        ic(df_mega_combined_counts.sort_values('tax_id').head(3))

        ic(df_mega_combined_counts.sort_values('tax_id').head(20))
        df_mega_combined_counts.rename(columns = {'count': title}, inplace = True)
        df_mega_combined_counts.fillna(0, inplace = True)

        return df_mega_combined_counts

    # df_mega = df_mega.query(
    #     '(`NCBI term` == "marine metagenome") or (`NCBI term` == "Saccharomyces cerevisiae") or (`NCBI term` == "Piscirickettsia salmonis") or (`NCBI term` == "Equisetum")')
    # df_mega = df_mega.query('(`NCBI term` == "Piscirickettsia salmonis")')

    #df_mega = df_mega.query( '(`scientific_name` == "Homo sapiens") & (lat > 1)')

    #ic(df_mega.query('scientific_name == "Corynebacterium suranareeae"'))

    df_mega = clean_df_mega(df_mega)
    ic(df_mega.head(10))
    df_mega_combined_counts = df_mega[['tax_id', 'scientific_name', 'taxonomy_type']]
    df_mega_combined_counts = df_mega_combined_counts.drop_duplicates()
    ic(df_mega_combined_counts.head(20))

    ic()
    ic(df_mega["taxonomy_type"].value_counts())

    ic(df_mega["location_designation"].value_counts())
    glossary = {}

    # Have coordinates and are classified as part of the marine domain (any)
    title = 'marine_any'
    ic('###', title)
    df_just_marine = df_mega.query('(location_designation_marine == True) or (`marine (ocean connected)` == True)'
                                            , engine = 'python')
    ic()
    ic(df_just_marine["taxonomy_type"].value_counts())

    out_file = analysis_dir + prefix + '_' + title + '.tsv'
    ic(out_file, df_just_marine.shape[0])
    ic(df_just_marine.head(5))
    df_just_marine.to_csv(out_file, sep = '\t', index = False)
    ic(df_just_marine["scientific_name"].value_counts())

    title = 'marine_any_counts'
    glossary[title] = 'count of all ENA samples for a tax_id where there is a marine location designation from at least one of tax and GPS(lower confidence)'
    ic('###', title)
    out_file = analysis_dir + prefix + '_' + title + '.tsv'
    df = df_just_marine.groupby(["tax_id", "scientific_name", "taxonomy_type"]).size().to_frame('count').reset_index()
    ic(out_file, df.shape[0])
    ic(df.head(5))
    df.to_csv(out_file, sep = '\t')
    #del df_just_marine
    #gc.collect()

    # This is the base of the combined counts dataframe
    df_mega_combined_counts = combine_count(df_mega_combined_counts, df, title)
    #df_mega_combined_counts = df.rename(columns={'count': title})
    df_mega_combined_counts[title] = df_mega_combined_counts[title].astype('Int64')
    ic(df_mega_combined_counts.head(5))

    # Have coordinates and are classified as part of the marine domain (and not (location_designation_terrestrial ==
    # True) or not occurring: ((`marine (ocean connected)` == True) and (`freshwater (land enclosed)` == True)))
    title = 'marine'
    ic('###', title)
    df_just_marine = df_mega.query('(location_designation_marine == True) or (`marine (ocean connected)` == True)'
                                            , engine = 'python')
    ic(df_just_marine.head(2))
    df_just_marine = df_just_marine.query('(location_designation != "marine and terrestrial") and \
                             ( (`marine (ocean connected)` == False) or (`freshwater (land enclosed)` == False) )' \
                                   , engine = 'python')
    ic()
    ic(df_just_marine["taxonomy_type"].value_counts())

    out_file = analysis_dir + prefix + '_' + title + '.tsv'
    ic(out_file, df_just_marine.shape[0])
    ic(df_just_marine.head(5))
    df_just_marine.to_csv(out_file, sep = '\t', index = False)
    ic(df_just_marine["scientific_name"].value_counts())

    title = 'marine_counts'
    glossary[title] = 'count of all ENA samples for a tax_id where there is a marine location designation from at '\
       + 'least one of tax and GPS(lower confidence)'\
       + ', but not where no indications of both marine and terrestrial'
    ic('###', title)
    out_file = analysis_dir + prefix + '_' + title + '.tsv'
    df = df_just_marine.groupby(["tax_id", "scientific_name", "taxonomy_type"]).size().to_frame('count').reset_index()
    ic(out_file, df.shape[0])
    ic(df.head(5))
    df.to_csv(out_file, sep = '\t')
    df_mega_combined_counts = combine_count(df_mega_combined_counts, df, title)

    # Have coordinates and are classified as part of the marine domain as high confidence
    title = 'marine_hc'
    ic('###', title)
    df_just_marine = df_mega.query('(location_designation_marine == True) and (`marine (ocean connected)` == True)'
                                   , engine = 'python')
    out_file = analysis_dir + prefix + '_' + title + '.tsv'
    ic(out_file, df_just_marine.shape[0])
    ic(df_just_marine.head(5))
    df_just_marine.to_csv(out_file, sep = '\t', index = False)
    ic(df_just_marine["scientific_name"].value_counts())

    title = 'marine_hc_counts'
    glossary[
        title] = 'count of all ENA samples for a tax_id where there is a marine location designation from both tax and GPS(high confidence)'
    ic('###', title)
    out_file = analysis_dir + prefix + '_' + title + '.tsv'
    df = df_just_marine.groupby(["tax_id", "scientific_name", "taxonomy_type"]).size().to_frame('count')
    ic(out_file, df.shape[0])
    ic(df.head(5))
    df.to_csv(out_file, sep = '\t')
    df_mega_combined_counts = combine_count(df_mega_combined_counts, df, title)
    del df_just_marine
    gc.collect()
    ic(df_mega_combined_counts.head(2))

    # Have coordinates and are classified as part of the terrestrial domain (lower confidence)
    title = 'terrestrial_any_counts'
    glossary[title] = 'count of all ENA samples for a tax_id where there is terrestrial location designation from either tax and GPS(lower confidence)'
    ic('###', title)
    ic(df_mega.query('`scientific_name` == "Homo sapiens"').head(5))
    ic(df_mega.query('`scientific_name` == "Equisetum"').head(5))
    df_just_terrestrial = df_mega.query('(location_designation_terrestrial == True) or \
    (`freshwater (land enclosed)` == True)', engine = 'python')
    ic(df_just_terrestrial.query('`scientific_name` == "Equisetum"'))

    out_file = analysis_dir + prefix + '_' + title + '.tsv'
    df = df_just_terrestrial.groupby(["tax_id", "scientific_name", "taxonomy_type"]).size().to_frame('count')
    ic(df.head())
    ic(df.query('`scientific_name` == "Homo sapiens"').head(2))
    ic(out_file, df_just_terrestrial.shape[0])
    ic(out_file, df.shape[0])
    df.to_csv(out_file, sep = '\t')
    ic(df.head(5))
    df_mega_combined_counts = combine_count(df_mega_combined_counts, df, title)
    ic(df_mega_combined_counts.head(10))

    # Have coordinates and are classified as part of the terrestrial domain (lower confidence) and not both
    title = 'terrestrial_counts'
    glossary[title] = 'count of all ENA samples for a tax_id where there is terrestrial location designation from '\
      + 'either tax and GPS(lower confidence), but not where no indications of both marine and terrestrial'
    ic('###', title)
    ic(df_mega.query('`scientific_name` == "Homo sapiens"').head(5))
    df_just_terrestrial = df_mega.query('(location_designation_terrestrial == True) or \
    (`freshwater (land enclosed)` == True)', engine = 'python')
    df_just_terrestrial = df_just_terrestrial.query('(location_designation != "marine and terrestrial") and \
                             ( (`marine (ocean connected)` == False) or (`freshwater (land enclosed)` == False) )'\
                                   , engine = 'python')
    ic(df_just_terrestrial.query('`scientific_name` == "Homo sapiens"'))
    out_file = analysis_dir + prefix + '_' + title + '.tsv'
    df = df_just_terrestrial.groupby(["tax_id", "scientific_name", "taxonomy_type"]).size().to_frame('count')
    ic(df.head())
    ic(df.head(2))
    ic(out_file, df_just_terrestrial.shape[0])
    ic(out_file, df.shape[0])
    df.to_csv(out_file, sep = '\t')
    df_mega_combined_counts = combine_count(df_mega_combined_counts, df, title)
    del df_just_terrestrial
    gc.collect()

    # Have coordinates and are classified as part of the terrestrial domain
    title = 'terrestrial_hc_counts'
    glossary[title] = 'count of all ENA samples for a tax_id where there is terrestrial location designation from both tax and GPS(high confidence)'
    ic('###', title)
    df_just_terrestrial = df_mega.query('(location_designation_terrestrial == True) and \
    (`freshwater (land enclosed)` == True)', engine = 'python')
    ic(df.head(2))
    out_file = analysis_dir + prefix + '_' + title + '.tsv'
    df = df_just_terrestrial.groupby(["tax_id", "scientific_name", "taxonomy_type"]).size().to_frame('count')
    ic(df.head(2))
    ic(out_file, df_just_terrestrial.shape[0])
    ic(out_file, df.shape[0])
    df.to_csv(out_file, sep = '\t')
    df_mega_combined_counts = combine_count(df_mega_combined_counts, df, title)

    del df_just_terrestrial
    gc.collect()

    #lat_lon_marine_or_terrestrial
    title = 'marine_or_terrestrial'
    ic('###', title)
    out_file = analysis_dir + prefix + '_' + title + '.tsv'
    # ~lat.isnull()
    # ic(df_mega["NCBI term"].value_counts())
    df_mega_filtered = df_mega.query(
        '(location_designation_marine == True) or (location_designation_terrestrial == True)',
        engine = 'python')
    df_mega_filtered.drop_duplicates(inplace=True)
    ic(out_file, df_mega_filtered.shape[0])
    df_mega_filtered.to_csv(out_file, sep = '\t', index = False)
    ic(df_mega_filtered.head(2))
    ic(df_mega_filtered.query('`scientific_name` == "Homo sapiens"'))
    df = df_mega_filtered.groupby(["tax_id", "scientific_name", "taxonomy_type"]).size().to_frame('count')
    df_mega_combined_counts = combine_count(df_mega_combined_counts, df, title)
    del df_mega_filtered   #memory expensive slice!
    gc.collect()

    # Have coordinates and are classified as part of both marine & terrestrial domains > to document the overlap
    title = 'marine_and_terrestrial_counts'
    glossary[title] = 'count of all ENA samples for a tax_id where there is "both" marine and terrestrial location ' \
                      'designation from tax and the GPS coordinates '
    ic('###', title)
    out_file = analysis_dir + prefix + '_' + title + '.tsv'
    df_both_mar_ter = df_mega.query('(location_designation == "marine and terrestrial") or \
                  ((`marine (ocean connected)` == True) and (`freshwater (land enclosed)` == True))', engine = 'python')
    # df = df_both_mar_ter.query('lat == lat')
    df = df_both_mar_ter
    df = df.groupby(["tax_id", "scientific_name", "taxonomy_type"]).size().to_frame('count')
    ic(out_file, df.shape[0])
    df.to_csv(out_file, sep = '\t')
    df_mega_combined_counts = combine_count(df_mega_combined_counts, df, title)

    # Have coordinates and are not classified as marine or terrestrial
    title = 'lat_lon_not_marine_or_terrestrial_counts'
    glossary[title] = 'count of all ENA samples for a tax_id where there is NO location designation from GPS coordinates'
    ic('###', title)
    out_file = analysis_dir + prefix + '_' + title + '.tsv'
    df_both_mar_ter = df_mega.query('(location_designation == "neither marine nor terrestrial")', engine = 'python')

    #and (`marine (ocean connected)` == False) and (`freshwater (land enclosed)` == False))
    df = df_both_mar_ter.groupby(["tax_id", "scientific_name", "taxonomy_type"]).size().to_frame('count')
    ic(out_file, df.shape[0])
    df.to_csv(out_file, sep = '\t')
    df_mega_combined_counts = combine_count(df_mega_combined_counts, df, title)
    del df_both_mar_ter
    gc.collect()

    #Do not have coordinates
    ic()
    title = "not_lat_lon_counts"
    glossary[title] = 'count of all ENA samples for a tax_id where there are NO GPS coordinates'
    ic('###', title)
    out_file = analysis_dir + prefix + '_' + title + '.tsv'
    #ic(df.query('(`NCBI term` == "marine metagenome") or (`NCBI term` == "Saccharomyces cerevisiae") or (`NCBI term` == "Piscirickettsia salmonis")'))
    ic(df_mega.head())
    # df_mega = df_mega.query('scientific_name == "Piscirickettsia salmonis"')
    ic(df_mega.head(20))
    df = df_mega[df_mega['lat'].isnull()]
    ic(df.head())
    ic(df.shape[0])
    df = df.groupby(["tax_id", "scientific_name", "taxonomy_type"]).size().to_frame('count')
    ic(out_file, df.shape[0])
    df.to_csv(out_file, sep = '\t')
    ic('before combine_count', df_mega_combined_counts.sort_values('tax_id').head(3))
    df_mega_combined_counts = combine_count(df_mega_combined_counts, df, title)
    ic('after combine_count', df_mega_combined_counts.sort_values('tax_id').head(3))

    df_mega_combined_counts["taxonomy_type"].fillna("unclassified_9999")
    df_mega_combined_counts.loc[df_mega_combined_counts['taxonomy_type'] == 0, 'taxonomy_type'] = "unclassified_8888"
    ic(df_mega_combined_counts["taxonomy_type"].value_counts())


    #all species for all samples
    title = "all_ena_counts"
    glossary[title] = 'count of all ENA samples for a tax_id'
    ic('###', title)
    out_file = analysis_dir + prefix + '_' + title + '.tsv'
    df = get_ena_species_count(sample_dir)
    df = df.reset_index()
    ic(df.columns)
    df = df.rename(columns={'scientific_term': 'NCBI term'})
    df['NCBI term'] = df['scientific_name']
    ic(df.columns)
    # ic(df.query('(`NCBI term` == "marine metagenome") or (`NCBI term` == "Saccharomyces cerevisiae") or (`NCBI term` == "Piscirickettsia salmonis")'))
    ic(df.head(5))
    ic(out_file, df.shape[0])
    df.to_csv(out_file, sep = '\t')
    ic('before combine_count_allspecies', df_mega_combined_counts.sort_values('tax_id').head(3))
    df_mega_combined_counts = combine_count_allspecies(df_mega_combined_counts, df, title)
    ic('after combine_count_allspecies', df_mega_combined_counts.sort_values('tax_id').head(3))
    del df
    gc.collect()



    """and finally to print out the combined counts"""
    df_mega_combined_counts = add_in_extra_cols(df_mega_combined_counts, df_mega)
    title = 'all_sample_counts'
    ic('### The final combined counts file: ', title)
    out_file = analysis_dir + prefix + '_' + title + '.tsv'

    # change the order, the tax_id slipped down the lists
    ic(df_mega_combined_counts.columns)

    df_mega_combined_counts = df_mega_combined_counts.loc[:, ~df_mega_combined_counts.columns.str.contains('^level')]
    df_mega_combined_counts["tax_id_index"] = df_mega_combined_counts["tax_id"]
    df_mega_combined_counts.set_index("tax_id_index", inplace = True)
    df_mega_combined_counts.drop_duplicates()
    # not sure why get a huge number of rows missing scientific_name etc. - too investigate! Think it is just when limited row selection in testing
    # df_mega_combined_counts = df_mega_combined_counts.drop(df_mega_combined_counts[df_mega_combined_counts.scientific_name == 0].index)

    df_mega_combined_counts = df_mega_combined_counts[["tax_id", "scientific_name", "taxonomy_type",
        "marine (ocean connected)", "freshwater (land enclosed)",
        "marine_any_counts", "marine_counts", "marine_hc_counts",
        "terrestrial_any_counts", "terrestrial_counts", "terrestrial_hc_counts",
        "marine_and_terrestrial_counts", "lat_lon_not_marine_or_terrestrial_counts",
        "not_lat_lon_counts",  "all_ena_counts"]]
    ic(df_mega_combined_counts.head(5))
    ic(out_file, df_mega_combined_counts.shape[0])
    df_mega_combined_counts.to_csv(out_file, sep = '\t', index=False)
    # df_mega_combined_counts = df_mega_combined_counts.query('(`NCBI term` == "marine metagenome") or (`NCBI term` == "Saccharomyces cerevisiae") or (`NCBI term` == "Piscirickettsia salmonis")')
    ic(df_mega_combined_counts.head(5))
    ic(glossary)

    return

def get_merged_all_categories_file(analysis_dir):
    """ get_merged_all_categories_file
    this file comes from analyseHits.py

    """

    key_name = 'df_merged_all_categories'
    if key_name in MyDataStuctures:
        df = MyDataStuctures[key_name]
        ic("yes! reusing: ", key_name)
    else:
        ic("generating from fresh: ", key_name)
        merged_all_categories_file = analysis_dir + "merged_all_categories.tsv"
        df = pd.read_csv(merged_all_categories_file, sep = "\t", index_col=None)
        #df["lat"] = df["lat"].astype(np.float32)
        #df["lon"] = df["lon"].astype(np.float32)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        ic(df.columns)

        # attempting to reduce the memory footprint
        most_cats = ['ena_country', 'ena_region', 'eez_category', 'longhurst_category', 'IHO_category',
             'sea_category', 'eez_iho_intersect_category', 'land_category', 'worldAdmin_category', 'feow_category',
             'ena_category', 'location_designation_marine',
             'location_designation_terrestrial', 'location_designation_other', 'location_designation']
        # ic(df.memory_usage())
        for my_cat in most_cats:
            df[my_cat] = df[my_cat].astype("category")
        #and even more, reduction of memory
        my_cols = [match for match in df.columns if "_category" in match]
        df= df.drop(columns=my_cols)
        # ic(df.memory_usage())
        MyDataStuctures[key_name] = df

    return df

def metag_taxa_with_ena_coords(stats_dict, df_ena_sample_detail, df_metag_tax, analysis_dir):
    """ taxa_with_ena_coords
    NCBI Taxa from samples that have at least 1 coordinate at ENA or marine org( via metagenome)
    Only implemented with metagenomes!

    For each taxon, please inform the following fields:

    NCBI taxID
    #samples in sea, sea & land, land
    #of associated runs in sea, sea & land, land (if possible, to assess relevance/importance)

    Strategy:
        get all samples in ENA.
             annotate the metag samples - joining on taxa id
             annotate the marine/terrestrial and other categorical data from the shapefiles - join on lat and lon

        __params__:
               passed_args:
               stats_dict - dictionary that gets past is gradually being populated
               df_ena_sample_detail - all of ENA from web services
                df_metag_tax, - this is just that taxa from Stephane's list
        __return__:
          stats_dict, df_merged_ena_metag_tax
    """
    ic()
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    df_metag_tax['taxonomy_type'] = 'metagenome'
    df_metag_tax['taxonomy_type'] = df_metag_tax["taxonomy_type"]
    ic(df_metag_tax.head(2))
    ic(df_ena_sample_detail.head(2))
    ic(df_ena_sample_detail.shape[0])
    #get all samples that have a metagenome tax id
    # df_merged_ena_metag_tax = pd.merge(df_ena_sample_detail, df_metag_tax, how = 'inner', left_on = ['tax_id'],
    #                                    right_on = ['NCBI:taxid'])

    df_merged_ena_metag_tax = pd.merge(df_ena_sample_detail, df_metag_tax, how = 'left', left_on = ['tax_id'],
                                       right_on = ['NCBI:taxid'])
    ic(df_merged_ena_metag_tax.head(3))

    ic("metag get counts of sample rows by NCBI taxid")
    df_merged_ena_metag_tax['accession_index'] = df_merged_ena_metag_tax['accession']
    df_merged_ena_metag_tax.set_index('accession_index', inplace=True)
    df_merged_ena_metag_tax.drop_duplicates(inplace=True)
    ic(df_merged_ena_metag_tax.head(2))
    ic(df_merged_ena_metag_tax.shape[0])
    df_just_metag = df_merged_ena_metag_tax.query('taxonomy_type == "metagenome"')
    ic(df_just_metag.head(3))

    # how many taxonomies did we and did not find? (in all not just GPS)
    stats_dict["metag_tax_ids_in_ena_count"] = df_just_metag["NCBI:taxid"].nunique()
    stats_dict["metag_tax_in_ena_sample_count"] = df_just_metag.shape[0]
    stats_dict["metag_tax_not_in_ena_count"] = stats_dict["_input_metag_tax_id_count"] - stats_dict[
        "metag_tax_ids_in_ena_count"]
    ic(stats_dict)

    """ metag get counts of sample rows by NCBI taxid" for simple plotting """
    out_file = analysis_dir + 'tax_metag_sample_counts.tsv'
    # df2 = df_merged_ena_metag_tax[["NCBI:taxid", "accession", "NCBI term", "marine (ocean connected)",
    # "freshwater (land enclosed)"]]
    ic(df_merged_ena_metag_tax.head(3))
    df3 = df_merged_ena_metag_tax.groupby(
        ["NCBI:taxid", "NCBI term", "NCBI metagenome category", "marine (ocean connected)",
         "freshwater (land enclosed)"]).size().to_frame('count').reset_index()
    df3["NCBI:taxid"] = df3["NCBI:taxid"].astype(np.int16).abs()
    ic(df3.head(2))
    ic(out_file)
    df3.to_csv(out_file, sep = '\t')
    ic(df3.head())

    out_file = analysis_dir + 'tax_metag_all_ENA_counts.tsv'
    df2 = df_merged_ena_metag_tax.groupby(["NCBI:taxid", "NCBI term"]).size().to_frame('count').reset_index()
    df2["NCBI:taxid"] = df2["NCBI:taxid"]
    ic(out_file, df2.shape[0])
    df2.to_csv(out_file, sep = '\t')

    out_file = analysis_dir + 'tax_metag_lat_lon_counts.tsv'
    df2 = df_merged_ena_metag_tax[["NCBI:taxid", "NCBI term", 'lat', 'lon']].drop_duplicates()
    ic('["NCBI:taxid", "NCBI term", "lat", "lon"].drop_dups', df2.shape[0])
    df2 = df2[df2['lat'].notna()]
    ic('after_rm_lat_nan', df2.shape[0])
    ic(df2.head(2))

    df3 = df2.groupby(["NCBI:taxid", "NCBI term"]).size().to_frame('count').reset_index()
    ic(df3.head(2))
    ic(out_file, df3.shape[0])
    df3.to_csv(out_file, sep = '\t')

    """ want to get samples in sea, sea & land, land"""
    ic(df_merged_ena_metag_tax.head(2))
    # this file comes from analyseHits.py
    df_merged_all_categories = get_merged_all_categories_file(analysis_dir)
    # merged_all_categories_file = analysis_dir + "merged_all_categories.tsv"
    # df_merged_all_categories = pd.read_csv(merged_all_categories_file, sep = "\t")
    # ic(df_merged_all_categories.head(2))
    # was inner when wanted just
    ic(df_merged_all_categories.columns)
    ic(df_merged_ena_metag_tax.query('scientific_name == "Corynebacterium suranareeae"'))
    df = pd.merge(df_merged_ena_metag_tax, df_merged_all_categories, how = 'left', left_on = ['lat', 'lon'],
                       right_on = ['lat', 'lon'])
    df['accession_index'] = df['accession']
    df_mega = df.set_index('accession_index').drop_duplicates()
    ic(df_mega.query('scientific_name == "Corynebacterium suranareeae"'))
    ic(df_mega.head(2))
    ic(df_mega.columns)
    ic(df_mega.shape[0])

    fileprex = "merge_tax_metag"
    ic("WARNING - not currently calling print_df_mega for the metag specifically")
    # print_df_mega(fileprex, df_mega)


    # quit()
    #
    # out_file = analysis_dir + 'tax_metag_sample_land_sea_counts.tsv'
    # df3 = df_mega.groupby(
    #     ["NCBI:taxid", "NCBI term", 'location_designation', "NCBI metagenome category", "marine (ocean connected)",
    #      "freshwater (land enclosed)"]).size().to_frame('count').reset_index()
    #
    # ic(df3.head())
    #
    # stats_dict["metag_tax_and_GPS_location_sample_count"] = df_mega.shape[0]
    # stats_dict["metag_tax_and_not_GPS_location_sample_count"] = stats_dict['metag_tax_in_ena_sample_count'] - stats_dict["metag_tax_and_GPS_location_sample_count"]
    # ic(out_file, df3.shape[0])
    # df3.to_csv(out_file, sep = '\t')

    # df_tax_metag_sample_land_sea_counts = df3

    # only commented out plotting whilst debugging
    # plotting_metag(plot_dir,df_tax_metag_sample_land_sea_counts )

    # """ tax 2 env get counts of sample rows by NCBI taxid"""
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

    return stats_dict, df_mega


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


def analyse_all_ena_just_metag(plot_dir, analysis_dir, stats_dict, df_ena_sample_detail, df_metag_tax):
    """ analyse_all_ena_just_metag
        __params__: plot_dir, analysis_dir, stats_dict, df_all_ena_sample_detail, df_metag_tax
               passed_args
               stats_dict, df_merged_all_metag
    """
    ic()
    ic(plot_dir)
    # df_ena_sample_detail = df_all_ena_sample_detail.drop(
    #     columns = ['altitude', 'elevation', 'checklist', 'collection_date',
    #                'collection_date_submitted', 'country', 'taxonomic_classification', 'salinity', 'depth',
    #                'environment_biome', 'environment_feature'])

    stats_dict, df_merged_all_categories = metag_taxa_with_ena_coords(stats_dict, df_ena_sample_detail, df_metag_tax,
                                                           analysis_dir)
    ic()
    ic(df_merged_all_categories["taxonomy_type"].value_counts())

    # taxa_notin_ena_coords(df_ena_sample_detail, df_metag_tax, df_tax2env, analysis_dir)
    ic()
    ic(df_merged_all_categories.head())
    ic(df_merged_all_categories.shape[0])

    return stats_dict, df_merged_all_categories


def taxonomic_environment_assignment(df_mega):
    """ taxonomic_environment_assignment"""
    ic()
    # "marine (ocean connected)",
    # "freshwater (land enclosed)"

    conditions = [
         ((df_mega["marine (ocean connected)"]) & (df_mega["freshwater (land enclosed)"])),
         ((df_mega["marine (ocean connected)"]) & (df_mega["freshwater (land enclosed)"] is False)),
         ((df_mega["marine (ocean connected)"] is False) & (df_mega["freshwater (land enclosed)"])),
         ((df_mega["marine (ocean connected)"] is False) & (df_mega["freshwater (land enclosed)"] is False))
    ]

    values = ["marine and freshwater", "marine (ocean connected)", "freshwater (land enclosed)", "undetermined"]
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

    """commented all below out as causing run of memory"""
    # df_mega = df_mega[
    #     (df_mega["location_designation"] != "no_gps") | (df_mega["taxonomic_environment"] != "undetermined")]
    #
    # """ Want to investigate where marine from GPS but no marine species """
    # df_marine_no_tax = df_mega.query("location_designation == 'marine' and taxonomic_environment == 'undetermined'")
    # ic()
    # df_ena_species = get_ena_species_info(sample_dir)
    # ic()
    # df_marine_no_tax = pd.merge(df_marine_no_tax, df_ena_species, how = 'inner', on = 'tax_id')
    # ic()
    # ic(df_marine_no_tax.shape[0])
    # ic(df_marine_no_tax.head())
    #
    # df = df_marine_no_tax.groupby(
    #     ["tax_id", 'scientific_name']).size().to_frame('count').reset_index().sort_values("count", ascending = False)
    # ic()
    # ic(df.head(20))
    # outfile = analysis_dir + 'marine_no-marine-tax_species_sample_count.tsv'
    # ic(outfile)
    # df.to_csv(outfile, sep = "\t")
    #
    # df_word_c = df_marine_no_tax["scientific_name"]
    # title = "Species observed where: marine (From GPS), but no-marine-tax-defined"
    # my_word_c(df_word_c, title, plot_dir + 'marine_no-marine-tax-defined-World_Cloud.png')

    return stats_dict

def my_word_c(df_word_c, title, outfile):
    """my_word_c
    providing a dataframe with just one column, it automatically generates counts.
    """
    plt.subplots(figsize = (8, 8))
    warnings.simplefilter('ignore')
    word_cloud = WordCloud(
        background_color = 'white',
        width = 512,
        height = 384
    ).generate(' '.join(df_word_c))
    warnings.resetwarnings()
    plt.imshow(word_cloud)  # image show
    plt.axis('off')  # to off the axis of x and y
    plt.title(title)
    ic(outfile)
    plt.savefig(outfile)
    plt.show()


# def combine_analysis_all_tax(analysis_dir, plot_dir, stats_dict, df_all_ena_sample_detail, df_metag_tax, df_tax2env):
#     """ combine_analysis_all_tax
#         __params__:
#                passed_args
#                stats_dict, df_merged_ena_combined_tax
#     """
#     ic()
#     ic(df_metag_tax.shape[0])
#     ic(df_tax2env.shape[0])
#     df = pd.concat([df_metag_tax, df_tax2env])
#     ic(df.shape[0])
#     ic(df.head())
#
#     # doing a left join, so all ENA samples represented.
#     df_merged_ena_combined_tax = pd.merge(df_all_ena_sample_detail, df, how = 'left', left_on = ['tax_id'],
#                                           right_on = ['NCBI:taxid'])
#     df = df_merged_ena_combined_tax.drop_duplicates()
#     df_merged_ena_combined_tax = df.loc[:, ~df.columns.str.contains('^Unnamed')]
#     ic(df_merged_ena_combined_tax.head(5))
#     ic(df_merged_ena_combined_tax.shape[0])
#     df = df_merged_ena_combined_tax
#
#     stats_dict["_global_total_samples_with_gps"] = df["lat"].count()
#     stats_dict["_global_total_samples_with_water_tax"] = df["NCBI:taxid"].count()
#     stats_dict["_global_total_samples_with_water_tax_and_gps"] = 0
#     """ comparing a column to itself gets rid of NaN"""
#     df["NCBI_taxid"] = df["NCBI:taxid"]
#     df_tmp = df.query('lat == lat')
#     ic(df_tmp.shape[0])
#     df_tmp = df_tmp.query('NCBI_taxid == NCBI_taxid')
#     ic(df_tmp.shape[0])
#     stats_dict["_global_total_samples_with_water_tax_and_gps"] = df_tmp.shape[0]
#
#     df_merged_all_categories = get_merged_all_categories_file(analysis_dir)
#
#     ic(df_merged_all_categories.head(2))
#     ic(df_merged_all_categories.shape[0])
#     ic(df_merged_ena_combined_tax.shape[0])
#     df_mega = pd.merge(df_merged_ena_combined_tax, df_merged_all_categories, how = 'left', left_on = ['lat', 'lon'],
#                        right_on = ['lat', 'lon'])
#     df_mega.drop_duplicates(inplace=True)
#     df_mega["location_designation"] = df_mega["location_designation"].fillna("no_gps")
#     df_mega["NCBI:taxid"] = df_mega["NCBI:taxid"].fillna("undetermined")
#     df_mega["NCBI term"] = df_mega["NCBI term"].fillna("undetermined")
#
#     # "marine (ocean connected)",
#     # "freshwater (land enclosed)
#     df_mega = taxonomic_environment_assignment(df_mega)
#     ic(df_mega["location_designation"].value_counts())
#     ic(df_mega.head())
#     ic(df_mega.shape[0])
#     out_file = analysis_dir + "all_ena_gps_tax_combined.tsv"
#     ic(out_file)
#     df_mega.to_csv(out_file, sep = '\t')
#
#     stats_dict = plot_combined_analysis(plot_dir, df_mega, stats_dict)
#     investigate_gps_tax(df_mega, stats_dict)
#
#     return stats_dict, df_mega

def plot_combined_analysis(plot_dir, df_mega, stats_dict):
    """plot_combined_analysis

    """
    """rm the rows where no_gps AND taxonomic_environment is no undetermined - reduce clutter"""
    # df_mega = df_mega[(df_mega["location_designation"] != "no_gps")]
    df_mega = df_mega[(df_mega["location_designation"] != "no_gps") | (df_mega["taxonomic_environment"] 
                                                                       != "undetermined")]

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
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()

    infile = analysis_dir + 'all_ena_gps_tax_combined.tsv'
    #df_mega = pd.read_csv(infile, sep = "\t", nrows = 1000000)
    df_mega = pd.read_csv(infile, sep = "\t", index_col=None)
    ic(df_mega.head(3))
    df_marine_undetermined = df_mega.query("location_designation == 'marine' and taxonomic_environment == 'undetermined'")
    ic(df_marine_undetermined.shape[0])
    title = 'World view env_undetermined in GPS "sea" for all taxa'
    fig = px.scatter_geo(df_marine_undetermined, lat = "lat", lon = "lon", title = title)
    outfile = plot_dir + title.replace(" ", "_") + '.png'
    outfile = outfile.replace('"', '')
    ic(outfile)
    fig.write_image(outfile)
    fig.show()

    infile = "/Users/woollard/projects/bluecloud/analysis/410658.tsv"
    ic(infile)
    df = pd.read_csv(infile, sep = "\t", index_col=None)
    ic(df.head())

    ic(df["location_designation"].value_counts())
    ic(df["taxonomic_environment"].value_counts())
    df_marine_undetermined = df.query("location_designation == 'marine' and taxonomic_environment == 'undetermined'")
    ic(df_marine_undetermined.shape[0])
    ic(df_marine_undetermined.head(2))
    taxa = '410658'
    inv_fields = ["environment_biome", "environment_feature", "environment_material"]

    for field in inv_fields:
        # ic(df_marine_undetermined[field].value_counts())
        df_count = df_marine_undetermined[field].value_counts().rename_axis(field).reset_index(name='count').head(10)
        # ic(df_count.head(2))
        title = field + ' Top 10 Counts for env_undetermined in GPS "marine" for specific taxa:' + taxa
        fig = px.pie(df_count, values = 'count', names = field, title = title)
        # fig.show()
        outfile = plot_dir + field + "Top1Counts_env_undetermined_gps_marine_for_taxa" + taxa + ".png"
        ic(outfile)
        fig.write_image(outfile)
    title = 'World view env_undetermined in GPS "marine" for specific taxa:' + taxa
    fig = px.scatter_geo(df_marine_undetermined, lat = "lat", lon = "lon", color = "environment_biome", title = title)
    outfile = plot_dir + title.replace(" ", "_") + '.png'
    outfile = outfile.replace('"', '')
    ic(outfile)
    fig.write_image(outfile)
    fig.show()

def merge_in_env_taxa(stats_dict, df_merge_metag, df_tax2env):
    """ merge_in_env_taxa
       merge the metagenome and env taxa rows and remove duplicate columns (after checking if values needed)

    :param stats_dict: merge_in_env_taxa
    :param df_merge_metag: 
    :param df_tax2env: 
    :return: stats_dict, df_merge_combined_tax
  
    merge_in_env_taxa(stats_dict, df_merge_metag)
    """
    ic()
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    ic(df_merge_metag.shape[0])
    ic(df_merge_metag.head(2))
    ic(df_tax2env.head(2))

    df_tax2env['taxonomy_type'] = 'env_taxa'
    ic(df_merge_metag.query('scientific_name == "Corynebacterium suranareeae"'))
    ic(df_merge_metag.query('tax_id == 16084'))
    ic(df_tax2env.query('`NCBI:taxid` == 16084'))

    df_merge_ena_combined_tax = pd.merge(df_merge_metag, df_tax2env, how = 'left', left_on = ['tax_id'],
                                          right_on = ['NCBI:taxid'], suffixes=('', '_y'))
    df_merge_ena_combined_tax.drop_duplicates(inplace = True)
    df_merge_ena_combined_tax['accession_index'] = df_merge_ena_combined_tax['accession']
    df_merge_ena_combined_tax = df_merge_ena_combined_tax.reset_index().set_index('accession_index')
    ic(df_merge_ena_combined_tax.columns)
    ic(df_merge_ena_combined_tax.shape[0])


    if 'taxonomy_type_y' in df_merge_ena_combined_tax:
        df = df_merge_ena_combined_tax
        df["taxonomy_type"].fillna(df["taxonomy_type_y"], inplace = True)
        #df.loc[df.loc['taxonomy_type'] == 'ena_classified', 'taxonomy_type'] = df["taxonomy_type_y"]
        #df.loc[df['c1'] == 'Value', 'c1'] = 10
        ic("taxonomy_type_y is found!")
        df_merge_ena_combined_tax = df

    ic(df_merge_ena_combined_tax.head(5))
    ic(df_merge_ena_combined_tax.query('scientific_name == "Corynebacterium suranareeae"'))

    # remove duplicate columns (after checking if values needed)
    columns_to_delete = []
    ic()
    all_cols = list(df_merge_ena_combined_tax.columns)
    r = re.compile(".*_y$")
    filtered_cols = list(filter(r.match, all_cols))
    rem_ycol = list(map(lambda st: str.replace(st, "_y", ""), filtered_cols))

    for field in rem_ycol:
        ic(field)
        df_merge_ena_combined_tax[field].fillna(df_merge_ena_combined_tax[field +'_y'], inplace=True)
        columns_to_delete.append(field +'_y')
    df_merge_ena_combined_tax = df_merge_ena_combined_tax.drop(columns_to_delete, axis = 1)
    df_merge_ena_combined_tax.drop_duplicates(inplace=True)
    ic(df_merge_ena_combined_tax.shape[0])
    ic(df_merge_ena_combined_tax.head(5))

    df_just_tax_env = df_merge_ena_combined_tax.query('taxonomy_type == "env_taxa"')
    stats_dict["env_tax_ids_in_ena_count"] = df_just_tax_env["NCBI:taxid"].nunique()
    stats_dict["env_tax_not_in_ena_count"] = stats_dict["_input_env_tax_id_count"] - stats_dict[
        "env_tax_ids_in_ena_count"]
    stats_dict["env_tax_in_ena_sample_count"] = df_just_tax_env.shape[0]

    return stats_dict,  df_merge_ena_combined_tax


def merge_in_all_categories(df_merge_combined_tax, df_merged_all_categories):
    """merge_in_all_categories
        Doing this as only included for metag and tax env. by default
        N.B. this massively consumes memory.
    :param df_merge_combined_tax:
    :param df_merged_all_categories:
    :return: df_merge_combined_tax
    """
    ic()
    # ic(df_merge_combined_tax.head())
    # ic(df_merge_combined_tax.shape[0])
    # ic(df_merged_all_categories.head())
    df_merge_combined_tax = pd.merge(df_merge_combined_tax, df_merged_all_categories, how = 'left',
                                     on = ['lat', 'lon'], suffixes = ('', '_y'))
    df_merge_combined_tax['accession_index'] = df_merge_combined_tax['accession']
    df_merge_combined_tax.set_index('accession_index', inplace=True)
    df_merge_combined_tax = df_merge_combined_tax.loc[:, ~df_merge_combined_tax.columns.str.contains('^Unnamed')]
    df_merge_combined_tax.drop_duplicates(inplace=True)
    ic(df_merge_combined_tax.shape[0])
    ic(df_merge_combined_tax.head())

    my_cols_y = [match for match in df_merge_combined_tax.columns if "_y" in match]
    # ic(my_cols_y)
    for my_y_col in my_cols_y:
        my_x_col = my_y_col[:-2]
        # ic(my_x_col, my_y_col)
        df_merge_combined_tax[my_x_col].fillna(df_merge_combined_tax[my_y_col], inplace=True)
    if 'taxonomy_type_y' in df_merge_combined_tax:
        df_merge_combined_tax["taxonomy_type"].fillna(df_merge_combined_tax["taxonomy_type_y"], inplace = True)
    df_merge_combined_tax.drop(columns = my_cols_y, inplace=True)
    ic(df_merge_combined_tax.head(5))
    ic()
    return df_merge_combined_tax

def addConfidence(df_merge_combined_tax):
    """addConfidence
        adding confidence for metadata assignments
    :param df_merge_combined_tax:
    :return:
    """
    ic()
    ic(df_merge_combined_tax.columns)
    # df = df_merge_combined_tax.query('`NCBI term` == "Piscirickettsia salmonis"')
    df = df_merge_combined_tax.query('location_designation_marine == True')
    ic()
    # for a sample, if GPS assignment:
    # high if , GPS and tax agreement for sample
    # low if , GPS and tax disagreement tax for sample
    ic(df.columns)
    df_tmp = df[["tax_id", "location_designation_marine", "location_designation_terrestrial", "environment_biome"]]
    ic(df_tmp.head())



    def dom_confidence(df_merge_combined_tax, conf_field):
        """marine_confidence
            method to add the marine evidence
        :param df_merge_combined_tax:
        :return:
        """
        ic()
        conf_score = conf_field + '_score'
        ic(df_merge_combined_tax.head())

        if(conf_field == "sample_confidence_marine"):
            df_tmp = df_merge_combined_tax[["tax_id", "scientific_name", "location_designation_marine", "sea_total", "marine (ocean connected)"]]
            df_tmp.loc[(df_tmp["sea_total"] > 1), ["location_designation_marine_conf"]] = True
            df_species = df_tmp.groupby(["tax_id", "location_designation_marine_conf"]).\
                size().to_frame('count').reset_index().fillna(False).set_index("tax_id")
            df_species = df_species.rename(columns={"count": "count_of_samples_having_marine_coords"})

        ic(df_species.head())
        df = pd.merge(df_merge_combined_tax, df_species, on="tax_id")
        ic(df.head())

        ic(df.environment_biome.value_counts())

        #set the defaults
        df[conf_score] = 0

        if (conf_field == "sample_confidence_marine"):
            df.loc[df["location_designation_marine"] == True, [conf_score]] = 1
            df.loc[df["marine (ocean connected)"] == True, [conf_score]] = 1

            #rules
            df.loc[(df["count_of_samples_having_marine_coords"] >= 2) & (df["location_designation_marine"] == True), [conf_score]] = 2
            df.loc[(df["sea_total"] > 1) & (df["marine (ocean connected)"] == True), [conf_score]] = 3
            df.loc[(df["sea_total"] > 1) & (df["location_designation"] == 'marine and terrestrial') & (df["marine (ocean connected)"] == True), [conf_score]] = 3
            df.loc[(df["sea_total"] <= 1) & (df["location_designation"] == 'marine and terrestrial') & (
                        df["marine (ocean connected)"] == True), [conf_score]] = 2
            df.loc[(df["location_designation"] == 'marine and terrestrial') & (df["marine (ocean connected)"] == False), [conf_score]] = 1
            df.loc[(df["location_designation_marine"] == False) & (df["marine (ocean connected)"] == True) & (df["freshwater (land enclosed)"] == True), [conf_score]] = 1
            df.loc[(df["count_of_samples_having_marine_coords"] >= 2) & (df[conf_score] == 0), [conf_score]] = 1



            quit(1)

        condlist = [
            df[conf_score] <= 0,
            df[conf_score] <= 1,
            df[conf_score] <= 2,
            df[conf_score] <= 3
        ]
        choicelist = ["zero", "low", "medium", "high"]
        df[conf_field] = np.select(condlist, choicelist, default = "zero")

        ic(df.head())
        ic(conf_field)
        if (conf_field == "sample_confidence_marine"):
            ic(df['sample_confidence_marine'].head())
            ic(df.query('sample_confidence_marine == "high"').head(5))
            ic(df.query('sample_confidence_marine == "medium"').head(5))
            ic(df.query('sample_confidence_marine == "low"').head(5))
            ic(df.query('sample_confidence_marine ==  "zero"').head(5))

        ic(df["sample_confidence_marine"].value_counts())
        return df

    df_merge_combined_tax = process_environment_biome(df_merge_combined_tax)
    quit(1)
    df = dom_confidence(df_merge_combined_tax, "sample_confidence_marine")



    # do a confidence:  conflict matrix, first. and the share with Josie and Stephane
    # do as numeric, + or - for pieces of evidence and then use threshold for the H/M/L/Zero   - look for missing rules
    # give more weight to conflict or missing?  Should missing be False?   Have a field for missing coordinates and similar taxonomy marine/freshwater assignment?
    # use the environmental_biome + coastal
    # N.B. do the GPS coordinates granularity, as another column? -
    # what if low granularity, do polygon searching?
    # first off, do a search of the relative amount of granularity

    # # what if other samples have GPS but particular ones don't?



    quit(1)


def main():
    """ main
        __params__:
               passed_args
    """

    stats_dict = {}
    """ This section can be deleted, plotting called elsewhere - is here as to allow plotting without 
    re-running everything"""
    # infile = analysis_dir + 'tax_metag_sample_land_sea_counts.tsv'
    # df_merged_cats_metag_land_sea_counts = pd.read_csv(infile, sep = "\t")
    # plotting_metag(plot_dir, df_merged_cats_metag_land_sea_counts)
    #
    # quit()

    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    ic(analysis_dir)
    ic(plot_dir)
    (df_metag_tax, df_tax2env) = get_taxonomy_info(taxonomy_dir)
    ic(df_tax2env.query('`NCBI:taxid` == 16084'))

    # df_ena_all_species_count = get_ena_species_count(sample_dir)
    # get category information from hit file
    ic()
    df_merged_all_categories = get_merged_all_categories_file(analysis_dir)
    # df_outliers = df_merged_all_categories[df_merged_all_categories["location_designation_other"].notna()]
    # ic(df_outliers)

    # gets all sample data rows in ENA(with or without GPS coords), and a rich but limited selection of metadata files
    ic()
    test_status = True
    df_all_ena_sample_detail = get_all_ena_detailed_sample_info(test_status)
    ic()
    ic(df_all_ena_sample_detail.head())
    ic(df_all_ena_sample_detail.shape[0])
    ic('-' * 100)

    stats_dict["_input_ena_sample_total_count"] = df_all_ena_sample_detail.shape[0]
    stats_dict["_input_metag_tax_id_count"] = df_metag_tax["NCBI:taxid"].nunique()
    stats_dict["_input_env_tax_id_count"] = df_tax2env["NCBI:taxid"].nunique()
    stats_dict["_input_total_tax_id_count"] = stats_dict["_input_metag_tax_id_count"] + stats_dict[
        "_input_env_tax_id_count"]
    ic()
    stats_dict, df_merge_metag = analyse_all_ena_just_metag(plot_dir, analysis_dir, stats_dict,
                                                            df_all_ena_sample_detail, df_metag_tax)
    ic(df_merge_metag.shape[0])
    ic(df_merge_metag.head(5))

    ic('-' * 100)
    ic()
    ic(df_merge_metag.query('scientific_name == "Corynebacterium suranareeae"'))

    stats_dict, df_merge_combined_tax = merge_in_env_taxa(stats_dict, df_merge_metag, df_tax2env)
    #df = df_merge_combined_tax.query('scientific_name == "Gasterosteus aculeatus"')
    # ic(df.head(20))
    #ic(df_merge_combined_tax.query('scientific_name == "Corynebacterium suranareeae"'))

    ic('-' * 100)
    df_merge_combined_tax = merge_in_all_categories(df_merge_combined_tax, df_merged_all_categories).reset_index()
    # ic(df_merge_combined_tax["NCBI term"].value_counts())
    df_merge_combined_tax = df_merge_combined_tax.loc[:, ~df_merge_combined_tax.columns.str.contains('^level_')]
    df_merge_combined_tax.drop_duplicates(inplace=True)
    # ic(df_merge_combined_tax["NCBI term"].value_counts())
    # ic(df_merge_combined_tax.query('`NCBI term` == "Piscirickettsia salmonis"').shape[0])

    #save save some memory and get rid of some stored structures
    # ic(memory_usage())
    global MyDataStuctures
    # del MyDataStuctures['df_all_ena_detailed_sample_info']  #need to reuse this!
    global WordCloud
    del WordCloud
    gc.collect()
    # ic(memory_usage())

    addConfidence(df_merge_combined_tax)
    quit(1)

    print_df_mega('merge_tax_combined', df_merge_combined_tax)
    #ic()
    # ic(memory_usage())
    #ic("about to quit")
    #ic(stats_dict)
    ic('-' * 80)
    #ic()

    # the rest of the below was used mainly when exploring the data, hence now commented.

    #
    # stats_dict, df_merge_metag = analyse_all_ena_just_metag(plot_dir, analysis_dir, stats_dict,
    #                                                         df_all_ena_sample_detail, df_metag_tax)
    #
    # stats_dict, df_merged_ena_combined_tax = combine_analysis_all_tax(analysis_dir, plot_dir, stats_dict,
    #                                                                   df_all_ena_sample_detail, df_metag_tax,
    #                                                                   df_tax2env)
    # stats_dict, df_merge_tax2env = analyse_all_ena_all_tax2env(plot_dir, stats_dict, df_all_ena_sample_detail,
    #                                                            df_tax2env)
    #
    # investigate_a_tax()

    # ic(stats_dict)
    ic()
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
