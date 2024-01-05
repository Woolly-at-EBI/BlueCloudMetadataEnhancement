#!/usr/bin/env python3
# BlueCloud
"""Script: getGeoLocationCategorisation.py to get the e.g. EEZ classification for a set of longitude and latitude coordinates
 is using GDAL via geopandas lib see:
https://geopandas.org/en/stable/docs/user_guide/data_structures.html#geoseries
https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoSeries.contains.html#geopandas.GeoSeries.contains

example: python3 getGeoLocationCategorisation.py -c /Users/woollard/projects/bluecloud/data/tests/test_lat_lon.tsv\
 -s /Users/woollard/projects/bluecloud/data/shapefiles/World_EEZ_v11_20191118/eez_v11.shp\
 -o /Users/woollard/projects/bluecloud/data/tests/test_EEZ_hits.tsv

N.B. It is significantly quicker if duplicate lat and lon entries are dropped (only 10% of ENA are unique).
DONE : implement internally to remove the lat lon duplicates (and keep just one lat lon if duplicated)

The underlying algorithms appear be O(N) for increases to number of image polygons (=EEZ's) being searched.
The underlying algorithms appear be O(N) for increases to the number of points being searched.

See the analyseHits.py script for merging the hit files and getting a summary etc.

___author___ = "woollard@ebi.ac.uk"
___start_date___ = "2022-11-30"
__docformat___ = 'reStructuredText'

"""
# /opt/homebrew/bin/pydoc3 getGeoLocationCategorisation   #interactive
# python3 -m pydoc -w getGeoLocationCategorisation.py     #to html file

from icecream import ic

import matplotlib.pyplot as plt
import geopandas as gpd
from geopandas.geoseries import *
from shapely.geometry import Point

import argparse
import sys
import os.path
pd.set_option('display.max_columns', None)


def read_shape(shapefile, geo_crs):
    """ read in the shape file
    n.b. it is assumed that the shapefile is using GPS style CRS
    else try a default provided on command line
    __params__:
      shapefile
    __returns__
        my_shape - geopanda object
    """
    ic(f"in read_shape: {shapefile}")
    my_shape = gpd.read_file(shapefile)
    ic(f"# of polygons in shape {len(my_shape.index)}")  # getting the total number of images

    if my_shape.crs is None:
        ic(f"No CRC in shape file so trying: {geo_crs}")
        my_shape = my_shape.set_crs(geo_crs)

    return my_shape


def geo_lon_lat2points_geodf(df, crs_value):
    """
        (points_series, points_geodf) = geo_lon_lat2points_geodf(df, crs_value)
        :param df: that contains lat and lon
        :param crs_value:
        :return: points_series, points_geodf
        """
    ic(f"creating both points GeoSeries and GeoDataFrame with crs_value = {crs_value}")

    df["lat"] = df["lat"].astype(float)
    df["lon"] = df["lon"].astype(float)
    points_series = geopandas.GeoSeries.from_xy(x = df.lon, y = df.lat)
    # points_series.drop_duplicates()  is very slow, so did the dropping in the panda data frames.
    # ic(points_series)
    df['coords'] = list(zip(df['lon'], df['lat']))
    df['coords'] = df['coords'].apply(Point)
    points_geodf = gpd.GeoDataFrame(df, geometry = 'coords', crs = crs_value)
    ic(points_geodf.count())
    ic(points_geodf.sample(n=3))
    return points_series, points_geodf

def create_points_geoseries(coordfile, debug):
    """ create a geoseries of lat and lon as multiple points
     the CRS version is what the EEZ shape file uses. The CRS of shapes and points etc. need to match.
        __params__:
                coordfile [needs to have columns lon and lat]
                debug True or False
        __returns__:
                points_series, points_geodf
    """
    ic()
    crs_value = "EPSG:4326"
    if debug:
        nrow = 10000000
        ic(f"debug={debug} nrows of point coordinates limited to {nrow}")
        df = pd.read_csv(coordfile, sep = '\t', nrows = nrow)
    else:
        df = pd.read_csv(coordfile, sep = '\t')
        ic(f"count of point coordinates = {df.shape[0]}")
    # Select just the specific columns and drop the duplicates, dropping duplicates cuts down much searching
    df = df[['lon', 'lat']]
    df = df.drop_duplicates(keep = 'first', ignore_index = True)
    (points_series, points_geodf) = geo_lon_lat2points_geodf(df, crs_value)

    return points_series, points_geodf


def plotting_hit_points(my_shape, shape_file_name, points_geodf):
    """  simple plot.

        __params__:
                my_shape
                point_in_polys_geod
                points_geodf

        __returns__:

    """
    title = shape_file_name
    ic(title)
    my_shape.plot()
    base = my_shape.boundary.plot(linewidth = 1, edgecolor = "black")
    points_geodf.plot(ax = base, linewidth = 1, color = "blue", markersize = 1, aspect = 1)
    plt.show()


def test_locations(my_shape, points_geodf):
    """ test the lat and lon coordinate
        this is done by polygon searching, using the GDAL libs via GEOPANDAS
         see this for more background to doing this fast  https://www.matecdev.com/posts/point-in-polygon.html
         it is only taking from 10 to 60 seconds.

         The coordinate references system if source and target are checked: if necessary the shapefile coordinates
         are re-projected.
        __params__:
                my_shape
                points_geodf
        __returns__:
                get_locations as df_with_hits
    """
    ic()

    # ic(type(points_series))
    # the points are the columns, the shapes are the row names
    # ic(points_geodf.crs)
    # ic(my_shape.crs)

    if points_geodf.crs != my_shape.crs:
        ic("CRS mismatch so re-projecting the CRS for the shape from: " + my_shape.crs)
        my_shape = my_shape.to_crs(points_geodf.crs)

    # The geo dataframe contains one row per query point, whether there are hits or not
    df_with_hits = gpd.tools.sjoin(points_geodf, my_shape, predicate = "within", how = 'left')

    ic(len(df_with_hits.index))
    return df_with_hits


def process_line_shapes(shape_line_file, points_geodf):
    """

    :param shape_line_file:
    :param points_geodf:
    :return:
    """
    ic()

    ic(shape_line_file)
    features = geopandas.read_file(shape_line_file)
    # get rid of superfluous columns
    columns2drop = [s for s in features.columns if "name_" in s]
    features = features.drop(columns2drop, axis = 1)
    # clean up superfluous columns
    #for col in ['note', 'min_zoom', 'min_label']
    ic(features.head(2))

    # egrep -Ei '(river|fresh)' merged_all_categories.tsv | head -1001 | cut -f 1-3 > test_freshwater_points.tsv
    # egrep -Ei '(river|fresh)' merged_all_categories.tsv  | cut -f 1-3 > test_freshwater_points.tsv
    # test_point_file = "/Users/woollard/projects/bluecloud/analysis/test_freshwater_points.tsv"
    # df_test_points = geopandas.read_file(test_point_file)
    # df_test_points.set_crs(geo_crs)
    # (test_points_series, test_points_geodf) = geo_lon_lat2points_geodf(df_test_points, geo_crs)
    # test_points['geometry'] = test_points["coords"]
    # test_points.set_geometry('geometry')
    # m = test_points_geodf.head(1000)
    # m = test_points_geodf
    # ic(m.head(2))

    if points_geodf.crs != features.crs:
        ic("Warning: the CRS for points and features don't match, so attempting to reproject")
        ic(points_geodf.crs)
        ic(features.crs)

    # reprojecting to metric as want distance in metres
    p = points_geodf.to_crs(crs = 3857)
    ic(f"point total = {points_geodf.shape[0]}")
    ic(p.sample(n = 3))
    features = features.to_crs(crs = 3857)
    max_distance = 5  # was 100
    ic(f"FYI: using max_distance from line = {max_distance} metres")

    df_hits = p.sjoin_nearest(features, how = "inner", distance_col = "distance")
    #implementation error with max_distance, annoying as this increases the run time
    #df_hits = p.sjoin_nearest(features, how = "inner", distance_col = "distance", max_distance = max_distance)
    #as this is not working manually doing
    df_hits['distance'] = df_hits['distance'].round(decimals = 2)
    df_hits = df_hits.query('distance < @max_distance')
    df_hits = df_hits.to_crs(crs = 4326)
    # degree_multiplier=111139
    # hits["distance_metres"] = hits["distance"] * degree_multiplier
    # hits["distance_metres"] = hits["distance_metres"].astype(int)
    ic(f"total hits = {df_hits.shape[0]}")
    ic(df_hits.head())
    ic(df_hits.crs.axis_info[0].unit_name)

    return df_hits


def main(passed_args):
    """ main
        __params__:
               passed_args
    """
    ic()

    debug_status = False
    geo_crc = 'EPSG:4326'
    if passed_args.coordinatesfile:
        coordinates_file = passed_args.coordinatesfile
        shape_file = passed_args.shapefile
        out_filename = passed_args.outfile
        geo_crc = passed_args.geo_crc
    else:
        ic("Testing: as no command line options provided")
        # coordinates_file = "/Users/woollard/projects/bluecloud/data/tests/test_lat_lon.tsv"
        coordinates_file = "/Users/woollard/projects/bluecloud/data/samples/all_sample_lat_longs_present_uniq.tsv"
        shape_file = "/Users/woollard/projects/bluecloud/data/shapefiles/World_EEZ_v11_20191118/eez_v11.shp"
        out_dirname = "/Users/woollard/projects/bluecloud/data/tests/"
        out_filename = out_dirname + "eez_hit.tsv"
        passed_args.typeofcontents = "polygon"

    # if os.path.isfile(out_filename):
    #     ic(f"skipping all processing as {out_filename} exits, uncomment these lines if you want to rerun the hit file")
    #     sys.exit()
    my_shape = read_shape(shape_file, geo_crc)
    (points_series, points_geodf) = create_points_geoseries(coordinates_file, debug_status)

    if passed_args.typeofcontents == "polygon":
        df_hits_geodf = test_locations(my_shape, points_geodf)
    elif passed_args.typeofcontents == "line":
        # line_shape_file = '/Users/woollard/projects/bluecloud/data/shapefiles/natural_earth_vector/10m_physical/ne_10m_rivers_lake_centerlines.shp'
        df_hits_geodf = process_line_shapes(shape_file, points_geodf)
    else:
        ic("ERROR: Can't currently work with{passed_args.typeofcontents }")
        sys.exit()

    print(f"writing to {out_filename}")
    df_hits_geodf.to_csv(out_filename, sep = "\t", index = False)  # actually is all points, but with hits marked
    #plotting_hit_points(my_shape, shape_file, points_geodf)

    return ()


if __name__ == '__main__':
    """
    mainly handles the command line params
    typeofcontents - only polygon and line are currently handled. 
    
    """
    ic()
    # Read arguments from command line
    prog_des = "Script to get any hits to supplied shapefiles for a set of longitude and latitude coordinates"
    parser = argparse.ArgumentParser(description = prog_des)

    # Adding optional argument, n.b. in debugging mode in IDE, had to turn required to false.
    parser.add_argument("-v", "--verbosity", type = int, help = "increase output verbosity", required = False)
    parser.add_argument("-o", "--outfile", help = "Output file", required = False)
    parser.add_argument("-s", "--shapefile", help = "shape file that contains the polygons", required = False)
    parser.add_argument("-c", "--coordinatesfile", help = "Latitude and longitude coordinate file, format=TBD",
                        required = False)
    parser.add_argument("-g", "--geo_crc", help = "geo_crc of the shapefile format=EPSG:4326",
                        required = False)
    parser.add_argument("-t", "--typeofcontents", help = "the type of the shapefile e.g. point, line, polygon",
                        default = "point", required = False)
    parser.parse_args()
    args = parser.parse_args()
    ic(args)
    if args.verbosity:
        ic("verbosity turned on")
    main(args)
