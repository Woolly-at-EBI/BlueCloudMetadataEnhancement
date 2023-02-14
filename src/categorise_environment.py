""" categorise_environment.py
    a set of funcitons

 ___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-14
__docformat___ = 'reStructuredText'

"""

from ena_samples import *
import pandas as pd
pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)

import re
import pickle
from re import match
import os.path

from get_directory_paths import get_directory_paths

MyDataStuctures = {}


def _process_remaining_values(df, value_col, allowed_vals, default_val):

    """  _process_remaining_values(df, value_col, allowed_vals):
       process the df an examine a particular column
       for those terms not in the allowed_values, replace them with the default_val
       the latter will typically be "unclassified"
    :param df:
    :param value_col:
    :param allowed_vals:
    :return: df
    """
    ic("Values not in allowed_values:")
    df_tmp = df.loc[~df[value_col].isin(allowed_vals)]
    ic(df_tmp[value_col].value_counts())

    df.loc[~df[value_col].isin(allowed_vals), value_col] = default_val

    return df

def process_environment_biome(df):
    """

    :param df:
    :param lookup_term:
    :return:
    """

    lookup_col = "environment_biome"
    lookup_value_col = lookup_col + "_hl"

    (my_lookup_dict) = get_values_as_dict(df, lookup_col,lookup_value_col)
    ic(my_lookup_dict)
    ic(len(my_lookup_dict))
    ic('***********************************************************************' )

    need_to_process = False
    if(len(my_lookup_dict) == 0):
        need_to_process = True

    if need_to_process:
        heavy_process_environment_biome(df, lookup_col, lookup_value_col)
    else:
        ic("do quick look up")
        lookup_process_environment_biome(df, my_lookup_dict, lookup_col, lookup_value_col)


def lookup_process_environment_biome(df, my_lookup_dict, lookup_col, lookup_value_col):
    """ lookup_process_environment_biome

    :param df:
    :param lookup_col:
    :param lookup_term:
    :return: df_wbiome, my_lookup_dict
    """

    df[lookup_value_col] = df[lookup_col].map(my_lookup_dict)
    ic(df.head())
    ic(df[lookup_value_col].value_counts())

    return df, my_lookup_dict

def heavy_process_environment_biome(df, lookup_col, lookup_value_col):
    """ process_environment_biome(df):
        creates a high level param

        environment_biome_hl == lookup_term

    :param df:
    :return: df_wbiome, my_lookup_dict
    """
    key_values = ["unclassified", "marine", "terrestrial", "terrestrial_probable", "marine_and_terrestrial"]
    
    df["environment_biome_hl"] = df["environment_biome"]
    df_wbiome = df
    ic('unclassified **********************************************************************************')
    pattern = r'(.*(^\d*$|N\. A\.|^space|^animal|^protist|^archaeal|^air|^leaf|^prokary|stool|sludge|host associate|oilfield|^aquatic|^control|^oral|^anthropogenic|^fecal|^faeces|^feces|subsurface|bird|water|^ENVO|^microb|^gut$|^gastrointestinal|sediment|^urine|^nasa|^lung|^skin|^colon|^organ|^hot$|^agar|^aquari).*)'

    df_wbiome["environment_biome_hl"] = df_wbiome.environment_biome_hl.str.replace(pattern, "unclassified", flags = re.I, regex=True)
    ic(df_wbiome.head())

    ic('marine **********************************************************************************')

    # pattern = r'(\bsea\b), (seawater),(ocean),(Ocean), (plankton),(marine[ -]water),(salt[ -]water),(coastal[ -]*water),(artic water/), (marine biome)'
    # mask = df.environment_biome.str.contains('|'.join(regex_list))
    # ic(df[mask].head(50))
    # pattern = r'(marine biome|ocean)'
    pattern = r'(.*(anemone|clams|^zebrafish|^cold seep|^mediterrean|epipelagic|^hydrothermal vent|deep[ -]sea|^westerlies biome|^sea$|fjord|lichen|sea[ -]| sea|seawater|sea biome|ocean|plankton|marine[ -]water|salt[ -]water|woastal[ -]*water|Artic water|marine biome|reef|coral|marine|dolphin|gulf).*)'

    df_wbiome["environment_biome_hl"] = df_wbiome.environment_biome_hl.str.replace(pattern, "marine", flags = re.I, regex=True)

    ic("terrestrial **************************************")
    # cat sample_env_biome.txt | sed
    # 's/^ *//;s/ /\t/' | cut - f2 | awk - F$'\t' '{ OFS = FS } { if (!/[Ss]ea[ -]| [Ss]ea|seawater|[Oo]cean|[Pp]lankton|marine[ -]water|salt[ -]water|[Cc]oastal[ -]*[Ww]ater|Artic water/) { print $1} }' | grep - iv
    # 'sea level' | awk - F$'\t' '{ OFS = FS } { if (!/wood|wetland|forest|grassland|tundra|savannah|shrubland|xeric|water[ \?]well|well[ \?]water|river|reservoir|wine|tomato|tobacco|bee|wheat|zoo|whey|blood|marsh|water-logged|village|urban|lowland|island|lake|vinyard|terrestrial|farmland|truffle|desert|arid|poplar|snow|pig|pasture soil|savanna|hill|compost|paddy|maize|meadow|steppe|peat|permafrost|beach|atomosphere|basil|boreal|^Bos|^brassica|buffalo|canis|cattle|chicken|plantation|church|coffee|cropland|crop land|cultivate|dairy|^dog|dune|drinking water|freshwater|greenhouse|horse|grasses|plain|pond|rice|rose|rural|tree|silage|deer|vinegar|reed bed|soybean|oak/) { print $1} }' | egrep - Ev
    # '(waste|wild accession|reactor)'

    # pattern = r'(.*(woodland|deciduous|river|land|forest|hot spring|sea level).*)'
    pattern = r'(.*(^sheep|grassland|grasses|^field|^chic|herdsmen|orchard|dense settlement|^indoor|temperate land|agricultur|^pika|^earthworm|rumen|ground|^solanum|^cow|salad|developed space|pampa|paramo|^bamboo|^Fresh water|termite|taiga|^monkey|^area of developed open space|green house|terrestirial|^farm$|poultry|panda|^amazon|^bovine|^broccoli|pepper|^city|ferment|glacial soil|peanut|^irrigated|^hot spring|deciduous|wood|wetland|forest|tundra|savannah|shrubland|xeric|water[ \?]well|well[ \?]water|river|reservoir|wine|tomato|tobacco|bee|wheat|zoo|whey|blood|marsh|water-logged|village|urban|lowland|island|lake|vinyard|terrestrial|farmland|truffle|desert|arid|poplar|snow|pig|pasture soil|savanna|hill|compost|paddy|maize|meadow|steppe|peat|permafrost|atomosphere|basil|boreal|^Bos|^brassica|buffalo|canis|cattle|chicken|plantation|church|coffee|cropland|crop land|cultivate|dairy|^dog|dune|drinking water|freshwater|greenhouse|horse|grasses|plain|pond|rice|rose|rural|tree|silage|deer|vinegar|reed bed|soybean|oak).*)'
    df_wbiome["environment_biome_hl"] = df_wbiome.environment_biome_hl.str.replace(pattern, "terrestrial", flags = re.I, regex=True)
    ic(df_wbiome.head())
    ic(df_wbiome["environment_biome_hl"].value_counts())

    ic('terrestrial_probable **********************************************************************************')

    pattern = r'(.*(continental|grass|^rat|human|Homo sapiens|soil|murine|mouse|mosue|mice|reactor|wastewater|shower hose|mine|aquifer|Rhizosphere|Vagina|digester|built environment|^ferment|laboratory).*)'
    df_wbiome["environment_biome_hl"] = df_wbiome.environment_biome_hl.str.replace(pattern, "terrestrial_probable",
                                                                             flags = re.I, regex=True)
    # ic(df_wbiome.head())

    # ic(df_wbiome["environment_biome_hl"].query('df.environment_biome_hl == "terrestrial_probable"').value_counts())
    # ah = df_wbiome.query('environment_biome_hl == "terrestrial_probable"')
    # ic(ah.value_counts())

    ic("marine_and_terrestrial **************************************")
    pattern = r'(.*(estuar|estur|intertidal|shore|mangrove|brackish|brin|costal|coast|bay|trout|beach).*)'
    df_wbiome["environment_biome_hl"] = df_wbiome.environment_biome_hl.str.replace(pattern, "marine_and_terrestrial",
                                                                             flags = re.I, regex=True)
    df_wbiome = _process_remaining_values(df_wbiome, "environment_biome_hl", key_values, "unclassified")
    
    ic(df_wbiome.head())
    ic(df_wbiome["environment_biome_hl"].value_counts())

    my_lookup_dict = store_values_as_dict(df, lookup_col, lookup_value_col)

    return df_wbiome, my_lookup_dict

def get_pickle_file_name(lookup_col):
    """

    :param analysis_dir:
    :param lookup_col:
    :return:
    """
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    file_name = analysis_dir + lookup_col + '.pickle'
    return file_name

def store_values_as_dict(df, lookup_col, value_col):
    """store_values_as_dict

    :param df:
    :param lookup_col:
    :param value_col:
    :return: my_dict
    """
    df = df[[lookup_col, value_col]]
    df = df.drop_duplicates()
    ic(df.head())
    my_dict = dict(zip(df[lookup_col],df[value_col]))
    ic(my_dict)


    pickle_file = get_pickle_file_name(lookup_col)

    with open(pickle_file, 'wb') as handle:
        pickle.dump(my_dict, handle, protocol = pickle.HIGHEST_PROTOCOL)



    return my_dict

def get_values_as_dict(df, lookup_col, lookup_value_col):
    """get_values_as_dict
         aims to use the pickled dictionary if it exists, else it creates it.
    :param df:
    :param lookup_col:
    :param value_col:
    :return: my_dict
    """
    ic()
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    pickle_file = get_pickle_file_name(lookup_col)
    my_dict = {}

    if os.path.isfile(pickle_file):
        ic(pickle_file + " exists, so using it")
        with open(pickle_file, 'rb') as handle:
            my_dict = pickle.load(handle)
    else:
        ic(pickle_file + " does not exist")

    return my_dict

def main():
    test_status = True
    df = get_all_ena_detailed_sample_info(test_status)
    df_processed = process_environment_biome(df)

    get_values_as_dict(df_processed, "environment_biome", "environment_biome_hl")

if __name__ == '__main__':
    ic()

    main()