#!/usr/bin/env python3
""" generate_clearinghouse_submissions.py
    from merge of shape hit files and also from waterTaxonomyAnalysis.p
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
import argparse

import pandas as pd
pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)

from clearinghouse_objects import *
from get_directory_paths import get_directory_paths
from project_utils import put_pickleObj2File,get_pickleObj
from ena_samples import get_all_ena_detailed_sample_info

def demo_format(test_status):
    ic()
    curation_count = 0
    my_record = NewSampleCuration(useENAAutoCurationValues=True)
    ic(my_record.get_filled_dict())
    sample_id = 'SAMD'
    ic(my_record.attributeDelete)
    my_record.recordId = sample_id
    ic(my_record.get_filled_dict())

def process_confidence_fields(df_merge_combined_tax, analysis_dir):
    """process_confidence_fields for marine and terrestrial
    generating JSON to have curated.

    :param df_merge_combined_tax:
    :param analysis_dir:
    :return: list of JSON's to curate
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
            # re-implement when taxa columns reincluded!
            # my_evidence_string += "; taxa_evidence:" + ("True" if row[tax_dom_field] else "False")
            my_evidence_string += "; taxa_evidence:"
            my_record.assertionAdditionalInfo = my_evidence_string
            my_record.emptyAssertionEvidence()
            my_record.addAutoAssertionEvidence("combinatorial")
        #print(my_record.get_filled_json())
        return my_record.get_filled_json()

    # inc_cols = ['accession', 'marine (ocean connected)', 'freshwater (land enclosed)', 'location_designation',
    #            'sample_confidence_marine_inc_biome', 'sample_confidence_terrestrial_inc_biome']
    inc_cols = ['accession', 'location_designation',
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

    local_list = df_specific['json_col'].values.tolist()
    # remove empty list items
    local_list = [i for i in local_list if i]

    out_file = analysis_dir + "curation_submissions:" + "domain.json"
    create_submit_curations_file(local_list, out_file)

    return local_list

def process_eez_fields(df_merge_sea_ena, clearinghouse_data_dir):
    """process_eez_fields
        process all the EEZ relevant fields and return a list of sample curations in JSON format to make.
        and print to file
    :param df_gps:
    :return: curation_list
    """
    ic()
    ic(df_merge_sea_ena.sample(n=10))
    ic(df_merge_sea_ena.columns)

    curation_list = []

    def createSubmissionsJson(row):
        ic()
        my_record = NewSampleCuration(useENAAutoCurationValues = True)
        my_record.recordId = row["accession"]
        my_record.attributePost = dom_type
        my_record.valuePost = row[field]
        my_record.assertionAdditionalInfo = assertionAdditionalInfo
        my_record.emptyAssertionEvidence()
        my_record.addAutoAssertionEvidence("EEZ")
        #print(my_record.get_filled_json())
        return my_record.get_filled_json()

    #comparing the first value with the rest, as want to know if all values are the same
    def is_unique(s):
        a = s.to_numpy()  # s.values (pandas<0.24)
        return (a[0] == a).all()

    curation_types2add = ['EEZ:GEONAME', 'EEZ:TERRITORY1', 'EEZ:TERRITORY2', 'EEZ:SOVEREIGN1', 'EEZ:SOVEREIGN2',\
                     'EEZ:MRGID', 'EEZ:MRGID_TER1', 'EEZ:MRGID_TER2', 'EEZ:MRGID_SOV1', 'EEZ:MRGID_SOV2']
    df_specific = df_merge_sea_ena.query('eez_category == "EEZ"').head(2)
    assertionAdditionalInfo = "confidence:high; evidence:GPS coordinate in EEZ shapefile"
    for dom_type in curation_types2add:
        (dummy, field) = dom_type.split(":")
        ic(field)

        if(df_specific[field].isnull().all() ):
            ic("field all values null or 0")
            # or is_unique(df_specific[field])
            #thus do not need
        else:
            ic()
            #during the below some empty "" values are created in json_col
            if field in ['GEONAME', 'TERRITORY1', 'TERRITORY2', 'SOVEREIGN1', 'SOVEREIGN2']:
                df_specific['json_col'] = df_specific.apply(createSubmissionsJson, axis=1)
                df_specific.loc[df_specific[field].isnull(), 'json_col'] = ""
            else:
                df_specific['json_col'] = df_specific.apply(createSubmissionsJson, axis=1)
                #earlier code filled in empty MRGID values to 0. Could not see an efficient way to stop doing an apply
                # on those, hence the below is necessary.

                #ic(df_specific[field].value_counts())
                df_specific.loc[df_specific[field] == 0, 'json_col'] = ""
                #ic(df_specific['json_col'].value_counts())

            ic()
            #to do, capture valid curation, from json_col each time
            #ic(df_specific.head())
            #ic(df_specific['json_col'].head(3))
            local_list = df_specific['json_col'].values.tolist()

            #remove empty list items
            #ic(local_list)
            local_list = [i for i in local_list if i]
            #ic(local_list)
            out_file = clearinghouse_data_dir + "curation_submissions:" + field + '.json'
            ic(out_file)
            create_submit_curations_file(local_list, out_file)
            curation_list.extend(local_list)
            # ic(len(curation_list))
    # ic(len(curation_list))
    ic()
    return curation_list

def merge_sea_ena(debug_status, hit_dir):
    """merge_sea_ena
        merge the sea hits from the shape files with ENA
        only selecting those ENA samples that intersect with EEZ
    :param hit_dir:
    :return: df_merge_sea_ena
    """

    df_ena_detail = get_all_ena_detailed_sample_info(debug_status)
    df_sea_hits = pd.read_csv(hit_dir + "merged_sea.tsv", sep='\t')
    int_cols = ['MRGID', 'MRGID_TER1', 'MRGID_TER2', 'MRGID_SOV1', 'MRGID_SOV2', 'MRGID_IHO', 'MRGID_EEZ']
    for mrg in int_cols:
        df_sea_hits[mrg] = df_sea_hits[mrg].fillna(0).astype(np.int32)
    cat_cols = []
    pats = ["UN_", "TERR", "SOVER", "_category", "ECOREGION", "ISO", "GEONAME", "POL_TYPE", 'NAME']
    # ic(df_sea_hits.columns)
    for col_name in df_sea_hits.columns:
        for pat in pats:
            if pat in col_name:
                cat_cols.append(col_name)
    # ic(cat_cols)
    for col in cat_cols:
        df_sea_hits[col] = df_sea_hits[col].fillna(0).astype("category")
    # ic(df_sea_hits.dtypes)
    # sys.exit()

    df_merge_sea_ena = pd.merge(df_ena_detail, df_sea_hits, on=["lat", "lon"], how="inner")

    if debug_status:
        ic(df_merge_sea_ena.shape)
        ic(df_merge_sea_ena.dtypes)
        ic(df_merge_sea_ena.head(3))

    return df_merge_sea_ena



def create_submit_curations_file(full_curation_list, out_file):
    """create_submit_curations_file
        If curations add them in JSON format to the out_file

    :param full_curation_list:
    :param  out_file name:
    :return: nowt
    """
    ic()

    if len(full_curation_list) == 0:
        ic("Warning no curations, so not creating: ", out_file)
    else:
        ic("creating ", len(full_curation_list), " curations for submission in ", out_file)
        #out_file = analysis_dir + "curations_submissions_json.txt"

        ic(out_file)
        # with open(out_file, 'w') as fp:
        #     fp.write('\n'.join(full_curation_list))
        submission_dict = {}
        submission_dict['curations'] = []

        for json_string in full_curation_list:
            json_data = json.loads(json_string)
            submission_dict['curations'].append(json_data)
        #ic(submission_dict)
        with open(out_file, 'w') as fp:
             fp.write(json.dumps(submission_dict, indent=2))

    return

def generate_marine_related_annotations(debug_status, hit_dir, analysis_dir, clearinghouse_data_dir):
    """
    
    :return: 
    """
    df_merged_ena_sea = merge_sea_ena(debug_status, hit_dir)
    ic(df_merged_ena_sea.shape)

    annotation_list = ["EEZ"]

    for annotation_type in annotation_list:
        if annotation_type == 'EEZ':
            df_merged_ena_sea = df_merged_ena_sea.query('eez_category == "EEZ"')
            local_curation_list = process_eez_fields(df_merged_ena_sea, clearinghouse_data_dir)
        else:
            print(f"ERROR: annotation_type: {annotation_type} is unknown")
            sys.exit()
        ic(len(local_curation_list))
    full_curation_list = []


    # demo_format(test_status)
    # in_file = analysis_dir + 'all_ena_gps_tax_combined.tsv'
    # df_gps = pd.read_csv(in_file, sep='\t', nrows =100)



    sys.exit()

    # pickle_file = analysis_dir + 'merge_combined_tax_all_with_confidence.pickle'
    # df_merge_combined_tax = get_pickleObj(pickle_file)
    # ic(df_merge_combined_tax.head())
    # # df_merge_combined_tax = df_merge_combined_tax.head(100000).query('taxonomic_source == "metagenome"')
    # df_merge_combined_tax = df_merge_combined_tax.head(100000)
    # # put_pickleObj2File(df_merge_combined_tax, "./tmp.pickle", True)
    # #
    # # df_merge_combined_tax = get_pickleObj("./tmp.pickle")


def main(args):
    """

    :param args:
    :return:
    """
    test_status = True
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    clearinghouse_data_dir = "/Users/woollard/projects/bluecloud/clearinghouse/submission_data/"

    ic(args.generate_specific_submissions)
    if args.generate_specific_submissions:
        ic("yipee")
        generate_marine_related_annotations(args.debug_status, hit_dir, analysis_dir, clearinghouse_data_dir)
    else:
        ic("nah")

    sys.exit()



    #submit_curations(full_curation_list, analysis_dir)

if __name__ == '__main__':
    ic()
    # Read arguments from command line
    prog_des = "Script to get the marine zone classification for a set of longitude and latitude coordinates\n" +\
                "Typical usage: ./ generate_clearinghouse_submissions.py - d True -s"
    parser = argparse.ArgumentParser(description = prog_des)

    # Adding optional argument, n.b. in debugging mode in IDE, had to turn required to false.
    parser.add_argument("-d", "--debug_status",
                        help = "Debug status True or False, if True just runs on a subset of the samples",
                        required = True)
    parser.add_argument("-s", "--generate_specific_submissions",
                        help = "Generate specific submissions",
                        required = False,
                        action="store_true"
                        )

    parser.parse_args()
    args = parser.parse_args()
    ic(args)
    print(args)

    main(args)