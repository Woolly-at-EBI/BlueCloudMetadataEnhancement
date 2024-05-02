#!/usr/bin/env python3
"""Script of 'filter_submission_json.py' is to filter  Clearinghouse submission JSON files for specific records

python3 filter_submission_json.py --help

usage: ./split_submission_json.py -i /Users/woollard/projects/bluecloud/clearinghouse/submission_data/full -o
/Users/woollard/projects/bluecloud/clearinghouse/submission_data/full/filter/

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-05-01
__docformat___ = 'reStructuredText'

"""

from icecream import ic
import argparse
import os
import json
import sys


def get_empty_curation_dict():
    curation_dict = {'curations': []}
    return curation_dict


def read_json(full_file_name):
    ic(f"processing {full_file_name} ")
    f = open(full_file_name)
    return json.load(f)

def file_2_list(file_path):
    """

    :param file_path:
    :return:
    """
    myFile = open(file_path, "r")
    strData = myFile.read()
    dataList = strData.split("\n")
    myFile.close()
    ic(len(dataList))
    return dataList
def select_specific_samples(full_file_name, out_dir, sample_ids_to_filter_for):
    directory = os.path.dirname(full_file_name)  # get path only
    short_filename = os.path.basename(full_file_name)  # get file name
    base_file_name, extension = os.path.splitext(short_filename)
    out_file = os.path.join(out_dir, base_file_name + "_filtered" + ".json")

    keep_sample_id_set = set(file_2_list(sample_ids_to_filter_for))
    data = read_json(full_file_name)
    record_count = 0
    local_count = 0
    batch_count = 0
    total_records = len(data['curations'])
    # ic(total_records)
    ic(sample_ids_to_filter_for)
    curation_dict = get_empty_curation_dict()
    ic(len(data['curations']))

    for record in data['curations']:
        # if record_count < 3:
        #     ic(record)
        if record['recordId'] not in keep_sample_id_set:
            # ic("not in keep list, so skipping")
            continue
        # else:
        #     ic("yippeeee")
        #     sys.exit()

        record_count += 1
        local_count += 1
        # print(".", end='')
        # ic(f"{record_count} {local_count}")
        curation_dict['curations'].append(record)

    ic(f"Writing filtered JSONs to {out_file}")
    with open(out_file, 'w') as of:
        json.dump(curation_dict, of)
    ic(len(curation_dict['curations']))



def main(args):
    """

    :param args: expecting full path json file
    :return:
    """



    if not os.path.isdir(args.out_dir):
        sys.exit(f"ERROR: out_dir does not exist: \'{args.out_dir}\', please create it!")
    else:
        ic(f"INFO: out_dir is a valid directory: {args.out_dir}")

    if os.path.isfile(args.in_file):
        json_file_name = args.in_file
        ic(json_file_name)
        if json_file_name.endswith(".json"):
            full_path = os.path.join(args.in_file, json_file_name)
            ic(full_path)
            select_specific_samples(json_file_name, args.out_dir, args.sample_ids_to_filter_for)
    else:
        print(f"ERROR: unknown file object {args.in_file}")


if __name__ == '__main__':
    ic()
    # Read arguments from command line
    prog_des = "filter_submission_json.py' is to filter  Clearinghouse submission JSON files for specific records"
    print(prog_des)
    parser = argparse.ArgumentParser(description = prog_des)

    # Adding optional argument, n.b. in debugging mode in IDE, had to turn required to false.
    parser.add_argument("-d", "--debug_status",
                        help = "Debug status i.e.True if selected, is verbose",
                        required = False, action = "store_true")
    parser.add_argument("-s", "--sample_ids_to_filter_for",
                        help = "sample_ids_to_filter_for",
                        required = False,
                        )
    parser.add_argument("-i", "--in_file",
                        help = "full path of json input file. If instead of a file a directory is provided, all the "
                               "JSON files in that directory are processed.",
                        required = True
                        )
    parser.add_argument("-o", "--out_dir",
                        help = "directory for the output files, default will be current directory",
                        required = False,
                        default = ""

                        )
    parser.parse_args()
    args = parser.parse_args()
    if args.debug_status:
        ic.enable()
    else:
        ic.disable()
    ic(args)

    main(args)
