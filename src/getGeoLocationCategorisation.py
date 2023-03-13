# BlueCloud
"""Script to get the e.g. EEZ classification for a set of longitude and latitude coordinates
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
        df = pd.read_csv(coordfile, sep = '\t', nrows = nrow)
    else:
        df = pd.read_csv(coordfile, sep = '\t')
    # Select just the specific columns and drop the duplicates, dropping duplicates cuts down much searching
    df = df[['lon', 'lat']]
    df = df.drop_duplicates(keep = 'first', ignore_index = True)

    ic("create points GeoDeries and then GeoDataFrame")
    points_series = geopandas.GeoSeries.from_xy(x = df.lon, y = df.lat)
    # points_series.drop_duplicates()  is very slow, so did the dropping in the panda data frames.
    ic(points_series.count())
    # ic(points_series)
    # reate points GeoDataFrame
    df['coords'] = list(zip(df['lon'], df['lat']))
    df['coords'] = df['coords'].apply(Point)
    points_geodf = gpd.GeoDataFrame(df, geometry = 'coords', crs = crs_value)

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
    base = my_shape.boundary.plot(linewidth = 1, edgecolor = "black")
    points_geodf.plot(ax = base, linewidth = 1, color = "blue", markersize = 1, aspect = 1, title=title)
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
    pd.set_option('display.max_columns', None)

    # ic(type(points_series))
    # the points are the columns, the shapes are the row names
    # ic(points_geodf.crs)
    # ic(my_shape.crs)

    if points_geodf.crs != my_shape.crs:
        ic("CRS mismatch so re-projecting the CRS for the shape")
        my_shape = my_shape.to_crs(points_geodf.crs)

    # The geo dataframe contains one row per query point, whether there are hits or not
    df_with_hits = gpd.tools.sjoin(points_geodf, my_shape, predicate = "within", how = 'left')

    ic(len(df_with_hits.index))
    return df_with_hits


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
    my_shape = read_shape(shape_file, geo_crc)

    if passed_args.typeofcontents == "point":
        (points_series, points_geodf) = create_points_geoseries(coordinates_file, debug_status)
        pointInPolys_geodf = test_locations(my_shape, points_geodf)
        print(f"writing to {out_filename}")
        pointInPolys_geodf.to_csv(out_filename, sep = "\t", index=False)  # actually is all points, but with hits marked
        # plotting_hit_points(my_shape, shape_file, points_geodf)
    else:
        ic("ERROR: Can't currently work with{passed_args.typeofcontents }")
        sys.exit()

    # getting all the ena_coordinates including regions in geometry format for the analysis
    # March 2023 don't think this is still being used ANYWHERE, or how if this is called last so commented! And not
    # all_ena_coordinates_file = '/Users/woollard/projects/bluecloud/data/samples/sample_lat_lon_country_clean.tsv'
    # all_ena_coordinates_file = coordinates_file
    # out_filename = '/Users/woollard/projects/bluecloud/data/samples/sample_lat_lon_country_geometry.tsv'
    # (points_series, points_geodf) = create_points_geoseries(all_ena_coordinates_file)
    # ic(out_filename)
    # points_geodf.to_csv(out_filename, sep = "\t")

    return ()


if __name__ == '__main__':
    """
    mainly handles the command line params
    typeofcontents - only polygon is currently handled. i.e. comparing points with polygons.
      lines e.g. for rivers needs to be done
    
    """
    ic()
    # Read arguments from command line
    prog_des = "Script to get the marine zone classification for a set of longitude and latitude coordinates"
    parser = argparse.ArgumentParser(description = prog_des)

    # Adding optional argument, n.b. in debugging mode in IDE, had to turn required to false.
    parser.add_argument("-v", "--verbosity", type = int, help = "increase output verbosity", required = False)
    parser.add_argument("-o", "--outfile", help = "Output file", required = False)
    parser.add_argument("-s", "--shapefile", help = "shape file that contains the polygons", required = False)
    parser.add_argument("-c", "--coordinatesfile", help = "Latitude and longitude coordinate file, format=TBD",
                        required = False)
    parser.add_argument("-g", "--geo_crc", help = "geo_crc of the shapefile format=EPSG:4326",
                        required = False)
    parser.add_argument("-t", "--typeofcontents", help = "the type of the coordinates file e.g. point, line, polygon",
                        default = "point", required = False)
    parser.parse_args()
    args = parser.parse_args()
    ic(args)
    print(args)
    if args.verbosity:
        print("verbosity turned on")

    # ic(passed_args.coordinatesfile)
    # ic(passed_args.shapefile)
    main(args)
