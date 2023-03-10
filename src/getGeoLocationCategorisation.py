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
from shapely.geometry import Polygon, Point

import argparse
import sys


def read_shape(shapefile, geo_crs):
    """ read in the shape file
    n.b. it is assumed that the shapefile is using GPS style CRS
    __params__:
      shapefile
    __returns__
         eez_shape - geopanda object
    """

    my_shape = gpd.read_file(shapefile)
    ic(f"finished reading my_shape{shapefile}")
    ic(f"# of polygons in shape {len(my_shape.index)}")  # getting the total number of images

    if my_shape.crs == None:
        ic(f"No CRC in shape file so trying: {geo_crs}")
        my_shape = my_shape.set_crs(geo_crs)

    pd.set_option('display.max_columns', None)
    # ic(eez_shape.head(1))
    # plt = eez_shape.plot()
    return my_shape


def old_test_location(eez_shape, lat, lon):
    """ Not being used"""
    ic(lat)
    ic(lon)

    ic(eez_shape.head(5))
    # see http://www.wvview.org/os_gisc/python/python_spatial/site/

    p1 = Point([1, 1])
    p2 = Point([100, 100])
    p3 = Point([1, 1.5])
    p4 = Point([1, 1])
    # points = GeoSeries([p1, p2, p3, p4])

    # poly = GeoSeries([Peez_v11.shpolygon([(0, 0), (0, 2), (2, 2), (2, 0)])])
    poly = Polygon([(0, 0), (0, 2), (2, 2), (2, 0)])
    ic(poly)
    ic(poly.centroid)
    ic(p1)
    ic(p1.within(poly))  # https://automating-gis-processes.github.io/CSC18/lessons/L4/point-in-polygon.html
    ic(p2)
    ic(p2.within(poly))
    ic(p3)
    ic(p3.within(poly))
    ic(p4)
    ic(p4.within(poly))


def create_points_geoseries(coordfile):
    """ create a geoseries of lat and lon as multiple points
     the CRS version is what the EEZ shape file uses. The CRS of shapes and points etc. need to match.
        __params__:
                coordfile [needs to have columns lon and lat]
        __returns__:
                points_series, points_geodf
    """
    ic()
    crs_value = "EPSG:4326"
    nrow = 10000000
    # ic(nrow)
    df = pd.read_csv(coordfile, sep = '\t', nrows = nrow)
    ic(df.head())

    # Select just the specific columns and drop the duplicates, dropping duplicates cuts down much searching
    df = df[['lon', 'lat']]
    df = df.drop_duplicates(keep = 'first', ignore_index = True)

    # ic("create GeoDataFrame")
    # points_gdf = geopandas.GeoDataFrame(
    #     df, geometry=geopandas.points_from_xy(x=df.lon, y=df.lat), crs=crs_value
    # )
    # ic(points_gdf.head(3))
    ic("create points geoseries")
    points_series = geopandas.GeoSeries.from_xy(x = df.lon, y = df.lat)
    # points_series.drop_duplicates()  is very slow, so did the dropping in the panda data frames.
    ic(points_series.count())
    # ic(points_series)

    ic("Create points GeoDataFrame")
    df['coords'] = list(zip(df['lon'], df['lat']))
    df['coords'] = df['coords'].apply(Point)
    points_geodf = gpd.GeoDataFrame(df, geometry = 'coords', crs = crs_value)

    ic(points_geodf.head(2))

    return points_series, points_geodf


def add_eez_details(eez_shape, points_series, df):
    """ add_eez_details for any hit points. Only hit points are returned.

    DEPRECATED
        __params__:
                eez_shape   -used to get the EEZ etc. details
                points_series  -used to get the lat and lon from
                df (data frame matrx of all the hits
        __returns__:
                df_eez_hit_points - lat lon coordinates of any hits and some eez details
    """
    ic()
    # ic(df)

    # find all point i.e. columns that are True as in they are in an EEZ
    # and give the EZZ details

    true_columns = df.columns[df.eq(True).any()]
    # ic(true_columns)
    df_eez_hit_points = pd.DataFrame()
    for hit_point in true_columns:
        # ic(hit_point)
        point = points_series[hit_point]
        row_hits = df.index[df[hit_point]].tolist()
        for row_hit in row_hits:
            image_row = eez_shape.loc[row_hit]
            # ic(eez_shape.loc[row_hit])
            tmp_df = pd.DataFrame({
                'lat': point.y,
                'lon': point.x,
                'MRGID': image_row['MRGID'],
                'GEONAME': image_row['GEONAME'],
                'TERRITORY1': image_row['TERRITORY1']}, index = [0])
            # ic(tmp_df)
            df_eez_hit_points = pd.concat([df_eez_hit_points, tmp_df], ignore_index = True)
    # ic(df_eez_hit_points)
    return df_eez_hit_points


def plotting_eez_points(eez_shape, point_in_polys_geodf, points_geodf):
    """ add_eez_details for any hit points. Only hit points are returned.

    DEPRECATED
        __params__:
                eez_shape   -used to get the EEZ etc. details
                point_in_polys_geod
                points_geodf

        __returns__:

    """
    ic(point_in_polys_geodf.head())
    ic("base plot")
    base = eez_shape.boundary.plot(linewidth = 1, edgecolor = "black")
    # ic("points_geodf.plot")
    # ic(points_geodf.head(2))
    #
    # quit()
    # ic("pointsInEEZ_geodf")
    ic(point_in_polys_geodf.ISO_SOV1 == 'USA')
    ic(points_geodf[point_in_polys_geodf.ISO_SOV1 == 'USA'])
    # pointsInEEZ_geodf = points_geodf[~point_in_polys_geodf['MRGID'].isnull()]
    # quit()
    # ic(pointsInEEZ_geodf.head(2))
    # N.b. if can have multiple plots over each other!
    # pointsInEEZ_geodf.plot(ax = base, linewidth = 1, color = "red", markersize = 8, aspect=1)
    points_geodf.plot(ax = base, linewidth = 1, color = "blue", markersize = 1, aspect = 1)
    plt.show()


def test_locations(my_shape, points_series, points_geodf):
    """ test the lat and lon coordinate
        this is done by polygon searching, using the GDAL libs via GEOPANDAS
         see this for more background to doing this fast  https://www.matecdev.com/posts/point-in-polygon.html
         it is only taking from 10 to 60 seconds.

         The coordinate references system if source and target are checked: if necessary the shapefile coordinates
         are re-projected.
        __params__:
                my_shape
                points_series
                points_geodf
        __returns__:
                get_locations as point_in_polys_geodf
    """
    ic()
    pd.set_option('display.max_columns', None)
    # ic(eez_shape.head(1))
    ic(points_series.head(3))
    # ic(type(points_series))
    # tmp_df = points_series.to_frame()
    # tmp_df = tmp_df.rename(columns = {0: 'geometry'}).set_geometry('geometry')
    # ic(tmp_df.head())

    # the points are the columns, the shapes are the rownames, True recorded if matches
    ic("run the eez_shape.contains(point)")
    # this loop works but is slow.
    # matches_df = pd.concat([eez_shape.contains(point) for point in points_series], axis=1)
    # matches_df = pd.concat([tmp_df.apply(lambda row: eez_shape.contains(row), axis=1)])
    # ic(points_series.head())
    # matches_df = points_series.apply(lambda point: eez_shape.contains(point))
    # ic(matches_df)
    # ic(type(matches_df))

    # ic(points_geodf.crs)
    # ic(my_shape.crs)

    if points_geodf.crs != my_shape.crs:
        ic("CRS mismatch so re-projecting the CRS for the shape")
        my_shape = my_shape.to_crs(points_geodf.crs)

    df = gpd.tools.sjoin(points_geodf, my_shape, predicate = "within", how = 'left')
    # the above geo dataframe contains one row per query point. So pick on points not matched, by checking GEONAME,
    # to ignore those for now
    # point_in_polys_geodf = df[df['GEONAME'].notna()]
    pointInPolys_geodf = df

    ic(len(pointInPolys_geodf.index))
    return pointInPolys_geodf


def main(passed_args):
    """ main
        __params__:
               passed_args
    """
    ic()

    # defaults if not specified on the command line
    # coordinates_file = "/Users/woollard/projects/bluecloud/data/tests/test_lat_lon.tsv"
    # coordinates_file = "/Users/woollard/projects/bluecloud/data/samples/all_sample_lat_longs_present.tsv"
    coordinates_file = "/Users/woollard/projects/bluecloud/data/samples/all_sample_lat_longs_present_uniq.tsv"
    # coordinates_file = "/Users/woollard/projects/bluecloud/data/tests/American_Somoa_some_points.tsv"
    shape_file = "/Users/woollard/projects/bluecloud/data/shapefiles/World_EEZ_v11_20191118/eez_v11.shp"
    # shape_file = "/Users/woollard/projects/bluecloud/data/tests/eez_top.shp"
    out_dirname = "/Users/woollard/projects/bluecloud/data/tests/"
    out_filename = out_dirname + "eez_hit.tsv"
    if passed_args.coordinatesfile:
        coordinates_file = passed_args.coordinatesfile
    if passed_args.shapefile:
        shape_file = passed_args.shapefile
    if passed_args.outfile:
        out_filename = passed_args.outfile
    if passed_args.geo_crc:
         geo_crc = passed_args.geo_crc
    ic(coordinates_file)
    ic(shape_file)
    ic(out_filename)

    eez_shape = read_shape(shape_file, geo_crc)

    ic(passed_args.typeofcontents)
    if passed_args.typeofcontents == "point":
        (points_series, points_geodf) = create_points_geoseries(coordinates_file)
        pointInPolys_geodf = test_locations(eez_shape, points_series, points_geodf)
        print(f"writing to {out_filename}")
        pointInPolys_geodf.to_csv(out_filename, sep = "\t")
        # plotting_eez_points(eez_shape, point_in_polys_geodf, points_geodf)
    elif passed_args.typeofcontents == "line":
        ic()

    # getting all the ena_coordinates including regions in geometry format for the analysis
    #all_ena_coordinates_file = '/Users/woollard/projects/bluecloud/data/samples/sample_lat_lon_country_clean.tsv'
    all_ena_coordinates_file = coordinates_file
    out_filename = '/Users/woollard/projects/bluecloud/data/samples/sample_lat_lon_country_geometry.tsv'
    (points_series, points_geodf) = create_points_geoseries(all_ena_coordinates_file)
    ic(out_filename)
    points_geodf.to_csv(out_filename, sep = "\t")

    return ()


if __name__ == '__main__':
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
    parser.add_argument("-g", "--geo_crc", help = "geo_crc of the shapefile format=TBD",
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

