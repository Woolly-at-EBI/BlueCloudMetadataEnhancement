"""Script of get_geo_props_using_dates.py is to


___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-23
__docformat___ = 'reStructuredText'

"""
import numpy as np
from icecream import ic

import matplotlib.pyplot as plt
import datetime
from astral.sun import sun
from astral import moon
from astral.moon import moonrise
from astral import LocationInfo


import argparse
import pandas as pd
pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)

from ena_samples import get_all_ena_detailed_sample_info
from get_directory_paths import get_directory_paths

def merge_sea_ena(hit_dir,df_ena_detail):
    """merge_sea_ena
        merge the sea hits from the shape files with ENA
        only selecting those ENA samples that intersect with EEZ
    :param hit_dir:
    :return: df_merge_sea_ena
    """

    df_sea_hits = pd.read_csv(hit_dir + "merged_sea.tsv", sep='\t')
    for mrg in ['MRGID', 'MRGID_TER1', 'MRGID_TER2', 'MRGID_SOV1', 'MRGID_SOV2']:
        df_sea_hits[mrg] = df_sea_hits[mrg].fillna(0).astype(int)
    df_merge_sea_ena = pd.merge(df_ena_detail,df_sea_hits, on=["lat", "lon"], how="inner")

    return df_merge_sea_ena


def get_df_4_collection_date(hit_dir):
    """"""
    test_status = True
    df_ena_detail = get_all_ena_detailed_sample_info(test_status)
    df_ena_detail = df_ena_detail[~df_ena_detail['collection_date'].isna()]
    ic(df_ena_detail.sample(n=10))

    #merge_sea_ena(hit_dir, df_ena_detail):

    ic()
    return(df_ena_detail)

def add_sunset_sunrise(df, date_field):
    """ add_sunset_sunrise

    :param df:
    :param date_field:
    :return:
    """
    ic()
    loc = LocationInfo(name = 'SJC', region = 'CA, USA', timezone = 'America/Los_Angeles',
                       latitude = 37.3713439, longitude = -121.944675)
    def get_light_info(row):
        ic(row)
        if row["lat"]==np.NaN or row["lon"]==np.NaN:
            ic("warning no valid lat or lon")
            return
        #loc = LocationInfo(latitude = 37.3713439, longitude = -121.944675)
        loc = LocationInfo(latitude = row["lat"], longitude = row["lon"])
        y = 2021
        m = 1
        d = 15
        tmz = loc.timezone
        print(loc)
        date_time=datetime.date(y, m, d)
        s = sun(loc.observer, date = date_time, tzinfo = tmz)
        for key in ['dawn', 'dusk', 'noon', 'sunrise', 'sunset']:
            print(f'{key:10s}: {s[key]:%H:%M}')
            row["astral_" + key] = f"{s[key]:%H:%M}"

        val = moonrise(loc.observer, date = date_time, tzinfo = tmz)
        term="moonrise"
        print(f"{term:10s}: {val:%H:%M}")

        phase = moon.phase(date_time)

        moon_phase_name = ""
        if phase < 7:
            moon_phase_name = "new moon"
        elif phase < 14:
            moon_phase_name = "first quarter"
        elif phase < 21:
            moon_phase_name = "full moon"
        elif phase < 28:
            moon_phase_name = "last quarter"
        else:
            ic("error")
        key="moon_phase"
        print(f"{key:10s}: {phase:.2f} name:{moon_phase_name}")
        row["astral_" + key] = "f{val:%H:%M}"
        row["astral_moon_phase_name"] = moon_phase_name

    df = df.sample(2)
    ic(df)
    df.apply(get_light_info, axis = 1)
    #df_ena_detail = df_ena_detail.sample(n = 10)

def main():
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    df = get_df_4_collection_date(hit_dir)
    add_sunset_sunrise(df, "collection_date")


if __name__ == '__main__':
    main()
    ic()


