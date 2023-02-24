"""
script to convert tab separated files to parquet format
e.g. python3 convertCSV2parquet.py -i ../data/samples/sample_much_raw.tsv -o ../data/samples/sample_much_raw.pa
"""

import pyarrow as pa
from pyarrow import csv
from pyarrow import parquet
from pyarrow.parquet import ParquetFile

import pandas as pd
from icecream import ic

import argparse


def convert_csv3parquet(args):
    # Convert from pandas to Arrow

    fn = args.infile
    ic(fn)
    ofn = args.outfile
    ic(ofn)

    def skip_comment(row):
        if row.text.startswith("# "):
            return 'skip'
        else:
            return 'error'

    parse_options = csv.ParseOptions(delimiter="\t", invalid_row_handler=skip_comment)

    table = pa.csv.read_csv(fn, read_options=None, parse_options=parse_options)
    df_new = table.to_pandas()
    ic(df_new.head())

    pa.parquet.write_table(table, ofn)

    pf = ParquetFile(ofn)
    first_ten_rows = next(pf.iter_batches(batch_size = 10))
    df_new = pa.Table.from_batches([first_ten_rows]).to_pandas()

    # table = pa.parquet.read_table(ofn)
    # # Convert back to pandas
    # df_new = table.to_pandas()
    ic(df_new.head())



def main():
    """ main
        __params__:
               passed_args
    """

    convert_csv3parquet(args)

if __name__ == '__main__':
    ic()
    # Read arguments from command line
    prog_des = "Script to convert csv to parquet"
    parser = argparse.ArgumentParser(description = prog_des)

    # Adding optional argument, n.b. in debugging mode in IDE, had to turn required to false.
    parser.add_argument("-v", "--verbosity", type = int, help = "increase output verbosity", required = False)
    parser.add_argument("-o", "--outfile", help = "Output file", required = True)
    parser.add_argument("-i", "--infile", help = "Input file", required = True)

    parser.parse_args()
    args = parser.parse_args()
    ic(args)
    print(args)
    if args.verbosity:
        print("verbosity turned on")

    main()
