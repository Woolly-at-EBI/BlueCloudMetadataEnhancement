#!/usr/bin/env python3
"""Script of testSwaggerGrab.py is to testSwaggerGrab.py

  example usage:  testSwaggerGrab.py -a IHO-sea-area-name -o cho_IHO-sea-area-name.json -s 723500 -b 100
___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2024-02-29
__docformat___ = 'reStructuredText'
chmod a+x testSwaggerGrab.py
"""

from icecream import ic
import sys
import argparse
import requests
import json
import time
import os.path

cho_url = "https://www.ebi.ac.uk/ena/clearinghouse/api/curations"


def get_query_params(attribute_name, offset, limit):
    query = {"offset": offset,
             "limit": limit,
             "recordType": "sample",
             "attribute": attribute_name
             }
    return query


def run_query(attribute_name, offset, limit):
    headers = {
        # 'cache-control': "no-cache"
    }
    query = get_query_params(attribute_name, offset, limit)
    ic(f"{cho_url}, headers = {headers}, params = {query}")
    response = requests.request("GET", cho_url, headers = headers, params = query)
    ic()

    if requests.codes.ok != 200:
        ic(f"warning {requests.codes.ok} will try again in a few seconds")
        time.sleep(5)  # sleep 5 seconds
        response = requests.request("GET", cho_url, headers = headers, params = query)
        if requests.codes.ok != 200:
            sys.exit(f"ERROR: {requests.status_codes} from running GET={cho_url}, header = {headers}, params = {query}")

    my_records = response.json()
    # ic(my_records)
    return my_records


def do_cho_queries(attribute_name, output_json_file, passed_offset_start, limit_max, batch_size):
    """"""
    ic()
    offset = passed_offset_start
    my_records = run_query(attribute_name, offset, 1)
    totalAttributes = my_records['totalAttributes']
    ic(totalAttributes)

    # totalAttributes = 3003

    ic(f"writing to {output_json_file}")
    if os.path.isfile(output_json_file):
        of_obj = open(output_json_file, "a")
    else:
        of_obj = open(output_json_file, "w")

    limit = offset_size = batch_size
    # limit = offset_size = 100
    if limit_max == 0:
        limit_max = totalAttributes
    off_set_start = offset
    # off_set_start = 377500
    ic(f"writing to {output_json_file} offset {off_set_start}")
    #      got to 15:30 on 29th Feb '377500 of 532401'
    #     '453000 of 532401' 1t 17:02
    # off_set_start = 453000
    # off_set_start = 532000
    # off_set_start = 532399

    ic(f"{off_set_start}, {limit_max}, {offset_size}")
    for offset in range(off_set_start, limit_max, offset_size):
        ic(f"{offset} of {totalAttributes}")
        if (offset + limit) > totalAttributes:  # don't want to query more than there are
            limit = totalAttributes - offset
        my_records = run_query(attribute_name, offset, limit)
        for curation_record in my_records['curations']:
            # ic(curation_record['recordId'])
            json.dump(curation_record, of_obj)
    of_obj.close()


def main(attribute_name, outfile, offset_start, limit_max, batch_size):
    do_cho_queries(attribute_name, outfile, offset_start, limit_max, batch_size)


if __name__ == '__main__':
    ic()
    # Read arguments from command line
    prog_des = "Script to extract all the curation records"
    parser = argparse.ArgumentParser(description = prog_des)

    # Adding optional argument, n.b. in debugging mode in IDE, had to turn required to false.
    parser.add_argument("-a", "--attribute_name", help = "attribute_name", required = True)
    parser.add_argument("-o", "--outfile", help = "Output file", required = True)
    parser.add_argument("-s", "--offset_start", type = int, help = "The offset to start from", required = True)
    parser.add_argument("-l", "--limit_max", type = int, help = "max to get records up to",
                        required = False, default = 0)
    parser.add_argument("-b", "--batch_size", type = int, help = "The batch size",
                        required = False, default = 500)
    parser.parse_args()
    args = parser.parse_args()
    ic(args)
    print(args)

    main(args.attribute_name, args.outfile, args.offset_start, args.limit_max, args.batch_size)
