#!/usr/bin/env python3
""" generate_clearinghouse_submissions.py
    from merge of shape hit files and also from waterTaxonomyAnalysis.py
     see the PDF details in https://www.ebi.ac.uk/ena/clearinghouse/api/

 ___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-16
__docformat___ = 'reStructuredText'

"""

import argparse
import re
import sys

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from clearinghouse_objects import *
from get_directory_paths import get_directory_paths
from ena_samples import get_all_ena_detailed_sample_info

pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)


def demo_format(test_status):
    ic()
    ic(test_status)
    my_record = NewSampleCuration(use_ena_auto_curation_values = True)
    ic(my_record.get_filled_dict())
    sample_id = 'SAMD'
    ic(my_record.attributeDelete)
    my_record.recordId = sample_id
    ic(my_record.get_filled_dict())


def get_multi_field_dict():
    """ get_multi_field_dict dictionary for providing which fields are associated and to thus provide together in the
    submission JSON The order of the list for the second level nested dictionary is important: [0] is the main term
    and its value will be the first part of the string for the attributePostValue. [1-:] are associated with the
    above. These useful terms and their values will all be bracketed. The order is important. :return: multi_field_dict
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
            'intersect_MARREGION': ['intersect_MARREGION', 'intersect_MRGID', 'intersect_EEZ', 'intersect_IHO_SEA',
                                    'intersect_MRGID_IHO']
        },
        'IHO': {
            'IHO_category': ['IHO_category', 'MRGID_IHO']
        }

    }

    return multi_field_dict


def process_supercat_fields(debug_status, df_merge_sea_ena, super_category, clearinghouse_data_dir, stats):
    """process_supercat_fields
        process all the EEZ etc. relevant fields and return a list of sample curations in JSON format to make.
        and print to file
        trying to do relatively efficiently by using the pandas, although doing apply to row by row!
            def createIndividualSubmissionsJson(row):
            def createMultiSubmissionsJson(row):
    :param debug_status:
    :param df_merge_sea_ena:
    :param super_category:
    :param clearinghouse_data_dir:
    :param stats:
    :return: curation_list
    """
    ic("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    ic()
    ic(debug_status)

    def createIndividualSubmissionsJson(row):
        """
        returns valid JSON if there is a hit, Notes: the attributePost format is super_category + : + lower_case(
        field) as lower case is the preferred INSDC format

            NewSampleCuration is Class from clearinghouse_object.pl
        :param row:
        :return:
        """
        if row[field] == "" or row[field] == 0:
            return
        else:
            my_record = NewSampleCuration(use_ena_auto_curation_values = True)
            my_record.recordId = row["accession"]
            my_record.attributePost = ":".join([super_category, lc_field])
            my_record.valuePost = row[field]
            my_record.putAssertionAdditionalInfo(assertion_additional_infoVal)
            my_record.emptyAssertionEvidence()
            my_record.addAutoAssertionEvidence(super_category)
            # print(my_record.get_filled_json())
            return my_record.get_filled_json()

    def createMultiSubmissionsJson(row):
        """
        returns valid JSON if there is a hit, Notes: the attributePost format is super_category + : + lower_case(
        field) as lower case is the preferred INSDC format NewSampleCuration is Class from clearinghouse_object.pl
        :param row: :return: local_stats
        """

        # ic("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        # ic()
        # ic(field)

        def get_mrgid_array_extra_annotation(my_field_name, value):
            if "mrgid" in my_field_name:
                return f"mrgid:{str(value)}"
            elif "iso" in my_field_name:  # iso & un are from sovereign and territory
                return f"ISO3166-1 alpha-3:{str(value)}"
            elif "un" in my_field_name:
                return f"ISO3166-1 num:{str(value)}"
            else:
                return ""  # possibly an error, but can handle later

        if row[field] == "" or row[field] == 0:
            return
        else:
            my_record = NewSampleCuration(use_ena_auto_curation_values = True)
            my_record.putAttributionType("shapefile")
            my_record.recordId = row["accession"]
            my_record.attributePost = attributePostVal
            my_record.putAssertionAdditionalInfo(assertion_additional_infoVal)
            my_record.emptyAssertionEvidence()
            my_record.addAutoAssertionEvidence(super_category)
            value_array = []
            extra_array = []
            # ic(row)
            matches = ["TERRITORY", "SOVEREIGN", "GEONAME", "IHO_category"]
            # ic(matches)
            if "intersect_MARREGION" in field:
                # ic()
                # ic("intersect_MARREGION in field")
                # ic(row)
                count = 0
                # if type(row["intersect_EEZ"]) is not str or row["intersect_EEZ"] == "":
                #     # as EEZ name is nan (actually float...)"
                #     ic(f"WARNING: {field} is not an intersect as EEZ is NaN so skipping record")
                #     return
                for component_field in multi_field_dict[super_category][field]:
                    # if component_field != "intersect_MARREGION":  #Peter, this is just in debuggig!
                    #    continue
                    # ic(f"   {super_category}; {component_field}")
                    if row[component_field] == "" or row[component_field] == 0:
                        continue
                    # else:
                    # ic(f"{component_field} component:{row[component_field]}<---")
                    field_name = component_field.lower().removeprefix('intersect_')

                    # if component_field == "intersect_MARREGION" and 'High' in row[component_field]:
                    #     ic(f"Yipeeeeee High found")
                    if count == 0:
                        value_array.append(str(row[component_field]))
                    else:
                        if field_name == "mrgid":
                            extra_array.append(get_mrgid_array_extra_annotation(field_name, row[component_field]))
                    count += 1
            elif any([x in field for x in matches]):  # are other EEZ related matches

                count = 0
                for component_field in multi_field_dict[super_category][field]:
                    if row[component_field] == "" or row[component_field] == 0:
                        continue
                    # else:
                    #     ic(f"component:{row[component_field]}<---")
                    field_name = component_field.lower().removesuffix("_category")
                    # ic(f"{field_name}")
                    if count == 0:
                        value_array.append(str(row[component_field]))
                    else:
                        extra_array.append(get_mrgid_array_extra_annotation(field_name, row[component_field]))
                    count += 1
                my_record.valuePost = "".join(value_array)
            else:
                for component_field in multi_field_dict[super_category][field]:
                    field_name = component_field.lower()
                    value_array.append(":".join([field_name, str(row[component_field])]))
                my_record.valuePost = "; ".join(value_array)

            if len(extra_array) > 0:
                # ic("have some extra_array fields")
                my_record.putValuePID("; ".join(extra_array))  # n.b. This ValuePID is not being used yet

                # Stephane wants, the value to look like "China (CHN; 156)"
                if my_record.attributePost in ['EEZ-sovereign-level-1', 'EEZ-territory-level-1']:
                    name_matches = [x for x in extra_array if re.match("ISO3166-1 alpha-3", x)]
                    if len(name_matches) > 0:
                        country_abbr = country_num = ""
                        if "ISO3166-1 alpha-3:" in name_matches[0]:
                            country_abbr = name_matches[0].removeprefix("ISO3166-1 alpha-3:")
                        num_matches = [x for x in extra_array if re.match("ISO3166-1 num", x)]
                        if len(num_matches) > 0 and "ISO3166-1 num:" in num_matches[0]:
                            # had a few cases where this did not exist
                            country_num = num_matches[0].removeprefix("ISO3166-1 num:")
                        value_array.append(f" ({country_abbr}; {country_num})")
            # else:
            #     ic("Don't have some extra_array fields")

            my_record.valuePost = "".join(value_array)
            # ic(my_record.valuePost)
            # ic(my_record.get_filled_dict())

            return my_record.get_filled_json()

    # ic(df_merge_sea_ena.sample(n = 2))
    # ic(df_merge_sea_ena.columns)
    # super_category = 'EEZ'
    curation_list = []

    # comparing the first value with the rest, as want to know if all values are the same
    assertion_additional_infoVal = ""
    multi_field_dict = get_multi_field_dict()

    if super_category == "EEZ":
        curation_types2add = ['GEONAME', 'TERRITORY1', 'TERRITORY2', 'TERRITORY3', 'SOVEREIGN1',
                              'SOVEREIGN2', 'SOVEREIGN3']
        # curation_types2add = ['TERRITORY1'
        super_category_name = 'GEONAME'
        # df_specific = df_merge_sea_ena.query('UN_TER3 != None & UN_TER2 != 0', engine='python').copy()
        df_specific = df_merge_sea_ena.query('GEONAME != None', engine = 'python').copy()
        assertion_additional_infoVal = "confidence:high; evidence:sample coordinates within EEZ shapefile"
    elif super_category == "IHO-EEZ":
        ic()
        curation_types2add = ['intersect_MARREGION']
        super_category_name = 'intersect_MARREGION'
        # df_specific = df_merge_sea_ena.query('intersect_UN_TER3 != None').copy()
        df_specific = df_merge_sea_ena.query('intersect_MARREGION != None').copy()
        ic(df_specific.shape)
        assertion_additional_infoVal = "confidence:high; evidence:sample coordinates within IHO-EEZ intersect shapefile"
    elif super_category == "IHO":
        curation_types2add = ['IHO_category']
        df_specific = df_merge_sea_ena.query('IHO_category != None').copy()
        assertion_additional_infoVal = "confidence:high; evidence:sample coordinates within IHO World Seas shapefile"
        super_category_name = "IHO_category"
    else:
        ic(f"ERROR: {super_category} not recognised")
        sys.exit()

    for field in curation_types2add:
        dom_type = ":".join([super_category, field])
        # ic(f"{dom_type} {super_category} {field}")
        lc_field = field.lower()

        # if(df_specific[field].isnull().all() or (df_specific.loc[0,field] == 0 and is_unique(df_specific[field]))):
        if super_category == "lion":
            ic("INFO: field all values null or 0")
        else:
            # ic(df_specific.columns)
            # ic(df_specific[field].dtype)

            # during the below some empty "" values are created in json_col
            if "TERRITORY" in field:
                result = re.search(r"(\d+)$", field)
                attributePostVal = "EEZ-territory-level-" + result.group(1)
                # Stephane's wish:   "EEZ-territory-level-1"
                # "Japan (mrgid:2121) (ISO3166-1 alpha-3:JPN) (ISO3166-1 num-3:392)"
            elif "SOVEREIGN" in field:
                result = re.search(r"(\d+)$", field)
                attributePostVal = "EEZ-sovereign-level-" + result.group(1)
            elif "GEONAME" in field:
                attributePostVal = "EEZ-name"
            elif "IHO_category" == field:
                attributePostVal = "IHO-sea-area-name"
            elif "MARREGION" in field:
                attributePostVal = "EEZ-IHO-intersect-name"
            else:
                attributePostVal = ":".join([super_category_name, lc_field.removeprefix('intersect_')])
            # ic(attributePostVal)

            if field in multi_field_dict[super_category]:
                ic(f"{field} in {multi_field_dict[super_category][field]}")
                local_stats = df_specific['json_col'] = df_specific.apply(createMultiSubmissionsJson, axis = 1)
                # sys.exit()
            else:
                # ic(f"{field} not in {multi_field_dict[super_category][field]}")
                local_stats = df_specific['json_col'] = df_specific.apply(createIndividualSubmissionsJson, axis = 1)

            if is_numeric_dtype(df_specific[field]):
                df_specific.loc[df_specific[field] == 0, 'json_col'] = ""
            else:
                df_specific.loc[df_specific[field].isnull(), 'json_col'] = ""
                df_specific.loc[df_specific[field] == 0, 'json_col'] = ""
            local_list = df_specific['json_col'].values.tolist()
            local_list = [i for i in local_list if i]  # remove empty list items
            out_file = clearinghouse_data_dir + dom_type + '.json'
            stats['by_curation_type'][field] = {'curation_count': len(local_list)}
            create_submit_curations_file(local_list, out_file)
            curation_list.extend(local_list)
        # sys.exit()
    ic(stats)
    return stats


def merge_sea_ena(debug_status, hit_dir):
    """merge_sea_ena
        merge the sea hits from the shape files with ENA
        currently only selecting those ENA samples that intersect with EEZ
    :param debug_status:
    :param hit_dir:
    :return: df_merge_sea_ena
    """
    ic()
    ic(debug_status)
    if not debug_status:
        print("WARNING: debug is False, so will run on the complete ENA dataset!")

    df_ena_detail = get_all_ena_detailed_sample_info(debug_status, 0)
    ic(df_ena_detail.shape)

    df_sea_hits = pd.read_csv(hit_dir + "merged_sea.tsv", sep = '\t')

    # For debugging getting just the High Sea containing entries
    ic(df_sea_hits.columns)
    # df_sea_hits = df_sea_hits[df_sea_hits['intersect_MARREGION'].str.contains("High", na=False)]
    # ic(df_sea_hits.head())
    ic(df_sea_hits.shape)
    # ic(df_sea_hits.columns)

    # 'intersect_MRGID', 'intersect_MARREGION', 'intersect_MRGID_IHO', 'intersect_IHO_SEA'

    int_cols = ['MRGID', 'intersect_MRGID', 'intersect_MRGID_IHO', 'MRGID_TER1', 'MRGID_TER2', 'MRGID_TER3',
                'MRGID_SOV1', 'MRGID_SOV2', 'MRGID_IHO', 'MRGID_EEZ',
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

    df_merge_sea_ena = pd.merge(df_ena_detail, df_sea_hits, on = ["lat", "lon"], how = "inner")

    if debug_status:
        ic(df_merge_sea_ena.shape)
        #
        # ic(df_merge_sea_ena.dtypes)
        # ic(df_merge_sea_ena.head(2))
        ic(df_merge_sea_ena.columns)
        # df_merge_sea_ena = df_merge_sea_ena[df_merge_sea_ena['intersect_MARREGION'].str.contains("High", na = False)]
        # ic(df_merge_sea_ena.shape)
        # df_merge_sea_ena = df_merge_sea_ena.head(5)
        # ic(df_merge_sea_ena)
    # sys.exit()
    return df_merge_sea_ena


def create_submit_curations_file(full_curation_list, out_file):
    """create_submit_curations_file
        If curations add them in JSON format to the out_file

    :param out_file:
    :param full_curation_list:
    :param  out_file: file name
    :return: total number of curations
    """
    print(f"Creating curations for {len(full_curation_list)} {out_file}")
    if len(full_curation_list) == 0:
        ic("Warning no curations, so not creating: ", out_file)
    else:
        ic("INFO: creating ", len(full_curation_list), " curations for submission in ", out_file)
        submission_dict = {'curations': []}

        for json_string in full_curation_list:
            json_data = json.loads(json_string)
            submission_dict['curations'].append(json_data)
        with open(out_file, 'w') as fp:
            fp.write(json.dumps(submission_dict, indent = 2))

    return len(full_curation_list)


def generate_marine_related_annotations(debug_status, hit_dir, analysis_dir, clearinghouse_data_dir):
    """
     generate_marine_related_annotations

     :param debug_status:
     :param hit_dir:
     :param analysis_dir:
     :param clearinghouse_data_dir:
     :return:
    """
    df_merged_ena_sea_full = merge_sea_ena(debug_status, hit_dir)
    ic(df_merged_ena_sea_full.shape)
    stats = {"by_curation_type": {}}

    annotation_list = ["EEZ", 'IHO-EEZ', 'IHO']
    annotation_list = ['IHO-EEZ']

    local_curation_list = []

    # trying to just have the specific rows for the annotation in question
    for annotation_type in annotation_list:
        df_merged_ena_sea = df_merged_ena_sea_full
        ic(annotation_type)
        if annotation_type == 'EEZ':
            df_merged_ena_sea = df_merged_ena_sea.query('eez_category == "EEZ"')
        elif annotation_type == 'IHO-EEZ' or annotation_type == 'IHO':
            df_merged_ena_sea = df_merged_ena_sea.query('intersect_MARREGION != ""')
        else:
            print(f"WARNING: annotation_type: {annotation_type} is unknown")
            continue
        # ic(f"filtered for {annotation_type}: {df_merged_ena_sea.shape}")
        local_curation_list = process_supercat_fields(debug_status, df_merged_ena_sea, annotation_type,
                                                      clearinghouse_data_dir, stats)
        # ic(len(local_curation_list))
    # ic()
    # full_curation_list = []
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

    if not args.debug_status:
        ic.disable()
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    # clearinghouse_data_dir = "/Users/woollard/projects/bluecloud/clearinghouse/submission_data/"
    # clearinghouse_data_dir = "/Users/woollard/projects/bluecloud/clearinghouse/corrections/"
    clearinghouse_data_dir = "/Users/woollard/projects/bluecloud/clearinghouse/high_seas/"

    ic(args.generate_specific_submissions)
    if args.generate_specific_submissions:
        ic(args.debug_status)
        ic(type(args.debug_status))
        generate_marine_related_annotations(args.debug_status, hit_dir, analysis_dir, clearinghouse_data_dir)
    else:
        ic("whoops, no specific submissions found")

    # submit_curations(full_curation_list, analysis_dir)


if __name__ == '__main__':
    ic()
    # Read arguments from command line
    prog_des = "Script to get the marine zone classification for a set of longitude and latitude coordinates\n" + \
               "Typical prod usage: ./generate_clearinghouse_submissions.py -s" + \
                "Typical debug usage: ./generate_clearinghouse_submissions.py -d -s" + \
                "Pre-requesites, uses these input files: merged_sea.tsv  which in turn uses hits files particularly the High seas one,"
    parser = argparse.ArgumentParser(description = prog_des)

    # Adding optional argument, n.b. in debugging mode in IDE, had to turn required to false.
    parser.add_argument("-d", "--debug_status",
                        help = "Debug status i.e.True, if True just runs on a subset of the samples",
                        required = False, action = "store_true")
    parser.add_argument("-s", "--generate_specific_submissions",
                        help = "Generate specific submissions, needed if you want to actually generate ought.",
                        required = True,
                        action = "store_true"
                        )

    parser.parse_args()
    args = parser.parse_args()
    ic(args)
    print(args)

    main(args)
