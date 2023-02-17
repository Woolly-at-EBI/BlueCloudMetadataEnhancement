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
    ic(df_merge_combined_tax.columns)

    def createSubmissionsJson(row):
        my_record = Sample(useENAAutoCurationValues = True)
        my_record.recordId = row["accession"]
        my_record.attributePost = dom_type
        my_evidence_string = "confidence:" + row[field]
        if row['location_designation'] == dom_type:
            my_evidence_string += "; GPS_evidence:True"
        elif row['location_designation'] == "marine and terrestrial":
            my_evidence_string += "; GPS_evidence:True (marine and terrestrial)"
        else:
            my_evidence_string += "; GPS_evidence:False"
        my_evidence_string += "; taxa_evidence:" + ("True" if row[tax_dom_field] else "False")
        my_record.assertionAdditionalInfo = my_evidence_string
        ic(my_record.get_filled_dict())
        return my_record.get_filled_dict()

    inc_cols = ['accession', 'marine (ocean connected)', 'freshwater (land enclosed)','location_designation',
                'sample_confidence_marine_inc_biome', 'sample_confidence_terrestrial_inc_biome']
    df_merge_combined_tax_res = df_merge_combined_tax[inc_cols]
    ic("collect marine high confidence")
    dom_type = 'marine'


    if dom_type == 'marine':
        field = "sample_confidence_marine_inc_biome"
        tax_dom_field = 'marine (ocean connected)'

    df_specific = df_merge_combined_tax_res.query('sample_confidence_marine_inc_biome == "high"').head(3)
    df_specific['json_col'] = df_specific.apply(createSubmissionsJson, axis=1)
    ic(df_specific.head(5))
    ic(df_specific['json_col'].head(3))



def main():
    test_status = True
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()


    demo_format(test_status)


    pickle_file = analysis_dir + 'merge_combined_tax_all_with_confidence.pickle'
    # df_merge_combined_tax = get_pickleObj(pickle_file)
    # df_merge_combined_tax = df_merge_combined_tax.head(100000).query('taxonomic_source == "metagenome"')
    #put_pickleObj2File(df_merge_combined_tax, "./tmp.pickle")
    df_merge_combined_tax = get_pickleObj("./tmp.pickle")
    process_confidence_fields(df_merge_combined_tax,analysis_dir)




if __name__ == '__main__':
    ic()

    main()