#!/usr/bin/env python3
"""Script of get_high_seas_info_4_all.py is to get_high_seas_info
to answer a request to get the high seas info for sample accessions

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2025-08-18
__docformat___ = 'reStructuredText'

"""
import sys
import pandas as pd
import logging
from getGeoLocationCategorisation import read_shape, geo_lon_lat2points_geodf, test_locations

logger = logging.getLogger(__name__)
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

hit_dir = "/Users/woollard/projects/bluecloud/data/hits"
sample_data_dir = "/Users/woollard/projects/bluecloud/data/samples"



def merge_dfs(df_sample, df_sea_info):
    """
    Merge sample and sea-info dataframes on latitude/longitude columns.

    This function performs an inner join between df_sample and df_sea_info
    on the columns ['lat', 'lon'] to retain only rows that match in both
    dataframes.

    :param df_sample: pandas.DataFrame containing at least columns ['lat', 'lon'] and sample attributes
    :param df_sea_info: pandas.DataFrame containing at least columns ['lat', 'lon'] and sea/intersection attributes
    :return: pandas.DataFrame resulting from the inner merge
    """
    first2_df = pd.merge(
     left=df_sample,
     right=df_sea_info,
     how='inner', #only want all matches
     left_on=['lat', 'lon'],
     right_on=['lat', 'lon'],
    )
    logger.info(f"FIRST Merge complete: {len(first2_df)}")
    logger.info(first2_df.head())

    return first2_df

def get_sea_info():
    """
    Load the merged sea file created by analyseHits.py.

    Reads a tab-separated file containing sea region annotations for
    coordinates and returns it as a pandas DataFrame.

    :return: pandas.DataFrame of merged sea annotations
    """
    infile = f"{hit_dir}/merged_sea.tsv"
    df = pd.read_csv(infile, sep="\t")
    logger.info(f"Number of samples: {len(df)}")
    logger.debug(df.head(10))

    return df

def get_sample_lat_lon(limit):
    """
    Load sample data (filtered) with latitude/longitude coordinates.

    The function currently reads a parquet file with pre-filtered samples
    and returns it as a pandas DataFrame.
    :limit: max number of rows to return, 0=all
    :return: pandas.DataFrame of samples with lat/lon
    """

    df = fetch_ena_accession_lat_lon(limit)

    # infile = "all_samples_with_lat_lon.tsv"
    # infile = f"{sample_data_dir}/all_sample_lat_longs_present_uniq.tsv"
    # infile = f"{sample_data_dir}/sample_much_filtered_lat_lon.pa"
    #
    # logger.info(f"Reading {infile}")
    # df = pd.read_parquet(infile, engine = 'pyarrow')
    #
    # # df = pd.read_csv(infile, sep="\t", nrows=100)
    # # df = pd.read_csv(infile, sep = "\t")
    logger.info(f"Number of samples: {len(df)}")
    logger.debug(df.sample(5))
    return df


def fetch_ena_accession_lat_lon(limit: int = 0, start_date: str | None = None, end_date: str | None = None) -> pd.DataFrame:
    """
    Query ENA Portal API to retrieve sample accessions with latitude and longitude.

    - Uses the ENA portal /search endpoint
    - Returns only rows where both lat and lon are present (non-null)
    - Casts lat/lon to numeric (float) when possible
    - Columns returned: ['accession', 'lon', 'lat']

    :param limit: max number of rows to return (0 means no limit from ENA side)
    :param start_date: optional ISO date (YYYY-MM-DD) for first_public lower bound
    :param end_date: optional ISO date (YYYY-MM-DD) for first_public upperbound
    :return: pandas.DataFrame with columns ['accession', 'lon', 'lat']
    """

    #https://www.ebi.ac.uk/ena/portal/api/search?result=sample&format=tsv&fields=%20lat,lon,location,country&query=location=%22*%22
    base = "https://www.ebi.ac.uk/ena/portal/api/search"
    # mandatory and useful parameters

    # "dataPortal=ena"
    # "&dccDataOnly=false"
    # "&download=false"
    # "&includeMetagenomes=true"

    params = (
        "&result=sample"
        "&fields=accession%2Clat%2Clon"
        "&format=tsv"
        f"&limit={int(limit) if limit is not None else 0}"
    )
    if start_date and end_date:
        query = f"first_public%3E%3D{start_date}%20AND%20first_public%3C%3D{end_date}"
        url = f"{base}?{params}&query={query}"
    else:
        query = (f"location=%22*%22")
        url = f"{base}?query={query}&{params}"

    logger.info(f"Fetching ENA data (accession, lat, lon) from: {url}")

    df = pd.read_csv(url, sep="\t")

    # Ensure expected columns exist and filter non-null coords
    expected = {'accession', 'lat', 'lon'}
    missing = expected - set(df.columns)
    if missing:
        raise RuntimeError(f"ENA API response missing expected columns: {missing}")

    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    df = df.loc[df['lat'].notna() & df['lon'].notna(), ['accession', 'lon', 'lat']].reset_index(drop=True)
    logger.info(f"Fetched {len(df)} rows with non-null lat/lon")
    return df

# ... existing code ...

def analysis():
    """
    Perform exploratory analysis on target_samples_sea_area.tsv.

    - Loads a subset of target_samples_sea_area.tsv for inspection
    - Logs column summaries and value counts
    - Adds a new column 'hs_or_eez' with values:
        * 'High Seas' if eez_iho_intersect_category starts with 'High Seas'
        * 'EEZ' otherwise (including NaN or non-matching strings)
    - Splits the dataframe for quick sanity checks
    """
    infile = f"{sample_data_dir}/target_samples_sea_area.tsv"
    df = pd.read_csv(infile, sep = "\t", nrows=10000)
    logger.info(f"Number of samples: {len(df)}")
    logger.info(df.sample(5).to_markdown())

    logger.info(f"columns={df.columns}")
    ffs= sorted(df.columns)
    for ff in ffs:
        if "intersect" in ff:
            print(ff)

    HighSeaEEZ_col = 'MarRegion'

    logger.info(f"{HighSeaEEZ_col}: {df[HighSeaEEZ_col].value_counts()}")

    logger.info(f"eez_category {df['eez_category'].value_counts()}")

    # Add 'hs_or_eez' based on eez_iho_intersect_category starting with 'High Seas'
    df['hs_or_eez'] = df[HighSeaEEZ_col].str.startswith("High Seas", na=False).map({True: "High Seas", False: "EEZ"})
    logger.info(f"hs_or_eez counts: {df['hs_or_eez'].value_counts().to_dict()}")
    logger.info(df[[HighSeaEEZ_col, 'hs_or_eez']].head(10).to_markdown())

    df_high_sea = df[df[HighSeaEEZ_col].str.startswith("High Seas", na = False)]
    df_not_high_sea = df[~df[HighSeaEEZ_col].str.startswith("High Seas", na = False)]

    logger.info(f"df_high_sea: total={len(df_high_sea)}  examples {df_high_sea.head()}")
    logger.info(f"df_not_high_sea: total={len(df_not_high_sea)}  examples {df_not_high_sea.head()}")

    df_new = df[['accession','eez_iho_intersect_category']]
    df_new = df_new[df_new['eez_iho_intersect_category']]
    logger.info(f"ddd: {df_new.head(5)}")

def search_coordinates_in_marine(df_sample, shape_file, geo_crc = "EPSG:4326"):
    """
    Searches and identifies coordinates within a marine boundary defined by a shapefile.

    This function processes a set of latitude and longitude coordinates from the
    input dataframe, de-duplicates them, and checks their presence within a marine
    boundary specified by the shapefile. It returns the corresponding geographic
    dataframe of hits showing which coordinates lie within the specified shapefile's
    geographic bounds.

    it only returns the hits, not the entire shapefile

    :param df_sample: Input dataframe containing latitude and longitude coordinates.
    :param shape_file: Path to the shapefile defining the marine boundary.
    :param geo_crc: Coordinate reference system (CRS) to be used for geographic data transformation.
                    The default is "EPSG:4326".
    :return: A geographical dataframe of points that lie within the specified shapefile's bounds.
    """
    df_lat_lons = df_sample[['lat', 'lon']].drop_duplicates()
    logger.info(f"df_lat_lons, start total={len(df_sample)} in de-duplicated total={len(df_lat_lons)}")
    logger.debug(df_lat_lons.head(5))

    my_shape = read_shape(shape_file, geo_crc)
    (points_series, points_geodf) = geo_lon_lat2points_geodf(df_lat_lons, geo_crc)
    df_hits_geodf = test_locations(my_shape, points_geodf)
    df_hits_geodf = (
        df_hits_geodf
        .assign(MRGID_num = pd.to_numeric(df_hits_geodf['MRGID'], errors = 'coerce'))
        .query("MRGID_num > 0")
        .drop(columns = 'MRGID_num')
    )
    logger.info(f"df_hits_geodf hits total={len(df_hits_geodf)}")

    logger.debug(f"df_hits_geodf: {df_hits_geodf.head(5)}")
    my_cols = list(df_hits_geodf.columns)

    return df_hits_geodf


def get_minimal_high_seas_df(limit):
    df_sample = get_sample_lat_lon(limit)

    df_sea_info = search_coordinates_in_marine(df_sample, shape_file = "/Users/woollard/projects/bluecloud/data/shapefiles/Intersect_EEZ_IHO_v5_20241010/Intersect_EEZ_IHO_v5_20241010.shp")
    out_file_name = f"{sample_data_dir}/sample_sea_water_hits.tsv"
    logger.info(f"Writing to {out_file_name} row_total={len(df_sea_info)}")
    df_sea_info.to_csv(out_file_name, sep="\t", index=False)

    # df_sea_info = get_sea_info()
    df_all = merge_dfs(df_sample, df_sea_info)

    # Add 'hs_or_eez' based on MarRegion starting with 'High Seas'
    HighSeaEEZ_col = 'MarRegion'
    df_all['hs_or_eez'] = df_all[HighSeaEEZ_col].str.startswith("High Seas", na = False).map({True: "High Seas", False: "EEZ"})

    df_minimal_high_sea = df_all[['accession', 'lat', 'lon', 'hs_or_eez']]
    logger.debug(f"df_minimal_high_sea: total={len(df_minimal_high_sea)}")
    logger.debug(f"df_minimal_high_sea: {df_minimal_high_sea.head(5)}")

    return df_minimal_high_sea


def main():
    """
    Entrypoint for this script.

    Currently, runs the analysis() function for exploratory inspection.
    When enabled (after removing the early exit), it:
      - Loads sample and sea-info data
      - Merges them on lat/lon
      - Writes a combined TSV to sample_data_dir
    """
    limit = 0
    df_minimal_high_sea = get_minimal_high_seas_df(limit)
    outfile = f"{sample_data_dir}/target_samples_sea_area.tsv"
    logger.info(f"Writing to {outfile} row_total={len(df_minimal_high_sea)}")
    df_minimal_high_sea.to_csv(outfile, sep="\t", index=False)


    # analysis()

if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO, format = '%(levelname)s - %(message)s')
    main()
