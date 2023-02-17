""" generate_clearinghouse_submissions.py
     see the PDF details in https://www.ebi.ac.uk/ena/clearinghouse/api/

 ___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-16
__docformat___ = 'reStructuredText'

"""
import json

from icecream import ic
import os.path

from clearinghouse_objects import *






def demo_format(test_status):


    curation_count = 0
    my_record = Sample(useENAAutoCurationValues=True)
    ic(my_record.get_filled_dict())
    sample_id = 'SAMD'
    ic(my_record.attributeDelete)
    my_record.recordId = sample_id
    ic(my_record.get_filled_dict())



def main():
    test_status = False
    demo_format(test_status)


if __name__ == '__main__':
    ic()

    main()