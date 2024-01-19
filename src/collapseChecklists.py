#!/usr/bin/env python3
"""Script of collapseChecklists.py is to collapseChecklists.py

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2024-01-18
__docformat___ = 'reStructuredText'
chmod a+x collapseChecklists.py
"""


from icecream import ic
import os
import argparse
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

def first_func():
    """"""

    ic()


    infile = "/Users/woollard/projects/ChecklistReviews/data/DataExports/checklist_fields.tsv"
    df = pd.read_csv(infile, sep="\t")
    ic(df.columns)
    # ic(df.columns)
    # df = df.query('CHECKLIST_FIELD_NAME in ["temperature", "sample volume or weight for DNA extraction"]')
    # # df = df.query('CHECKLIST_FIELD_NAME in ["temperature"]')
    # ic(df.head(3))
    df_new = df.groupby(['CHECKLIST_FIELD_GROUP_NAME', 'CHECKLIST_FIELD_NAME', 'CHECKLIST_FIELD_DESCRIPTION'])["CHECKLIST_ID"].apply(';'.join).reset_index()
    #ic(df_new)
    outfile = "/Users/woollard/projects/ChecklistReviews/data/DataExports/checklist_collapsed_cls.tsv"
    df_new.to_csv(outfile, sep = "\t", index=False)
    ic(f"writing to {outfile}")

def main():
    first_func()

if __name__ == '__main__':
    ic()
    main()
