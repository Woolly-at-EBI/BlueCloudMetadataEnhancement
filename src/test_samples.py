#!/usr/bin/env python3
"""Script of 'test_samples.py' is to allow some date led testing of BlueCloud related code and data

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-03-24
__docformat___ = 'reStructuredText'

"""


from icecream import ic

import argparse
from ena_samples import *
from project_utils import *
import numpy as np
import re
import json

def get_narrow_blue(analysis_dir):
    """ get_narrow_blue

    :param analysis_dir:
    :return:
    """


    dtype_dict = {
        'accession': 'object',
        'tax_id': 'float32',
        'scientific_name': 'object',
        'lat': 'float32',
        'lon': 'float32',
        'environment_biome': 'object',
        'taxa_marine': 'bool',
        'taxa_terrestrial_or_freshwater': 'bool',
        'NCBI-to-marine' : 'category',
        'NCBI-to-terrestrial-or-freshwater': 'category',
        'combined_location_designation': 'category',
        'combined_location_designation_confidence': 'category',
        'blue_partition': 'category',
        'blue_partition_confidence': 'category'

    }
    df = pd.read_csv(analysis_dir + "merge_combined_tax_all_with_confidence_narrow_blue.tsv", dtype = dtype_dict, sep="\t")
    int_cols = ['tax_id', 'lat', 'lon']
    df[int_cols] = df[int_cols].fillna(0).applymap(np.int32)
    ic(df.columns)
    # ic(df.dtypes)

    return df

def generate_test_samples(analysis_dir,test_dir):
    """
    
    :param analysis_dir: 
    :param test_dir: 
    :return: 
    """
    df_narrow_blue = get_narrow_blue(analysis_dir)
    sample_size = 100

    my_test_samples_dict = {}
    my_test_samples_dict['blue_partition_category'] = {}
    my_test_samples_dict['all_test_accessions'] = []

    cats = ['marine', 'land']
    #df_narrow_blue = df_narrow_blue.query('blue_partition in @cats')
    ic(df_narrow_blue["blue_partition"].value_counts())
    blue_partition_part_of_cat = ["marine", "freshwater", "marine_and_terrestrial"]
    for blue_cat in df_narrow_blue["blue_partition"].unique():
        ic(blue_cat)
        df_tmp = df_narrow_blue.query('blue_partition == @blue_cat')
        my_test_samples_dict['blue_partition_category'][blue_cat] = {}

        cat_dict = my_test_samples_dict["blue_partition_category"][blue_cat]
        if blue_cat in blue_partition_part_of_cat:
            cat_dict['part_of'] = True
        else:
            cat_dict['part_of'] = False
        cat_dict['confidence_level'] = {}

        for blue_cat_conf in df_tmp["blue_partition_confidence"].unique():
            ic(blue_cat_conf)
            cat_dict['confidence_level'][blue_cat_conf] = {}
            df_test = df_tmp.query('blue_partition_confidence == @blue_cat_conf & lat > 0')
            # may only be a limited number of rows...
            actual_sample_size = sample_size if (sample_size <= df_test.shape[0]) else df_test.shape[0]
            df_test = df_test.sample(n=actual_sample_size)
            cat_dict['confidence_level'][blue_cat_conf]['accession'] = df_test['accession'].tolist()
            my_test_samples_dict['all_test_accessions'].extend(df_test['accession'].tolist())
    ic(my_test_samples_dict)
    out_file_name = test_dir + "my_test_samples.json"
    out_file = open(out_file_name, "w")
    ic(out_file_name)
    json.dump(my_test_samples_dict, out_file, indent = 4)
    out_file.close()







    ic()

def main():
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    match = re.search('(^.*)analysis/$', analysis_dir)

    test_dir = match.group(1) + "testing/data/"
    ic(test_dir)

    generate_test_samples(analysis_dir, test_dir)

if __name__ == '__main__':
    ic()
    main()


