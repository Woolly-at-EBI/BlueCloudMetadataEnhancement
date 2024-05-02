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
import re


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
      :return: json list of records string_ffs
    """
    json_file = ('/Users/woollard/projects/bluecloud/clearinghouse/high_seas/past_curations_records'
                 '/pull_all_curations_done/output/cho_EEZ-name.json_old')
    ic(json_file)
    # ic("JSON file contains multiple JSON document, so having to join them before reading.")
    with open(json_file, 'r') as infile:
        new_data = infile.read()
        # removing newlines initially to allow some other patterns matching work
        new_data = new_data.replace('\n', '').replace('}{', '},{').replace('}\n{', '},{').replace('{"id"', '\n{"id"')
        # ic(f"before replacements: {len(new_data)}")
        start_size = len(new_data)
        # re.sub('\n{"id"[^\n]*},\n', '', new_data) remove lines that only have a partial pattern!  want to delete
        # any "line" that starts /{"id"/ and doesn't /end }/ these should not exist, but they do... after some
        # exploration it is those that have a single white space. new_data = re.sub(r'\n{"id"[^\n]+^((?!},).)\n',
        # '\n', new_data) need to remove partial records. Cause broken JSON. We think that there was possibly an
        # interruption to streaming
        new_data = re.sub('\n{"id".* \n', '\n', new_data)
        end_size = len(new_data)
        if end_size < start_size:
            ic(f"WARNING Removed some defective JSON records: went from start_len={start_size} to end_len={end_size}")

        # ic("trying to debug json")
        # # string_ffs = '}{'
        # string_ffs = '\n{"id'
        # match = re.search(string_ffs, new_data)
        #
        # if match:
        #     print(f"Yes! found {string_ffs}")
        # else:
        #     print(f"No match to  {string_ffs}")
        # out_file = "FFS_not.json"
        # ic(f"writing to -->{out_file}<--")
        #
        # with open(out_file, 'w') as outfile:
        #     outfile.write(new_data)

        # json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 102557150 (
        # char 102557149) ic(f"102557148:102557150  {new_data[102557148:102557150]}") ic(f"102557000:102557300 {
        # new_data[102556000:102557400]}")
        # ic("end of trying to debug json")
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
    """
    getting all the curations that were generated by curation
    :return:
    """

    data_dir = "/Users/woollard/projects/bluecloud/clearinghouse/high_seas"
    # json_data = json.loads
    samples_by_cat_dict = {}

    name_dict = {
        'EEZ:SOVEREIGN1.json': 'EEZ:SOVEREIGN1',
        'IHO-EEZ:intersect_MARREGION.json': 'EEZ-IHO-intersect-name',
        'EEZ:TERRITORY2.json': 'EEZ:TERRITORY2',
        'EEZ:TERRITORY3.json': 'EEZ:TERRITORY3',
        'IHO:IHO_category.json': 'IHO-sea-area-name',
        'EEZ:GEONAME.json': 'EEZ-name',
        'EEZ:TERRITORY1.json': 'EEZ:TERRITORY1',
        'EEZ:SOVEREIGN3.json': 'EEZ:SOVEREIGN3',
        'EEZ:SOVEREIGN2.json': 'EEZ:SOVEREIGN2'
    }

    json_file_list = list(filter(lambda x: '.json' in x, os.listdir(data_dir)))
    ic(json_file_list)
    # json_file_list = ['IHO:IHO_category.json', 'IHO-EEZ:intersect_MARREGION.json']
    # json_file_list = ['IHO:IHO_category.json']
    json_file_list = ['IHO-EEZ:intersect_MARREGION.json']
    json_file_list = ['EEZ:GEONAME.json']
    ic(json_file_list)
    for json_file in json_file_list:
        sample_id_list = []
        full_file = data_dir + "/" + json_file
        json_data = json.loads(open(full_file).read())
        json_data = json_data['curations']
        ic(len(json_data))
        for record in json_data:
            sample_id_list.append(record['recordId'])

        name = name_dict[json_file]
        samples_by_cat_dict[name] = list(set(sample_id_list))  # make it unique.
        name_json = name + '_json'
        ic(f"{name} {len(samples_by_cat_dict[name])}")
        samples_by_cat_dict[name_json] = json_data
        ic()
    return samples_by_cat_dict


def json_list_to_json(my_list, out_file_name):
    ic(type(my_list))
    f = open(out_file_name, "w")
    # my_list = my_list[:2]
    curations_dict = {'curations': my_list}
    # ic(curations_dict)
    json.dump(curations_dict, f)
    f.close()


def analyse_submitted_data(samples_by_cat_dict):
    ic()
    ic("+++++++++++++++++++++++++++++++++++++++++++++++++++++")
    outdir = ("/Users/woollard/projects/bluecloud/clearinghouse/high_seas/past_curations_records"
              "/pull_all_curations_done/output/tmp_for_IHO-sea-area-name/")
    ic(samples_by_cat_dict.keys())
    my_list = ['EEZ-name']
    # my_list = list(samples_by_cat_dict.keys())
    # sys.exit()
    for name in my_list:
        ic(len(samples_by_cat_dict[name]))
        try_file_name = outdir + name + "_sample_ids_unsuppressed.txt"
        ic(try_file_name)
        if not os.path.isfile(try_file_name):
            ic(f" {try_file_name} does not exist, so trying to recreate")
            for sample in samples_by_cat_dict[name]:
                ic(sample)
                ic(samples_by_cat_dict[name][sample])
                break

        else:
            ic("already exists")
        sample_ids_unsuppressed_idfile = try_file_name
        sys.exit()

        # sample_ids_unsuppressed_idfile = ("/Users/woollard/projects/bluecloud/clearinghouse/high_seas"
        #                                   "/past_curations_records/pull_all_curations_done/output/tmp_for_IHO-sea"
        #                                   "-area-name/EEZ-IHO-intersect-name_sample_ids_unsuppressed.txt")
        sample_unsuppressed_id_set = set(get_file_ids(sample_ids_unsuppressed_idfile))
        ic(len(sample_unsuppressed_id_set))
        name_json = name + '_json'
        not_found_json_record_list = []
        for record in samples_by_cat_dict[name_json]:
            # ic(record['recordId'])
            if record['recordId'] not in sample_unsuppressed_id_set:
                not_found_json_record_list.append(record)
        ic(len(not_found_json_record_list))
        ic(type(not_found_json_record_list))
        out_file_name = outdir + name + '_to_resubmit' + ".json"
        ic(out_file_name)
        json_list_to_json(not_found_json_record_list, out_file_name)
        # cat EEZ-IHO-intersect-name_to_resubmit.json | jq '. | .curations[].recordId' | wc -l
    ic()
    sys.exit()


def get_file_ids(id_file_name):
    """
    takes the first column of id_file_name and returns a list of ids
    :param id_file_name:
    :return: a list of ids
    """
    with open(id_file_name, "r") as file:
        id_list = [line.split()[0] for line in file.readlines()]
    return id_list


def main():
    #  #################### looking at data being submitted to the clearinghouse ####################

    samples_by_cat_dict = get_generated_curations()
    ic(samples_by_cat_dict.keys())
    analyse_submitted_data(samples_by_cat_dict)
    sys.exit()

    #  #################### looking at data from the clearinghouse ####################
    data_dir = ("/Users/woollard/projects/bluecloud/clearinghouse/high_seas/past_curations_records"
                "/pull_all_curations_done/output/")
    json_file_list = list(filter(lambda x: '.json' in x, os.listdir(data_dir)))
    ic(json_file_list)

    # json_file_list = ["cho_IHO-name.json", "cho_IHO-sea-area-name.json", 'cho_intersect_MARREGION:marregion.json',
    #                   'cho_EEZ-IHO-intersect-name.json']
    # json_file_list = ["cho_IHO-sea-area-name.json"]
    # json_file_list = ['cho_intersect_MARREGION:marregion.json']
    # json_file_list = ["cho_IHO-name.json"]
    # json_file_list = ['cho_IHO-name.json_new']
    json_file_list = ['cho_EEZ-IHO-intersect-name.json']
    jsonfile_mapping = {'cho_EEZ-IHO-intersect-name.json': {'short_name': 'EEZ-IHO-intersect-name'},
                        'cho_EEZ-name.json': {'short_name': 'EEZ-name'},
                        'cho_EEZ-territory-level-1.json': {'short_name': 'EEZ-territory-level-1'},
                        'cho_EEZ-sovereign-level-1.json': {'short_name': 'EEZ-sovereign-level-1'}
                        }
    json_file_list = ['cho_EEZ-name.json', 'cho_EEZ-territory-level-1.json', 'cho_EEZ-sovereign-level-1.json']
    json_file_list = ['cho_EEZ-name.json']
    merged_json_list = []

    for json_file in json_file_list:
        ic(json_file)
        short_name = jsonfile_mapping[json_file]['short_name']
        ic(short_name)
        full_path = os.path.join(data_dir, json_file)
        ic(full_path)
        curation_json_data = get_curation_json_data(full_path)
        ic(f"{type(curation_json_data)} {len(curation_json_data)}")
        merged_json_list.extend(curation_json_data)
        # ic(len(merged_json_list))
        # ic(merged_json_list[5])

        sample_id_list = list(set(get_sample_ids(curation_json_data, 'unsuppressed')))
        ic(len(sample_id_list))
        outfile_name = data_dir + short_name + "_sample_ids_unsuppressed.txt"
        ic(outfile_name)
        print_list(sample_id_list, outfile_name)
        ic()
        # sys.exit()

    analyse_curations(merged_json_list)
    curation_id_list = get_curation_ids(merged_json_list, 'unsuppressed')
    outfile_name = data_dir + "all_curation_ids_unsuppressed.txt"
    ic(outfile_name)
    print_list(curation_id_list, outfile_name)


if __name__ == '__main__':
    ic()
    main()
