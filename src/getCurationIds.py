#!/usr/bin/env python3
"""Script of getCurationIds.pl is to generate curl commands for extractions to certain time periods.

Was getting time outs if did dump of all, per month, or sometimes even per day.
So have put some functionality to this per hour too.

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2024-01-25
__docformat___ = 'reStructuredText'

"""


from icecream import ic
import os
import argparse
import sys
import calendar
from datetime import datetime, timedelta
import subprocess

def get_list_dates(start_date, end_date, do_per_hour):
    """
    want to get a tuple list of dates one day apart in the format
    """
    day_inc = 1

    def get_date_obj(my_date_string):
        (year, month, day) = my_date_string.split("-")
        return(datetime(int(year), int(month), int(day)))

    def get_date_obj_by_hour_array(my_date_string):
        (year, month, day) = my_date_string.split("-")
        date_array = []
        # ic(year, month, day)
        if do_per_hour:
            for hour_start in range(23):
                my_date_obj = datetime(int(year), int(month), int(day), int(hour_start))
                date_array.extend(my_date_obj)
        return(date_array)

    def get_objs_proper_iso_string(my_date_obj):
      return my_date_obj.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    def get_objs_date_string(my_date_obj):
      return my_date_obj.strftime('%Y-%m-%dT%H')

    def get_output_file_name(date1_obj,date2_obj):
        date1_str = get_objs_date_string(date1_obj)
        date2_str = get_objs_date_string(date2_obj)
        outfile_name = f"cho_{date1_str}_{date2_str}.json"
        return outfile_name

    ic()
    # num_days = calendar.monthrange(year, month)[1]

    start = get_date_obj(start_date)
    end = get_date_obj(end_date)

    if start > end:
        ic(f"ERROR: start={start} > end={end}")
        sys.exit()
    still_time = True
    date_tuple = []

    do_per_hour = True
    next_day = current_day = start
    current_day_iso_string = get_objs_proper_iso_string(current_day)
    while still_time:
       current_day = next_day
       next_day = current_day + timedelta(days=day_inc)
       # ic(type(next_day))
       if next_day <= end:
          # ic(get_objs_proper_iso_string(next_day))
          # ic(get_objs_date_string(current_day))

          if do_per_hour:
            for start_hour in range(24):
              actual_start =  current_day + timedelta(hours=start_hour)
              if start_hour < 23:
                  actual_end = actual_start + timedelta(hours=1)
              else:
                  actual_end = next_day
              current_day_iso_string = get_objs_proper_iso_string(actual_start)
              next_day_iso_string = get_objs_proper_iso_string(actual_end)
              # ic(f"{current_day_iso_string}, {next_day_iso_string}")
              my_tuple = (current_day_iso_string, next_day_iso_string, get_output_file_name(actual_start, actual_end))
              date_tuple.append(my_tuple)

          else:
              next_day_iso_string = get_objs_proper_iso_string(next_day)
              my_tuple = (current_day_iso_string, next_day_iso_string, get_output_file_name(current_day, next_day))
              date_tuple.append(my_tuple)
          current_day_iso_string = next_day_iso_string # then only have had called get_objs_proper_iso_string() once.
       else:
           still_time = False

    return date_tuple

def prepare(start_date, end_date, do_per_hour):
    """"""
    # time curl -X 'GET' \
    # 'https://www.ebi.ac.uk/ena/clearinghouse/api/curations?offset=0&providerName=European%20Nucleotide%20Archive&recordType=sample&startTime=2023-04-06T00%3A00%3A00.000Z&endTime=2023-04-07T00%3A00%3A00.000Z' \
    # -H 'accept: */*'

    date_list_pairs = get_list_dates(start_date, end_date, do_per_hour)
    ic(len(date_list_pairs))

    def run_cmd_line(cmd):
        print(cmd)
        as_commands = cmd.split(" ")
        ic(as_commands)
        process = subprocess.Popen(as_commands,
                           stdout=subprocess.PIPE,
                           universal_newlines=True)

        while True:
             output = process.stdout.readline()
             print(output.strip())
             # Do something else
             return_code = process.poll()
             if return_code is not None:
                 print('RETURN CODE', return_code)
                 # Process has finished, read rest of the output
                 for output in process.stdout.readlines():
                    print(output.strip())
                 break

    def get_curl_cmd(startTime, endTime):
        start = r"""curl 'https://www.ebi.ac.uk/ena/clearinghouse/api/curations?offset=0&providerName=European%20Nucleotide%20Archive&recordType=sample"""
        # time_part = r"""&startTime=2023-04-06T00%3A00%3A00.000Z&endTime=2023-04-07T00%3A00%3A00.000Z' """
        my_string = f"&startTime={startTime}&endTime={endTime}&limit=0" + r"""'"""
        full_curl = f"{start}{my_string}"
        # run_cmd_line(full_curl)
        return full_curl

    # selection_pipeline = r""" |  sed 's/{"id"/\n{"id"/g' | rg 'IHO' |  sed '$ s/,$//' |  sed '1s/^/{ "curations": [\n/' | sed -e $'$a\\\n]}\\' | sed 's/,/,\n/g' | sed 's/],"totalAttributes":[0-9]*}$//'  | jq '.[][] | {id, attributePost}' | sed 's/^{//;s/^}//;/^$/d;s/^  //;s/,$// ' """
    # cat test_out.json | jq | jq -s '.[] | .curations | .[] | select(.attributePost == "IHO-name") | .id'
    # selection_pipeline = """ | jq > test_out.json """


    for date_pair in date_list_pairs:
        selection_pipeline  = f" > {date_pair[2]}"
        do_per_hour = True
        full_cmd = get_curl_cmd(date_pair[0], date_pair[1]) + selection_pipeline
        print(full_cmd)
        # run_cmd_line(full_cmd)

    return

def main():
#    start_date = "2023-04-01"
#    end_date = "2023-05-01"
#    end_date = "2023-04-05"
#    start_date = "2023-04-06"
#    end_date = "2023-04-07"
#
#    start_date = "2023-04-01"
#    end_date = "2023-05-01"

    start_date = "2023-04-06"
    end_date = "2023-04-07"

    start_date = "2023-03-01"
    end_date = "2023-04-01"

    start_date = "2023-05-01"
    end_date = "2023-06-01"

    do_per_hour = True
    prepare(start_date, end_date, True)

if __name__ == '__main__':
    ic()
    main()
