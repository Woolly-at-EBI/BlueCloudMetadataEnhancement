""" generate_clearinghouse_submissions.py
     see the PDF details in https://www.ebi.ac.uk/ena/clearinghouse/api/

 ___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-16
__docformat___ = 'reStructuredText'

"""
import json

from icecream import ic
import os.path
import pickle
import sys
import numpy as np

import pandas as pd
pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)

from clearinghouse_objects import *
from get_directory_paths import get_directory_paths
from project_utils import put_pickleObj2File,get_pickleObj
from ena_samples import get_all_ena_detailed_sample_info

def demo_format(test_status):


    curation_count = 0
    my_record = NewSampleCuration(useENAAutoCurationValues=True)
    ic(my_record.get_filled_dict())
    sample_id = 'SAMD'
    ic(my_record.attributeDelete)
    my_record.recordId = sample_id
    ic(my_record.get_filled_dict())

def process_confidence_fields(df_merge_combined_tax, analysis_dir):
    """

    :param df_merge_combined_tax:
    :param analysis_dir:
    :return:
    """
    ic(df_merge_combined_tax.head())
    ic(df_merge_combined_tax.columns)

    def createSubmissionsJson(row):
        my_record = NewSampleCuration(useENAAutoCurationValues = True)
        my_record.recordId = row["accession"]
        my_record.attributePost = dom_type
        if dom_type == 'marine' or dom_type == "terrestrial":
            my_evidence_string = "confidence:" + row[field] + "; GPS_evidence:"
            if row['location_designation'] == dom_type:
                my_evidence_string += "True"
            elif row['location_designation'] == "marine and terrestrial":
                my_evidence_string += "True (marine and terrestrial)"
            else:
                my_evidence_string += "False"
            my_evidence_string += "; taxa_evidence:" + ("True" if row[tax_dom_field] else "False")
            my_record.assertionAdditionalInfo = my_evidence_string
        #print(my_record.get_filled_json())
        return my_record.get_filled_json()

    inc_cols = ['accession', 'marine (ocean connected)', 'freshwater (land enclosed)','location_designation',
                'sample_confidence_marine_inc_biome', 'sample_confidence_terrestrial_inc_biome']
    df_merge_combined_tax_res = df_merge_combined_tax[inc_cols]
    ic("collect marine high confidence")
    dom_type = 'marine'

    if dom_type == 'marine':
        field = "sample_confidence_marine_inc_biome"
        tax_dom_field = 'marine (ocean connected)'

    df_specific = df_merge_combined_tax_res.query('sample_confidence_marine_inc_biome == "high"').head(1)
    df_specific['json_col'] = df_specific.apply(createSubmissionsJson, axis=1)
    ic(df_specific.head(5))
    ic(df_specific['json_col'].head())

def process_eez_fields(df_merge_sea_ena):
    """process_eez_fields

    :param df_gps:
    :return:
    """
    ic()
    ic(df_merge_sea_ena.sample(n=10))
    ic(df_merge_sea_ena.columns)

    def createSubmissionsJson(row):
        my_record = NewSampleCuration(useENAAutoCurationValues = True)
        my_record.recordId = row["accession"]
        my_record.attributePost = dom_type
        my_record.valuePost = row[field]
        my_record.assertionAdditionalInfo = assertionAdditionalInfo
        print(my_record.get_filled_json())
        return my_record.get_filled_json()

    curations2add = ['EEZ:GEONAME', 'EEZ:TERRITORY1', 'EEZ:TERRITORY2', 'EEZ:SOVEREIGN1', 'EEZ:SOVEREIGN2',\
                     'EEZ:MRGID', 'EEZ:MRGID_TER1', 'EEZ:MRGID_TER2', 'EEZ:MRGID_SOV1', 'EEZ:MRGID_SOV2']
    df_specific = df_merge_sea_ena.query('eez_category == "EEZ"').head(1)
    assertionAdditionalInfo = "Confidence:high; evidence:GPS coordinate in EEZ shapefile"
    for dom_type in curations2add:
        (dummy, field) = dom_type.split(":")
        ic(field)
        if field in ['GEONAME', 'TERRITORY1', 'TERRITORY2', 'SOVEREIGN1', 'SOVEREIGN2']:
            df_specific['json_col'] = df_specific.apply(createSubmissionsJson, axis=1)
            df_specific.loc[df_specific[field].isnull(), 'json_col'] = ""
        else:
            df_specific['json_col'] = df_specific.apply(createSubmissionsJson, axis=1)
            #below could not see an elegant way of dealing when MRGID's are 0.
            df_specific.loc[df_specific[field] > 0, 'json_col'] = ""

    #to do, capture valid curation, from json_col each time
        ic(df_specific.head())
        ic(df_specific['json_col'].head(3))

def merge_sea_ena(hit_dir):
    """merge_sea_ena
        merge the sea hits from the shape files with ENA
        only selecting those ENA samples that intersect with EEZ
    :param hit_dir:
    :return: df_merge_sea_ena
    """
    test_status = True
    df_ena_detail = get_all_ena_detailed_sample_info(test_status)
    df_sea_hits = pd.read_csv(hit_dir + "merged_sea.tsv", sep='\t')
    for mrg in ['MRGID', 'MRGID_TER1', 'MRGID_TER2', 'MRGID_SOV1', 'MRGID_SOV2']:
        df_sea_hits[mrg] = df_sea_hits[mrg].fillna(0).astype(int)
    df_merge_sea_ena = pd.merge(df_ena_detail,df_sea_hits, on=["lat", "lon"], how="inner")

    return df_merge_sea_ena


def main():
    test_status = True
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()

    df_merged_ena_sea = merge_sea_ena(hit_dir)
    df_merged_ena_sea = df_merged_ena_sea.query('eez_category == "EEZ"')

    #demo_format(test_status)
    # in_file = analysis_dir + 'all_ena_gps_tax_combined.tsv'
    # df_gps = pd.read_csv(in_file, sep='\t', nrows =100)
    process_eez_fields(df_merged_ena_sea)

    sys.exit()

    pickle_file = analysis_dir + 'merge_combined_tax_all_with_confidence.pickle'
    # df_merge_combined_tax = get_pickleObj(pickle_file)
    # df_merge_combined_tax = df_merge_combined_tax.head(100000).query('taxonomic_source == "metagenome"')
    #put_pickleObj2File(df_merge_combined_tax, "./tmp.pickle")
    df_merge_combined_tax = get_pickleObj("./tmp.pickle")
    process_confidence_fields(df_merge_combined_tax, analysis_dir)




if __name__ == '__main__':
    ic()

    main()