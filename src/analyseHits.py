# BlueCloud
"""Script to get analyse the hits from

___author___ = "woollard@ebi.ac.uk"
___start_date___ = "2022-12-08"
__docformat___ = 'reStructuredText'

"""
# /opt/homebrew/bin/pydoc3 getGeoLocationCategorisation   #interactive
# python3 -m pydoc -w getGeoLocationCategorisation.py     #to html file

import os
from icecream import ic
import pandas as pd
from functools import reduce

import matplotlib.pyplot as plt
import geopandas as gpd
from geopandas import GeoDataFrame
from geopandas.geoseries import *
from shapely.geometry import Polygon, Point
import earthpy as et
import argparse
import re
import plotly.express as px
import plotly

import base64
import xhtml2pdf

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

def get_directory_paths(base_dir):
    """ get_directory_paths
             takes a base directory, checks this exists
             also sets the directory paths for analysis and plots etc. and checks that these all exist
        __params__:
               args: base_dir
        __returns__:
            (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir)
    """
    analysis_dir = base_dir + "analysis/"
    plot_dir = base_dir + "analysis/plots/"
    hit_dir = base_dir + "data/hits/"
    sample_dir = base_dir + 'data/samples/'
    shape_dir = base_dir + 'data/shapefiles/'

    dir_list = [base_dir, hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir]
    dir_err = False
    for my_dir in dir_list:
        if not os.path.isdir(my_dir):
            print(f"This directory path does not exist, please create it: {my_dir}")
            dir_err = True
    if dir_err:
        print("Please fix all this configuration")
        quit()

    return(hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir)


def extra_plots(df_merged_all_categories, plot_dir, shape_dir):
    """ extra_plots
            plotting some special graphs, that needs some customisation
            e.g. a specific shapefile as the base for the plot
        __params__:
               args: df_merged_all_categories, plot_dir, shape_dir
    """
    crs_value = "EPSG:4326"
    shapefile = shape_dir + "GIS_hs_snapped/feow_hydrosheds.shp"

    ic(df_merged_all_categories.head(3))

    gpd_shape = gpd.read_file(shapefile)
    base = gpd_shape.boundary.plot(linewidth = 1, edgecolor = "black")

    df = df_merged_all_categories
    df['coords'] = list(zip(df['lon'], df['lat']))
    df['coords'] = df['coords'].apply(Point)
    points_geodf: GeoDataFrame = gpd.GeoDataFrame(df, geometry = 'coords', crs = crs_value)

    pointsInHydroshed_geodf = points_geodf[~points_geodf['feow_category'].isnull()]
    notPointsInHydroshed_geodf = points_geodf[points_geodf['feow_category'].isnull()]
    # quit()
    ic(pointsInHydroshed_geodf.head(2))
    pointsInHydroshed_geodf.plot(ax = base, linewidth = 1, color = "red", markersize = 1, aspect=1)
    out_graph_file = plot_dir + "pointsInJustHydroshed.pdf"
    plt.title("All ENA sample coords in(red) the FEOW hydroshed polygons", )
    ic(out_graph_file)
    fig1 = plt.gcf()
    fig1.savefig(out_graph_file)

    pointsInHydroshed_geodf.plot(ax = base, linewidth = 1, color = "red", markersize = 1, aspect = 1)
    notPointsInHydroshed_geodf.plot(ax = base, linewidth = 1, color = "blue", markersize = 1, aspect = 1)
    plt.title("All ENA sample coords(blue) in(red) the FEOW hydroshed polygons",)
    fig1 = plt.gcf()

    out_graph_file = plot_dir + "pointsInHydroshed.pdf"
    ic(out_graph_file)
    fig1.savefig(out_graph_file)

    return

def plot_merge_all(df_merged_all, plot_dir):
    """ plot_merge_all
              takes the largest merge all of all columns of the merged hit results and does plots that need all this,
              not just the category subset of columns
        __params__:
               args df_merged_all, plot_dir)
    """

    out_graph_file = plot_dir + 'IHO_ocean_by_lon.pdf'
    ic(out_graph_file)
    fig = px.scatter(df_merged_all, title ="IHO, lats and longhurst", x = "IHO_category", y = "lat", width = 1500, color = "longhurst_category")
    # fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    out_graph_file = plot_dir + 'EEZ_continent_counts.pdf'
    fig = px.histogram(df_merged_all, title ="EEZ by country + continent (logscale)", x = "GEONAME",
                       width = 1500, color ="continent", log_y=True, labels={'count': "log(count)", 'GEONAME':"EEZ GEONAME"})
    fig.update_xaxes(categoryorder="total descending")
    fig.update_xaxes(tickangle = 60, tickfont = dict(size=6))
    # fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    out_graph_file = plot_dir + 'IHO_longhurst_counts.pdf'
    fig = px.histogram(df_merged_all, title ="IHO country + Longhurst biome (logscale)", x = "IHO_category", width = 1500, color ="longhurst_category", log_y=True)
    fig.update_xaxes(categoryorder="total descending")
    fig.update_xaxes(tickangle = 60, tickfont = dict(size=8))
    # fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    out_graph_file = plot_dir + 'country_lon_lat_counts.pdf'
    fig = px.histogram(df_merged_all, title ="EEZ country + continent (logscale)", x = "SOVEREIGN1", width = 1500, color = "continent", log_y=True)
    fig.update_xaxes(categoryorder="total descending")
    fig.update_xaxes(tickangle = 60)
    fig.update_xaxes(tickangle = 60, tickfont = dict(size=8))
    # fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    fig = px.scatter(df_merged_all, x = "lon", y = "lat", width = 1500, color = "AREA_SKM")
    # fig.show()
    out_graph_file = plot_dir + 'feow_category_by_skm.pdf'
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')


    return


def cleanDF(hitfile, filterField, catName, filterSwapValue):
    """  cleanDF
        __params__:
            hitfile
            filterField
            catName
            filterSwapValue
        __returns__:
            df

    """

    ic(hitfile)
    crs_value = "EPSG:4326"

    # nrow=100
    # df = pd.read_csv(hitfile, sep = '\t', nrows = nrow)
    df = pd.read_csv(hitfile, sep = '\t', low_memory = False)
    # ic(df.head(8))
    # df = gpd.GeoDataFrame(df, geometry = 'coords', crs = crs_value)
    ic(df.columns)
    # ic(df.head(15))
    ''' they all have the index, first col, drop it'''
    df = df.iloc[:, 1:]
    df = df[~df[filterField].isnull()]
    # the first one captures feow_category
    if filterField == "index_right":
        if 'x' in df.columns:
            df = df.drop(['x', 'y'], axis = 1)
        df[filterField] = filterSwapValue
        df = df.rename({'index_right': catName}, axis = 1)
    elif filterField == "MARREGION":
        if 'X_1' in df.columns:
            df = df.drop(['X_1', 'Y_1'], axis = 1)
        df = df.rename({'index_right': catName}, axis = 1)
        df[catName] = df[filterField]
        all_cols = ['fid', 'MRGID', 'MARREGION', 'MRGID_IHO', 'IHO_SEA', 'MRGID_EEZ', 'EEZ', 'MRGID_TER1', 'TERRITORY1', 'ISO_TER1', 'UN_TER1', 'MRGID_SOV1', 'SOVEREIGN1', 'ISO_SOV1', 'UN_SOV1', 'MRGID_TER2', 'TERRITORY2', 'ISO_TER2', 'UN_TER2', 'MRGID_SOV2', 'SOVEREIGN2', 'ISO_SOV2', 'UN_SOV2', 'MRGID_TER3', 'TERRITORY3', 'ISO_TER3', 'UN_TER3', 'MRGID_SOV3', 'SOVEREIGN3', 'ISO_SOV3', 'UN_SOV3', 'AREA_KM2']
        for col in all_cols:
            oldName = col
            newName = 'intersect_' + oldName
            df = df.rename({oldName: newName}, axis = 1)

    elif filterField == "region": # ie.. for the World admin
        df['french_shor'] = df['french_shor'].str.replace('Ã', 'e')
        df['french_shor'] = df['french_shor'].str.replace('©', '')
        df['french_shor'] = df['french_shor'].str.replace('e', 'E')
        df['french_shor'] = df['french_shor'].str.replace('¯', '')
        # df['french_shor'] = df['french_shor'].str.replace('\x8', '')
        df['french_shor'] = df['french_shor'].str.replace('¨', '')
        df['index_right'] = filterSwapValue
        df = df.rename({'name': catName}, axis = 1)
        # print(df['french_shor'].unique())
    # next is IHO
    elif filterField == "MRGID":
        df = df.drop(['min_X', 'max_X', 'min_Y', 'max_Y', 'Longitude', 'Latitude'], axis = 1)
        df['index_right'] = df['NAME']
        df = df.rename({'index_right': catName, 'MRGID': "MRGID_IHO"}, axis = 1)
    elif catName == "longhurst_category":
        df = df.rename({'index_right': catName}, axis = 1)
        df[catName] = df['ProvDescr'].str.extract('^([A-Za-z]*)', expand = True)
    elif catName == "eez_category":
        # leave in these as, Stephane finds valuable
        df = df.drop(['X_1', 'Y_1'], axis = 1)
        # df = df.drop(['X_1', 'Y_1', 'MRGID_TER2', 'MRGID_SOV2', 'TERRITORY2', 'ISO_TER2', 'SOVEREIGN2', 'MRGID_TER3',
        #               'MRGID_SOV3', 'TERRITORY3', 'ISO_TER3', 'SOVEREIGN3', 'ISO_SOV2', 'ISO_SOV3', 'UN_SOV1',
        #               'UN_SOV2', 'UN_SOV3', 'UN_TER1', 'UN_TER2', 'UN_TER3'], axis = 1)
        df['index_right'] = filterSwapValue
        df = df.rename({'index_right': catName}, axis = 1)
    ic(df.columns)
    # ic(df.head(15))
    return df


def mergeDFs(data_frames, out_filename):
    ''' mergeDFs
        __params__:
            list of data_frames merging on ['coords', 'lon', 'lat']
            out_filename if it has length >1
        __returns__:
            df_merged
    '''
    df_merged = reduce(lambda left, right: pd.merge(left, right, on = ['coords', 'lon', 'lat'],
                                                    how = 'outer'), data_frames)
    # df_merged = df_merged.loc[~df_merged.index.duplicated(), :].copy()
    # df_merged.reset_index(inplace=True)
    ic(df_merged.head(2))
    ic(df_merged.shape[0])
    ic(df_merged.columns)

    if len(out_filename) > 1:
        df_merged.to_csv(out_filename, sep = "\t")
    ic(out_filename)
    return df_merged

def createTotal(df_merged_all_categories, categories, total):
    """  createTotal
            Sums up the occurrences of evidence from different sources(essentially the categories)
            i.e. count the none null values.
            The solution in the end was simple, but took me 2 hours to work out!
        __params__:
            df_merged_all_categories, categories, total
        __returns__:
            df_merged_all_categories

    """
    # was getting warnings about working on a copy of slice, this turns this off
    pd.options.mode.chained_assignment = None  # default='warn'
    ic(total)

    df_just_cats = df_merged_all_categories[categories]
    number_of_cats = len(categories)
    df_merged_all_categories[total] = number_of_cats - df_just_cats.isnull().sum(axis =1)

    return df_merged_all_categories

def get_all_ena_lat_lon(samples_dir):
    '''  get_all_ena_lat_lon inc. country and accession(sample_id)
          This file was created by
          curl -X GET "https://www.ebi.ac.uk/ena/portal/api/search?dataPortal=ena&dccDataOnly=false&download=false&fields=accession%2C%20lon%2C%20lat%2C%20country&includeMetagenomes=true&result=sample&sortDirection=asc" -H "accept: */*" > sample_lat_lon_country.tsv
            awk '$2 ~ /^[0-9*]|^lon$/{print;}' sample_lat_lon_country.tsv > sample_lat_lon_country_clean.tsv
          :param
            samples_dir_
          :return
             dataframe
    '''

    crs_value = "EPSG:4326"
    pd.set_option('display.max_columns', None)
    ena_file = samples_dir + "sample_lat_lon_country_clean.tsv"
    df = pd.read_csv(ena_file, sep = '\t')

    df['coords'] = list(zip(df['lon'], df['lat']))
    df['coords'] = df['coords'].apply(Point)
    points_geodf = gpd.GeoDataFrame(df, geometry = 'coords', crs = crs_value)
    points_geodf = points_geodf.drop(['accession'], axis=1)
    points_geodf = points_geodf.drop_duplicates()

    # ic("look for dups")
    # boolean = points_geodf.duplicated(subset = ['coords']).any()
    # print(boolean, end = '\n\n')  # True
    #
    # ic("look for dups")
    # (tmp_df) = points_geodf.duplicated(subset = None, keep = 'first')
    # doing the following rather than rename as it changes the order too.
    #
    points_geodf[['ena_country', 'ena_region']] = points_geodf['country'].str.split(":", expand=True)
    points_geodf = points_geodf.drop(['country'], axis=1)
    points_geodf['ena_category'] = 'ena'
    # ic(points_geodf.head(15))
    # nightmare with unhashable Points
    df1 = pd.DataFrame(points_geodf)
    ena_tmp_file = samples_dir + "sample_lat_lon_country_clean_tmp.tsv"
    points_geodf.to_csv(ena_tmp_file, sep = '\t')
    df1 = pd.read_csv(ena_tmp_file, sep = '\t')
    # ic(df1.head(10))
    # quit()

    return(df1)

def categoryPlotting(df_merged_all_categories, plot_dir):
    """  categoryPlotting

        __params__:
            df_merged_all_categories, plot_dir
        __returns__:

    """
    marker_size = 4

    ic(df_merged_all_categories.head(3))
    width = 1500

    scope = 'europe'
    title_string = 'ENA samples in eez_iho_intersect_category in ' + scope
    fig = px.scatter_geo(df_merged_all_categories, "lat", "lon",
                     width = 1500, color = "eez_iho_intersect_category",
                     title = title_string,
                     scope = scope)
    fig.update_traces(marker = dict(size = marker_size))
    out_graph_file = plot_dir + 'merge_all_intersect_eez_iho_cats' + scope + '.pdf'
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')
    # fig.show()

    scope = 'north america'
    title_string = 'ENA samples in eez_iho_intersect_category in ' + scope
    fig = px.scatter_geo(df_merged_all_categories, "lat", "lon",
                     width = 1500, color = "eez_iho_intersect_category",
                     title = title_string,
                     scope = scope)
    fig.update_traces(marker = dict(size = marker_size))
    out_graph_file = plot_dir + 'merge_all_intersect_eez_iho_cats' + scope + '.pdf'
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')
    # fig.show()

    scope = 'africa'
    title_string = 'ENA samples in eez_iho_intersect_category in ' + scope
    fig = px.scatter_geo(df_merged_all_categories, "lat", "lon",
                     width = 1500, color = "eez_iho_intersect_category",
                     title = title_string,
                     scope = scope)
    fig.update_traces(marker = dict(size = marker_size))
    out_graph_file = plot_dir + 'merge_all_intersect_eez_iho_cats' + scope + '.pdf'
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')
    # fig.show()

    scope = 'world'
    title_string = 'ENA samples in eez_iho_intersect_category in ' + scope
    fig = px.scatter_geo(df_merged_all_categories, "lat", "lon",
                     width = 1500, color = "eez_iho_intersect_category",
                     title = title_string,
                     scope = scope)
    fig.update_traces(marker = dict(size = marker_size))
    out_graph_file = plot_dir + 'merge_all_intersect_eez_iho_cats' + scope + '.pdf'
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')
    # fig.show()

    title_string = 'ENA samples in IHO Categories'
    fig = px.scatter(df_merged_all_categories, x = "lon", y = "lat",width = 1500, color = "IHO_category", title = title_string)
    # fig.show()
    out_graph_file = plot_dir + 'merge_all_IHO_cats.pdf'
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    title_string = 'ENA samples in ENA Country Categories'
    fig = px.scatter(df_merged_all_categories, x = "lon", y = "lat",width = 1500, color = "ena_country", title = title_string)
    # fig.show()
    out_graph_file = plot_dir + 'merge_all_ENA_country_cats.pdf'
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    title_string = 'ENA samples in World Admin Categories'
    fig = px.scatter(df_merged_all_categories, x = "lon", y = "lat",width = 1500, color = "worldAdmin_category", title = title_string)
    # fig.show()
    out_graph_file = plot_dir + 'merge_all_worldAdmin_category.pdf'
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    title_string = 'ENA samples in Location Designation based on multiple shapefiles'
    fig = px.scatter(df_merged_all_categories, x = "lon", y = "lat",width = 1500, color = "location_designation", title = title_string)
    # fig.show()
    out_graph_file = plot_dir + 'merge_all_location_designation.pdf'
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    title_string = 'ENA samples in EEZ categories'
    fig = px.scatter(df_merged_all_categories, x = "lon", y = "lat", width = 1500, color = "eez_category", title = title_string)
    # fig.show()
    out_graph_file = plot_dir + 'merge_all_eez_category.pdf'
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    titl_string ="ENA Samples in Hydrosheds"
    fig = px.scatter(df_merged_all_categories, x = "lon", y = "lat", width = 1500, color = "feow_category", title = title_string)
    # fig.show()
    out_graph_file = plot_dir + 'feow_category.pdf'
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    return

def analysis(df_merged_all,analysis_dir, plot_dir):
    """  analysis

        __params__:
            df_merged_all, analysis_dir, plot_dir
        __returns__:

    """
    all_columns = df_merged_all.columns
    ic(all_columns)

    categories = []
    for match in all_columns:
        if "category" in match:
            categories.append(match)

    columns2keep = ['lat', 'lon', 'coords', 'ena_country', 'ena_region'] + categories
    ic(columns2keep)
    df_merged_all_categories = df_merged_all[columns2keep]
    ic(df_merged_all_categories.head(2))
    sea_categories = ['eez_category', 'longhurst_category', 'IHO_category', 'sea_category']
    land_categories = ['land_category', 'worldAdmin_category', 'feow_category']

    df_merged_all_categories = createTotal(df_merged_all_categories, sea_categories, 'sea_total')
    df_merged_all_categories = createTotal(df_merged_all_categories, land_categories, 'land_total')

    df_merged_all_categories.loc[(df_merged_all_categories['sea_total'] > 0) & (df_merged_all_categories['land_total'] > 0),
        'location_designation'] = 'sea and land'
    df_merged_all_categories.loc[(df_merged_all_categories['sea_total'] > 0) & (df_merged_all_categories['land_total'] == 0),
        'location_designation'] = 'sea'
    df_merged_all_categories.loc[(df_merged_all_categories['sea_total'] == 0) & (df_merged_all_categories['land_total'] > 0),
        'location_designation'] = 'land'
    df_merged_all_categories.loc[(df_merged_all_categories['sea_total'] == 0) & (df_merged_all_categories['land_total'] == 0),
        'location_designation'] = 'neither land nor sea'

    ic(df_merged_all_categories.head(15))
    out_file = analysis_dir + 'merged_all_categories.tsv'
    ic(out_file)
    df_merged_all_categories.to_csv(out_file, sep = '\t')


    ic("========================================================")
    return out_file


def mergeAndAnalysis(df_ena, df_eez, df_longhurst, df_seaIHO, df_seawater, df_land, df_worldAdmin, df_hydrosheds, df_intersect_eez_iho, hit_dir):
    """  mergeAndAnalysis
            is used to merge a bunch of data frames.

        __params__:
        df_ena, df_eez, df_longhurst, df_seaIHO, df_seawater, df_land, df_worldAdmin, df_hydrosheds,
        df_intersect_eez_iho , hit_Dir

        __returns__:

    """
    sea_data_frames = [df_eez, df_longhurst, df_seaIHO, df_seawater, df_intersect_eez_iho]
    out_filename = hit_dir + 'merged_sea.tsv'
    df_merged_sea = mergeDFs(sea_data_frames, out_filename)

    land_data_frames = [df_land, df_worldAdmin, df_hydrosheds]
    out_filename = hit_dir + 'merged_land.tsv'
    df_merged_land = mergeDFs(land_data_frames, out_filename)

    data_frames = [df_merged_sea, df_merged_land, df_ena]
    out_filename = hit_dir + 'merged_all.tsv'
    df_merged_all = mergeDFs(data_frames, out_filename)
    ic(df_merged_all.head(3))
    ic(df_ena.head(3))

    df_merged_all = mergeDFs(data_frames, out_filename)

    return df_merged_all

def processHitFiles(hit_dir):
    """  processHitFiles
         drop rows where no hits
         some tidying up: e.g. columns that usually empty, regex of strange chars.
         generating a column_category to give a gross overview
        __params__:

        __returns__:
         (df_eez, df_longhurst, df_seaIHO, df_seawater, df_land, df_worldAdmin, df_hydrosheds, df_intersect_eez_iho)

    """
    ic(hit_dir)
    hitfile = hit_dir + 'intersect_eez_iho_hits.tsv'
    df_intersect_eez_iho = cleanDF(hitfile, 'MARREGION', 'eez_iho_intersect_category', 'eez_iho_intersect')
    ic(df_intersect_eez_iho.head(2))

    hitfile = hit_dir + 'seawater_polygons_hits.tsv'
    df_seawater = cleanDF(hitfile, 'index_right', 'sea_category', 'seawater')

    hitfile = hit_dir + 'land_polygons_hits.tsv'
    df_land = cleanDF(hitfile, 'index_right', 'land_category', 'land')

    hitfile = hit_dir + 'world-administrative-boundaries_hits.tsv'
    df_worldAdmin = cleanDF(hitfile, 'region', 'worldAdmin_category', 'land')

    hitfile = hit_dir + 'World_Seas_IHO_v3_hits.tsv'
    df_seaIHO = cleanDF(hitfile, 'MRGID', 'IHO_category', 'sea')

    hitfile = hit_dir + 'feow_hydrosheds_hits.tsv'
    df_hydrosheds = cleanDF(hitfile, 'index_right', 'feow_category', 'hydroshed')

    hitfile = hit_dir + 'longhurst_v4_hits.tsv'
    df_longhurst = cleanDF(hitfile, 'ProvCode', 'longhurst_category', 'blank')

    hitfile = hit_dir + 'eez_hits.tsv'
    df_eez = cleanDF(hitfile, 'GEONAME', 'eez_category', 'EEZ')

    ic(df_eez.head())
    ic(df_eez.shape[0])

    return(df_eez, df_longhurst, df_seaIHO, df_seawater, df_land, df_worldAdmin, df_hydrosheds, df_intersect_eez_iho)


def main():
    """ main takes the "hit" files from the getGeoLocationCategorisation.py files, integrates and plots them
        __params__:
               args
    """
    base_dir = "/Users/woollard/projects/bluecloud/"
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir) = get_directory_paths(base_dir)

    df_ena = get_all_ena_lat_lon(sample_dir)

    (df_eez, df_longhurst, df_seaIHO, df_seawater, df_land, df_worldAdmin, df_hydrosheds, df_intersect_eez_iho)\
        = processHitFiles(hit_dir)
    df_merged_all = mergeAndAnalysis(df_ena, df_eez, df_longhurst, df_seaIHO, df_seawater, df_land, df_worldAdmin,\
                                     df_hydrosheds, df_intersect_eez_iho, hit_dir)
    merged_all_categories_file = analysis(df_merged_all, analysis_dir, plot_dir)

    ic("Do the plotting")
    ''' these are the plotting sections , can comment out all above and just run these.
        Done so that can save the time etc. of re-running the merging
     '''

    merged_all_categories_file = analysis_dir + "merged_all_categories.tsv"
    df_merged_all_categories = pd.read_csv(merged_all_categories_file, sep = "\t")
    categoryPlotting(df_merged_all_categories, plot_dir)

    infile = hit_dir + "merged_all.tsv"
    df_merged_all = pd.read_csv(infile, sep = "\t")
    extra_plots(df_merged_all, plot_dir, shape_dir)
    plot_merge_all(df_merged_all, plot_dir)

    return ()


if __name__ == '__main__':
    ic()

    main()
