#!/usr/bin/env python3
"""Script of water_taxonomyAnalysis.py is to take the taxonomy environment assignments
   and combine them with the output from analyseHits.py
   to allow one to get analysis of what is marine or terrestrial/freshwater from different methods

   usage: python3 ./waterTaxonomyAnalysis.py [--stage 4] [--verbosity=True]
   The stage allows one to not run from start, useful when debugging.
   verbosity support not implemented yet!

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2022-12-21
__docformat___ = 'reStructuredText'

"""
from ena_samples import *
from categorise_environment import process_environment_biome
from project_utils import *

import os.path
import pandas as pd
from icecream import ic
import sys  # system specific parameters and names
import gc   # garbage collector interface
import re

import json
import plotly.express as px
import plotly
import argparse
import warnings
import numpy as np

pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)
global MyDataStuctures
MyDataStuctures = {}


def get_taxonomy_info(taxonomy_dir):
    """ get_taxonomy_info
     read in the relevant marine taxonomic terms.
      These came from Stephane Pesant
        __params__:
             taxonomy_dir
        __returns__:
                df_tax2env
    """
    ic()

    taxa_env_file = taxonomy_dir + "Blue-domain_environmental-flags-based-on-taxonomy.csv"
    # my_cols = ['NCBI taxID', 'NCBI taxID Name', 'rule set description', 'marine', 'terrestrial or freshwater',
    #            'NCBI-to-marine', 'NCBI-to-terrestrial-or-freshwater']
    df_tax2env = pd.read_csv(taxa_env_file, skiprows=1, index_col=None)
    df_tax2env = df_tax2env.drop(0)
    ic(df_tax2env.columns)
    ic(df_tax2env.head())

    df_tax2env = clean_up_df_tax2env(df_tax2env)
    ic(df_tax2env.info())
    ic(df_tax2env.shape[0])
    ic(df_tax2env.head(10))

    ic(df_tax2env.query('`NCBI:taxid` == 24'))

    return df_tax2env


def clean_up_df_tax2env(df):
    """ clean_up_df_tax2env
        standardising the column names
        making the columns with 1 and 0's to be true boolean

        __params__:
               passed_args: df_tax2env
        __return__: df_tax2env

    """
    ic()
    # N.B. changed all NaN's to 0. Mapping 1's to True and 0's to False
    warnings.simplefilter('ignore')
    my_cols = ['marine', 'terrestrial or freshwater', 'NCBI-to-marine', 'NCBI-to-terrestrial-or-freshwater']
    df = df.rename(columns = {'marine': 'taxa_marine', 'terrestrial or freshwater': 'taxa_terrestrial_or_freshwater',
                              'NCBI taxID': "NCBI:taxid", "NCBI taxID Name": "NCBI:name"})


    df["taxa_marine"] = df["taxa_marine"].replace('-',0).replace(np.nan, 0).astype(int).astype(bool)
    df["taxa_terrestrial_or_freshwater"] = df["taxa_terrestrial_or_freshwater"].replace('-',0).replace(np.nan, 0).astype(int).astype(bool)
    # ic(df.head(100))

    warnings.resetwarnings()

    ic(df.query('taxa_marine == True').head())
    ic(df.query('taxa_terrestrial_or_freshwater == False').head())

    # get all those where it is water based and marine inclusive OR  terrestrial
    # df = df.loc[(df["NCBI-to-marine.1"] | df["NCBI-to-terrestrial.1"])]

    # These are highly important NCBI-to-marine NCBI-to-terrestrial-or-freshwater, as taxa dom confidence mapping
    # clean the ^[ and ]$ from each if there
    my_cols = ['NCBI-to-marine', 'NCBI-to-terrestrial-or-freshwater', 'rule set description']
    my_regex1 = r"\["
    my_regex2 = r"\]"
    for col in my_cols:
        df[col] = df[col].replace(regex = [my_regex1, my_regex2], value = '')
        df[col] = df[col].astype('category')
        ic(col, df[col].value_counts())


    ic(df.sample(n=10))

    # set taxonomy_type
    df['taxonomy_type'] = 'environment'
    df.loc[df['NCBI:name'].str.contains('metagenome'), 'taxonomy_type'] = 'metagenome'

    return df


def get_taxonomy_mapping_confidence_flags():
    """get_taxonomy_mapping_confidence_flags
    mapped them as confidence of the marine designation i.e. whether this is correctly True or False

    taxa confidence rules  from Stephane Pesant

    :usage: taxonomy_map_conf_flags dictionary = get_taxonomy_mapping_confidence_flags()

    :return: taxonomy_map_conf_flags dictionary
    """

    marine_json = """{
        "taxa_marine": {
            "NCBI-to-marine": {
                "is exclusively": {
                    "NCBI-to-terrestrial-or-freshwater": {
                        "is not": 1
                    }
                },
                "may be exclusively": {
                    "NCBI-to-terrestrial-or-freshwater": {
                        "not flagged as": 1
                    }
                },
                "is not exclusively": {
                    "NCBI-to-terrestrial-or-freshwater": {
                        "is not exclusively": 1
                    }
                },
                "is not": {
                    "NCBI-to-terrestrial-or-freshwater": {
                        "is not": 1,
                        "is exclusively": 1,
                        "not flagged as": 0.5
                    }
                },
                "not flagged as": {
                    "NCBI-to-terrestrial-or-freshwater": {
                        "is not": 0,
                        "may be exclusively": 0,
                        "not flagged as": 0
                    }
                }
            }
        }
    }"""

    taxonomy_map_conf_flags =json.loads(marine_json)
    #print(json.dumps(taxonomy_map_conf_flags, indent = 2, default = str))

    return taxonomy_map_conf_flags


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

    #drop_columns = ["ena_country", "ena_region", "sea_total",  "land_total", 'coords']
    drop_columns = ["sea_total", "land_total", 'coords']
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
        ic()
        #    'taxa_marine', 'taxa_terrestrial_or_freshwater'
        df = pd.merge(df_mega_combined_counts,
                      df_mega[['tax_id', 'taxa_marine', 'taxa_terrestrial_or_freshwater']], on = 'tax_id',
                      how = 'inner')
        ic(df.head(5))
        ic(df.shape)
        # don't understand why this merge duplicates so f. much
        df.drop_duplicates(inplace = True)
        ic(df.shape)
        df.fillna(False, inplace = True)
        ic(df.head(5))
        ic()
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
    df_just_marine = df_mega.query('(location_designation_marine == True) or (`taxa_marine` == True)'
                                            , engine = 'python')
    ic()
    ic(df_just_marine["taxonomy_type"].value_counts())

    out_file = analysis_dir + prefix + '_' + title + '.tsv'
    ic(out_file, df_just_marine.shape[0])
    ic(df_just_marine.head(5))
    df_just_marine.to_csv(out_file, sep = '\t', index = False)
    #ic(df_just_marine["scientific_name"].value_counts())

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
    # True) or not occurring: ((`taxa_marine` == True) and (`taxa_terrestrial_or_freshwater` == True)))
    title = 'marine'
    ic('###', title)
    df_just_marine = df_mega.query('(location_designation_marine == True) or (`taxa_marine` == True)'
                                            , engine = 'python')
    ic(df_just_marine.head(2))
    df_just_marine = df_just_marine.query('(location_designation != "marine and terrestrial") and \
                             ( (`taxa_marine` == False) or (`taxa_terrestrial_or_freshwater` == False) )'
                                   , engine = 'python')
    ic()
    ic(df_just_marine["taxonomy_type"].value_counts())

    out_file = analysis_dir + prefix + '_' + title + '.tsv'
    ic(out_file, df_just_marine.shape[0])
    ic(df_just_marine.head(5))
    df_just_marine.to_csv(out_file, sep = '\t', index = False)
    #ic(df_just_marine["scientific_name"].value_counts())

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
    ic(df_mega.sample(n=5))

    # df_just_marine = df_mega.query('(location_designation_marine == True) and (`taxa_marine` == True)'
    #                                , engine = 'python')
    df_just_marine = df_mega.query('sample_confidence_marine == "high"', engine = 'python')
    out_file = analysis_dir + prefix + '_' + title + '.tsv'
    ic(out_file, df_just_marine.shape[0])
    ic(df_just_marine.head(5))
    df_just_marine.to_csv(out_file, sep = '\t', index = False)
    #ic(df_just_marine["scientific_name"].value_counts())


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
    (`taxa_terrestrial_or_freshwater` == True)', engine = 'python')
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
    (`taxa_terrestrial_or_freshwater` == True)', engine = 'python')
    df_just_terrestrial = df_just_terrestrial.query('(location_designation != "marine and terrestrial") and \
                             ( (`taxa_marine` == False) or (`taxa_terrestrial_or_freshwater` == True) )'
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
    # df_just_terrestrial = df_mega.query('(location_designation_terrestrial == True) and \
    # (`taxa_terrestrial_or_freshwater` == True)', engine = 'python')
    df_just_terrestrial = df_mega.query('sample_confidence_terrestrial == "high"', engine = 'python')
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
                  ((`taxa_marine` == True) and (`taxa_terrestrial_or_freshwater` == True))', engine = 'python')
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

    #and (`taxa_marine` == False) and (`taxa_terrestrial_or_freshwater` == False))
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
        "taxa_marine", "taxa_terrestrial_or_freshwater",
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
        most_cats = ['location_designation_terrestrial', 'location_designation_other', 'location_designation',
              'location_designation_freshwater', 'location_designation_aquatic']
        for my_cat in most_cats:
            df[my_cat] = df[my_cat].astype("category")
        #and even more, reduction of memory
        my_cols = [match for match in df.columns if "_category" in match]
        for my_cat in my_cols:
            df[my_cat] = df[my_cat].astype("category")
        #df= df.drop(columns=my_cols)
        # ic(df.memory_usage())
        MyDataStuctures[key_name] = df

    return df


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
        if df["taxa_marine"] and df["taxa_terrestrial_or_freshwater"]:
            return "tax:marine and freshwater"
        elif df["taxa_marine"] and not df["taxa_terrestrial_or_freshwater"]:
            return "tax:taxa_marine"
        elif not df["taxa_marine"] and df["taxa_terrestrial_or_freshwater"]:
            return "tax:taxa_terrestrial_or_freshwater"

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

    df = df.sort_values(["taxa_marine", "taxa_terrestrial_or_freshwater"])
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


def merge_ena_w_taxa(plot_dir, analysis_dir, stats_dict, df_ena_sample_detail, df_tax2env):
    """
        __params__: plot_dir, analysis_dir, stats_dict, df_all_ena_sample_detail, df_tax
               passed_args
               stats_dict, df_merged_tax
    """
    ic()
    ic(plot_dir)

    # stats_dict, df_merged_all_categories = metag_taxa_with_ena_coords(stats_dict, df_ena_sample_detail, df_tax2env,
    #                                                        analysis_dir)
    df_merged_ena_tax = pd.merge(df_ena_sample_detail, df_tax2env, how = 'left', left_on = ['tax_id'],
                                       right_on = ['NCBI:taxid'])
    ic(df_merged_ena_tax.shape)
    #ic(df_merged_ena_tax.sample(n=100))  #definitely as geninuine taxa_* True andG False
    ic(df_merged_ena_tax["taxonomy_type"].value_counts())

    ic("about to quit merge_ena_w_taxa")
    #sys.exit()

    return stats_dict, df_merged_ena_tax


def taxonomic_environment_assignment(df_mega):
    """ taxonomic_environment_assignment"""
    ic()
    # "taxa_marine",
    # "taxa_terrestrial_or_freshwater"

    conditions = [
         ((df_mega["taxa_marine"]) & (df_mega["taxa_terrestrial_or_freshwater"])),
         ((df_mega["taxa_marine"]) & (df_mega["taxa_terrestrial_or_freshwater"] is False)),
         ((df_mega["taxa_marine"] is False) & (df_mega["taxa_terrestrial_or_freshwater"])),
         ((df_mega["taxa_marine"] is False) & (df_mega["taxa_terrestrial_or_freshwater"] is False))
    ]

    values = ["marine and freshwater", "taxa_marine", "taxa_terrestrial_or_freshwater", "undetermined"]
    df_mega['taxonomic_environment'] = np.select(conditions, values, default = "undetermined")
    ic(df_mega['taxonomic_environment'].value_counts())
    df_mega['taxonomic_environment'] = df_mega['taxonomic_environment'].astype('category')

    return df_mega



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


def merge_in_all_categories(df_merge_combined_tax, df_merged_all_categories):
    """merge_in_all_categories
        Doing this as only included for metag and tax env. by default
        N.B. this massively consumes memory.
    :param df_merge_combined_tax:
    :param df_merged_all_categories:
    :return: df_merge_combined_tax
    """
    ic()
    ic(df_merge_combined_tax.head())
    # ic(df_merge_combined_tax.shape[0])
    ic(df_merged_all_categories.head())
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

    #cleanup
    df_merge_combined_tax['sea_total'] = df_merge_combined_tax['sea_total'].fillna(0).astype(int)
    df_merge_combined_tax['land_total'] = df_merge_combined_tax['land_total'].fillna(0).astype(int)

    ic(df_merge_combined_tax.shape[0])
    ic(df_merge_combined_tax.sample(n = 5))

    return df_merge_combined_tax

def apply_rules(df, marine_NCBI_to_marine_dict, conf_score, dom_type, dom_coord_designation, taxa_term, coord_dom_total, count_of_sample_having_dom_coords):
        """apply_rules
            Applies logic to generate a numerical confidence score for this domain: marine or terrestrial
            allows some to be both! Need to tighten this up if want this to be categorical and a sample can only be
            in one:

            marine
            terrestrial
            marine and terrestrial

        :param df:
        :param conf_score: column name to fill out with the numerical score for this domain type
        :param dom_type: marine or terrestrial
        :param dom_coord_designation: from GPS coordinates/shapefile hits, if marine or terrestrial
        :param taxa_term: from metagenome or environmental taxa for if marine or freshwater(terrestrial)
        :param coord_dom_total: the total different shapefiles hit by GPS coordinates/shapefile hits:
                 if marine(sea) or terrestrial(
        :param count_of_sample_having_dom_coords: number of other samples for the same taxa with GPS coordinates/
                 shapefile hits, if marine or terrestrial
        :return: df
        """
        ic()
        ic(df.sample(n=3))

        ic(dom_type)

        # set the defaults
        df[conf_score] = 0
        #Label(conf_score_inc_biome, text =  conf_score + "_inc_biome")

        """ rules, ordered by score as subsequent rule matches will overwrite earlier
           some rules that would not add further score are commented, but left here for completeness or later changes
        """

        df["opp_location_designation"] = "none"
        if dom_type == "marine" or dom_type == "terrestrial":
            df.loc[df[taxa_term] == True, [conf_score]] = 1
            df.loc[df[dom_coord_designation] == True, [conf_score]] = 1

            df.loc[(df["location_designation"] == 'marine'), "opp_location_designation"] = "terrestrial"
            df.loc[(df["location_designation"] == 'terrestrial'), "opp_location_designation"] = "marine"

            #This often lowers the score:
            df.loc[(df["location_designation"] == 'marine and terrestrial') & (df[taxa_term] == False), [conf_score]] = 0.5

            #e.g. multiple samples in same domain by coordinates - not convinced on score
            #df.loc[(df[count_of_sample_having_dom_coords] > 1) & (df["location_designation"] == 'marine and terrestrial')\
            #        , [conf_score]] = 1.5
            df.loc[(df[coord_dom_total] == 1) & (df[taxa_term] == True), [conf_score]] = 1.5
            df.loc[(df["location_designation"] == 'marine and terrestrial') & (df[taxa_term] == True), [conf_score]] = 1.5

            #Coping with particularly marine cases where the GPS coordinates are wrong or absebnt , but the taxonomy are clear

            df.loc[(df[dom_coord_designation] == False) & (df[taxa_term] == True) &
                   (df["opp_location_designation"] == False), [conf_score]] = 1.5
            df.loc[(df["lat"].isna()) & (df[taxa_term] == True) & (df["opp_location_designation"] == False), [conf_score]] = 2

            df.loc[(df[coord_dom_total] > 1) & (df[dom_coord_designation] == True), [conf_score]] = 2

            #(df["location_designation"] == 'marine and terrestrial')
            #next is the highest confidence as multiple hits of relevant shapefiles and a relevant taxonomy
            df.loc[(df[coord_dom_total] > 1) & (df[taxa_term] == True) & (df["opp_location_designation"] == False), [conf_score]] = 3

            if dom_type == "marine":
                ic(marine_NCBI_to_marine_dict)
                ic(df['NCBI-to-marine'].value_counts())

                for NCBI_to_marine_param in marine_NCBI_to_marine_dict:
                    ic(NCBI_to_marine_param)
                    tmp = marine_NCBI_to_marine_dict[NCBI_to_marine_param]
                    for terra_param in tmp['NCBI-to-terrestrial-or-freshwater']:
                        message = "if marine \"" + NCBI_to_marine_param + "\" and terra_param: \"" + terra_param + "\" - confidence factor of this dependency: "
                        ic(message, tmp['NCBI-to-terrestrial-or-freshwater'][terra_param])
                        df.loc[(df[taxa_term] == True) & (df['NCBI-to-marine'] == terra_param) & (df[conf_score] <= 2), conf_score] += 1 * tmp['NCBI-to-terrestrial-or-freshwater'][terra_param]
                        df.loc[(df[taxa_term] == False) & (df['NCBI-to-marine'] == terra_param), conf_score] -= 1 * tmp['NCBI-to-terrestrial-or-freshwater'][terra_param]
                    ic('***************************************')

            ic(df[taxa_term].value_counts())
            ic(df["opp_location_designation"].value_counts())

            #ic(df.sample(n=250))

        elif dom_type == "marine_and_terrestrial":
            df.loc[(df["taxa_marine"] == True) & (df["taxa_terrestrial_or_freshwater"] == True), [
                conf_score]] = 2
            df.loc[(df["location_designation"] == 'marine and terrestrial')\
                    , [conf_score]] += 0.5

        else:
            ic("ERROR: should never get here!")

        df = df.drop(["opp_location_designation"], axis = 1)

        #Tops ups by automated regex high level mapping of the environment_biome ena field etc.
        conf_score_inc_biome = conf_score + "_inc_biome"
        df[conf_score_inc_biome] = df[conf_score]
        df.loc[(df["environment_biome_hl"] == dom_type), [conf_score_inc_biome]] += 1
        df.loc[(df["environment_biome_hl"] == "marine_and_terrestrial"), [conf_score_inc_biome]] += 0.5
        if dom_type == "terrestrial":
            df.loc[(df["environment_biome_hl"] == "terrestrial_probable"), [conf_score_inc_biome]] += 0.5

        ic(df[conf_score].value_counts().sort_values())
        ic(df[conf_score_inc_biome].value_counts().sort_values())

        ic(df.head())
        ic(df.shape)
        #to restrict this to certain
        #df = df.query('(tax_id == 408172) or (tax_id == 939928) or (tax_id == 408170) or (tax_id == 1561972)')
        ic(df.sample(n=5))

        return df

def scores2categories(df, conf_score, conf_field):
        """ scores2categories
            convert the confidence scores to a categorical value and capture in conf_field
            ["zero", "low", "medium", "high"]
        :param df:
        :param conf_score:
        :param conf_field:
        :return: df
        usage: df = scores2categories(df, conf_score, conf_field)
        """
        ic()
        ic(conf_score, conf_field)
        #ic(df[conf_score].value_counts())

        condlist = [
            df[conf_score] <= 0,
            df[conf_score] <= 1,
            df[conf_score] <= 2,
            df[conf_score] > 2
        ]
        choicelist = ["zero", "low", "medium", "high"]
        df[conf_field] = np.select(condlist, choicelist, default = "zero")
        df[conf_field] = df[conf_field].astype('category')
        ic(df[conf_field].value_counts())
        return df
def dom_confidence_special(df, marine_NCBI_to_marine_dict, special_dom):
    """

    :param df_merge_combined_tax:
    :param marine_NCBI_to_marine_dict:
    :param special_dom:
    :return:

    for freshwater population 
    'sample_confidence_freshwater_score_inc_biome', 'sample_confidence_freshwater_confidence_inc_biome'

    usage:  dom_confidence_special(df_merge_combined_tax, marine_NCBI_to_marine_dict, "freshwater")
    """
    ic()
    if (special_dom == "freshwater"):
        # sample_confidence_freshwater_score  sample_confidence_freshwater_score_inc_biome sample_confidence_freshwater
        # sample_confidence_terrestrial_inc_freshwater,count_of_samples_having_freshwater_coords
        cols2keep = ["accession", "scientific_name", "environment_biome", "environment_biome_hl", "environment_biome_hl2", "freshwater_total", "sample_confidence_freshwater_score", "sample_confidence_freshwater_score_inc_biome", "sample_confidence_freshwater", "sample_confidence_terrestrial_inc_freshwater", "count_of_samples_having_freshwater_coords"]
        df_tmp = df[cols2keep]
        df_tmp = df_tmp.query('freshwater_total > 1')
        df_tmp = df_tmp[df_tmp['environment_biome'].str.len() > 3]
        ic(df_tmp["scientific_name"].value_counts())
        ic(df_tmp["environment_biome"].value_counts())
        ic(df_tmp["environment_biome_hl2"].value_counts())
        ic(df_tmp.sample(n = 10))

        df.sample_confidence_freshwater_score = 0

        df.loc[(df.freshwater_total > 0), 'sample_confidence_freshwater_score'] = 1
        df.loc[(df.freshwater_total > 1), 'sample_confidence_freshwater_score'] = 1.5
        df.loc[(df.freshwater_total > 2) & (df.location_designation == "terrestrial"), 'sample_confidence_freshwater_score'] = 2
        df.loc[(df.freshwater_total > 2) & (df.taxa_terrestrial_or_freshwater == True), 'sample_confidence_freshwater_score'] = 2.5
        df.loc[(df.freshwater_total > 3), 'sample_confidence_freshwater_score'] = 3

        pattern = r'freshwater|lake|river'
        df.loc[(df.scientific_name.str.contains(pattern)), 'sample_confidence_freshwater_score'] += 1
        pattern = r'soil|mouse|fungus'
        df.loc[(df.scientific_name.str.contains(pattern)), 'sample_confidence_freshwater_score'] -= 0.5
        df['sample_confidence_freshwater_score_inc_biome'] = df['sample_confidence_freshwater_score']
        df.loc[(df.environment_biome_hl2 == "freshwater"), 'sample_confidence_freshwater_score_inc_biome'] += 1
        df.loc[(df.environment_biome_hl2 == "other_terrestrial_water"), 'sample_confidence_freshwater_score_inc_biome'] += 0.5
        df.loc[(df.environment_biome_hl2 == "land"), 'sample_confidence_freshwater_score_inc_biome'] -=1
        df.loc[(df.environment_biome_hl == "marine"), 'sample_confidence_freshwater_score_inc_biome'] -= 0.5
        # having to be careful, not many species have taxa designation
        df.loc[(df.taxa_terrestrial_or_freshwater == False), 'sample_confidence_freshwater_score_inc_biome'] -= 0.5

        df = scores2categories(df, 'sample_confidence_freshwater_score_inc_biome', 'sample_confidence_freshwater_confidence_inc_biome')

        ic(df.query('sample_confidence_freshwater_score_inc_biome > 2').sample(n=10))
        # cols2keep = ["accession", "scientific_name", "taxa_terrestrial_or_freshwater", "NCBI-to-terrestrial-or-freshwater", "environment_biome", "environment_biome_hl",
        #              "environment_biome_hl2", "freshwater_total", "sample_confidence_freshwater_score",
        #              "sample_confidence_freshwater_score_inc_biome", 'sample_confidence_freshwater_confidence_inc_biome',
        #              "sample_confidence_freshwater",
        #              "sample_confidence_terrestrial_inc_freshwater", "count_of_samples_having_freshwater_coords"]
        #
        # df_tmp = df[cols2keep]
        # df_tmp = df_tmp.query('sample_confidence_freshwater_score_inc_biome > 1')
        # ic(df_tmp["scientific_name"].value_counts())
        # sys.exit()
        # ic(df_tmp.query('sample_confidence_freshwater_score_inc_biome > 2').sample(n=20))
        # # df_tmp = df_tmp.query('freshwater_total > 1')
        # # df_tmp = df_tmp[df_tmp['environment_biome'].str.len() > 3]
        # df_tmp = df_tmp.query('sample_confidence_freshwater_score_inc_biome > 1 & sample_confidence_freshwater_score_inc_biome <= 2')
        # ic(df_tmp["scientific_name"].value_counts())
        # ic(df_tmp["environment_biome"].value_counts())
        # ic(df_tmp["environment_biome_hl2"].value_counts())
        #
        # ic(df_tmp["environment_biome_hl2"].value_counts())
        #
        # ic(df_tmp.sample(n = 10))
        # ic(df_tmp["taxa_terrestrial_or_freshwater"].value_counts())
        # ic(df_tmp["NCBI-to-terrestrial-or-freshwater"].value_counts())
        #
        # sys.exit()

    return df

def dom_confidence(df_merge_combined_tax, marine_NCBI_to_marine_dict, conf_field, conf_field_inc_biome):
        """dom_confidence
            method to add the domain(e.g. marine) evidence
        :param df_merge_combined_tax:
        :param conf_field i.e. "sample_confidence_marine" or "sample_confidence_terrestrial":
        :return:
        """
        ic()

        conf_score = conf_field + '_score'
        ic(df_merge_combined_tax.sample(n=5))
        count_field = ""
        if(conf_field == "sample_confidence_marine"):
            df_tmp = df_merge_combined_tax[["tax_id", "scientific_name", "location_designation_marine", "sea_total", "taxa_marine"]]
            df_tmp["location_designation_marine_conf"] = False
            df_tmp = df_tmp.query('sea_total > 1')
            count_field = "count_of_samples_having_marine_coords"
        elif(conf_field == "sample_confidence_terrestrial"):
            df_tmp = df_merge_combined_tax[["tax_id", "scientific_name", "location_designation_terrestrial", "land_total", "taxa_terrestrial_or_freshwater"]]
            df_tmp = df_tmp.query('land_total >= 1')
            count_field = "count_of_samples_having_terrestrial_coords"
        elif(conf_field == "sample_confidence_marine_and_terrestrial"):
             df_tmp = df_merge_combined_tax[["tax_id", "scientific_name", "location_designation"]]
             df_tmp = df_tmp.query('location_designation == "marine and terrestrial"')
             count_field = "count_of_samples_having_marine_and_terrestrial_coords"
        elif(conf_field == "sample_confidence_freshwater"):
            df_tmp = df_merge_combined_tax[["tax_id", "scientific_name", "location_designation_terrestrial", "freshwater_total", "taxa_terrestrial_or_freshwater"]]
            df_tmp = df_tmp.query('freshwater_total >= 1')
            count_field = "count_of_samples_having_freshwater_coords"
        else:
            ic("ERROR: conf_field is unknown: " + conf_field)
            sys.exit()
        df_species = df_tmp.groupby(["tax_id"]). \
            size().to_frame('count').reset_index().fillna(False).set_index("tax_id")
        df_species["count"] = df_species["count"].astype(int)
        df_species = df_species.rename(columns = {"count": count_field})

        ic(df_species.head())
        ic(f"about to do pd.merge for: {count_field}")
        df = pd.merge(df_merge_combined_tax, df_species, on="tax_id", how="left")
        df[count_field] = df[count_field].fillna(0).astype(int)
        ic(df.sample(n=3))
        ic(df.environment_biome_hl.value_counts())

        # if conf_field == "sample_confidence_freshwater":
        #
        #     sys.exit()

        if (conf_field == "sample_confidence_marine"):
            dom_type = "marine"
            dom_coord_designation = "location_designation_" + dom_type
            taxa_term = "taxa_marine"
            coord_dom_total = "sea_total"
            count_of_sample_having_dom_coords = "count_of_samples_having_marine_coords"
        elif (conf_field == "sample_confidence_terrestrial"):
            dom_type = "terrestrial"
            dom_coord_designation = "location_designation_" + dom_type
            taxa_term = "taxa_terrestrial_or_freshwater"
            coord_dom_total = "land_total"
            count_of_sample_having_dom_coords = "count_of_samples_having_terrestrial_coords"
        else:
            dom_coord_designation = taxa_term = coord_dom_total = count_of_sample_having_dom_coords = "to stop IDE warnings"
            dom_type = "marine_and_terrestrial"
            count_of_sample_having_dom_coords = "count_of_samples_having_marine_and_terrestrial_coords"
        df = apply_rules(df, marine_NCBI_to_marine_dict, conf_score, dom_type, dom_coord_designation, taxa_term, coord_dom_total, count_of_sample_having_dom_coords)
        df = scores2categories(df, conf_score, conf_field)

        conf_score_inc_biome = conf_score + "_inc_biome"
        df = scores2categories(df, conf_score_inc_biome, conf_field_inc_biome)
        #df_selected = ~df[df[conf_field_inc_biome] == df[conf_field]]
        ic(conf_field_inc_biome, conf_field)
        # df_selected = df.query('`{0}` != `{1}`'.format(conf_field_inc_biome, conf_field))
        # if df_selected.shape[0] > 0:
        #     ic(df_selected.sample(n=5, replace=True))
        # else:
        #     ic("sorry: no rows")

        df_grouped = df.groupby([conf_field_inc_biome, conf_field]).size().to_frame('count').reset_index()
        ic(df_grouped.head(10))
        ic("*********************************************************")
        ic(df.columns)
        ic(df.head())
        ic()
        return df


def add_combined_single_domain_call_score(df_merge_combined_tax):
    """

    :param df_merge_combined_tax:
    :return: df
    """
    ic()
    df = df_merge_combined_tax
    df["combined_location_designation_confidence"] = "low"
    df.loc[(df["combined_location_designation"] == "marine") & (df["sample_confidence_marine_inc_biome"] == 'high') & ((df["sample_confidence_terrestrial_inc_biome"] == 'low') | (df["sample_confidence_terrestrial_inc_biome"] == 'zero')),  "combined_location_designation_confidence"] = "high"

    df.loc[(df["combined_location_designation"] == "marine") & (df["sample_confidence_terrestrial_inc_biome"] == 'medium'),
    "combined_location_designation_confidence"] = "medium"

    df.loc[(df["combined_location_designation"] == "marine") & (df["sample_confidence_marine_inc_biome"] == 'medium') & (df["sample_confidence_terrestrial_inc_biome"] == 'zero'),
            "combined_location_designation_confidence"] = "high"
    #############################################

    df.loc[(df["combined_location_designation"] == "terrestrial") & (df["sample_confidence_terrestrial_inc_biome"] == 'high') & \
           ((df["sample_confidence_marine_inc_biome"] == 'low') | (df["sample_confidence_marine_inc_biome"] == 'zero')),\
    "combined_location_designation_confidence"] = "high"

    df.loc[(df["combined_location_designation"] == "terrestrial") & (df["sample_confidence_terrestrial_inc_biome"] == 'medium'),\
            "combined_location_designation_confidence"] = "medium"

    df.loc[(df["combined_location_designation"] == "terrestrial") & (df["sample_confidence_terrestrial_inc_biome"] == 'medium') & \
            (df["sample_confidence_marine_inc_biome"] == 'zero'), "combined_location_designation_confidence"] = "high"
   #############################################

    df.loc[(df["combined_location_designation"] == "marine_and_terrestrial") & \
           (df["sample_confidence_marine_and_terrestrial_inc_biome"] == 'high'),\
           "combined_location_designation_confidence"] = "high"
    df.loc[(df["combined_location_designation"] == "marine_and_terrestrial") & (
                df["sample_confidence_marine_and_terrestrial_inc_biome"] == 'medium'),\
                "combined_location_designation_confidence"] = "medium"
    df.loc[(df["combined_location_designation"] == "marine_and_terrestrial") & (
                df["sample_confidence_marine_and_terrestrial_inc_biome"] == 'low') \
           & ((df["sample_confidence_marine_inc_biome"] == 'high') | (df["sample_confidence_marine_inc_biome"] == 'medium')) & \
            ((df["sample_confidence_terrestrial_inc_biome"] == 'high') | (df["sample_confidence_terrestrial_inc_biome"] == 'medium')), \
            "combined_location_designation_confidence"] = "high"

    return df

def make_combined_single_domain_call(df_merge_combined_tax):
    """
     make a single combined domain call

    :param df_merge_combined_tax:
    :return: df
    usage: df = make_combined_single_domain_call(df_merge_combined_tax)
    """
    ic()
    ic(df_merge_combined_tax.columns)
    ic(df_merge_combined_tax.shape)
    df = df_merge_combined_tax
    key_cols = ["scientific_name","sample_confidence_marine_inc_biome", "sample_confidence_terrestrial_inc_biome", "sample_confidence_marine_and_terrestrial_inc_biome"]
    df_grouped = df.groupby(key_cols).size().to_frame('count').reset_index()
    ic(df_grouped.head(10))

    df["combined_location_designation"] = "none"

    zero_low = ['low', 'zero']
    df.loc[((df["sample_confidence_terrestrial_inc_biome"] == 'high') | (df["sample_confidence_terrestrial_inc_biome"] == 'medium')) &
           ((df["sample_confidence_marine_inc_biome"] == 'low') | (df["sample_confidence_marine_inc_biome"] == 'zero')), "combined_location_designation"] = "terrestrial"

    df.loc[((df["sample_confidence_terrestrial_inc_biome"] == 'high') | (
                df["sample_confidence_terrestrial_inc_biome"] == 'medium')) &
           ((df["sample_confidence_marine_inc_biome"] == 'high') | (df[
                                                                       "sample_confidence_marine_inc_biome"] == 'medium')), "combined_location_designation"] = "marine_and_terrestrial"

    df.loc[((df["sample_confidence_marine_inc_biome"] == 'high') |(df["sample_confidence_marine_inc_biome"] == 'medium')) & ((df["sample_confidence_terrestrial_inc_biome"] == 'low')
        | ((df["sample_confidence_terrestrial_inc_biome"] == 'zero') | (df["sample_confidence_terrestrial_inc_biome"] == 'low'))), "combined_location_designation"] = "marine"
    df.loc[df["sample_confidence_marine_and_terrestrial_inc_biome"] == 'high', "combined_location_designation"] = "marine_and_terrestrial"
    df.loc[((df["sample_confidence_terrestrial_inc_biome"] == 'low') | (df["sample_confidence_terrestrial_inc_biome"] == 'zero')) & ((df["sample_confidence_terrestrial_inc_biome"] == 'low') | (df["sample_confidence_terrestrial_inc_biome"] == 'zero')) & (df["sample_confidence_marine_and_terrestrial_inc_biome"] == 'medium'), "combined_location_designation"] = "marine_and_terrestrial"
    df.loc[(df["sample_confidence_marine_inc_biome"] == 'high') & ((df["sample_confidence_terrestrial_inc_biome"] == 'low') | (df["sample_confidence_terrestrial_inc_biome"] == 'zero')), "combined_location_designation"] = "marine"
    df.loc[(df["sample_confidence_terrestrial_inc_biome"] == 'high') & ((df["sample_confidence_marine_inc_biome"] == 'low') | (df["sample_confidence_marine_inc_biome"] == 'zero')), "combined_location_designation"] = "terrestrial"

    #some remedial
    df.loc[(df["combined_location_designation"] == "marine_and_terrestrial") & (df["NCBI-to-terrestrial-or-freshwater"] == "is not"), "combined_location_designation"] = "marine"
    df.loc[(df["combined_location_designation"] == "marine_and_terrestrial") & (
                df["NCBI-to-marine"] == "is not"), "combined_location_designation"] = "terrestrial"
    df.loc[(df["combined_location_designation"] == "terrestrial") & (df["NCBI-to-marine"] == "may be exclusively"), "combined_location_designation"] = "marine_and_terrestrial"
    df.loc[(df["combined_location_designation"] == "marine") & (df["NCBI-to-terrestrial-or-freshwater"] == "may be exclusively"), "combined_location_designation"] = "marine_and_terrestrial"
    df.loc[(df["combined_location_designation"] == "none") & (df["NCBI-to-terrestrial-or-freshwater"] == "may be exclusively"), "combined_location_designation"] = "terrestrial"
    df.loc[(df["combined_location_designation"] == "none") & (df["NCBI-to-marine"] == "may be exclusively"), "combined_location_designation"] = "marine"

    df.loc[(df["combined_location_designation"] == "none") & (len(df["location_designation"])>5), "combined_location_designation"] = df["location_designation"]
    #cope with a use case of the above
    df.loc[(df["combined_location_designation"] == "marine and terrestrial"), "combined_location_designation"] = "marine_and_terrestrial"
    ic(df.query('combined_location_designation == "marine_and_terrestrial"'))
    ic(df.head(2))
    ic(df.query('combined_location_designation == "marine_and_terrestrial"').head(2))


    key_cols.append("combined_location_designation")
    ic(key_cols)
    df_grouped = df.groupby(key_cols).size().to_frame('count').reset_index().sort_values(by=["sample_confidence_marine_and_terrestrial_inc_biome"])
    ic(df_grouped.head(10))
    ic(df["combined_location_designation"].value_counts())

    # tmp_keys = ["scientific_name", "NCBI-to-marine", "NCBI-to-terrestrial-or-freshwater","combined_location_designation"]
    # ic(df[tmp_keys].query('combined_location_designation == "marine_and_terrestrial"').sample(n=1000))

    ic(df["NCBI-to-marine"].value_counts())
    ic()
    ic("Doing some hight level checks using the taxonomy")
    ic(df.query('combined_location_designation == "terrestrial" and `NCBI-to-marine` == "is exclusively"').shape[0])
    ic(df.query('combined_location_designation == "terrestrial" and `NCBI-to-marine` == "may be exclusively" ').shape[0])
    ic(df.query('combined_location_designation == "terrestrial" and `NCBI-to-terrestrial-or-freshwater` == "is not" ').shape[0])
    ic(df.query(
        'combined_location_designation == "terrestrial" and `NCBI-to-terrestrial-or-freshwater` == "not flagged as" ').shape[0])
    ic(df.query('combined_location_designation == "terrestrial" and `NCBI-to-terrestrial-or-freshwater` == "is exclusively"').shape[0])
    ic(df.query('combined_location_designation != "terrestrial" and `NCBI-to-terrestrial-or-freshwater` == "is exclusively"').shape[0])
    ic(df.query('combined_location_designation == "terrestrial" and `NCBI-to-terrestrial-or-freshwater` == "may be exclusively" ').shape[0])
    ic(df.query('combined_location_designation != "terrestrial" and `NCBI-to-terrestrial-or-freshwater` == "may be exclusively" ').shape[0])
    ic("*********************************************************")
    ic(df.query('combined_location_designation == "marine" and `NCBI-to-terrestrial-or-freshwater` == "is exclusively"').shape[0])
    ic(df.query('combined_location_designation == "marine" and `NCBI-to-terrestrial-or-freshwater` == "may be exclusively"').shape[0])
    ic(df.query('combined_location_designation == "marine" and `NCBI-to-marine` == "is not"').shape[0])
    ic(df.query('combined_location_designation == "marine" and `NCBI-to-marine` == "not flagged as"').shape[0])
    ic(df.query('combined_location_designation == "marine" and `NCBI-to-marine` == "is exclusively"').shape[0])
    ic(df.query('combined_location_designation != "marine" and `NCBI-to-marine` == "is exclusively"').shape[0])
    ic(df.query('combined_location_designation == "marine" and `NCBI-to-marine` == "may be exclusively"').shape[0])
    ic(df.query('combined_location_designation != "marine" and `NCBI-to-marine` == "may be exclusively"').shape[0])
    ic("*********************************************************")
    ic(df.query('combined_location_designation == "marine_and_terrestrial" and `NCBI-to-marine` == "is not"').shape[0])
    ic(df.query('combined_location_designation == "marine_and_terrestrial" and `NCBI-to-marine` == "not flagged as"').shape[0])
    ic(df.query('combined_location_designation == "marine_and_terrestrial" and `NCBI-to-terrestrial-or-freshwater` == "is not"').shape[0])
    ic(df.query('combined_location_designation == "marine_and_terrestrial" and `NCBI-to-terrestrial-or-freshwater` == "not flagged as"').shape[0])


    ic("*********************************************************")
    ic(df["combined_location_designation"].value_counts())

    df = add_combined_single_domain_call_score(df)

    df_to_check = df.query('combined_location_designation != "marine" and `NCBI-to-marine` == "may be exclusively"')
    ic(df_to_check[key_cols].shape[0])
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    out_file = analysis_dir + "tmp_check_df.tsv"
    df_to_check.to_csv(out_file, sep = '\t')

    return df


def addConfidence(df_merge_combined_tax):
    """addConfidence
        adding confidence for metadata assignments
        want to try and separate into 3 categories: "marine, marine and terrestrial and terrestrial"
    :param df_merge_combined_tax:
    :return:
    """
    ic()
    ic(df_merge_combined_tax.shape)
    ic(df_merge_combined_tax.sample(n=5))

    #df_merge_combined_tax = df_merge_combined_tax.head(1000000).query('taxonomic_source == "metagenome"')

    ic(df_merge_combined_tax.columns)
    # df = df_merge_combined_tax.query('`NCBI term` == "Piscirickettsia salmonis"')
    df = df_merge_combined_tax[["tax_id", "location_designation", "location_designation_marine", "location_designation_terrestrial", "environment_biome"]]

    taxonomy_map_conf_flags = get_taxonomy_mapping_confidence_flags()
    ic(taxonomy_map_conf_flags)
    tmp = taxonomy_map_conf_flags['taxa_marine']
    marine_NCBI_to_marine_dict = tmp['NCBI-to-marine']
    ic(marine_NCBI_to_marine_dict)

    df_merge_combined_tax["taxa_marine"] = df_merge_combined_tax["taxa_marine"].fillna(False)
    df_merge_combined_tax["taxa_terrestrial_or_freshwater"] = df_merge_combined_tax["taxa_terrestrial_or_freshwater"].fillna(False)
    df_merge_combined_tax = process_environment_biome(df_merge_combined_tax)
    ic(df_merge_combined_tax.sample(n=5))   #definitely working!
    ic(df_merge_combined_tax.shape)
    ic("*********************************************************")

    df_merge_combined_tax = dom_confidence(df_merge_combined_tax, marine_NCBI_to_marine_dict, "sample_confidence_marine", "sample_confidence_marine_inc_biome")
    ic(df_merge_combined_tax.shape)
    ic("*********************************************************")
    df_merge_combined_tax = dom_confidence(df_merge_combined_tax, marine_NCBI_to_marine_dict, "sample_confidence_terrestrial", "sample_confidence_terrestrial_inc_biome")
    df_merge_combined_tax = dom_confidence(df_merge_combined_tax, marine_NCBI_to_marine_dict,
                                           "sample_confidence_freshwater", "sample_confidence_terrestrial_inc_freshwater")
    ic("*********************************************************")
    df_merge_combined_tax = dom_confidence(df_merge_combined_tax, marine_NCBI_to_marine_dict, "sample_confidence_marine_and_terrestrial", "sample_confidence_marine_and_terrestrial_inc_biome")
    df_merge_combined_tax = dom_confidence_special(df_merge_combined_tax, marine_NCBI_to_marine_dict, "freshwater")

    ic(df_merge_combined_tax.sample(n = 5))  #taxa marine etc.mix of True and False

    ic(df_merge_combined_tax.head())
    ic(df_merge_combined_tax.query('(sample_confidence_marine_inc_biome == "high") & (sample_confidence_terrestrial_inc_biome == "high")').head())
    ic(df_merge_combined_tax.query(
        '(sample_confidence_marine_inc_biome == "low") & (sample_confidence_terrestrial_inc_biome == "low")').sample(
        n = 5, replace = True))
    ic(df_merge_combined_tax.query(
        '(sample_confidence_marine_inc_biome == "low") & (sample_confidence_terrestrial_inc_biome == "medium")').sample(
        n = 5, replace = True))

    # do a confidence:  conflict matrix, first. and the share with Josie and Stephane
    # do as numeric, + or - for pieces of evidence and then use threshold for the H/M/L/Zero   - look for missing rules
    # give more weight to conflict or missing?  Should missing be False?   Have a field for missing coordinates and similar taxonomy marine/freshwater assignment?
    # use the environmental_biome + coastal
    # N.B. do the GPS coordinates granularity, as another column? -
    # what if low granularity, do polygon searching?
    # first off, do a search of the relative amount of granularity

    # # what if other samples have GPS but particular ones don't?

    #ic(df_merge_combined_tax.sample(n = 250)) # all fine!
    ic("about to leave the following")
    ic()
    return df_merge_combined_tax
def get_lon_lat_dps(sample_dir):
    """ get the properties with the number of decimal places for lon and lat
    usage  df_lon_lat_dps = get_lon_lat_dps()
    :return:
    """
    df_lon_lat_dps = pd.read_csv(sample_dir + "dps.txt")
    df_lon_lat_dps["lat_dps"] = df_lon_lat_dps["lat_dps"].astype(int)
    df_lon_lat_dps["lon_dps"] = df_lon_lat_dps["lon_dps"].astype(int)
    ic(df_lon_lat_dps.head())
    return df_lon_lat_dps

def analyse_lon_lat_dps(df_merge_combined_tax_all_with_confidence, analysis_dir, df_lon_lat_dps):
    """

    :return: df_merge_combined_tax_all_with_confidence
    """
    ic()
    df_merge_combined_tax_all_with_confidence = pd.merge(df_merge_combined_tax_all_with_confidence,df_lon_lat_dps,how="left", on="accession")
    df_merge_combined_tax_all_with_confidence["lat_dps"] = df_merge_combined_tax_all_with_confidence["lat_dps"].fillna(0).astype(int)
    df_merge_combined_tax_all_with_confidence["lon_dps"] = df_merge_combined_tax_all_with_confidence["lon_dps"].fillna(0).astype(int)
    # ic(df_merge_combined_tax_all_with_confidence.head())
    df = df_merge_combined_tax_all_with_confidence
    ic(df.sample(n=3))
    my_cols = ["accession","sample_confidence_marine_inc_biome", "sample_confidence_terrestrial_inc_biome", "sample_confidence_marine_and_terrestrial_inc_biome","lat_dps","lon_dps"]
    df_mini = df[my_cols]
    ic(df_mini.sample(n=7))
    my_cols = ["sample_confidence_marine_inc_biome", "sample_confidence_terrestrial_inc_biome", "sample_confidence_marine_and_terrestrial_inc_biome","lat_dps","lon_dps"]
    df_group = df_mini.groupby(my_cols).size().reset_index(name='counts').sort_values("counts", ascending = False)
    ic(df_group.head())
    ic(df_group.shape)
    out_file = analysis_dir + 'merge_combined_tax_all_with_confidence_dps_analysis.tsv'
    # ic(out_file)
    # df_group.to_csv(out_file, sep="\t", index=False)

    return df_merge_combined_tax_all_with_confidence

def get_ordered_score_dict():
    """
    usage: (ordered_score_array,ordered_score_dict) = get_ordered_score_array()
    """
    choicelist = ["zero", "low", "medium", "high"]
    ordered_score_dict = {}

    for i in range(4):
        ordered_score_dict[choicelist[i]] = i

    return choicelist, ordered_score_dict

def make_blue_domain_call(df_merge_combined_tax):
    """make_blue_domain_call

    :param df_merge_combined_tax:
    :return: df_merge_combined_tax

    usage: df_merge_combined_tax = make_blue_domain_call(df_merge_combined_tax)
    """
    ic(df_merge_combined_tax.columns)

    def determine_blue_dom_vector(df,ordered_score_dict):
        """

        :param df:
        :param ordered_score_dict:
        :return:
        """
        ic()
        df["blue_partition"] = "False"
        #will overwrite this
        df["blue_partition_confidence"] = df["combined_location_designation_confidence"]
        df.loc[(df["combined_location_designation"] != "marine_and_terrestrial") | \
               (df["combined_location_designation"] != "marine"), "blue_partition_confidence"] = "zero"
        df.loc[(df["combined_location_designation"] == "marine"), "blue_partition"] = "marine"
        df.loc[(df["combined_location_designation"] == "marine_and_terrestrial"), "blue_partition"] = "marine_and_terrestrial"
        df.loc[(df["combined_location_designation"] == "marine") | (df["combined_location_designation"] == "marine_and_terrestrial"), \
            "blue_partition_confidence"] = df["combined_location_designation_confidence"]

        ic(df["combined_location_designation"].value_counts())

        df.loc[((df["combined_location_designation"] == "terrestrial") & (df["sample_confidence_freshwater_confidence_inc_biome"] == "high")), \
            "blue_partition"] = "freshwater"
        df.loc[((df["combined_location_designation"] == "terrestrial") & (
                    df["sample_confidence_freshwater_confidence_inc_biome"] == "high")), \
            "blue_partition_confidence"] = "high"
        df.loc[((df["combined_location_designation"] == "terrestrial") & (
                    df["sample_confidence_freshwater_confidence_inc_biome"] == "medium")), \
            "blue_partition"] = "freshwater"
        df.loc[((df["combined_location_designation"] == "terrestrial") & (
                df["sample_confidence_freshwater_confidence_inc_biome"] == "medium")), \
            "blue_partition_confidence"] = "medium"


        ic(df.query('blue_partition == "freshwater"').sample(n=20))
        ic(df["sample_confidence_freshwater_confidence_inc_biome"].value_counts())
        ic(df["blue_partition"].value_counts())
        ic(df["blue_partition_confidence"].value_counts())
        sys.exit()

        return df

    # def determine_blue_dom(row,  ordered_score_dict):
    #     """
    #     Did as an apply. Considered vector approach, as faster, but the conditionals seemed a little too complex
    #     :param row:
    #     :param  ordered_score_dict:
    #     :return: value
    #     """
    #     blue_partition_assignment = "False"
    #     terrestrial_confidence = marine_comb_confidence = blue_partition_confidence = "zero"
    #
    #     if row["combined_location_designation"] == "marine" or row["combined_location_designation"] == "marine_and_terrestrial":
    #         blue_partition_assignment = row["combined_location_designation"]
    #         marine_comb_confidence = row["combined_location_designation_confidence"]
    #         blue_partition_confidence = marine_comb_confidence
    #     elif row["combined_location_designation"] == "terrestrial":
    #         if row["location_designation_freshwater"] == True:
    #             blue_partition_assignment = "freshwater"
    #
    #     if blue_partition_assignment != "False":
    #         # coping with cases where freshwater and marine combinations occur and using the highest confidence
    #         if ordered_score_dict[terrestrial_confidence] > ordered_score_dict[marine_comb_confidence]:
    #                if row["location_designation_freshwater"] == True:
    #                     blue_partition_assignment = "freshwater"
    #                     blue_partition_confidence = ordered_score_dict[terrestrial_confidence]
    #     row['blue_partition'] = blue_partition_assignment
    #     row['blue_partition_confidence'] = blue_partition_confidence
    #
    #     return row

    (ordered_score_array, ordered_score_dict) = get_ordered_score_dict()
    ic(ordered_score_dict)

    #pattern = r"marine"
    #matches = re.search(pattern, df_merge_combined_tax.columns)
    matches = [s for s in df_merge_combined_tax.columns if "water" in s]
    ic(matches)

    ic(df_merge_combined_tax.query('sample_confidence_marine_score_inc_biome > 0').sample(n=5))
    ic(df_merge_combined_tax["combined_location_designation"].value_counts())
    ic(df_merge_combined_tax.query('combined_location_designation == "marine"').sample(n = 5))
    ic(ordered_score_dict)
    #df_merge_combined_tax = df_merge_combined_tax.apply(determine_blue_dom, osd=ordered_score_dict, axis=1)
    df_merge_combined_tax = determine_blue_dom_vector(df_merge_combined_tax, ordered_score_dict)
    ic(df_merge_combined_tax.query('blue_partition !=  "False"').sample(n = 5))
    ic(df_merge_combined_tax["blue_partition"].value_counts())
    ic(df_merge_combined_tax["blue_partition_confidence"].value_counts())

    ic()
    return df_merge_combined_tax

def mini_exploration(df_merge_combined_tax):
    """

    :param df_merge_combined_tax:
    :return:
    """
    ic()
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()

    df_mini = df_merge_combined_tax[["lat_dps", "lon_dps", "collection_date", "combined_location_designation"]]
    df_mini = df_mini[df_mini['lat_dps'].notnull()].query('lat_dps > 0')

    # df_mini["collection_year"] = df_mini["collection_date"].astype('datetime64[ns]', errors="ignore").dt.year
    fig = px.histogram(df_mini, x = "lat_dps", log_y = True, color = "combined_location_designation")
    fig.update_xaxes(type = 'category')
    fig.update_xaxes(tickangle = 60, tickfont = dict(size = 18))
    fig.update_xaxes(categoryorder = 'array',
                     categoryarray = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13'])
    out_file = plot_dir + "merged_all_combined_lat_dps." + 'png'
    ic(out_file)
    fig.write_image(out_file)
    #fig.show()

    # df_mini["collection_year"] = df_mini["collection_date"].astype('datetime64[ns]', errors="ignore").dt.year
    fig = px.histogram(df_mini, x = "lon_dps", log_y = True, color = "combined_location_designation")
    fig.update_xaxes(type = 'category')
    fig.update_xaxes(tickangle = 60, tickfont = dict(size = 18))
    fig.update_xaxes(categoryorder = 'array',
                     categoryarray = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13'])
    out_file = plot_dir + "merged_all_combined_lon_dps." + 'png'
    ic(out_file)
    fig.write_image(out_file)
    #fig.show()

    df_mini = df_mini[~(df_mini["combined_location_designation"] == 'terrestrial')]
    fig = px.histogram(df_mini, x = "lat_dps", log_y = True, color = "combined_location_designation")
    fig.update_xaxes(type = 'category')
    fig.update_xaxes(tickangle = 60, tickfont = dict(size = 18))
    fig.update_xaxes(categoryorder = 'array',
                     categoryarray = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13'])
    out_file = plot_dir + "merged_all_combined_lat_wo_terrestrial_dps." + 'png'
    ic(out_file)
    fig.write_image(out_file)
    #fig.show()

    fig = px.histogram(df_mini, x = "lon_dps", log_y = True, color = "combined_location_designation")
    fig.update_xaxes(type = 'category')
    fig.update_xaxes(tickangle = 60, tickfont = dict(size = 18))
    fig.update_xaxes(categoryorder = 'array',
                     categoryarray = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13'])
    out_file = plot_dir + "merged_all_combined_lon_wo_terrestrial_dps." + 'png'
    ic(out_file)
    fig.write_image(out_file)
    #fig.show()

    df_mini = df_mini[df_mini['collection_date'].notnull()]

    # #df_mini["collection_date"] = df_mini["collection_date"].astype('datetime64[ns]', errors="ignore")
    # df_mini["collection_date"] = pd.to_datetime(df_mini["collection_date"], errors = 'coerce')
    # ic(df_mini.dtypes)
    # df_mini["collection_date"] = df_mini["collection_date"].dt.date
    # ic(df_mini["collection_date"].head(3))
    # start_date = pd.to_datetime('2000-01-01').date()
    # end_date = pd.to_datetime('2024-01-01').date()
    # df_mini = df_mini[(df_mini["collection_date"] > start_date) & (df_mini["collection_date"] < end_date)]
    # fig = px.scatter(df_mini, title = "Lat/Lon over time since year=2000", x = "collection_date", y = "lat_dps", width = width,
    #                  color = "combined_location_designation")
    # # cat_order = {}
    # # cat_order[]
    # # fig.update_layout(category_order= "reversed")
    # out_file = plot_dir + "merged_all_combined_lat_lon." + 'png'
    # ic(out_file)
    # fig.write_image(out_file)
    # fig.show()
    # df_mini["collection_year"] = df_mini["collection_date"].astype('datetime64[ns]', errors="ignore").dt.year
    # fig = px.histogram(df_mini, x = "collection_year", log_y=True, color = "combined_location_designation")
    # fig.update_xaxes(type = 'category')
    # fig.update_xaxes(tickangle = 60, tickfont = dict(size = 6))
    # fig.update_xaxes(categoryorder = 'category ascending')
    # out_file = plot_dir + "merged_all_combined_collection." + 'png'
    # ic(out_file)
    # fig.write_image(out_file)
    # fig.show()
    #
    # df_mini["collection_year"] = df_mini["collection_date"].astype('datetime64[ns]', errors="ignore").dt.year
    # fig = px.histogram(df_mini, x = "collection_year", log_y=True, color = "lat_dps")
    # fig.update_xaxes(type = 'category')
    # fig.update_xaxes(tickangle = 60, tickfont = dict(size = 6))
    # fig.update_xaxes(categoryorder = 'category ascending')
    # fig.show()


def add_input_stats(stats_dict, df_all_ena_sample_detail, df_tax2env):
    """

    :param stats_dict:
    :param df_all_ena_sample_detail:
    :param df_tax2env:
    :return:
    """
    stats_dict["_input_ena_sample_total_count"] = df_all_ena_sample_detail.shape[0]
    df_tmp = df_tax2env.query('taxonomy_type == "metagenome"')
    stats_dict["_input_metag_tax_id_count"] = df_tmp["NCBI:taxid"].nunique()
    df_tmp = df_tax2env.query('taxonomy_type == "environment"')
    stats_dict["_input_env_tax_id_count"] = df_tmp["NCBI:taxid"].nunique()
    stats_dict["_input_total_taxa_tax_id_count"] = df_tax2env["NCBI:taxid"].nunique()
    ic(stats_dict)
    return stats_dict


def summary_plots(df_merge_combined_tax):
    """

    :param df_merge_combined_tax:
    :return:
    """
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    df_groupby = df_merge_combined_tax.groupby(
        ["combined_location_designation", "combined_location_designation_confidence"]).size().to_frame(
        'count').reset_index()
    ic(df_groupby.head(10))

    format = 'png'
    cat = "combined_location_designation"
    title = cat
    log_y = False
    width = 1500
    other_params = {}

    u_plot_pie(df_groupby, cat, "count", cat + " sample counts", "value", plot_dir + cat + "_pie." + format)
    u_plot_hist(df_merge_combined_tax, cat, "combined_location_designation_confidence", title + "+score", log_y,
                plot_dir + cat + "_hist." + format, width, format, other_params)
    u_plot_hist(df_merge_combined_tax, cat, "combined_location_designation", title, log_y,
                plot_dir + cat + "." + format, width, format, other_params)
    u_plot_pie(df_merge_combined_tax, cat, "combined_location_designation", title, "value",
               plot_dir + cat + "_pie." + format)

    log_y = True
    u_plot_hist(df_merge_combined_tax, cat, "combined_location_designation_confidence", title + "+score" + " (log scale)",
                log_y,
                plot_dir + cat + "_score_log." + format, width, format, other_params)
    u_plot_hist(df_merge_combined_tax, cat, "combined_location_designation", title + " (log scale)", log_y,
                plot_dir + cat + "." + format,
                width, format, other_params)


def get_df_from_pickle(pickle_file):
    """

    :param pickle_file:
    :return: df
    """

    if (os.path.isfile(pickle_file) == True):
        df = get_pickleObj(pickle_file)
    else:
        ic("ERROR, can't read ", pickle_file)
        sys.exit()
    return df


def main(verbosity, stage, debug_status):
    """ main
        __params__: verbosity
        __params__: stage for data_testing_down_stream
               passed_args
    """
    ic()
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()

    stats_dict = {}
    ic(analysis_dir)
    ic(plot_dir)
    df_tax2env = get_taxonomy_info(taxonomy_dir)

    # This takes over 20mins to run all the way through with a full ENA dataset as broke into chunks that can be started downstream
    if stage:
        got_data_testing_down_stream = int(stage)
    else:
        got_data_testing_down_stream = 1
    ic(got_data_testing_down_stream)

    if got_data_testing_down_stream == 1:
        ic("*********** got_data_testing_down_stream >=1 combine GPS and evidence columns")
        # get category information from hit file
        df_merged_all_categories = get_merged_all_categories_file(analysis_dir)
        # gets all sample data rows in ENA(with or without GPS coords), and a rich but limited selection of metadata files
        df_all_ena_sample_detail = get_all_ena_detailed_sample_info(debug_status)
        ic(df_all_ena_sample_detail.head())
        ic(df_all_ena_sample_detail.shape[0])
        ic('-' * 100)
        stats_dict = add_input_stats(stats_dict,df_all_ena_sample_detail, df_tax2env)
        (stats_dict, df_merge_combined_tax) = merge_ena_w_taxa(plot_dir, analysis_dir, stats_dict,
                                                                   df_all_ena_sample_detail, df_tax2env)
        ic(df_merge_combined_tax.shape[0])
        ic(df_merge_combined_tax.head(5))

        ic('-' * 100)
        df_merge_combined_tax = merge_in_all_categories(df_merge_combined_tax, df_merged_all_categories).reset_index()

        #save save some memory and get rid of some stored structures
        # ic(memory_usage())
        out_file = analysis_dir + 'merge_combined_tax.pickle'
        ic(out_file)
        put_pickleObj2File(df_merge_combined_tax, out_file, True)
    if got_data_testing_down_stream <= 2:
        ic("*********** got_data_testing_down_stream <=2 individual domain confidence calling")
        if got_data_testing_down_stream >= 2:
            df_merge_combined_tax = get_df_from_pickle(analysis_dir + 'merge_combined_tax.pickle')
            ic(df_merge_combined_tax.shape)
        df_groupby = df_merge_combined_tax.groupby(["location_designation"]).size().to_frame('count').reset_index()
        cat = "location_designation"
        out_graph_file = plot_dir + "location_designation_sample_counts_value." + "png"
        ic(df_groupby.head(10))
        u_plot_pie(df_groupby, cat, "count", cat + " sample counts", "value", out_graph_file)
        out_graph_file = plot_dir + "location_designation_sample_counts_percent." + "png"
        u_plot_pie(df_groupby, cat, "count", cat + " sample counts", "percent", out_graph_file)

        #adding in confidence rules
        df_merge_combined_tax = addConfidence(df_merge_combined_tax)
        ic(df_merge_combined_tax.columns)
        put_pickleObj2File(df_merge_combined_tax, analysis_dir + 'merge_combined_tax_all_with_confidence.pickle', True)
        out_file = analysis_dir + 'merge_combined_tax_all_with_confidence.tsv'
        ic(out_file)
        df_merge_combined_tax.to_csv(out_file, sep="\t", index=False)

    if got_data_testing_down_stream <= 3:
        ic("*********** got_data_testing_down_stream <=3 doing lat/lon DPS analysis")
        if got_data_testing_down_stream >= 3:
            df_merge_combined_tax = get_df_from_pickle(analysis_dir + 'merge_combined_tax_all_with_confidence.pickle')
            ic(df_merge_combined_tax.shape)
        df_lon_lat_dps = get_lon_lat_dps(sample_dir)
        df_merge_combined_tax = analyse_lon_lat_dps(df_merge_combined_tax, analysis_dir, df_lon_lat_dps)
        pickle_file = analysis_dir + 'merge_combined_tax_all_with_confidence_dps.pickle'
        ic("writing: ", pickle_file)
        put_pickleObj2File(df_merge_combined_tax, pickle_file, True)

    if got_data_testing_down_stream <= 4:
        ic("*********** got_data_testing_down_stream <=4 making combined domain call on location: marine, terrestrial or m+t")
        if got_data_testing_down_stream >= 4:
            df_merge_combined_tax = get_df_from_pickle(analysis_dir + 'merge_combined_tax_all_with_confidence_dps.pickle')
            ic(df_merge_combined_tax.shape)
        df_merge_combined_tax = make_combined_single_domain_call(df_merge_combined_tax)
        ic(df_merge_combined_tax.head(5))

        pickle_file = analysis_dir + 'merge_combined_tax_all_with_confidence_complete.pickle'
        put_pickleObj2File(df_merge_combined_tax, pickle_file, True)

    if got_data_testing_down_stream <= 5:
        ic("*********** got_data_testing_down_stream <=5 is the Blue Partition")
        if got_data_testing_down_stream >= 5:
            pickle_file = analysis_dir + 'merge_combined_tax_all_with_confidence_complete.pickle'
            df_merge_combined_tax = get_df_from_pickle(pickle_file)
        df_merge_combined_tax = make_blue_domain_call(df_merge_combined_tax)

        pickle_file = analysis_dir + 'merge_combined_tax_all_with_confidence_complete_blue.pickle'
        put_pickleObj2File(df_merge_combined_tax, pickle_file, True)
        out_file = analysis_dir + "merge_combined_tax_all_with_confidence_complete_blue.tsv"
        ic(out_file)
        df_merge_combined_tax.to_csv(out_file, sep = '\t', index = False)

    if got_data_testing_down_stream <= 6:
        ic("*********** got_data_testing_down_stream <=6 mini exploring")
        quickie = False
        if quickie == False:
            df_merge_combined_tax = get_df_from_pickle(pickle_file = analysis_dir + 'merge_combined_tax_all_with_confidence_complete_blue.pickle')
        else:
            ic("*** WARNING DEBUGGING SO RESTRICTED ROWS BEING USED")
            df_merge_combined_tax = pd.read_csv(analysis_dir + "merge_combined_tax_all_with_confidence_complete_blue.tsv" ,sep = "\t", nrows=100000)
        ic(df_merge_combined_tax.shape)
        mini_exploration(df_merge_combined_tax)
        summary_plots(df_merge_combined_tax)

    #exploring cat merge_combined_tax_all_with_confidence_complete.tsv |  awk -F '\t' 'NR==1 || $46 == "marine" {print}' | head -10 | awk -f ~/bin/transpose.awk | cat -n

    ic("about to quit")
    sys.exit()

    print_df_mega('merge_tax_combined', df_merge_combined_tax)
    #ic()
    # ic(memory_usage())
    ic('-' * 80)
    #ic()

    # the rest of the below was used mainly when exploring the data, hence now commented.
    # investigate_a_tax()

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
    parser.add_argument("-s", "--stage", help = "The stage to start the build from", required = False)
    parser.add_argument("-d", "--debug_status", help = "Debug status True or False, if True just runs on a subset of the samples", required = False)

    parser.parse_args()
    args = parser.parse_args()
    ic(args)
    print(args)

    main(args.verbosity, args.stage, args.debug_status)

