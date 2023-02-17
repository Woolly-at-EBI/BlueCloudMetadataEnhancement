""" generate_clearinghouse_submissions.py
     see the PDF details in https://www.ebi.ac.uk/ena/clearinghouse/api/

 ___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-16
__docformat___ = 'reStructuredText'

"""
import json

from icecream import ic
import os.path
import pickle
import pandas as pd
pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)

from clearinghouse_objects import *
from get_directory_paths import get_directory_paths
from project_utils import put_pickleObj2File,get_pickleObj

def demo_format(test_status):


    curation_count = 0
    my_record = Sample(useENAAutoCurationValues=True)
    ic(my_record.get_filled_dict())
    sample_id = 'SAMD'
    ic(my_record.attributeDelete)
    my_record.recordId = sample_id
    ic(my_record.get_filled_dict())

def process_confidence_fields(df_merge_combined_tax, analysis_dir):
    """

    :param df_merge_combined_tax:
    :param analysis_dir:
    :return:
    """
    ic(df_merge_combined_tax.head())




def main():
    test_status = True
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()


    demo_format(test_status)


    pickle_file = analysis_dir + 'df_merge_combined_tax.pickle'
    df_merge_combined_tax = get_pickleObj(pickle_file)
    df_merge_combined_tax = df_merge_combined_tax.head(100000).query('taxonomic_source == "metagenome"')
    put_pickleObj2File(df_merge_combined_tax, "./tmp.pickle")
    df_merge_combined_tax = get_pickleObj("./tmp.pickle")
    process_confidence_fields(df_merge_combined_tax,analysis_dir)




if __name__ == '__main__':
    ic()

    main()