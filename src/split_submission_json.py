#!/usr/bin/env python3
"""Script of 'split_submission_json.py' is to split large Clearinghouse submission JSON files with records into
smaller chunks If a directory is provided it will process the immediate child JSON files.

python3 split_submission_json.py --help

usage: ./split_submission_json.py -i /Users/woollard/projects/bluecloud/clearinghouse/submission_data/full -o
/Users/woollard/projects/bluecloud/clearinghouse/submission_data/full/splits/

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-03-30
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


def split_json(full_file_name, file_name, batch_size, out_dir):
    ic(f"processing {full_file_name} {batch_size}")
    f = open(full_file_name)
    data = json.load(f)
    # ic(data)

    record_count = 0
    local_count = 0
    batch_count = 0
    file_name_prefix = file_name.removeprefix(".json")
    total_records = len(data['curations'])
    ic(total_records)

    for record in data['curations']:
        # ic(record)
        record_count += 1
        local_count += 1
        # print(".", end='')
        ic(f"{record_count} {local_count}")
        if local_count == 1:
            curation_dict = get_empty_curation_dict()
            # ic(curation_dict)
        curation_dict['curations'].append(record)
        if local_count == batch_size or total_records == record_count:
            batch_count += 1
            split_file = os.path.join(out_dir, file_name_prefix + "_split_" + str(batch_count) + ".json")
            print(f"\nwriting to: {split_file}")
            with open(split_file, 'w') as of:
                json.dump(curation_dict, of)
            local_count = 0


def main(args):
    """

    :param args:
    :return:
    """

    def split_helper(in_file, batch_size, out_dir):
        json_file_name = os.path.basename(in_file)
        split_json(in_file, json_file_name, batch_size, out_dir)

    if not os.path.isdir(args.out_dir):
        sys.exit(f"ERROR: out_dir does not exist: \'{args.out_dir}\', please create it!")
    else:
        ic(f"INFO: out_dir is a valid directory: {args.out_dir}")

    if os.path.isfile(args.in_file):
        split_helper(args.in_file, int(args.batch_size), args.out_dir)
    elif os.path.isdir(args.in_file):
        print(f"You have provided a directory: {args.in_file}, so the JSON files in that will be processed")
        for json_file_name in os.listdir(args.in_file):
            ic(json_file_name)
            if json_file_name.endswith(".json"):
                full_path = os.path.join(args.in_file, json_file_name)
                ic(full_path)
                split_json(full_path, json_file_name, int(args.batch_size), args.out_dir)
    else:
        print(f"ERROR: unknown file object {args.in_file}")


if __name__ == '__main__':
    ic()
    # Read arguments from command line
    prog_des = "Script to split large Clearinghouse submission JSON files with records into smaller chunks"
    print(prog_des)
    parser = argparse.ArgumentParser(description = prog_des)

    # Adding optional argument, n.b. in debugging mode in IDE, had to turn required to false.
    parser.add_argument("-d", "--debug_status",
                        help = "Debug status i.e.True if selected, is verbose",
                        required = False, action = "store_true")
    parser.add_argument("-b", "--batch_size",
                        help = "Batch size, if note specified default is 1000",
                        required = False,
                        default = 1000
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
