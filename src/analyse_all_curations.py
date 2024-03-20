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


def get_curation_json_data():
    """
      Read curation json data file and return json dict
      :return: json dict
    """
    my_file = ('/Users/woollard/projects/bluecloud/clearinghouse/high_seas/past_curations_records'
               '/pull_all_curations_done/output/') + 'swagger-grab2.json'
    ic(my_file)


    ic("JSON file contains multiple JSON document, so having to join them before reading.")
    with open(my_file, 'r') as infile:
        data = infile.read()
        new_data = data.replace('}{', '},{')
        json_data = json.loads(f'[{new_data}]')
    # returns JSON object as
    # a dictionary
    return json_data


def analyse_curations(curation_json_data):
    """
    analyse curation records providing some basic statistics about them
    :param curation_json_data:
    :return:
    """
    ic()
    my_stats = {'attribute': {}}
    record_count =0
    ic(f"{len(curation_json_data)} records")
    for record in curation_json_data:
        # ic(record)

        if record['attributePost'] not in my_stats['attribute']:
            my_stats['attribute'][record['attributePost']] = {'count': 1, 'suppressed_count': 0, 'unsuppressed_count': 0}
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


def main():
    curation_json_data = get_curation_json_data()
    analyse_curations(curation_json_data)


if __name__ == '__main__':
    ic()
    main()
