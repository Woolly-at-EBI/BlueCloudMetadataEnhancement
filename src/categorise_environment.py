#!/usr/bin/env python3
""" categorise_environment.py
    a set of functions to do high level mappings of the rather variable environment_biome.
        The main one to use is:
    - process_environment_biome(df)

    Includes creating a pickled dictionary of environment_biome to some high level terms. This uses regex's across
    the single environment_biome column, but for all rows in ena samples. It is thus time-consuming (5 mins if run
    outside an IDE!) so once this dictionary is created, it is pickled so that it can be fully reused. To update
    the high level mappings delete this file:  analysis_dir/environment_biome.pickle

     creates a CSV file with  3 columns: environment_biome, environment_biome_hl, environment_biome_hl2"

 ___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-14
__docformat___ = 'reStructuredText'

"""
import re
import pickle
import os.path
from ena_samples import *
from get_directory_paths import get_directory_paths

pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)

pd.set_option('display.max_rows', 100000)

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
    """process_environment_biome
        provided with a df with an environment_biome column

       calculate and return a dataframe with 2 new fields: environment_biome_hl and environment_biome_hl2
       which is the high level mapping, to one of the following:
       hl1 = ["unclassified", "marine", "terrestrial", "terrestrial_probable", "marine_and_terrestrial"]
       hl2 = ["unclassified", "freshwater", "other_terrestrial_water", "land"]

    :param df:
    :return: df
    """
    ic()
    lookup_col = "environment_biome"
    lookup_hl1_value_col = lookup_col + "_hl"
    lookup_hl2_value_col = lookup_col + "_hl2"

    (my_hl1_lookup_dict) = get_values_as_dict(df, lookup_col, lookup_hl1_value_col)

    need_to_process = False
    if len(my_hl1_lookup_dict) == 0:
        need_to_process = True
    else:
        ic(len(my_hl1_lookup_dict))

    if need_to_process:
        df, my_hl1_lookup_dict = heavy_process_environment_biome(df, lookup_col, lookup_hl1_value_col)
    else:
        df, my_hl1_lookup_dict = lookup_process_environment_biome(df, my_hl1_lookup_dict, lookup_col,
                                                                  lookup_hl1_value_col)

    (df_hl2_processed, sub_cat_dict) = addSubCats(df)
    df, my_hl2_lookup_dict = lookup_process_environment_biome(df, sub_cat_dict, lookup_col, lookup_hl2_value_col)
    ic(df.query('environment_biome_hl2 == "freshwater"').sample(n = 2))

    return df


def lookup_process_environment_biome(df, my_lookup_dict, lookup_col, lookup_value_col):
    """ lookup_process_environment_biome
         looks up the hl mapping in a dictionary
         returns the dataframe
         adds the new column as a categorical
    :param df:
    :param my_lookup_dict:
    :param lookup_col:
    :param lookup_value_col:
    :return: df_wbiome, my_lookup_dict
    """
    ic()
    df[lookup_value_col] = df[lookup_col].map(my_lookup_dict)
    df[lookup_value_col] = df[lookup_value_col].astype('category')
    ic(df[lookup_value_col].value_counts())

    return df, my_lookup_dict


def heavy_process_environment_biome(df, lookup_col, lookup_value_col):
    """ process_environment_biome(df): creates a high level mapping. many regular expressions that are mapping the
    environment_biome to a few domain categories. It will of course be missing mapping some valid biomes and have
    some miss-maps.

        current categories: marine, marine_and_terrestrial, terrestrial, terrestrial_probable, unclassified The
        terrestrial_probable category is where terrestrial is the most likely e.g. human or rodent species referred
        to in the environment_biome if not recognised by another regex, but any of these could of course be found on
        boats or on the coast etc.! Unclassified is a long tail of what has not yet been mapped (or can’t simply be).

        environment_biome_hl == lookup_term

        This ultimately gets translated into a dictionary and the dictionary is pickled.
        If the ENA_sample file is updated or the regexs are, will need to delete the picked file.

    :param df:
    :param lookup_col:
    :param lookup_value_col:
    :return: df_wbiome, my_lookup_dict
    """
    key_values = ["unclassified", "marine", "terrestrial", "terrestrial_probable", "marine_and_terrestrial"]

    df["environment_biome_hl"] = df["environment_biome"]
    df_wbiome = df

    ic("marine_and_terrestrial  - regex")
    # maps to a temporary pattern that is cleaned up later, as otherwise marine or terrestrial recognises it!
    pattern = r'(^.*(estuar|estur|intertidal|shore|mangrove|brackish|brin|costal|coast|bay|trout|beach|^tidal|^tide).*)'
    df_wbiome["environment_biome_hl"] = df_wbiome.environment_biome_hl.str.replace(pattern, "m_and_t",
                                                                                   flags = re.I, regex = True)

    ic('marine  - regex')
    pattern = (r'(^.*(rock pool|kelp|sea|marine|^subtidal|sound|shrimp|^see floor|anemone|clams|^zebrafish|^cold '
               r'seep|^mediterrean|epipelagic|^hydrothermal vent|deep[ -]sea|^westerlies biome|fjord|lichen| '
               r'sea|^sea|ocean|plankton|marine|salt[ -]water|coastal[ -]*water|Artic '
               r'water|reef|coral|dolphin|gulf).*)')
    df_wbiome["environment_biome_hl"] = df_wbiome.environment_biome_hl.str.replace(pattern, "marine", flags = re.I,
                                                                                   regex = True)

    ic("terrestrial  - regex")
    # cat sample_env_biome.txt | sed 's/^ *//;s/ /\t/' | cut - f2 | awk - F$'\t' '{ OFS = FS } { if (!/[Ss]ea[ -]| [
    # Ss]ea|seawater|[Oo]cean|[Pp]lankton|marine[ -]water|salt[ -]water|[Cc]oastal[ -]*[Ww]ater|Artic water/) { print
    # $1} }' | grep - iv 'sea level' | awk - F$'\t' '{ OFS = FS } { if (
    # !/wood|wetland|forest|grassland|tundra|savannah|shrubland|xeric|water[ \?]well|well[
    # \?]water|river|reservoir|wine|tomato|tobacco|bee|wheat|zoo|whey|blood|marsh|water-logged|village|urban|lowland
    # |island|lake|vinyard|terrestrial|farmland|truffle|desert|arid|poplar|snow|pig|pasture
    # soil|savan|hill|compost|paddy|maize|meadow|steppe|peat|permafrost|beach|atomosphere|basil|boreal|^Bos|^brassica
    # |buffalo|canis|cattle|chicken|plantation|church|coffee|cropland|crop land|cultivate|dairy|^dog|dune|drinking
    # water|freshwater|greenhouse|horse|grasses|plain|pond|rice|rose|rural|tree|silage|deer|vinegar|reed
    # bed|soybean|oak/) { print $1} }' | egrep - Ev '(waste|wild accession|reactor)'
    pattern = r'' \
              r'(^.*(mushroom|moor|' \
        (r'orchard|permafrost|peat|\bstream|^vine|^urban|terrestial|^tea|^sugarcane|^subsahelian|highland'
         r'|^stream|barley|spruce|vegetable|fairy ring|arable|crop|^shrub|^silkworm|^shelterbelt|cactus|pricklr '
         r'pear|^sawdust|^salt mine|^sheep|grassland|grasses|^field|^chic|herdsmen|orchard|dense '
         r'settlement|^indoor|temperate '
         r'land|agricultur|^pika|^earthworm|rumen|ground|^solanum|^cow|salad|developed '
         r'space|pampa|paramo|^bamboo|^fresh water|freshwater|headwater|termite|taiga|^monkey|^area of '
         r'developed open space|green house|terrestirial|^farm$|poultry|panda|^amazon|^bovine|^broccoli|pepper'
         r'|^city|ferment|glacial soil|peanut|^irrigated|^hot '
         r'spring|deciduous|wood|wetland|forest|tundra|savannah|shrubland|xeric|water[ \?]well|well[ '
         r'\?]water|river|reservoir|wine|tomato|tobacco|bee|wheat|zoo|whey|blood|marsh|water-logged|village'
         r'|lowland|island|lake|vinyard|terrestrial|farmland|truffle|desert|arid|poplar|snow|pig|pasture '
         r'soil|savanna|hill|compost|paddy|maize|meadow|steppe|peat|permafrost|atomosphere|basil|boreal|^Bos'
         r'|^brassica|buffalo|canis|cattle|chicken|plantation|church|coffee|cropland|crop '
         r'land|cultivate|dairy|^dog|dune|drinking '
         r'water|freshwater|greenhouse|horse|grasses|plain|pond|rice|rose|rural|tree|silage|deer|vinegar|reed '
         r'bed|soybean|oak).*)')
    df_wbiome["environment_biome_hl"] = df_wbiome.environment_biome_hl.str.replace(pattern, "terrestrial", flags = re.I,
                                                                                   regex = True)

    ic('terrestrial_probable - regex')
    pattern = (r'(^.*(soil|Tea|land|land|^sauerkraut|continental|grass|^rat|patient|human|Homo '
               r'sapiens|soil|murine|mouse|mosue|mice|reactor|wastewater|shower '
               r'hose|mine|aquifer|Rhizosphere|Vagina|digester|built environment|^ferment|laboratory).*)')
    df_wbiome["environment_biome_hl"] = df_wbiome.environment_biome_hl.str.replace(pattern, "terrestrial_probable",
                                                                                   flags = re.I, regex = True)

    ic('unclassified  - regex')
    pattern = (r'(^.*(^\d*$|N\. A\.|^space|^animal|^protist|^archaeal|^air|^leaf|^prokary|stool|sludge|host '
               r'associate|oilfield|^aquatic|^control|^oral|^anthropogenic|^fecal|^faeces|^feces|subsurface|bird'
               r'|^water|^microb|^gut$|^gastrointestinal|sediment|^urine|^nasa|^lung|^skin|^colon|^organ|^hot$|^agar'
               r'|^aquari).*)')
    df_wbiome["environment_biome_hl"] = df_wbiome.environment_biome_hl.str.replace(pattern, "unclassified",
                                                                                   flags = re.I, regex = True)

    df_wbiome["environment_biome_hl"] = df_wbiome.environment_biome_hl.str.replace("m_and_t", "marine_and_terrestrial")

    df_wbiome = _process_remaining_values(df_wbiome, "environment_biome_hl", key_values, "unclassified")
    ic(df_wbiome["environment_biome_hl"].value_counts())
    my_lookup_dict = store_values_as_dict(df, lookup_col, lookup_value_col)

    return df_wbiome, my_lookup_dict


def get_pickle_file_name(lookup_col):
    """get_pickle_file_name

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
    my_dict = dict(df[lookup_col], zip(df[value_col]))

    pickle_file = get_pickle_file_name(lookup_col)

    with open(pickle_file, 'wb') as handle:
        pickle.dump(my_dict, handle, protocol = pickle.HIGHEST_PROTOCOL)

    return my_dict


def get_values_as_dict(df, lookup_col, lookup_value_col):
    """get_values_as_dict
         aims to use the pickled dictionary if it exists, else  returns empty dict.

         typically this function is called from process_environment_biome, which will automatically process and
         generate the dictionary if needed.
    :param df:
    :param lookup_col:
    :param value_value_col:
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
        ic("WARNING: ", pickle_file + " does not exist")

    return my_dict


def addSubCats(df):
    """
        creates a dict lookup by environment_biome
    :param df:
    :return: df, sub_cat_dict
    """
    ic()
    df["environment_biome_hl2"] = "unclassified"
    pattern = r'water|Water|sewage|marsh|creek|river|pond|watershed|wetland|Wetland|bog|lake|swampy pool|stream|brackish|aquatic|Aquatic'
    stop_pattern = r'sea|oil'
    df.loc[(df["environment_biome_hl"] == "terrestrial") & (df["environment_biome"].str.contains(pattern)) & (
            df["environment_biome"].str.contains(
                stop_pattern) == False), "environment_biome_hl2"] = "other_terrestrial_water"
    # ic(df["environment_biome_hl2"].value_counts())
    # and at a lower std, not asking for a terrestrial designation
    df.loc[(df["environment_biome_hl2"] == "unclassified") & (df["environment_biome"].str.contains(pattern)) & (
            df["environment_biome"].str.contains(
                stop_pattern) == False), "environment_biome_hl2"] = "other_terrestrial_water"
    # ic(df["environment_biome_hl2"].value_counts())

    # cat ~/envo_tmp.txt | grep ENVO: | sed -E 's/.*(ENVO:[0-9]*)/\1/' | tr '\t' '|'
    pattern = (r'water and sediment in basin|headwater|Aquatic|aquatic|well|headwater|lake|Lake|resh Water|resh '
               r'water|reshwater|\bstream|River|river\b|RIVER|riverine|headwater|reservoir|reservoir|Reservoir|pond\b'
               r'|ponds|stream|ENVO:00000021|ENVO:00000053|ENVO:00000243|ENVO:00000873|ENVO:01000252|ENVO:01000253'
               r'|ENVO:01000297|ENVO:01000306|ENVO:01000409|ENVO:01000598|ENVO:01001253|ENVO:01001344|ENVO:01001511'
               r'|ENVO:01001515|ENVO:01001789|ENVO:2000005|ENVO:00000891|ENVO:00000892|ENVO:01000394|ENVO:01000398'
               r'|ENVO:01001028|ENVO:04000005')
    stop_pattern = (r'side|saline|Saline|salt|Salt|petroleum|\boil|former '
                    r'lake|Island|island|near|Asphalt|trailing|Tailing|Tailling|oil')
    df.loc[(df["environment_biome_hl"] == "terrestrial") & (df["environment_biome"].str.contains(pattern)) & (
            df["environment_biome"].str.contains(stop_pattern) == False), "environment_biome_hl2"] = "freshwater"

    # ic(df.query('environment_biome_hl2 == "freshwater"'))

    # ic(df.query('environment_biome_hl2 != "freshwater"')['environment_biome'])
    stop_pattern = r'water|river|Aquatic|aquatic|lake'
    pattern = (r'^vine|^urban|terrestial|^tea|^sugarcane|^subsahelian|highland|barley|spruce|vegetable|fairy '
               r'ring|arable|crop|^shrub|^silkworm|^shelterbelt|cactus|pricklr pear|^sawdust|^salt '
               r'mine|^sheep|grassland|grasses|^field|^chic|herdsmen|orchard|dense settlement|^indoor|temperate '
               r'land|agricultur|^pika|^earthworm|rumen|ground|^solanum|^cow|salad|developed '
               r'space|pampa|paramo|^bamboo|termite|taiga|^monkey|^area of developed open space|green '
               r'house|terrestirial|^farm$|panda|^amazon|^bovine|^broccoli|pepper|^city|ferment|glacial '
               r'soil|peanut|^irrigated|deciduous|wood|wetland|forest|tundra|savannah|shrubland|xeric|wine|tomato'
               r'|tobacco|bee|wheat|zoo|whey|blood|marsh|water-logged|village|lowland|island|vinyard|terrestrial'
               r'|farmland|truffle|desert|arid|poplar|snow|pig|pasture '
               r'soil|savanna|hill|compost|paddy|maize|meadow|steppe|peat|permafrost|atomosphere|basil|boreal|^Bos'
               r'|^brassica|buffalo|canis|cattle|chicken|plantation|church|coffee|cropland|crop '
               r'land|cultivate|dairy|^dog|dune|greenhouse|horse|grasses|plain|rice|rose|rural|tree|silage|deer'
               r'|vinegar|soybean|oak')
    df.loc[((df["environment_biome_hl"] == "terrestrial") & (df["environment_biome"].str.contains(pattern)) & (
            df["environment_biome"].str.contains(stop_pattern) == False)), "environment_biome_hl2"] = "land"

    pattern = (r'potato|poultry|prairie|land|land|^sauerkraut|continental|grass|^rat|human|Homo '
               r'sapiens|soil|murine|mouse|mosue|mice|reactor|shower hose|mine|Rhizosphere|Vagina|digester|built '
               r'environment|^ferment|laboratory')
    df.loc[((df["environment_biome_hl"] == "terrestrial_probable") & (
        df["environment_biome"].str.contains(pattern)) & (df["environment_biome"].str.contains(pattern)) & (
                    df["environment_biome"].str.contains(stop_pattern) == False)), "environment_biome_hl2"] = "land"
    sub_cat_dict = dict(zip(df.environment_biome, df.environment_biome_hl2))
    # ic(df["environment_biome_hl2"].value_counts())

    return df, sub_cat_dict


def main():
    test_status = True
    df_processed = []
    if not test_status:
        df = get_all_ena_detailed_sample_info(test_status, 0)
        df_processed = process_environment_biome(df)
    else:
        my_dict = get_values_as_dict(df_processed, "environment_biome", "environment_biome_hl")
        # ic(my_dict)
        df_processed = pd.DataFrame.from_dict(my_dict, orient = 'index').reset_index()
        df_processed.columns = ['environment_biome', 'environment_biome_hl']
        ic(df_processed.sample(n = 3))
        ic(df_processed['environment_biome_hl'].value_counts())

        df_processed = df_processed[["environment_biome", "environment_biome_hl"]]
        (df_processed, sub_cat_dict) = addSubCats(df_processed)
        # ic(sub_cat_dict)
        df_processed = df_processed.drop_duplicates()
        ic(df_processed.shape)
        ic(df_processed.sample(n = 3))
        ic(df_processed["environment_biome_hl2"].value_counts())

        ic("testing")
        df = get_all_ena_detailed_sample_info(test_status, 0)
        df_processed = process_environment_biome(df)

    out_file = "environment_biome_mapping.tsv"
    ic(out_file)
    df_processed.to_csv(out_file, sep = "\t", index = False)
    ic("all processed  in categorise environment, bye.")


if __name__ == '__main__':
    ic()

    main()
