
#script to run the lat lon coordinates against various shapefiles, using geopandas - the script automatically re-projects if different coordinate reference systems(CRS) are used.
# it returns a file one row per coordinate. Additionally annotation from the shapefile is only added if a hit else nowt (NaN).
#Peter Woollard, ENA, EMBL-EBI, December 2022

prog='/Users/woollard/projects/bluecloud/src/getGeoLocationCategorisation.py'
coordinates_file=/Users/woollard/projects/bluecloud/data/tests/test_lat_lon.tsv
coordinates_file=/Users/woollard/projects/bluecloud/data/samples/all_sample_lat_longs_present_uniq.tsv
outdir=/Users/woollard/projects/bluecloud/data/hits
shapefile_dir=/Users/woollard/projects/bluecloud/data/shapefiles

function run_geolocation () {
    shape_file=$1
    out_file=$2
    cmd="time python3 $prog -c $coordinates_file -s $shape_file -o $out_file"
    echo $cmd
    $cmd
}

shape_file=$shapefile_dir/Intersect_EEZ_IHO_v4_2020/Intersect_EEZ_IHO_v4_2020.shp
out_file=$outdir/intersect_eez_iho_hits.tsv
run_geolocation $shape_file  $out_file
exit;

# oprvs_watercourse
shape_file=$shapefile_dir/shape_file/oprvrs_essh_gb/data/WatercourseLink.shp
out_file=$outdir/oprvs_hits.tsv
run_geolocation $shape_file  $out_file

# GEBCO undersea feature names  (zero hits for multiline with the points ) 
shape_file=$shapefile_dir/features/features-multilinestring.shp
out_file=$outdir/GEBCO_undersea_multiline_hits.tsv
run_geolocation $shape_file  $out_file

shape_file=$shapefile_dir/features/features-multipolygon.shp
out_file=$outdir/GEBCO_undersea_polyg_hits.tsv
run_geolocation $shape_file  $out_file

# SeaVoX_sea_areasthis for land (may be rivers too
shape_file=$shapefile_dir/SeaVoX_sea_areas_polygons_v18/SeaVoX_sea_areas_polygons_v18.shp
out_file=$outdir/SeaVox_seaareas_hits.tsv
run_geolocation $shape_file  $out_file

# this for land (may be rivers too)
shape_file=$shapefile_dir/land-polygons-split-4326/land_polygons.shp
out_file=$outdir/land_polygons_hits.tsv
run_geolocation $shape_file  $out_file

# this for sea water
shape_file=$shapefile_dir/water-polygons-split-4326/water_polygons.shp
out_file=$outdir/seawater_polygons_hits.tsv
run_geolocation $shape_file  $out_file

shape_file=$shapefile_dir/world-administrative-boundaries/world-administrative-boundaries.shp
out_file=$outdir/world-administrative-boundaries_hits.tsv
run_geolocation $shape_file  $out_file

shape_file=$shapefile_dir/GIS_hs_snapped/feow_hydrosheds.shp
out_file=$outdir/feow_hydrosheds_hits.tsv
run_geolocation $shape_file  $out_file

shape_file=$shapefile_dir/World_EEZ_v11_20191118/eez_v11.shp
out_file=$outdir/eez_hits.tsv
run_geolocation $shape_file  $out_file

shape_file=$shapefile_dir/longhurst_v4_2010/Longhurst_world_v4_2010.shp
out_file=$outdir/longhurst_v4_hits.tsv
run_geolocation $shape_file  $out_file

shape_file=$shapefile_dir/World_Seas_IHO_v3/World_Seas_IHO_v3.shp
out_file=$outdir/World_Seas_IHO_v3_hits.tsv
run_geolocation $shape_file  $out_file