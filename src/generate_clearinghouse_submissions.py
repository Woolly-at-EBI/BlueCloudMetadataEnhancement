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
import re

import pandas as pd
from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype
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

    df_specific = df_merge_combined_tax_res.query('sample_confidence_marine_inc_biome == "high"').sample(n=1)
    df_specific['json_col'] = df_specific.apply(createSubmissionsJson, axis=1)
    ic(df_specific.head(5))
    ic(df_specific['json_col'].head())

    local_list = df_specific['json_col'].values.tolist()
    # remove empty list items
    local_list = [i for i in local_list if i]

    out_file = analysis_dir + "curation_submissions:" + "domain.json"
    create_submit_curations_file(local_list, out_file)

    return local_list

def get_multi_field_dict():
    """
    dictionary for providing which fields are associated together and to thus provide together in the submission JSON
    :return: multi_field_dict
    """
    multi_field_dict = {
        'EEZ': {
                'GEONAME': ['GEONAME', 'MRGID'],
                'TERRITORY1': ['TERRITORY1', 'MRGID_TER1', 'ISO_TER1', 'UN_TER1'],
                'TERRITORY2': ['TERRITORY2', 'MRGID_TER2', 'ISO_TER2', 'UN_TER2'],
                'TERRITORY3': ['TERRITORY3', 'MRGID_TER3', 'ISO_TER3', 'UN_TER3'],
                'SOVEREIGN1': ['SOVEREIGN1', 'MRGID_SOV1', 'ISO_SOV1', 'UN_SOV1'],
                'SOVEREIGN2': ['SOVEREIGN2', 'MRGID_SOV2', 'ISO_SOV2', 'UN_SOV2'],
                'SOVEREIGN3': ['SOVEREIGN3', 'MRGID_SOV3', 'ISO_SOV3', 'UN_SOV3'],
               },
        'IHO-EEZ': {
                 'intersect_MARREGION': ['intersect_MARREGION', 'intersect_MRGID', 'intersect_MRGID_IHO', 'intersect_IHO_SEA', 'intersect_EEZ']
               }

    }

    return multi_field_dict


def process_supercat_fields(df_merge_sea_ena, super_category, clearinghouse_data_dir):
    """process_supercat_fields
        process all the EEZ relevant fields and return a list of sample curations in JSON format to make.
        and print to file
    :param df_gps:
    :return: curation_list
    """
    ic()
    ic(df_merge_sea_ena.sample(n=10))
    ic(df_merge_sea_ena.columns)
    #super_category = 'EEZ'

    curation_list = []


    def createIndividualSubmissionsJson(row):
        """
            returns valid JSON if there is a hit,
            Notes:
                the attributePost format is super_category + : + lower_case(field) as lower case is the preferred INSDC format
        :param row:
        :return:
        """
        ic()
        if row[field] == "" or row[field] == 0:
            return
        else:
            my_record = NewSampleCuration(useENAAutoCurationValues = True)
            my_record.recordId = row["accession"]
            my_record.attributePost = ":".join([super_category, lc_field])
            my_record.valuePost = row[field]
            my_record.assertionAdditionalInfo = assertion_additional_infoVal
            my_record.emptyAssertionEvidence()
            my_record.addAutoAssertionEvidence(super_category)
            #print(my_record.get_filled_json())
            return my_record.get_filled_json()

    def createMultiSubmissionsJson(row):
        """
            returns valid JSON if there is a hit,
            Notes:
                the attributePost format is super_category + : + lower_case(field) as lower case is the preferred INSDC format
        :param row:
        :return:
        """
        ic()
        if row[field] == "" or row[field] == 0:
            return
        else:
            my_record = NewSampleCuration(useENAAutoCurationValues = True)
            my_record.recordId = row["accession"]
            my_record.attributePost = attributePostVal
            value_array = []
            extra_array = []
            if "TERRITORY" in field or "SOVEREIGN" in field or "GEONAME" in field:
                count =0
                for component_field in multi_field_dict[super_category][field]:
                    if row[component_field] == "" or row[component_field] == 0:
                        continue
                    else:
                        ic(f"component:{row[component_field]}<---")
                    field_name = component_field.lower()
                    if (count == 0):
                        value_array.append(str(row[component_field]) + " (")
                    else:
                        if "mrgid" in field_name:
                            extra_array.append("mrgid:" + str(row[component_field]))
                        elif "iso" in field_name:
                            extra_array.append("ISO3166-1 alpha-3:" + str(row[component_field]))
                        elif "un" in field_name:
                            extra_array.append("ISO3166-1 num:" + str(row[component_field]))

                    count += 1
                value_array.append("; ".join(extra_array) + ")")
                ic(value_array)
                my_record.valuePost = "".join(value_array)

            else:
                for component_field in multi_field_dict[super_category][field]:
                     field_name = component_field.lower().removeprefix('intersect_')
                     value_array.append(":".join([field_name, str(row[component_field])]))
                my_record.valuePost = "; ".join(value_array)
            my_record.assertionAdditionalInfo = assertion_additional_infoVal
            my_record.emptyAssertionEvidence()
            my_record.addAutoAssertionEvidence(super_category)
            # print(my_record.get_filled_json())
            # sys.exit()
            return my_record.get_filled_json()

    #comparing the first value with the rest, as want to know if all values are the same
    def is_unique(s):
        a = s.to_numpy()  # s.values (pandas<0.24)
        return (a[0] == a).all()

    curation_types2add = []
    assertion_additional_infoVal = ""
    super_category_name = super_category
    if super_category == "EEZ":
        curation_types2add = ['GEONAME', 'TERRITORY1', 'TERRITORY2', 'TERRITORY3', 'SOVEREIGN1',
                'SOVEREIGN2', 'SOVEREIGN3']
        curation_types2add = ['TERRITORY1', 'TERRITORY2', 'TERRITORY3']
        curation_types2add = ['SOVEREIGN1','SOVEREIGN2', 'SOVEREIGN3']
        curation_types2add = ['GEONAME']
        # curation_types2add = ['TERRITORY1']
        #df_specific = df_merge_sea_ena.query('eez_category == "EEZ"').head(100)
        df_specific = df_merge_sea_ena.query('UN_TER3 != None & UN_TER2 != 0', engine='python').head(1)
        ic(df_specific[["TERRITORY1", "MRGID_TER1", "UN_TER1", "ISO_TER1", "UN_TER2", "UN_TER3"]].head(1))
        #sys.exit()

        assertion_additional_infoVal = "confidence:high; evidence:sample coordinates within EEZ shapefile"
    elif super_category == "IHO-EEZ":
        curation_types2add = ['intersect_MARREGION']
        df_specific = df_merge_sea_ena.query('intersect_UN_TER3 != None').head(1)
        assertion_additional_infoVal = "confidence:high; evidence:sample coordinates within IHO-EEZ intersect shapefile"
        super_category_name = "IHO-EEZ_intersect"
    else:
        ic("WARNING: {super_category} not recognised")
        sys.exit()


    multi_field_dict = get_multi_field_dict()
    for field in curation_types2add:
        dom_type = (":").join([super_category, field])
        ic(dom_type)
        ic(super_category + " " + field)
        lc_field = field.lower()

        #if(df_specific[field].isnull().all() or (df_specific.loc[0,field] == 0 and is_unique(df_specific[field]))):
        if super_category == "lion":
            ic("field all values null or 0")
            # or is_unique(df_specific[field])
            ic("thus do not need")
        else:
            ic(df_specific[field].dtype)
            #ic(df_specific[field].value_counts())
            #during the below some empty "" values are created in json_col
            attributePostVal = ":".join([super_category_name, lc_field.removeprefix('intersect_')])
            if "TERRITORY" in field:
                result = re.search(r"(\d+)$", field)
                attributePostVal = "EEZ-territory-level-" + result.group(1)

                #Stephane's wish
                # "EEZ-territory-level-1"
                #"Japan (mrgid:2121) (ISO3166-1 alpha-3:JPN) (ISO3166-1 num-3:392)"

                ic(attributePostVal)
            elif "SOVEREIGN" in field:
                result = re.search(r"(\d+)$", field)
                attributePostVal = "EEZ-sovereign-level-" + result.group(1)
            elif "GEONAME" in field:
                attributePostVal = "EEZ-name"
            else:
                next

            if field in multi_field_dict[super_category]:
                ic(f"{field} in {multi_field_dict[super_category][field]}")
                df_specific['json_col'] = df_specific.apply(createMultiSubmissionsJson, axis = 1)
            else:
                df_specific['json_col'] = df_specific.apply(createIndividualSubmissionsJson, axis = 1)
            if is_numeric_dtype(df_specific[field]):
                ic(f"{field} is numeric!")
                df_specific.loc[df_specific[field] == 0, 'json_col'] = ""
            else:
                ic(f"{field} is not numeric!")
                df_specific.loc[df_specific[field].isnull(), 'json_col'] = ""
                df_specific.loc[df_specific[field] == 0, 'json_col'] = ""
            local_list = df_specific['json_col'].values.tolist()
            #remove empty list items
            local_list = [i for i in local_list if i]
            #ic("============", local_list)

            out_file = clearinghouse_data_dir + dom_type + '.json'
            ic(out_file)
            create_submit_curations_file(local_list, out_file)
            curation_list.extend(local_list)
            # ic(len(curation_list))
    return curation_list

def merge_sea_ena(debug_status, hit_dir):
    """merge_sea_ena
        merge the sea hits from the shape files with ENA
        currently only selecting those ENA samples that intersect with EEZ
    :param hit_dir:
    :return: df_merge_sea_ena
    """
    ic()
    ic(debug_status)

    df_ena_detail = get_all_ena_detailed_sample_info(debug_status)
    ic(df_ena_detail.shape)

    df_sea_hits = pd.read_csv(hit_dir + "merged_sea.tsv", sep='\t')
    ic(df_sea_hits.columns)

    #'intersect_MRGID', 'intersect_MARREGION', 'intersect_MRGID_IHO', 'intersect_IHO_SEA'

    int_cols = ['MRGID', 'intersect_MRGID', 'intersect_MRGID_IHO', 'MRGID_TER1', 'MRGID_TER2', 'MRGID_TER3', 'MRGID_SOV1', 'MRGID_SOV2', 'MRGID_IHO', 'MRGID_EEZ', \
                'UN_TER1', 'UN_TER2', 'UN_TER3', 'UN_SOV1', 'UN_SOV2', 'UN_SOV3']
    for mrg in int_cols:
        if mrg in df_sea_hits.columns:
            df_sea_hits[mrg] = df_sea_hits[mrg].fillna(0).astype(np.int32)
        else:
            ic(f"Warning: did not find {mrg} in df_sea_hits")
    cat_cols = []
    pats = ["TERR", "SOVER", "_category", "ECOREGION", "ISO", "GEONAME", "POL_TYPE", 'NAME']
    # ic(df_sea_hits.columns)
    for col_name in df_sea_hits.columns:
        for pat in pats:
            if pat in col_name:
                cat_cols.append(col_name)
    # ic(cat_cols)
    for col in cat_cols:
        df_sea_hits[col] = df_sea_hits[col].fillna("").astype("category")
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
     generate_marine_related_annotations

     :param debug_status:
     :param hit_dir:
     :param analysis_dir:
     :param clearinghouse_data_dir:
     :return:
    """
    df_merged_ena_sea = merge_sea_ena(debug_status, hit_dir)
    ic(df_merged_ena_sea.shape)
    #annotation_list = ["EEZ", 'IHO-EEZ']
    annotation_list = ['IHO-EEZ']
    annotation_list = ["EEZ"]

    ic(df_merged_ena_sea.columns)

    for annotation_type in annotation_list:
        if annotation_type == 'EEZ':
            df_merged_ena_sea = df_merged_ena_sea.query('eez_category == "EEZ"')
            ic(f"filtered for {annotation_type}: {df_merged_ena_sea.shape}")
            local_curation_list = process_supercat_fields(df_merged_ena_sea, annotation_type, clearinghouse_data_dir)
        elif annotation_type == 'IHO-EEZ':
            df_merged_ena_sea = df_merged_ena_sea.query('intersect_MARREGION != ""')
            ic(f"filtered for {annotation_type}: {df_merged_ena_sea.shape}")
            local_curation_list = process_supercat_fields(df_merged_ena_sea, annotation_type, clearinghouse_data_dir)
        else:
            print(f"ERROR: annotation_type: {annotation_type} is unknown")
        ic(len(local_curation_list))
    full_curation_list = []
    # demo_format(test_status)
    # in_file = analysis_dir + 'all_ena_gps_tax_combined.tsv'
    # df_gps = pd.read_csv(in_file, sep='\t', nrows =100)

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
        ic(args.debug_status)
        ic(type(args.debug_status))
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
                        help = "Debug status=True, if True just runs on a subset of the samples",
                        required = True, action = "store_true")
    parser.add_argument("-s", "--generate_specific_submissions",
                        help = "Generate specific submissions",
                        required = False,
                        action = "store_true"
                        )

    parser.parse_args()
    args = parser.parse_args()
    ic(args)
    print(args)

    main(args)