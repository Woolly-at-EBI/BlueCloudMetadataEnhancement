# BlueCloud
"""Script to merger, analyse and plot the hits from etGeoLocationCategorisation.py
    directories for the hits, samples, analysis, plot etc. are set in "def get_directory_paths"
    The hits and plot files are additionally manually copied to a google drive shared with Stephane and Josie.
___author___ = "woollard@ebi.ac.uk"
___start_date___ = "2022-12-08"
__docformat___ = 'reStructuredText'

"""
# /opt/homebrew/bin/pydoc3 getGeoLocationCategorisation   #interactive
# python3 -m pydoc -w getGeoLocationCategorisation.py     #to html file

from icecream import ic
from functools import reduce

import matplotlib.pyplot as plt
import geopandas as gpd
from geopandas import GeoDataFrame
from geopandas.geoseries import *
from shapely.geometry import Point

import plotly.express as px
import plotly
from get_directory_paths import get_directory_paths

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
import decimal
import math


def extra_plots(df_merged_all_categories, plot_dir, shape_dir):
    """ extra_plots
            plotting some special graphs, that needs some customisation
            e.g. a specific shapefile as the base for the plot
        __params__:
               passed_args: df_merged_all_categories, plot_dir, shape_dir
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
    pointsInHydroshed_geodf.plot(ax = base, linewidth = 1, color = "red", markersize = 1, aspect = 1)
    out_graph_file = plot_dir + "pointsInJustHydroshed.pdf"
    plt.title("All ENA sample coords in(red) the FEOW hydroshed polygons", )
    ic(out_graph_file)
    fig1 = plt.gcf()
    fig1.savefig(out_graph_file)

    pointsInHydroshed_geodf.plot(ax = base, linewidth = 1, color = "red", markersize = 1, aspect = 1)
    notPointsInHydroshed_geodf.plot(ax = base, linewidth = 1, color = "blue", markersize = 1, aspect = 1)
    plt.title("All ENA sample coords(blue) in(red) the FEOW hydroshed polygons", )
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
               passed_args df_merged_all, plot_dir)
    """
    width = 300
    out_graph_file = plot_dir + 'IHO_ocean_by_lon.pdf'
    ic(out_graph_file)
    fig = px.scatter(df_merged_all, title = "IHO, lats and longhurst", x = "IHO_category", y = "lat", width = width,
                     color = "longhurst_category")
    # fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    out_graph_file = plot_dir + 'EEZ_continent_counts.pdf'
    fig = px.histogram(df_merged_all, title = "EEZ by country + continent (logscale)", x = "GEONAME",
                       width = width, color = "continent", log_y = True, labels = {'count': "log(count)",
                                                                                   'GEONAME': "EEZ GEONAME"})
    fig.update_xaxes(categoryorder = "total descending")
    fig.update_xaxes(tickangle = 60, tickfont = dict(size = 6))
    # fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    out_graph_file = plot_dir + 'IHO_longhurst_counts.pdf'
    fig = px.histogram(df_merged_all, title = "IHO country + Longhurst biome (logscale)", x = "IHO_category",
                       width = width, color = "longhurst_category", log_y = True)
    fig.update_xaxes(categoryorder = "total descending")
    fig.update_xaxes(tickangle = 60, tickfont = dict(size = 8))
    # fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    out_graph_file = plot_dir + 'country_lon_lat_counts.pdf'
    fig = px.histogram(df_merged_all, title = "EEZ country + continent (logscale)", x = "SOVEREIGN1",
                       width = width, color = "continent", log_y = True)
    fig.update_xaxes(categoryorder = "total descending")
    fig.update_xaxes(tickangle = 60)
    fig.update_xaxes(tickangle = 60, tickfont = dict(size = 8))
    # fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    fig = px.scatter(df_merged_all, x = "lon", y = "lat", width = width, color = "AREA_SKM")
    # fig.show()
    out_graph_file = plot_dir + 'feow_category_by_skm.pdf'
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    return


def clean_df(hit_file, filter_field, cat_name, filter_swap_value):
    """  clean_df
        __params__:
            hit_file
            filter_field
            cat_name
            filter_swap_value
        __returns__:
            df

    """

    ic(hit_file)

    # nrow=100
    # df = pd.read_csv(hit_file, sep = '\t', nrows = nrow)
    df = pd.read_csv(hit_file, sep = '\t', low_memory = False)
    # ic(df.head(8))
    # df = gpd.GeoDataFrame(df, geometry = 'coords', crs = crs_value)
    ic(df.columns)
    # ic(df.head(15))
    ''' they all have the index, first col, drop it'''
    df = df.iloc[:, 1:]
    df = df[~df[filter_field].isnull()]
    # the first one captures feow_category
    if filter_field == "index_right":
        if 'x' in df.columns:
            df = df.drop(['x', 'y'], axis = 1)
        df[filter_field] = filter_swap_value
        df = df.rename({'index_right': cat_name}, axis = 1)
    elif filter_field == "MARREGION":
        if 'X_1' in df.columns:
            df = df.drop(['X_1', 'Y_1'], axis = 1)
        df = df.rename({'index_right': cat_name}, axis = 1)
        df[cat_name] = df[filter_field]
        all_cols = ['fid', 'MRGID', 'MARREGION', 'MRGID_IHO', 'IHO_SEA', 'MRGID_EEZ', 'EEZ', 'MRGID_TER1',
                    'TERRITORY1', 'ISO_TER1', 'UN_TER1', 'MRGID_SOV1', 'SOVEREIGN1', 'ISO_SOV1', 'UN_SOV1',
                    'MRGID_TER2', 'TERRITORY2', 'ISO_TER2', 'UN_TER2', 'MRGID_SOV2', 'SOVEREIGN2', 'ISO_SOV2',
                    'UN_SOV2', 'MRGID_TER3', 'TERRITORY3', 'ISO_TER3', 'UN_TER3', 'MRGID_SOV3', 'SOVEREIGN3',
                    'ISO_SOV3', 'UN_SOV3', 'AREA_KM2']
        for col in all_cols:
            oldName = col
            newName = 'intersect_' + oldName
            df = df.rename({oldName: newName}, axis = 1)

    elif filter_field == "region":  # ie.. for the World admin
        df['french_shor'] = df['french_shor'].str.replace('Ã', 'e')
        df['french_shor'] = df['french_shor'].str.replace('©', '')
        df['french_shor'] = df['french_shor'].str.replace('e', 'E')
        df['french_shor'] = df['french_shor'].str.replace('¯', '')
        # df['french_shor'] = df['french_shor'].str.replace('\x8', '')
        df['french_shor'] = df['french_shor'].str.replace('¨', '')
        df['index_right'] = filter_swap_value
        df = df.rename({'name': cat_name}, axis = 1)
        # print(df['french_shor'].unique())
    # next is IHO
    elif filter_field == "MRGID":
        df = df.drop(['min_X', 'max_X', 'min_Y', 'max_Y', 'Longitude', 'Latitude'], axis = 1)
        df['index_right'] = df['NAME']
        df = df.rename({'index_right': cat_name, 'MRGID': "MRGID_IHO"}, axis = 1)
    elif cat_name == "longhurst_category":
        df = df.rename({'index_right': cat_name}, axis = 1)
        df[cat_name] = df['ProvDescr'].str.extract('^([A-Za-z]*)', expand = True)
    elif cat_name == "eez_category":
        # leave in these as, Stephane finds valuable
        df = df.drop(['X_1', 'Y_1'], axis = 1)
        # df = df.drop(['X_1', 'Y_1', 'MRGID_TER2', 'MRGID_SOV2', 'TERRITORY2', 'ISO_TER2', 'SOVEREIGN2', 'MRGID_TER3',
        #               'MRGID_SOV3', 'TERRITORY3', 'ISO_TER3', 'SOVEREIGN3', 'ISO_SOV2', 'ISO_SOV3', 'UN_SOV1',
        #               'UN_SOV2', 'UN_SOV3', 'UN_TER1', 'UN_TER2', 'UN_TER3'], axis = 1)
        df['index_right'] = filter_swap_value
        df = df.rename({'index_right': cat_name}, axis = 1)
    ic(df.columns)
    # ic(df.head(15))
    return df


def mergeDFs(data_frames, out_filename):
    """ mergeDFs
        __params__:
            list of data_frames merging on ['coords', 'lon', 'lat']
            out_filename if it has length >1
        __returns__:
            df_merged
    """
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
    df_merged_all_categories[total] = number_of_cats - df_just_cats.isnull().sum(axis = 1)

    return df_merged_all_categories


def get_all_ena_lat_lon(samples_dir):
    """  get_all_ena_lat_lon inc. country and accession(sample_id)
          This file was created by
          curl -X GET "https://www.ebi.ac.uk/ena/portal/api/search?dataPortal=ena&dccDataOnly=false&download=false&
          fields=accession%2C%20lon%2C%20lat%2C%20country&includeMetagenomes=true&result=sample&sortDirection=asc"
          -H "accept: */*" > sample_lat_lon_country.tsv
            awk '$2 ~ /^[0-9*]|^lon$/{print;}' sample_lat_lon_country.tsv > sample_lat_lon_country_clean.tsv
          :param
            samples_dir_
          :return
             dataframe
    """

    crs_value = "EPSG:4326"
    pd.set_option('display.max_columns', None)
    ena_file = samples_dir + "sample_lat_lon_country_clean.tsv"
    df = pd.read_csv(ena_file, sep = '\t')

    df['coords'] = list(zip(df['lon'], df['lat']))
    df['coords'] = df['coords'].apply(Point)
    points_geodf = gpd.GeoDataFrame(df, geometry = 'coords', crs = crs_value)
    points_geodf = points_geodf.drop(['accession'], axis = 1)
    points_geodf = points_geodf.drop_duplicates()

    # ic("look for dups")
    # boolean = points_geodf.duplicated(subset = ['coords']).any()
    # print(boolean, end = '\n\n')  # True
    #
    # ic("look for dups")
    # (tmp_df) = points_geodf.duplicated(subset = None, keep = 'first')
    # doing the following rather than rename as it changes the order too.
    #
    points_geodf[['ena_country', 'ena_region']] = points_geodf['country'].str.split(":", expand = True)
    points_geodf = points_geodf.drop(['country'], axis = 1)
    points_geodf['ena_category'] = 'ena'
    # ic(points_geodf.head(15))
    # nightmare with unhashable Points
    # df1 = pd.DataFrame(points_geodf)
    ena_tmp_file = samples_dir + "sample_lat_lon_country_clean_tmp.tsv"
    points_geodf.to_csv(ena_tmp_file, sep = '\t')
    df1 = pd.read_csv(ena_tmp_file, sep = '\t')
    # ic(df1.head(10))
    # quit()

    return df1


def categoryPlotting(df_merged_all_categories, plot_dir):
    """  categoryPlotting
                plotting using the category column subset
                is using the scope aspect of plotly, this uses the inbuilt maps rather than the shapefile maps
        __params__:
            df_merged_all_categories, plot_dir
        __returns__:

    """
    marker_size = 4

    ic(df_merged_all_categories.head(3))
    width = 1500

    def create_cat_figure(title_string, color_value, scope, out_graph_file, width, marker_size):
        fig = px.scatter_geo(df_merged_all_categories, "lat", "lon",
                             width = width, color = color_value,
                             title = title_string,
                             scope = scope)
        fig.update_traces(marker = dict(size = marker_size))

        ic(out_graph_file)
        plotly.io.write_image(fig, out_graph_file, format = 'pdf')
        # fig.show()
        return

    def eez_iho_intersect_category_scope_plots(plot_dir, width, marker_size, scope):
        title_string = 'ENA samples in eez_iho_intersect_category in ' + scope
        out_graph_file = plot_dir + 'merge_all_intersect_eez_iho_cats' + scope + '.pdf'
        color_value = "eez_iho_intersect_category"
        create_cat_figure(title_string, color_value, scope, out_graph_file, width, marker_size)

    eez_iho_intersect_category_scope_plots(plot_dir, width, marker_size, 'europe')
    eez_iho_intersect_category_scope_plots(plot_dir, width, marker_size, 'north america')
    eez_iho_intersect_category_scope_plots(plot_dir, width, marker_size, 'africa')
    eez_iho_intersect_category_scope_plots(plot_dir, width, marker_size, 'world')

    scope = 'world'

    title_string = 'ENA samples in IHO Categories'
    color_value = "IHO_category"
    out_graph_file = plot_dir + 'merge_all_IHO_cats.pdf'
    create_cat_figure(title_string, color_value, scope, out_graph_file, width, marker_size)

    title_string = 'ENA samples in ENA Country Categories'
    color_value = "ena_country"
    out_graph_file = plot_dir + 'merge_all_ENA_country_cats.pdf'
    create_cat_figure(title_string, color_value, scope, out_graph_file, width, marker_size)

    title_string = 'ENA samples in World Admin Categories'
    color_value = "worldAdmin_category"
    out_graph_file = plot_dir + 'merge_all_worldAdmin_category.pdf'
    create_cat_figure(title_string, color_value, scope, out_graph_file, width, marker_size)

    title_string = 'ENA samples in Location Designation based on multiple shapefiles'
    color_value = "location_designation"
    out_graph_file = plot_dir + 'merge_all_location_designation.pdf'
    create_cat_figure(title_string, color_value, scope, out_graph_file, width, marker_size)

    title_string = 'ENA samples in EEZ categories'
    color_value = "eez_category"
    out_graph_file = plot_dir + 'merge_all_eez_category.pdf'
    create_cat_figure(title_string, color_value, scope, out_graph_file, width, marker_size)

    title_string = "ENA Samples in Hydrosheds"
    color_value = "feow_category"
    out_graph_file = plot_dir + 'feow_category.pdf'
    create_cat_figure(title_string, color_value, scope, out_graph_file, width, marker_size)

    return

def get_category_stats(ena_total_sample_count, df_merged_all_categories, df_merged_all):
    """  get_category_stats

        __params__:
            ena_total_sample_count, df_merged_all_categories, df_merged_all
        __returns__:

    """
    ic()
    ic(df_merged_all_categories.head())

    ena_uniq_lat_lon_total = df_merged_all_categories.shape[0]
    ic(ena_uniq_lat_lon_total)
    ic(df_merged_all_categories["eez_category"].value_counts())
    ic(df_merged_all_categories["location_designation"].value_counts())
    stats_dict = {}
    stats_dict["terrestrial"] = df_merged_all_categories["location_designation_terrestrial"].count()
    stats_dict["marine_total"] = df_merged_all_categories["location_designation_marine"].count()
    stats_dict["other_total"] = df_merged_all_categories["location_designation_other"].count()
    stats_dict["total_uniq_GPS_coords"] = ena_uniq_lat_lon_total
    ic(stats_dict)

    print(f"ena_total_sample_count = {ena_total_sample_count}")
    field_name: str
    for field_name in stats_dict:
        print(f"{field_name}={stats_dict[field_name]} = {(100 * stats_dict[field_name]/ena_uniq_lat_lon_total):.2f}%")

    return

def analysis(df_merged_all, analysis_dir, plot_dir):
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

    df_merged_all_categories.loc[
        (df_merged_all_categories['sea_total'] > 0),
        'location_designation_marine'] = True
    df_merged_all_categories.loc[
        (df_merged_all_categories['land_total'] > 0),
        'location_designation_terrestrial'] = True
    df_merged_all_categories.loc[
        (df_merged_all_categories['sea_total'] == 0) & (df_merged_all_categories['land_total'] == 0),
        'location_designation_other'] = 'neither marine nor terrestrial'

   # NOT preferentially choosing marine
    df_merged_all_categories.loc[
        (df_merged_all_categories['land_total'] > 0),
        'location_designation'] = 'terrestrial'
    df_merged_all_categories.loc[
        (df_merged_all_categories['sea_total'] > 0),
        'location_designation'] = 'marine'
    df_merged_all_categories.loc[
        (df_merged_all_categories['sea_total'] == 0) & (df_merged_all_categories['land_total'] == 0),
        'location_designation_other'] = 'neither marine nor terrestrial'
    df_merged_all_categories.loc[
        (df_merged_all_categories['sea_total'] > 0) & (df_merged_all_categories['land_total'] > 0),
        'location_designation'] = 'marine and terrestrial'
    df_merged_all_categories.loc[
        (df_merged_all_categories['sea_total'] == 0) & (df_merged_all_categories['land_total'] == 0),
        'location_designation'] = 'neither marine nor terrestrial'

    ic(df_merged_all_categories.head(15))
    out_file = analysis_dir + 'merged_all_categories.tsv'
    ic(out_file)
    ic(df_merged_all_categories["location_designation"].value_counts())
    df_merged_all_categories.to_csv(out_file, sep = '\t')

    ic("========================================================")

    return out_file


def mergeAndAnalysis(df_ena, df_eez, df_longhurst, df_seaIHO, df_seawater, df_land, df_worldAdmin, df_hydrosheds,
                     df_intersect_eez_iho, hit_dir):
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
    df_intersect_eez_iho = clean_df(hitfile, 'MARREGION', 'eez_iho_intersect_category', 'eez_iho_intersect')
    ic(df_intersect_eez_iho.head(2))

    hitfile = hit_dir + 'seawater_polygons_hits.tsv'
    df_seawater = clean_df(hitfile, 'index_right', 'sea_category', 'seawater')

    hitfile = hit_dir + 'land_polygons_hits.tsv'
    df_land = clean_df(hitfile, 'index_right', 'land_category', 'land')

    hitfile = hit_dir + 'world-administrative-boundaries_hits.tsv'
    df_worldAdmin = clean_df(hitfile, 'region', 'worldAdmin_category', 'land')

    hitfile = hit_dir + 'World_Seas_IHO_v3_hits.tsv'
    df_seaIHO = clean_df(hitfile, 'MRGID', 'IHO_category', 'sea')

    hitfile = hit_dir + 'feow_hydrosheds_hits.tsv'
    df_hydrosheds = clean_df(hitfile, 'index_right', 'feow_category', 'hydroshed')

    hitfile = hit_dir + 'longhurst_v4_hits.tsv'
    df_longhurst = clean_df(hitfile, 'ProvCode', 'longhurst_category', 'blank')

    hitfile = hit_dir + 'eez_hits.tsv'
    df_eez = clean_df(hitfile, 'GEONAME', 'eez_category', 'EEZ')

    ic(df_eez.head())
    ic(df_eez.shape[0])

    return (df_eez, df_longhurst, df_seaIHO, df_seawater, df_land, df_worldAdmin, df_hydrosheds, df_intersect_eez_iho)

def processTrawlFindings(yes, yes_both_not_eez , no, skip,trawl_count):
    """ processTrawlFindings
        __params__:
               passed_args
                 3 dictionaries: yes, yes_both_not_eez no, skip
                 1 integer: trawl_count
    """
    ic(skip)
    ic(trawl_count)
    ic(len(yes))
    ic(len(yes_both_not_eez))
    ic(len(skip))

    coordinate_entry_errors = {}
    one_coordinate_not_mapped = {}
    different_EEZs = {}
    other_no = {}
    """ Doing the search for nan last as otherwise could miss errors in coorinates"""
    for external_id in no:
        # ic(no[external_id])
        if no[external_id]['start_coords'][0] == '-' and no[external_id]['end_coords'][0] != '-':
            # ic("error in latitudes")
            coordinate_entry_errors[external_id] = no[external_id]
        elif no[external_id]['end_coords'][0] != '-' and no[external_id]['end_coords'][0] == '-':
            # ic("error in latitudes")
            coordinate_entry_errors[external_id] = no[external_id]
        else:
            start_lon_minus_found = '_-' in no[external_id]['start_coords']
            end_lon_minus_found = '_-' in no[external_id]['end_coords']
            if start_lon_minus_found != end_lon_minus_found :
                # ic("error in longitudes")
                coordinate_entry_errors[external_id] = no[external_id]
            elif no[external_id]['start_GEONAME'] == 'nan' and no[external_id]['end_GEONAME'] == 'nan':
                ic('Error Two nan found, should have been captured earlier')
                quit()
            elif no[external_id]['start_GEONAME'] == 'nan' or no[external_id]['end_GEONAME'] == 'nan':
                one_coordinate_not_mapped[external_id] = no[external_id]
            elif no[external_id]['start_GEONAME'] != no[external_id]['end_GEONAME']:
                different_EEZs[external_id] = no[external_id]
            else:
                other_no[external_id] = no[external_id]
    ic(len(no))
    ic("no matches breakdown:")
    ic(len(coordinate_entry_errors))
    ic(len(one_coordinate_not_mapped))
    ic(len(different_EEZs))
    ic(len(other_no))
    ic(different_EEZs)
    ic(coordinate_entry_errors)

def analyse_trawl_data(df_merged_all,df_trawl_samples):
    """ analyse_trawl_data(df_merged_all,df_trawl_samples)
        __params__:
               passed_args
                analyse_trawl_data(df_merged_all,df_trawl_samples)
    """

    ic(df_merged_all.shape[0])
    ic(df_merged_all.head(2))
    ic(df_trawl_samples.shape[0])
    ic(df_trawl_samples.head(2))
    df_trawl_samples['start_index'] = df_trawl_samples['lon_start'].apply(str) + "_" + \
                                      df_trawl_samples['lat_start'].apply(str) + "_" + \
                                      df_trawl_samples['external_id'].apply(str)
    df_trawl_samples['actual_start_index'] = df_trawl_samples['start_index']


    df_trawl_samples['end_index'] = df_trawl_samples['lon_end'].apply(str) + "_" + \
                                      df_trawl_samples['lat_end'].apply(str)+ "_" + \
                                      df_trawl_samples['external_id'].apply(str)
    df_trawl_samples['actual_end_index'] = df_trawl_samples['end_index']

    """ want to look up each pair of lat/lon starts and sea if they are in the same EEZ as lat/lon ends
    so doing via doing two intersection's """
    df_merged_starts = pd.merge(df_merged_all,df_trawl_samples, how='inner',left_on=['lon','lat'],
                                right_on=['lon_start','lat_start'])

    df_merged_starts = df_merged_starts.set_index('actual_start_index')
    # df_merged_starts = df_merged_starts[df_merged_starts['external_id'].notna()].reset_index()
    ic(df_merged_starts.shape[0])
    ic(df_merged_starts.head(2))

    df_merged_ends = pd.merge(df_merged_all,df_trawl_samples, how='inner',left_on=['lon','lat'],
                                right_on=['lon_end','lat_end'])
    df_merged_ends = df_merged_ends.set_index('actual_end_index')
    # df_merged_ends = df_merged_ends[df_merged_ends['external_id'].notna()].reset_index()
    ic(df_merged_ends.shape[0])
    ic(df_merged_ends.head(2))


    count = 0
    yes = {}
    yes_both_not_eez = {}
    no = {}
    skip = {}
    """ looping though panda dataframe, bad form! 
        need to index on lat lon and extenal_id for uniq rows
    """
    ic(df_merged_starts.shape[0])
    for start_index, row in df_merged_starts.iterrows():
        ic('-----------------------------------------------------------------------')
        count += 1
        ic(start_index)
        ic(row['end_index'])
        # ic(row)
        if 'end_index' not in row:
            local_dict = {'start_coords': start_index, 'problem': 'no end_index defined in start dict'}
            ic(local_dict)
            next
        elif 'end_index' not in df_merged_ends:
            local_dict = {'start_coords': start_index, 'problem': 'no end_index defined in end dict'}
            ic(local_dict)
            next
        else:
            ic("so end_index found in both row and in df_merged_ends")

        df = pd.DataFrame()
        row_end_index = row['end_index']
        ffs=0

        try:
            ic("in try for looking up merged_ends")
            ic(row_end_index)
            df  = df_merged_ends.loc[[row_end_index]]
            ffs=1
            df = df.reset_index()
            # ic(df)
            ic(df.shape[0])

        except:
            local_dict = {'start_coords': start_index, 'problem': 'not able able to reset_index'}
            next

        # ic(df)
        # ic(df.columns)
        # ic(df.shape[0])
        if df.shape[0] == 0:
            ic('df is 0---------------------------------so next')
            next

        ic(row['external_id'])
        external_id = row['external_id']
        # ic(df.columns)
        # if 'external_id' not in df.columns:
        #     if 'end_index' in df.columns:
        #         ic(df['end_index'][0])
        #         (lat,lon,external_id) = df['end_index'][0].split('_')
        #         ic(external_id)
        #         df['external_id'] = external_id
        #     elif 'start_index' in df.columns:
        #         ic(df['start_index'][0])
        #         (lat,lon,external_id) = df['start_index'][0].split('_')
        #         ic(external_id)
        #         df['external_id'] = external_id

        if 'external_id' not in df.columns:
            ic('external_id not in cols')
            # ic(df)
            local_dict = {'start_coords': start_index, 'problem': 'external_id not in df.columns'}
            ic(df.columns)
            skip[row['external_id']] = local_dict
            # ic(local_dict)
            next
        else:
            df = df.set_index('external_id')
            # ic(df.head(3))

            # df = df.set_index('external_id')
            ic(df.loc[[row['external_id']]])
            ic(df.loc[[row['external_id']]].shape[0])
            df_total_row_num= df.loc[[row['external_id']]].shape[0]
            short_end = []
            if(df_total_row_num == 1):
                short_end = df.loc[row['external_id']].to_dict()
            elif(df_total_row_num >1):
                ic("Multiple matches! So just select first one, as all checked are identical.")
                df_tmp = df.loc[[row['external_id']]].head(1)
                short_end = df_tmp.squeeze().to_dict()
                ic(short_end)
            else:
                short_end = df.loc[row['external_id']].to_dict()
                ic("ERROR Getting zero matches, this should not happen")
                quit()

            key_name = 'GEONAME'
            start_key = "start_" + key_name
            end_key = "end_" + key_name
            local_dict = {'start_coords': start_index , start_key: row[key_name], end_key: short_end[key_name],
                          'end_coords': short_end['end_index'] }
            if row[key_name] == short_end[key_name]:
                yes[row['external_id']] = local_dict
            elif row[key_name] == 'nan' and short_end[key_name] == 'nan':
                yes_both_not_eez[row['external_id']] = local_dict
                ic(yes_both_not_eez)
                # quit()
            else:
                no[row['external_id']] = local_dict

                if row['external_id'] == 'SAMEA3692423':
                    ic(local_dict)
                    ic(short_end)
                    print(f"start=\"{row[key_name]}\"")
                    print(f"  end=\"{short_end[key_name]}\"")
                    quit()

            # if count > 100:
            #      break

    processTrawlFindings(yes,yes_both_not_eez,no,skip,count)


    return

def clean_merge_all(df_merged_all):
    """ clean_merge_all
        __params__:
               passed_args
                  df_merged_all
        __rtn__
           df_merged_all

        return
    """
    df_merged_all['GEONAME'] = df_merged_all['GEONAME'].astype(str)

    geoname_list = df_merged_all['GEONAME'].unique()
    # ic(sorted(geoname_list))

    return df_merged_all

def analysis_lat_lon(sample_dir):
    """ analysis_lat_lon
        __params__:
               passed_args: sample_dir
        rtn: df
    """
    sample_file = sample_dir + 'sample_much_raw.tsv'
    cols = ["accession", "lat", "lon"]
    df = pd.read_csv(sample_file, sep = "\t", index_col=None, usecols=cols, nrows=100000)
    df_filtered = df.loc[df['lat'].notnull()]
    # df_filtered['lat_decimal_len'] = str(df_filtered['lat'])[::-1].find('.')
    # df_filtered['lat_decimal_len'] = len(str(df_filtered['lat']).split(".")[1])
    df_filtered['lat_decimal'] = df_filtered['lat'].astype(str).str.split(".").str[1]
    df_filtered['lat_len'] = df_filtered['lat_decimal'].str.len()

    df_filtered['lon_decimal'] = df_filtered['lon'].astype(str).str.split(".").str[1]
    df_filtered['lon_len'] = df_filtered['lon_decimal'].str.len()

    ic(df_filtered.head(100))

    ic(df_filtered['lat_len'].value_counts())
    df_tmp = df_filtered.drop(columns=['lat', 'lon']).groupby('lat_len').size().to_frame('count').reset_index()
    ic(df_tmp)

    df_tmp = df_filtered.drop(columns=['lat', 'lon']).groupby('lon_len').size().to_frame('count').reset_index()
    ic(df_tmp)


    return df


def get_ena_total_sample_count(sample_dir):
    """ get_ena_total_sample_count
        __params__:
               passed_args: sample_dir
        rtn: integer line count
    """
    sample_file = sample_dir + 'sample_much_raw.tsv'
    num_lines = sum(1 for line in open(sample_file))

    return num_lines


def main():
    """ main takes the "hit" files from the getGeoLocationCategorisation.py files, integrates and plots them
        __params__:
               passed_args
    """
    full_rerun = True

    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    analysis_lat_lon(sample_dir)

    quit(1)

    ena_total_sample_count = get_ena_total_sample_count(sample_dir)
    ic(ena_total_sample_count)



    # get all the files processed
    if full_rerun:
        df_ena = get_all_ena_lat_lon(sample_dir)
        (df_eez, df_longhurst, df_seaIHO, df_seawater, df_land, df_worldAdmin, df_hydrosheds, df_intersect_eez_iho) \
            = processHitFiles(hit_dir)
        df_merged_all = mergeAndAnalysis(df_ena, df_eez, df_longhurst, df_seaIHO, df_seawater, df_land, df_worldAdmin,
                                         df_hydrosheds, df_intersect_eez_iho, hit_dir)
        merged_all_categories_file = analysis(df_merged_all, analysis_dir, plot_dir)



    df_merged_all = pd.read_csv(hit_dir + "merged_all.tsv", sep = "\t")
    df_merged_all = clean_merge_all(df_merged_all)

    merged_all_categories_file = analysis_dir + "merged_all_categories.tsv"
    df_merged_all_categories = pd.read_csv(merged_all_categories_file, sep = "\t")

    get_category_stats(ena_total_sample_count, df_merged_all_categories, df_merged_all)

    # df_trawl_samples = pd.read_csv(sample_dir + 'sample_trawl_all_start_ends_clean.tsv', sep = "\t")
    # analyse_trawl_data(df_merged_all,df_trawl_samples)

    ic("Do the plotting")
    ''' these are the plotting sections , can comment out all above once they have all they all been run.
        Done so that can save the time etc. of re-running the merging
     '''

    extra_plots(df_merged_all, plot_dir, shape_dir)
    plot_merge_all(df_merged_all, plot_dir)
    categoryPlotting(df_merged_all_categories, plot_dir)

    return ()


if __name__ == '__main__':
    ic()

    main()
