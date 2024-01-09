#!/usr/bin/env python3
# BlueCloud
"""Script to merge, analyse and plot the hits from getGeoLocationCategorisation.py
    directories for the hits, samples, analysis, plot etc. are set in "def get_directory_paths"
    The hits and plot files are additionally manually copied to a Google Drive shared with Stephane and Josie.

    The key product of this is this file:
    analysis/merged_all_categories.tsv

    if you want to add new categories or hit files, make changes to:
        clean_df, get_category_dict and add_cat()

___author___ = "woollard@ebi.ac.uk"
___start_date___ = "2022-12-08"
__docformat___ = 'reStructuredText'

"""
import sys
# /opt/homebrew/bin/pydoc3 getGeoLocationCategorisation   #interactive
# python3 -m pydoc -w getGeoLocationCategorisation.py     #to html file

from functools import reduce

import geopandas as gpd
import matplotlib.pyplot as plt
from geopandas import GeoDataFrame
from geopandas.geoseries import *
from shapely.geometry import Point

from get_directory_paths import get_directory_paths
from ena_samples import get_ena_total_sample_count
from ena_samples import get_all_ena_detailed_sample_info
from project_utils import *
from hitDataInfoClasses import MyHitDataInfo

pio.renderers.default = "browser"
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def extra_plots(df_merged_all_categories, plot_dir, shape_dir):
    """ extra_plots
            plotting some special graphs, that needs some customisation
            e.g. a specific shapefile as the base for the plot
        __params__:
               passed_args: df_merged_all_categories, plot_dir, shape_dir
    """
    crs_value = "EPSG:4326"
    shapefile = shape_dir + "GIS_hs_snapped/feow_hydrosheds.shp"
    out_format = 'png'

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
    out_graph_file = plot_dir + "pointsInJustHydroshed." + out_format
    plt.title("All ENA sample coords in(red) the FEOW hydroshed polygons", )
    ic(out_graph_file)
    fig1 = plt.gcf()
    fig1.savefig(out_graph_file)

    pointsInHydroshed_geodf.plot(ax = base, linewidth = 1, color = "red", markersize = 1, aspect = 1)
    notPointsInHydroshed_geodf.plot(ax = base, linewidth = 1, color = "blue", markersize = 1, aspect = 1)
    plt.title("All ENA sample coords(blue) in(red) the FEOW hydroshed polygons", )
    fig1 = plt.gcf()

    out_graph_file = plot_dir + "pointsInHydroshed." + out_format
    ic(out_graph_file)
    fig1.savefig(out_graph_file)

    sys.exit()

    return


def plot_merge_all(df_merged_all, plot_dir):
    """ plot_merge_all
              takes the largest merge all of all columns of the merged hit results and does plots that need all this,
              not just the category subset of columns
        __params__:
               passed_args (df_merged_all, plot_dir)
    """
    width = 1000
    out_format = 'png'

    def plot_scatter(cat, color, y, title, plot_width, outformat, out_graph_file):
        fig = px.scatter(df_merged_all, title = title, x = cat, y = y, width = plot_width,
                         color = color)
        ic(out_graph_file)
        plotly.io.write_image(fig, out_graph_file, format = outformat)

    plot_scatter("IHO_category", "IHO_category", "lat", "IHO, lats and longhurst", width, out_format,
                 plot_dir + 'IHO_by_lon.' + out_format)
    plot_scatter("IHO_category", "longhurst_category", "lat", "IHO, lats and longhurst", width, out_format,
                 plot_dir + 'IHO_ocean_by_lon.' + out_format)

    def plot_hist(cat, color, log_y, title, outformat, out_graph_file):
        plot_width = 1500
        fig = px.histogram(df_merged_all, title = title, x = cat,
                           width = plot_width, color = color, log_y = log_y, labels = {'count': "log(count)",
                                                                                       cat: cat})
        fig.update_xaxes(categoryorder = "total descending")
        fig.update_xaxes(tickangle = 60, tickfont = dict(size = 6))
        ic(out_graph_file)
        plotly.io.write_image(fig, out_graph_file, format = outformat)
        # fig.show()

    plot_hist("GEONAME", "continent", True, "EEZ by country + continent (logscale)", out_format,
              plot_dir + 'EEZ_continent_counts.' + out_format)
    plot_hist("IHO_category", "longhurst_category", True, "IHO country + Longhurst biome (logscale)", out_format,
              plot_dir + 'IHO_longhurst_counts.' + out_format)
    plot_hist("SOVEREIGN1", "continent", True, "EEZ country + continent (logscale)", out_format,
              plot_dir + 'country_lon_lat_counts.' + out_format)
    plot_scatter("lon", "AREA_SKM", "lat", 'feow_category_by_skm.', width, out_format,
                 plot_dir + 'feow_category_by_skm.' + out_format)

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
    ic()
    ic(hit_file, filter_field, cat_name, filter_swap_value)
    df = pd.read_csv(hit_file, sep = '\t', low_memory = False)
    # ic(df.columns)
    df = df[~df[filter_field].isnull()]
    # ic(df.head(2))
    # the first one captures feow_category
    if cat_name in ["g200_fw_category", "g200_marine_category", "g200_terr_category"]:
        df = df.rename({'index_right': cat_name}, axis = 1)
        if cat_name == "g200_fw_category":
            df[cat_name] = df['MHT']
        elif cat_name == "g200_terr_category":
            # cut -f5 g200_terr_hits.tsv | sort | uniq -c | sort -n | sed -E 's/.*,//;s/(Woodlands and Steppe|Deserts
            # and Shrublands|Woodlands|Steppe|Mangroves|Forest|Forests|Desert|Deserts|Mangrove|Alpine
            # Meadows|Savannas|Shrubland|Shrublands|scrub|Rainforests|Grasslands|Taiga|Tundra|Highlands|Prairies
            # |Scrub|Spiny Thicket|Moorlands|Shrubs)$/=====>\1<======/' | grep -v '='
            df[cat_name] = df["G200_REGIO"]
        elif cat_name == "g200_marine_category":
            df[cat_name] = df['G200_REGIO']
        ic(df[cat_name].value_counts())
    elif cat_name in ["ne_10m_river_lake_line_category", "ne_10m_river_lake_aus_line_category",
                      "ne_10m_river_eur_line_category",
                      "ne_10m_river_nam_line_category", "ne_10m_river_lake_line_category"]:
        df = df.rename({'index_right': cat_name}, axis = 1)
        df[cat_name] = df['featurecla']
    elif cat_name in ["ne_10m_lake_hit.tsv", "ne_50m_lakes_hit.tsv"]:
        df = df.rename({'index_right': cat_name}, axis = 1)
        df[cat_name] = df['featurecla']
    elif cat_name in ["glwd_1_category", "glwd_2_category"]:
        df = df.rename({'index_right': cat_name}, axis = 1)
        df[cat_name] = df['TYPE']
        ic(df[cat_name].value_counts())
    elif filter_field == "index_right":
        if 'x' in df.columns:
            df = df.drop(['x', 'y'], axis = 1)
        df[filter_field] = filter_swap_value
        df = df.rename({'index_right': cat_name}, axis = 1)
    elif filter_field == "intersect_MARREGION" or filter_swap_value == "eez_iho_intersect":
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

    elif filter_field == "region":  # i.e. for the World admin
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
    elif cat_name in ['eez_category']:
        # leave in these as, Stephane finds valuable
        df = df.drop(['X_1', 'Y_1'], axis = 1)
        # df = df.drop(['X_1', 'Y_1', 'MRGID_TER2', 'MRGID_SOV2', 'TERRITORY2', 'ISO_TER2', 'SOVEREIGN2', 'MRGID_TER3',
        #               'MRGID_SOV3', 'TERRITORY3', 'ISO_TER3', 'SOVEREIGN3', 'ISO_SOV2', 'ISO_SOV3', 'UN_SOV1',
        #               'UN_SOV2', 'UN_SOV3', 'UN_TER1', 'UN_TER2', 'UN_TER3'], axis = 1)
        df['index_right'] = filter_swap_value
        df = df.rename({'index_right': cat_name}, axis = 1)
    else:
        ic(f"ERROR {cat_name} not matching anything! please edit clean_df()")
        sys.exit()
    ic(df.columns)
    # ic(df.head(15))
    ic()
    return df


def merge_dfs(data_frames, out_filename):
    """ merge_dfs
        __params__:
            list of data_frames merging on ['coords', 'lon', 'lat']
            out_filename if it has length >1
        __returns__:
            df_merged
    """
    # ic()

    df_merged = reduce(lambda left, right: pd.merge(left, right, on = ['coords', 'lon', 'lat'],
                                                    how = 'outer', suffixes = ('', '_y')), data_frames)
    # now get rid of duplicated columns, yes will sometimes lose some data...
    df_merged.drop(df_merged.filter(regex = '_y$').columns, axis = 1, inplace = True)

    # df_merged = df_merged.loc[~df_merged.index.duplicated(), :].copy()
    # df_merged.reset_index(inplace=True)
    # ic(df_merged.head(2))
    # ic(df_merged.shape[0])
    # ic(df_merged.columns)

    if len(out_filename) > 1:
        df_merged.to_csv(out_filename, sep = "\t", index = False)
        ic(out_filename)
    return df_merged


def create_total(df_merged_all_categories, categories, total_key_to_be):
    """  create_total
            Sums up the occurrences of evidence from different sources(essentially the categories)
            i.e. count the none null values.
            The solution in the end was simple, but took me 2 hours to work out!
        __params__:
            df_merged_all_categories, categories, total_key_to_be
        __returns__:
            df_merged_all_categories

    """
    ic()
    # was getting warnings about working on a copy of slice, this turns this off
    pd.options.mode.chained_assignment = None  # default='warn'
    ic(total_key_to_be)

    df_just_cats = df_merged_all_categories[categories]
    number_of_cats = len(categories)
    df_merged_all_categories[total_key_to_be] = number_of_cats - df_just_cats.isnull().sum(axis = 1)

    ic(df_merged_all_categories[total_key_to_be].value_counts())

    pd.options.mode.chained_assignment = 'warn'

    return df_merged_all_categories


# def get_all_ena_lat_lon_geo(samples_dir):
#     """  get_all_ena_lat_lon_geo inc. country and accession(sample_id)
#           This file was created by
#           curl -X GET "https://www.ebi.ac.uk/ena/portal/api/search?dataPortal=ena&dccDataOnly=false&download=false&
#           fields=accession%2C%20lon%2C%20lat%2C%20country&includeMetagenomes=true&result=sample&sortDirection=asc"
#           -H "accept: */*" > sample_lat_lon_country.tsv
#             awk '$2 ~ /^[0-9*]|^lon$/{print;}' sample_lat_lon_country.tsv > sample_lat_lon_country_clean.tsv
#           :param
#             samples_dir_
#           :return
#              dataframe
#     """
#     ic()
#     crs_value = "EPSG:4326"
#     pd.set_option('display.max_columns', None)
#     ena_file = samples_dir + "all_sample_lat_lon_country.tsv"
#     df = pd.read_csv(ena_file, sep = '\t')
#
#     df['coords'] = list(zip(df['lon'], df['lat']))
#     df['coords'] = df['coords'].apply(Point)
#     points_geodf = gpd.GeoDataFrame(df, geometry = 'coords', crs = crs_value)
#     points_geodf = points_geodf.drop(['accession'], axis = 1)
#     points_geodf = points_geodf.drop_duplicates()
#
#     # ic("look for dups")
#     # boolean = points_geodf.duplicated(subset = ['coords']).any()
#     # print(boolean, end = '\n\n')  # True
#     #
#     # ic("look for dups")
#     # (tmp_df) = points_geodf.duplicated(subset = None, keep = 'first')
#     # doing the following rather than rename as it changes the order too.
#     #
#     points_geodf[['ena_country', 'ena_region']] = points_geodf['country'].str.split(":", expand = True)
#     points_geodf = points_geodf.drop(['country'], axis = 1)
#     points_geodf['ena_category'] = 'ena'
#     # ic(points_geodf.head(15))
#     # nightmare with unhashable Points
#     # df1 = pd.DataFrame(points_geodf)
#     #read to and from a flat file as a workaround - was getting some strange behaviours and not time to debug
#     ena_tmp_file = samples_dir + "sample_lat_lon_country_clean_tmp.tsv"
#     points_geodf.to_csv(ena_tmp_file, sep = '\t', index=False)
#     df1 = pd.read_csv(ena_tmp_file, sep = '\t')
#
#     return df1


def category_plotting(df_merged_all_categories, plot_dir, hit_cats_info, full_rerun):
    """  category_plotting
                plotting using the category column subset
                is using the scope aspect of plotly, this uses the inbuilt maps rather than the shapefile maps
        __params__:
            df_merged_all_categories, plot_dir
        __returns__:

    """
    ic(full_rerun)
    marker_size = marker_size_default = 4

    ic(df_merged_all_categories.head(3))
    width = 1500
    scope = 'world'
    # cat = 'ena_country'
    # ic(cat)
    # df_all = df_merged_all_categories[cat].value_counts().rename_axis(cat).to_frame('counts').reset_index()
    # ic(df_all.head())
    # ic(df_all.describe())
    # ic(df_all["counts"].sum())

    cat = 'worldAdmin_category'
    ic(cat)
    df_all = df_merged_all_categories[cat].value_counts().rename_axis(cat).to_frame('counts').reset_index()
    ic(df_all.head())
    ic(df_all.describe())
    ic(df_all["counts"].sum())

    all_categories = hit_cats_info.get_category_list()
    all_categories.append("freshwater_key_combined")
    for cat in all_categories:
        ic(cat)
        ic(df_merged_all_categories[cat].value_counts().rename_axis('unique_values').reset_index(name = 'counts').head(
            5))

    def create_cat_figure(figure_title_string, color_value, scope, out_graph_file, width, marker_size, showlegendStatus,
                          figure_format):
        """create_cat_figure
        plots the data on a map essentially

        :param figure_title_string:
        :param color_value:
        :param scope:
        :param out_graph_file:
        :param width:
        :param marker_size:
        :param showlegendStatus:
        :param figure_format:
        :return:
        """
        if not showlegendStatus:
            figure_title_string = ""
        fig = px.scatter_geo(df_merged_all_categories, "lat", "lon",
                             width = width, color = color_value,
                             title = figure_title_string,
                             scope = scope)
        fig.update_traces(marker = dict(size = marker_size))
        fig.update_layout(
            autosize = False,
            width = 1000,
            height = 1000, )
        if not showlegendStatus:
            fig.update_layout(showlegend = False)

        ic(out_graph_file)
        plotly.io.write_image(fig, out_graph_file, format = figure_format)
        # fig.show()
        return fig

    def create_cat_figure_w_color(df, title_string, color_value, color_discrete_map, scope, out_graph_file, width,
                                  marker_size, showlegendStatus, figure_format):
        """create_cat_figure
        plots the data on a map essentially

        :param df:
        :param title_string:
        :param color_value:
        :param scope:
        :param out_graph_file:
        :param width:
        :param marker_size:
        :param showlegendStatus:
        :param figure_format:
        :return:
        """
        if not showlegendStatus:
            title_string = ""
        fig = px.scatter_geo(df, "lat", "lon",
                             width = width, color = color_value,
                             title = title_string,
                             scope = scope,
                             color_discrete_map = color_discrete_map
                             )
        fig.update_traces(marker = dict(size = marker_size))
        if not showlegendStatus:
            fig.update_layout(showlegend = False)

        ic(out_graph_file)
        plotly.io.write_image(fig, out_graph_file, format = figure_format)
        # fig.show()
        return fig

    def plot_pie(df, cat, out_file):
        title = cat
        fig = px.pie(df[cat],
                     values = df['counts'],
                     names = df[cat], title = title)
        fig.update_traces(hoverinfo = 'label+percent', textinfo = 'value')
        fig.update_layout(title_text = title, title_x = 0.5)
        fig.update_layout(legend = dict(yanchor = "top", y = 0.9, xanchor = "left", x = 0.5))
        ic(out_file)
        fig.write_image(out_file)
        # fig.show()
        return fig

    # def plot_location_designation():
    #     """
    #
    #     :return:
    #     """
    #     showlegendStatus = True
    #     title_string = 'ENA samples in Location Designation based on multiple shapefiles'
    #     color_value = "location_designation"
    #     color_discrete_map = {'terrestrial': 'rgb(30,144,255)', 'marine': 'rgb(220,20,60)',
    #                           'marine and terrestrial': 'rgb(50,205,50)',
    #                           'neither marine nor terrestrial': 'rgb(148,0,211)'}
    #
    #     format = 'png'
    #     out_graph_file = plot_dir + 'merge_all_location_designation.' + format
    #     fig = px.scatter_geo(df_merged_all_categories, "lat", "lon",
    #                          width = width, color = color_value,
    #                          title = title_string,
    #                          scope = scope,
    #                          color_discrete_map = color_discrete_map)
    #     fig.update_traces(marker = dict(size = marker_size))
    #     ic(out_graph_file)
    #     fig.show()
    #     plotly.io.write_image(fig, out_graph_file, format = format)
    #
    # df_merged_all_categories_just = df_merged_all_categories.query( 'location_designation == "marine and
    # terrestrial"') out_file = plot_dir + 'merge_all_location_designation_m+t.' + format cat =
    # 'location_designation' title = 'merge_all_location_designation_m+t.' create_cat_figure_w_color(
    # df_merged_all_categories_just, title, cat, color_discrete_map, scope, out_file, width, marker_size,
    # showlegendStatus, format)
    #
    #     title = 'location_designation using GPS coordinates'
    #     out_file = plot_dir + "location_designation_using_GPS_pie.png"
    #     fig = px.pie(df_merged_all_categories["location_designation"],
    #                  values = df_merged_all_categories["location_designation"].value_counts().values,
    #                  names = df_merged_all_categories["location_designation"].value_counts().index, title = title,
    #                  color_discrete_map = color_discrete_map)
    #     fig.update_traces(hoverinfo = 'label+percent', textinfo = 'value')
    #     ic(out_file)
    #     fig.show()
    #     fig.write_image(out_file)
    #
    #     ic(df_merged_all_categories["location_designation"].value_counts())
    #
    #     # plot_location_designation() as a pie chart
    #
    #     ic(df_merged_all_categories.columns)
    #     cat = "eez_iho_intersect_category"
    #     title = cat
    #     df_all = df_merged_all_categories[cat].value_counts().rename_axis(cat).to_frame('counts').reset_index()
    #     ic(df_all.describe())
    #     df_top = df_all.head(10)
    #     df_rest = df_all.iloc[10:]
    #     other_count = df_rest["counts"].sum()
    #     df_top.loc[len(df_top)] = ['other_areas', other_count]
    #     out_file = plot_dir + "eez_iho_intersect_category_using_GPS_pie.png"
    #     plot_pie(df_top, cat, out_file)

    def plot_longhurst():

        # plot_ longhurst as a pie chart
        cat = "longhurst_category"
        title = cat
        df_all = df_merged_all_categories[cat].value_counts().rename_axis(cat).to_frame('counts').reset_index()
        ic(df_all.describe())
        out_file = plot_dir + "longhurst_category_using_GPS_pie.png"
        plot_pie(df_all, cat, out_file)
        out_file = plot_dir + "longhurst_category_using_GPS_map.png"
        format = "png"
        showlegendStatus = True
        color_discrete_map = {'Coastal': 'rgb(30,144,255)', 'Trades': 'rgb(220,20,60)',
                              'Westerlies': 'rgb(50,205,50)',
                              'Polar': 'rgb(148,0,211)'}
        create_cat_figure_w_color(df_merged_all_categories, title, cat, color_discrete_map, scope, out_file, width,
                                  marker_size, showlegendStatus, format)

    # plotting freshwater
    format = 'png'
    showlegendStatus = True
    marker_size = 2
    for cat in ['freshwater_key_combined']:
        scope = 'europe'
        title_string = "ENA Samples in " + cat + " in " + scope
        color_value = cat
        out_graph_file = plot_dir + cat + scope + '.' + format
        width = 1500
        create_cat_figure(title_string, color_value, scope, out_graph_file, width, marker_size, showlegendStatus,
                          format)

    # ic("early abort")
    # sys.exit()

    title_string = 'ENA samples in Sea category (water polygons)'
    color_value = "sea_category"
    out_graph_file = plot_dir + 'merge_all_sea_category.' + format
    create_cat_figure(title_string, color_value, scope, out_graph_file, width, marker_size, showlegendStatus, format)

    title_string = "ENA Samples in Hydrosheds"
    marker_size = 1
    color_value = "feow_category"
    out_graph_file = plot_dir + 'feow_category.' + format
    create_cat_figure(title_string, color_value, scope, out_graph_file, width, marker_size, showlegendStatus, format)

    scope = 'europe'
    title_string = "ENA Samples in Hydrosheds in " + scope
    color_value = "feow_category"
    out_graph_file = plot_dir + 'feow_category_' + scope + '.' + format
    create_cat_figure(title_string, color_value, scope, out_graph_file, width, marker_size, showlegendStatus, format)

    def eez_iho_intersect_category_scope_plots(plot_dir, width, marker_size, scope, showlegendStatus):
        title_string = 'ENA samples in eez_iho_intersect_category in ' + scope
        format = 'png'
        out_graph_file = plot_dir + 'merge_all_intersect_eez_iho_cats' + scope + '.' + format
        color_value = "eez_iho_intersect_category"
        create_cat_figure(title_string, color_value, scope, out_graph_file, width, marker_size, showlegendStatus,
                          format)

    scope = "world"
    marker_size = marker_size_default
    showlegendStatus = False
    eez_iho_intersect_category_scope_plots(plot_dir, width, marker_size, 'europe', showlegendStatus)
    eez_iho_intersect_category_scope_plots(plot_dir, width, marker_size, 'north america', showlegendStatus)
    eez_iho_intersect_category_scope_plots(plot_dir, width, marker_size, 'africa', showlegendStatus)
    eez_iho_intersect_category_scope_plots(plot_dir, width, marker_size, 'world', showlegendStatus)

    showlegendStatus = True
    format = 'png'
    title_string = 'ENA samples in IHO Categories'
    color_value = "IHO_category"

    out_graph_file = plot_dir + 'merge_all_IHO_cats.' + format
    create_cat_figure(title_string, color_value, scope, out_graph_file, width, marker_size, showlegendStatus, format)

    # figure_title_string = 'ENA samples in ENA Country Categories' color_value = "ena_country" out_graph_file =
    # plot_dir + 'merge_all_ENA_country_cats.' + figure_format create_cat_figure(figure_title_string, color_value,
    # scope, out_graph_file, width, marker_size, showlegendStatus, figure_format)

    title_string = 'ENA samples in World Admin Categories'
    color_value = "worldAdmin_category"
    out_graph_file = plot_dir + 'merge_all_worldAdmin_category.' + format
    create_cat_figure(title_string, color_value, scope, out_graph_file, width, marker_size, showlegendStatus, format)

    title_string = 'ENA samples in EEZ categories'
    color_value = "eez_category"
    out_graph_file = plot_dir + 'merge_all_eez_category.' + format
    create_cat_figure(title_string, color_value, scope, out_graph_file, width, marker_size, showlegendStatus, format)

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
    ic(df_merged_all_categories["location_designation"].value_counts())
    stats_dict = {}
    stats_dict["terrestrial"] = df_merged_all_categories["location_designation_terrestrial"].count()
    stats_dict["marine_total"] = df_merged_all_categories["location_designation_marine"].count()
    stats_dict["other_total"] = df_merged_all_categories["location_designation_other"].count()
    stats_dict["total_uniq_GPS_coords"] = ena_uniq_lat_lon_total
    ic(stats_dict)

    ic(df_merged_all_categories.count())
    print(f"ena_total_sample_count = {ena_total_sample_count}")
    field_name: str
    for field_name in stats_dict:
        print(f"{field_name}={stats_dict[field_name]} = {(100 * stats_dict[field_name] / ena_uniq_lat_lon_total):.2f}%")

    return


def extra_cat_merging(hit_cats_info, df_merged_all_categories):
    """"
    df_merged_all_categories = extra_cat_merging(df_merged_all_categories)
    """
    ic()

    ic("freshwater extra merging, to get the freshwater type, n.b. is populated in order from "
       ".get_freshwater_cats_narrow()")
    ic(hit_cats_info.get_terrestrial_cats())
    ic(hit_cats_info.get_freshwater_cats_narrow())
    for cat in hit_cats_info.get_freshwater_cats_narrow():
        ic(cat)
        df_merged_all_categories.loc[df_merged_all_categories[cat].notnull(), 'freshwater_key_combined'] = \
            df_merged_all_categories[cat]

    # ic(df_merged_all_categories["feow_category"].value_counts())
    # df_merged_all_categories.loc[df_merged_all_categories[cat].notnull(), 'freshwater_key_combined'] = \
    #    df_merged_all_categories["feow_category"]

    # some basic harmonisation
    df_merged_all_categories.loc[
        df_merged_all_categories['freshwater_key_combined'] == "Lakes", 'freshwater_key_combined'] = "Lake"
    df_merged_all_categories.loc[
        df_merged_all_categories['freshwater_key_combined'] == "Lake Centerline", 'freshwater_key_combined'] = "Lake"
    # ic(df_merged_all_categories['freshwater_key_combined'].value_counts())
    # sys.exit()

    return df_merged_all_categories


def choose_location_designations(df_merged_all_categories):
    """choose_location_designations

    :return: df_merged_all_categories
    """
    ic()

    pd.options.mode.chained_assignment = None  # default='warn'

    df_merged_all_categories.loc[
         (df_merged_all_categories['sea_total'] > 0),'location_designation_marine'] = True

    df_merged_all_categories.loc[
            (df_merged_all_categories['land_total'] > 0),
            'location_designation_terrestrial'] = True

    df_merged_all_categories.loc[
            (df_merged_all_categories['sea_total'] == 0) & (df_merged_all_categories['land_total'] == 0),
            'location_designation_other'] = 'neither marine nor terrestrial'

    df_merged_all_categories.loc[
        (df_merged_all_categories['freshwater_total'] > 0),
        'location_designation_freshwater'] = True

    # NOTE preferentially choosing marine
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
    df_merged_all_categories.loc[
        df_merged_all_categories['location_designation_marine'] == True, 'location_designation_aquatic'] = True
    df_merged_all_categories.loc[
        df_merged_all_categories['location_designation_freshwater'] == True, 'location_designation_aquatic'] = True
    pd.options.mode.chained_assignment = 'warn'
    return df_merged_all_categories


def analyseFreshwater():
    """

    :return:
    """
    ic()
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    result_file = analysis_dir + '/merged_all_categories.tsv'
    df = pd.read_csv(result_file, sep = "\t")
    ic(df.shape)
    ic(df.sample(n = 4))

    hit_cats_info = MyHitDataInfo(hit_dir)
    # hit_cats_info.put_category_info_dict(category_info_dict)
    # hit_cats_info.write_category_info_dict_json()
    # hit_cats_info.read_category_info_dict_json()
    cols2keep = []
    other = ["lat", "lon", "location_designation_freshwater", "location_designation_aquatic", "freshwater_key_combined",
             "freshwater_total"]
    for col in other:
        cols2keep.append(col)
    for col in hit_cats_info.get_freshwater_cats():
        cols2keep.append(col)
    (df["freshwater_total"].value_counts())
    df = df[cols2keep].query('freshwater_total > 0')
    ic(df.shape)
    ic(df.sample(n = 4))
    ic(df["freshwater_total"].value_counts())
    ic(df["freshwater_key_combined"].value_counts())
    ic(df["feow_category"].value_counts())
    ic(df.count())


def analysis(df_merged_all, analysis_dir, plot_dir, hit_cats_info):
    """  analysis
         an important method:
            - this create totals for different category groupings

        __params__:
            df_merged_all, analysis_dir, plot_dir
        __returns__:

    """
    ic(df_merged_all.columns)
    test_cats = [match for match in list(df_merged_all.columns) if "category" in match]
    ic(test_cats)
    sys.exit()
    ic(df_merged_all.head(2))
    categories = hit_cats_info.get_category_list()
    # ic(categories)
    # columns2keep = ['lat', 'lon', 'coords', 'ena_country', 'ena_region'] + categories
    columns2keep = ['lat', 'lon', 'coords'] + categories
    ic(columns2keep)
    ic(df_merged_all.columns)
    df_merged_all_categories = df_merged_all[columns2keep]


    category_dict = hit_cats_info.get_domain_cat_dict()
    ic(category_dict)
    ic()

    for cat in category_dict.keys():
        if cat == "marine":
            total_label = 'sea_total'
        else:
            total_label = cat + "_total"
        df_merged_all_categories = create_total(df_merged_all_categories, category_dict[cat], total_label)

    df_merged_all_categories = choose_location_designations(df_merged_all_categories)
    df_merged_all_categories = extra_cat_merging(hit_cats_info, df_merged_all_categories)

    ic(df_merged_all_categories.head(5))
    out_file = analysis_dir + 'merged_all_categories.tsv'
    ic(df_merged_all_categories.shape[0])
    ic(df_merged_all_categories["location_designation"].value_counts())
    ic(out_file)
    df_merged_all_categories.to_csv(out_file, sep = '\t', index = False)

    ic("========================================================")

    return out_file


def mergeAndAnalysis(hit_df_dict, hit_dir, hit_cats_info):
    """  mergeAndAnalysis is used to merge a bunch of data frames. df_ena, df_eez, df_longhurst, df_seaIHO,
    df_seawater, df_land, df_worldAdmin, df_hydrosheds, df_intersect_eez_iho

        __params__:
        df_ena, df_eez, df_longhurst, df_seaIHO, df_seawater, df_land, df_worldAdmin, df_hydrosheds,
        df_intersect_eez_iho , hit_Dir

        __returns__:

    """
    ic()
    #  ic(hit_df_dict.keys())

    category_info_dict = hit_cats_info.get_category_info_dict()
    # ic(category_info_dict)

    domain_cat_dict = hit_cats_info.get_domain_cat_dict()
    # ic(domain_cat_dict)

    # temporarily removed the freshwater and land_data to get the f%&K£@% IHO_EEZ intersect working
    freshwater_frames = []
    for cat in domain_cat_dict['freshwater']:
        freshwater_frames.append(hit_df_dict[cat])
    out_filename = hit_dir + 'merged_freshwater.tsv'
    ic(out_filename)
    df_merged_freshwater = merge_dfs(freshwater_frames, out_filename)
    #
    sea_data_frames = []
    for cat in domain_cat_dict['marine']:
        sea_data_frames.append(hit_df_dict[cat])
    out_filename = hit_dir + 'merged_sea.tsv'
    df_merged_sea = merge_dfs(sea_data_frames, out_filename)
    #
    land_data_frames = []
    for cat in domain_cat_dict['terrestrial']:
        land_data_frames.append(hit_df_dict[cat])
    out_filename = hit_dir + 'merged_land.tsv'
    df_merged_land = merge_dfs(land_data_frames, out_filename)

    data_frames = [df_merged_sea, df_merged_land, df_merged_freshwater]
    #data_frames = [df_merged_sea]
    out_filename = hit_dir + 'merged_all.tsv'
    df_merged_all = merge_dfs(data_frames, out_filename)
    # ic(df_merged_all.head(3))

    return df_merged_all


def processHitFiles(hit_dir, hit_cats_info):
    """  processHitFiles This is where one has to add a little metadata about the category and domain for each hit
    file. This is used else where!

         drop rows where no hits
         some tidying up: e.g. columns that usually empty, regex of strange chars.
         generating a column_category to give a gross overview

         category_info_dict metadata about the category and domain  -->   get_category_info_dict object method at top
         of file

        __params__: hit_dir,
                    hit_cats_info   - object reference for putting data to reuse later in script.

        __returns__:   hit_df_dict  is a dictionary of data frames of merge info from all the hit files


    """
    ic()
    hit_df_dict = {}
    category_info_dict = {}

    def add_cat(category_info_dict, short, hit_dir, hitfile, category, domains):
        """
        Add a category and domain, is one of the most important functions.
        add_cat will need to be edited  whenever a new hitfile is being added
        :param category_info_dict:
        :param short:
        :param hit_dir:
        :param hitfile:
        :param category:
        :param domains:
        :return:
        """
        ic(category)
        category_info_dict[category] = {}
        category_info_dict[category]["hitfile"] = hit_dir + hitfile
        category_info_dict[category]["category"] = category
        category_info_dict[category]["short"] = short
        category_info_dict[category]["domains"] = domains
        return category_info_dict, category

    (category_info_dict, category) = add_cat(category_info_dict, "intersect_eez_iho", hit_dir,
                                             'intersect_eez_iho_hits.tsv', 'eez_iho_intersect_category', ['marine'])
    hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'MARREGION', category,
                                     'eez_iho_intersect')

    # (category_info_dict, category) = add_cat(category_info_dict, "g200_fw", hit_dir, 'g200_fw_hits.tsv',
    #                                          'g200_fw_category', ['freshwater'])
    # ic(category_info_dict)
    # hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'index_right', category, 'freshwater')
    #
    # (category_info_dict, category) = add_cat(category_info_dict, "g200_marine", hit_dir, 'g200_marine_hits.tsv',
    #                                          'g200_marine_category', ['marine'])
    # hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'index_right', category, 'freshwater')
    #
    # (category_info_dict, category) = add_cat(category_info_dict, "g200_terr", hit_dir, 'g200_terr_hits.tsv',
    #                                          'g200_terr_category', ['terrestrial'])
    # hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'index_right', category, 'freshwater')
    #
    # (category_info_dict, category) = add_cat(category_info_dict, "g200_terr", hit_dir, 'glwd_1_hits.tsv',
    #                                          'glwd_1_category', ['freshwater'])
    # hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'index_right', category, 'freshwater')
    #
    # (category_info_dict, category) = add_cat(category_info_dict, "glwd_2", hit_dir, 'glwd_2_hits.tsv',
    #                                          'glwd_2_category', ['freshwater'])
    # hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'index_right', 'glwd_2_category',
    #                                  'freshwater')
    #
    # (category_info_dict, category) = add_cat(category_info_dict, "ne_10m_river_lake_line", hit_dir,
    #                                          'ne_10m_river_lake_line_hits.tsv', 'ne_10m_river_lake_line_category',
    #                                          ['freshwater'])
    # hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'index_right', category, 'Lakes')
    # (category_info_dict, category) = add_cat(category_info_dict, "ne_10m_lake", hit_dir, 'ne_10m_lake_hits.tsv',
    #                                          'ne_10m_lake_category', ['freshwater'])
    # hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'index_right', category, 'Lakes')
    # (category_info_dict, category) = add_cat(category_info_dict, "ne_10m_river_aus_line", hit_dir,
    #                                          'ne_10m_rivers_australia_line_hits.tsv',
    #                                          'ne_10m_river_lake_aus_line_category', ['freshwater'])
    # hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'index_right', category, 'Lakes')
    # (category_info_dict, category) = add_cat(category_info_dict, "ne_10m_river_eur_line", hit_dir,
    #                                          'ne_10m_rivers_europe_line_hits.tsv', 'ne_10m_river_eur_line_category',
    #                                          ['freshwater'])
    # hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'index_right', category, 'Lakes')
    # (category_info_dict, category) = add_cat(category_info_dict, "ne_10m_river_nam_line", hit_dir,
    #                                          'ne_10m_rivers_north_america_line_hits.tsv',
    #                                          'ne_10m_river_nam_line_category', ['freshwater'])
    # hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'index_right', category, 'Lakes')
    # (category_info_dict, category) = add_cat(category_info_dict, "ne_50m_lake", hit_dir, 'ne_50m_lakes_hits.tsv',
    #                                          'ne_50m_lake_category', ['freshwater'])
    # hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'index_right', category, 'Lakes')
    # (category_info_dict, category) = add_cat(category_info_dict, "ne_50m_river_lake_line", hit_dir,
    #                                          'ne_50m_river_lake_line_hits.tsv', 'ne_10m_river_lake_line_category',
    #                                          ['freshwater'])
    # hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'index_right', category, 'Lakes')
    #
    (category_info_dict, category) = add_cat(category_info_dict, "hydrosheds", hit_dir, 'feow_hydrosheds_hits.tsv',
                                             'feow_category',
                                             ['freshwater', 'terrestrial'])
    hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'index_right', category, 'hydroshed')
    #
    #
    # #
    # (category_info_dict, category) = add_cat(category_info_dict, "seawater", hit_dir, 'seawater_polygons_hits.tsv',
    #                                          'sea_category', ['marine'])
    # hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'index_right', category, 'seawater')
    # #
    # (category_info_dict, category) = add_cat(category_info_dict, "land", hit_dir, 'land_polygons_hits.tsv',
    #                                          'land_category', ['terrestrial'])
    # hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'index_right', category, 'land')
    # #
    # (category_info_dict, category) = add_cat(category_info_dict, "worldAdmin", hit_dir,
    #                                          'world-administrative-boundaries_hits.tsv', 'worldAdmin_category',
    #                                          ['terrestrial'])
    # hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'region', category, 'land')
    # #
    (category_info_dict, category) = add_cat(category_info_dict, "seaIHO", hit_dir, 'World_Seas_IHO_v3_hits.tsv',
                                              'IHO_category', ['marine'])
    hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'MRGID', category, 'sea')
    # #
    # (category_info_dict, category) = add_cat(category_info_dict, "longhurst", hit_dir, 'longhurst_v4_hits.tsv',
    #                                          'longhurst_category', ['marine'])
    # hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'ProvCode', category, 'blank')
    # #
    (category_info_dict, category) = add_cat(category_info_dict, "eez", hit_dir, 'eez_hits.tsv', 'eez_category',
                                             ['marine'])
    hit_df_dict[category] = clean_df(category_info_dict[category]["hitfile"], 'GEONAME', category, 'EEZ')

    ic(hit_df_dict.keys())
    ic(hit_cats_info.get_domain_cat_dict())
    hit_cats_info.put_category_info_dict(category_info_dict)
    ic(hit_cats_info.get_category_list())

    return (hit_df_dict)


def processTrawlFindings(yes, yes_both_not_eez, no, skip, trawl_count):
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
            if start_lon_minus_found != end_lon_minus_found:
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


def analyse_trawl_data(df_merged_all, df_trawl_samples):
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
                                    df_trawl_samples['lat_end'].apply(str) + "_" + \
                                    df_trawl_samples['external_id'].apply(str)
    df_trawl_samples['actual_end_index'] = df_trawl_samples['end_index']

    """ want to look up each pair of lat/lon starts and sea if they are in the same EEZ as lat/lon ends
    so doing via doing two intersection's """
    df_merged_starts = pd.merge(df_merged_all, df_trawl_samples, how = 'inner', left_on = ['lon', 'lat'],
                                right_on = ['lon_start', 'lat_start'], suffixes = ('', '_y'))

    df_merged_starts = df_merged_starts.set_index('actual_start_index')
    # df_merged_starts = df_merged_starts[df_merged_starts['external_id'].notna()].reset_index()
    ic(df_merged_starts.shape[0])
    ic(df_merged_starts.head(2))

    df_merged_ends = pd.merge(df_merged_all, df_trawl_samples, how = 'inner', left_on = ['lon', 'lat'],
                              right_on = ['lon_end', 'lat_end'], suffixes = ('', '_y'))
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

        try:
            ic("in try for looking up merged_ends")
            ic(row_end_index)
            df = df_merged_ends.loc[[row_end_index]]
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
            df_total_row_num = df.loc[[row['external_id']]].shape[0]
            short_end = []
            if df_total_row_num == 1:
                short_end = df.loc[row['external_id']].to_dict()
            elif df_total_row_num > 1:
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
            local_dict = {'start_coords': start_index, start_key: row[key_name], end_key: short_end[key_name],
                          'end_coords': short_end['end_index']}
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

    processTrawlFindings(yes, yes_both_not_eez, no, skip, count)

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
    if 'GEONAME' in df_merged_all.columns:
        df_merged_all['GEONAME'] = df_merged_all['GEONAME'].astype(str)

        # geoname_list = df_merged_all['GEONAME'].unique()
        # ic(sorted(geoname_list))

    return df_merged_all


def analysis_lat_lon(sample_dir):
    """ analysis_lat_lon
        __params__:
               passed_args: sample_dir
        rtn: df
    """
    ic()

    test_status = True
    df = get_all_ena_detailed_sample_info(test_status)
    cols = ["accession", "lat", "lon"]

    df_filtered = df.loc[df['lat'].notnull()]
    # df_filtered['lat_decimal_len'] = str(df_filtered['lat'])[::-1].find('.')
    # df_filtered['lat_decimal_len'] = len(str(df_filtered['lat']).split(".")[1])
    df_filtered['lat_decimal'] = df_filtered['lat'].astype(str).str.split(".").str[1]
    df_filtered['lat_len'] = df_filtered['lat_decimal'].str.len()

    df_filtered['lon_decimal'] = df_filtered['lon'].astype(str).str.split(".").str[1]
    df_filtered['lon_len'] = df_filtered['lon_decimal'].str.len()

    ic(df_filtered.head(100))

    ic(df_filtered['lat_len'].value_counts())
    df_tmp = df_filtered.drop(columns = ['lat', 'lon']).groupby('lat_len').size().to_frame('count').reset_index()
    ic(df_tmp)

    df_tmp = df_filtered.drop(columns = ['lat', 'lon']).groupby('lon_len').size().to_frame('count').reset_index()
    ic(df_tmp)

    return df


def main():
    """ main takes the "hit" files from the getGeoLocationCategorisation.py files, integrates and plots them
        __params__:
               passed_args
    """
    # analyseFreshwater()
    # sys.exit()

    full_rerun = True

    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()
    #  analysis_lat_lon(sample_dir)
    hit_cats_info = MyHitDataInfo(hit_dir)

    ena_total_sample_count = get_ena_total_sample_count(sample_dir)
    ic(ena_total_sample_count)

    # get all the files processed
    if full_rerun:
        # df_ena = get_all_ena_lat_lon_geo(sample_dir)
        fast_run = True
        pickle_file = analysis_dir + "in_analysis_df_merged_all.pickle"
        if not os.path.isfile(pickle_file) or (fast_run is False):
            hit_df_dict = processHitFiles(hit_dir, hit_cats_info)
            df_merged_all = mergeAndAnalysis(hit_df_dict, hit_dir, hit_cats_info)
            put_pickleObj2File(df_merged_all, pickle_file, True)
        else:
            df_merged_all = get_pickleObj(pickle_file)
        ic(df_merged_all.columns)
        ic(hit_cats_info.get_freshwater_cats())
        ic(hit_cats_info.get_marine_cats())
        category_fields = [match for match in df_merged_all.columns if "category" in match]
        ic(category_fields)
        merged_all_categories_file = analysis(df_merged_all, analysis_dir, plot_dir, hit_cats_info)
        ic("Finished full_rerun, including generation of ", merged_all_categories_file)
    else:
        df_merged_all = pd.read_csv(hit_dir + "merged_all.tsv", sep = "\t")
    df_merged_all = clean_merge_all(df_merged_all)

    merged_all_categories_file = analysis_dir + "merged_all_categories.tsv"
    df_merged_all_categories = pd.read_csv(merged_all_categories_file, sep = "\t")

    get_category_stats(ena_total_sample_count, df_merged_all_categories, df_merged_all)

    analyseFreshwater()

    ic("Finishing before the plotting")
    sys.exit()

    # df_trawl_samples = pd.read_csv(sample_dir + 'sample_trawl_all_start_ends_clean.tsv', sep = "\t")
    # analyse_trawl_data(df_merged_all,df_trawl_samples)

    ic("Do the plotting")
    ''' these are the plotting sections , can comment out all above once they have all they all been run.
        Done so that can save the time etc. of re-running the merging
     '''

    category_plotting(df_merged_all_categories, plot_dir, hit_cats_info, full_rerun)
    ic("Aborting early")
    # sys.exit()
    if full_rerun == False:
        ic("Aborting early")
        sys.exit()
    plot_merge_all(df_merged_all, plot_dir)
    extra_plots(df_merged_all, plot_dir, shape_dir)

    return ()


if __name__ == '__main__':
    ic()

    main()
