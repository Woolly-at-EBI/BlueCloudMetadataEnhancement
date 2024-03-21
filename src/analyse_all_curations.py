#!/usr/bin/env python3
"""Script of analyse_all_curations.py is to analyse_all_curations.py

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2024-03-19
__docformat___ = 'reStructuredText'
chmod a+x analyse_all_curations.py
"""

import json
import sys
from icecream import ic
import os


def get_curation_json_data(json_file):
    """
      Read curation json data file and return list of records, each of type
      {'assertionAdditionalInfo': 'confidence:high; evidence:sample coordinates '
                                                   'within IHO World Seas shapefile',
                        'assertionEvidences': [{'identifier': 'ECO:0000203',
                                                'label': 'automatic assertion',
                                                'shortForm': 'ECO_0000203'},
                                               {'identifier': 'ECO:0000366',
                                                'label': 'evidence based on logical inference from '
                                                         'automatic annotation used in automatic '
                                                         'assertion',
                                                'shortForm': 'ECO_0000366'}],
                        'assertionMethod': 'automatic assertion',
                        'assertionSource': 'https://www.marineregions.org',
                        'attributeDelete': False,
                        'attributePost': 'IHO-sea-area-name',
                        'checklistCompliant': False,
                        'id': 'e1347a28-7fc2-45db-995f-844a97563321',
                        'primaryRecordId': 'SAMEA11124721',
                        'providerName': 'European Nucleotide Archive',
                        'providerUrl': 'https://www.ebi.ac.uk/ena/browser/home',
                        'recordId': 'SAMEA11124721',
                        'recordType': 'sample',
                        'submittedTimestamp': '2024-01-24T09:07:56.316+0000',
                        'suppressed': False,
                        'updatedTimestamp': '2024-01-24T09:07:56.316+0000',
                        'valuePost': 'North Atlantic Ocean'}
      :return: json list of records
    """

    # ic("JSON file contains multiple JSON document, so having to join them before reading.")
    with open(json_file, 'r') as infile:
        data = infile.read()
        new_data = data.replace('}{', '},{')
        json_data = json.loads(f'[{new_data}]')

    ic(type(json_data))
    return json_data


def analyse_curations(curation_json_data):
    """
    analyse curation records providing some basic statistics about them
    :param curation_json_data:
    :return:
    """
    ic()
    my_stats = {'attribute': {}}
    record_count = 0
    ic(f"{len(curation_json_data)} records")
    for record in curation_json_data:
        # ic(record)

        if record['attributePost'] not in my_stats['attribute']:
            my_stats['attribute'][record['attributePost']] = {'count': 1, 'suppressed_count': 0,
                                                              'unsuppressed_count': 0}
        else:
            my_stats['attribute'][record['attributePost']]['count'] += 1

        if record['suppressed']:
            my_stats['attribute'][record['attributePost']]['suppressed_count'] += 1
        else:
            my_stats['attribute'][record['attributePost']]['unsuppressed_count'] += 1

        record_count += 1
        # if record_count > 10:
        #     break

    ic(my_stats)


def get_curation_ids(curation_json_data_list, suppression_type):
    curation_id_list = []
    target_count = 0
    if suppression_type == 'unsuppressed':
        for record in curation_json_data_list:
            if not record['suppressed']:
                # ic(f"{record['recordId']} {record['suppressed']}")
                curation_id_list.append(record['id'])
                target_count += 1
    # ic(curation_id_list)
    ic(target_count)
    return curation_id_list


def get_sample_ids(curation_json_data_list, suppression_type):
    """
    getting sample ids unsuppressed (for the desired field)
    :param curation_json_data_list:
    :param suppression_type:
    :return:
    """
    sample_id_list = []
    target_count = 0
    if suppression_type == 'unsuppressed':
        for record in curation_json_data_list:
            if not record['suppressed']:
                # ic(f"{record['recordId']} {record['suppressed']}")
                sample_id_list.append(record['primaryRecordId'])
                target_count += 1
    # ic(curation_id_list)
    ic(target_count)
    return sample_id_list


def print_list(my_list, outfile):
    ic(f"writing to {outfile} for {len(my_list)}")
    with open(outfile, "w") as outfile_obj:
        ic("inside outfile_obj")
        outfile_obj.write("\n".join(my_list))

def get_generated_curations():
    curation_id_list = []
    dir = "/Users/woollard/projects/bluecloud/clearinghouse/high_seas"
    # json_data = json.loads

def main():

    get_generated_curations()

    sys.exit()
    data_dir = ("/Users/woollard/projects/bluecloud/clearinghouse/high_seas/past_curations_records"
                "/pull_all_curations_done/output/")
    json_file_list = list(filter(lambda x: '.json' in x, os.listdir(data_dir)))
    ic(json_file_list)

    # json_file_list = ["cho_IHO-name.json", "cho_IHO-sea-area-name.json", 'cho_intersect_MARREGION:marregion.json',
    #                   'cho_EEZ-IHO-intersect-name.json']

    json_file_list = ["cho_IHO-sea-area-name.json"]
    merged_json_list = []

    for json_file in json_file_list:
        ic(json_file)
        full_path = os.path.join(data_dir, json_file)
        ic(full_path)
        curation_json_data = get_curation_json_data(full_path)
        ic(f"{type(curation_json_data)} {len(curation_json_data)}")
        merged_json_list.extend(curation_json_data)
    # ic(len(merged_json_list))
    # ic(merged_json_list[5])
    analyse_curations(merged_json_list)
    # curation_id_list = get_curation_ids(merged_json_list, 'unsuppressed')
    # print_list(curation_id_list, data_dir + "curation_ids_2_suppress.txt")
    sample_id_list = list(set(get_sample_ids(merged_json_list, 'unsuppressed')))
    ic(len(sample_id_list))
    print_list(sample_id_list, data_dir + "sample_ids_unsuppressed.txt")


if __name__ == '__main__':
    ic()
    main()
