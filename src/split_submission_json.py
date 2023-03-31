#!/usr/bin/env python3
"""Script of 'split_json.py' is to split large Clearinghouse submission JSON files with records into smaller chunks

python3 split_json.py --help

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-03-30
__docformat___ = 'reStructuredText'

"""

from icecream import ic
import argparse
import os
import json

def get_empty_curation_dict():
    curation_dict = {}
    curation_dict['curations'] = []
    return curation_dict
def split_json(full_file_name, file_name, batch_size, out_dir):
    ic(f"processing {full_file_name}")
    f = open(full_file_name)
    data = json.load(f)
    #ic(data)

    record_count = 0
    local_count = 0
    batch_count = 0
    file_name_prefix = file_name.removeprefix(".json")
    total_records = len(data['curations'])
    ic(total_records)

    for record in data['curations']:
        #ic(record)
        record_count += 1
        local_count += 1
        #print(".", end='')
        ic(f"{record_count} {local_count}")
        if local_count == 1:
            curation_dict = get_empty_curation_dict()
            #ic(curation_dict)
        curation_dict['curations'].append(record)
        if(local_count == batch_size or total_records == record_count):
            batch_count += 1
            split_file = os.path.join(out_dir , file_name_prefix + "_split_" + str(batch_count) + ".json")
            print("\nwriting to: " + split_file)
            with open(split_file, 'w') as of:
                json.dump(curation_dict, of)
            local_count = 0


def main():

    # Read arguments from command line
    prog_des = "Script to split large Clearinghouse submission JSON files with records into smaller chunks"
    print(prog_des)
    parser = argparse.ArgumentParser(description = prog_des)

    # Adding optional argument, n.b. in debugging mode in IDE, had to turn required to false.
    parser.add_argument("-d", "--debug_status",
                        help = "Debug status i.e.True if selected, is verbose",
                        required = False, action = "store_true")
    parser.add_argument("-b", "--batch_size",
                        help = "Batch size, if note specified default is 100",
                        required = False,
                        default = 100
                        )
    parser.add_argument("-i", "--in_file",
                        help = "full path of json input file",
                        required = True
                        )
    parser.add_argument("-o", "--out_dir",
                        help = "directory for the output files, default will be current directory",
                        required = False,
                        default = ""

                        )

    parser.parse_args()
    args = parser.parse_args()
    if args.debug_status == True:
        ic.enable()
    else:
        ic.disable()
    ic(args)
    json_file_name = os.path.basename(args.in_file)
    split_json(args.in_file, json_file_name, int(args.batch_size), args.out_dir)

if __name__ == '__main__':
    ic()
    main()
