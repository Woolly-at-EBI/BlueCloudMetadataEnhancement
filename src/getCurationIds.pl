#!/usr/bin/env python3
"""Script of getCurationIds.pl is to getCurationIds.pl

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2024-01-25
__docformat___ = 'reStructuredText'

"""


from icecream import ic
import os
import argparse
import sys
import calendar
import datetime

def get_list_dates(start_date, end_date):
    """
    want to get a list of dates one day apart
    """
    day_inc = 1

    def get_date_obj(my_date_string):
        (year, month, day) = my_date_string.split("-")
        ic(year, month, day)
        my_date_obj = datetime.datetime(int(year), int(month), int(day))
        return(my_date_obj)

    def get_objs_proper_iso_string(my_date_obj):
      return my_date_obj.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    ic()
    # num_days = calendar.monthrange(year, month)[1]


    start = get_date_obj(start_date)
    ic(start.strftime('%Y-%m-%dT%H:%M:%SZ'))
    end = get_date_obj(end_date)
    ic(end.strftime('%Y-%m-%dT%H:%M:%SZ'))
    ic(type(start))
    ic(type(end))

    if start > end:
        ic(f"ERROR: start={start} > end={end}")
        sys.exit()
    still_time = True
    next_day = start
    start_isoformat = get_objs_proper_iso_string(start)
    ic(start_isoformat)
    while still_time:
       next_day += datetime.timedelta(days=day_inc)
       # ic(type(next_day))
       if next_day <= end:
          ic(get_objs_proper_iso_string(next_day))
       else:
           still_time = False

    sys.exit()

def prepare(start_date, end_date):
    """"""
    # time curl -X 'GET' \
    # 'https://www.ebi.ac.uk/ena/clearinghouse/api/curations?offset=0&providerName=European%20Nucleotide%20Archive&recordType=sample&startTime=2023-04-06T00%3A00%3A00.000Z&endTime=2023-04-07T00%3A00%3A00.000Z' \
    # -H 'accept: */*'

    data_list_pairs = get_list_dates(start_date, end_date)

    sys.exit()
    start = r""" curl -X 'GET'  'https://www.ebi.ac.uk/ena/clearinghouse/api/curations?offset=0&providerName=European%20Nucleotide%20Archive&recordType=sample"""
    print(start)
    time_part = r"""&startTime=2023-04-06T00%3A00%3A00.000Z&endTime=2023-04-07T00%3A00%3A00.000Z' """

    selection_pipeline = r""" |  sed 's/{"id"/\n{"id"/g' | rg 'IHO' |  sed '$ s/,$//' |  sed '1s/^/{ "curations": [\n/' | sed -e $'$a\\\n]}\\' | sed 's/,/,\n/g' | sed 's/],"totalAttributes":[0-9]*}$//'  | jq '.[][] | {id, attributePost}' | sed 's/^{//;s/^}//;/^$/d;s/^  //;s/,$// ' """

    print(start + time_part + selection_pipeline)

def main():
    start_date = "2023-04-01"
    end_date = "2023-05-01"
    end_date = "2023-04-05"

    prepare(start_date, end_date)

if __name__ == '__main__':
    ic()
    main()
