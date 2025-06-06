
#!/usr/bin/env python3
# script to run the lat lon coordinates against various shapefiles, using geopandas - the script automatically re-projects if different coordinate reference systems(CRS) are used.
# it returns a file one row per coordinate. Additionally annotation from the shapefile is only added if a hit else nowt (NaN).
# key thing to check is the EPSG coding system for the shape file and to specify that on the command line
# Peter Woollard, ENA, EMBL-EBI, December 2022

#usage:   ./run_all.sh [-b basedir]
#if not argument will use the default basedir as below

basedir='/Users/woollard/projects/bluecloud'
while getopts b: flag
do
    # shellcheck disable=SC2220
    case "${flag}" in
        b) basedir=${OPTARG};;
    esac
done

prog=$basedir/src/getGeoLocationCategorisation.py
# coordinates_file=$basedir/data/tests/test_lat_lon.tsv
coordinates_file=$basedir/data/samples/all_sample_lat_longs_present_uniq.tsv
outdir=$basedir/data/hits
shapefile_dir=$basedir/data/shapefiles

if [ -f "$prog" ]
then
    echo "Path of $prog is found."
else
    echo "Error: Path to $prog does not exist"
    exit;
fi

function run_geolocation () {
    shape_file=$1
    out_file=$2
    geo_crc=$3
    shape_type=$4
    cmd="time python3 $prog -c $coordinates_file -s $shape_file -t $shape_type -g $geo_crc -o $out_file"
    echo "$cmd"
    $cmd
    echo "*****************************************************\n\n"
}

function run_polygon_geolocation () {
    run_geolocation $1 $2 $3 "polygon"
}

function run_line_geolocation () {
    run_geolocation $1 $2 $3 "line"
}


geo_crc="EPSG:4326"

echo "Natural Earth <----------------------------------------------------------"
run_line_geolocation "$shapefile_dir/natural_earth_vector/10m_physical/ne_10m_lakes.shp"  "$outdir/ne_10m_lake_hits.tsv" "$geo_crc"
shape_file=$shapefile_dir/natural_earth_vector/50m_physical/ne_50m_lakes.shp
out_file=$outdir/ne_50m_lakes_hits.tsv
run_polygon_geolocation "$shape_file"  "$out_file" "$geo_crc"

run_line_geolocation "$shapefile_dir/natural_earth_vector/50m_physical/ne_50m_rivers_lake_centerlines.shp"  "$outdir/ne_50m_river_lake_line_hits.tsv" "$geo_crc"
run_line_geolocation "$shapefile_dir/natural_earth_vector/10m_physical/ne_10m_rivers_lake_centerlines.shp"  "$outdir/ne_10m_river_lake_line_hits.tsv" "$geo_crc"
run_line_geolocation "$shapefile_dir/natural_earth_vector/10m_physical/ne_10m_rivers_australia.shp"  "$outdir/ne_10m_rivers_australia_line_hits.tsv" "$geo_crc"
run_line_geolocation "$shapefile_dir/natural_earth_vector/10m_physical/ne_10m_rivers_europe.shp"  "$outdir/ne_10m_rivers_europe_line_hits.tsv" "$geo_crc"
run_line_geolocation "$shapefile_dir/natural_earth_vector/10m_physical/ne_10m_rivers_north_america.shp"  "$outdir/ne_10m_rivers_north_america_line_hits.tsv" "$geo_crc"
run_line_geolocation "$shapefile_dir/wise_large_rivers/Large_rivers.shp"  "$outdir/wise_large_rivers_line_hits.tsv" "ETRS89"

echo "wwf_global200ecoregions <----------------------------------------------------------"
run_polygon_geolocation "$shapefile_dir/wwf_global200ecoregions/g200_fw.shp"  "$outdir/g200_fw_hits.tsv" "$geo_crc"
run_polygon_geolocation "$shapefile_dir/wwf_global200ecoregions/g200_marine.shp"  "$outdir/g200_marine_hits.tsv" "$geo_crc"
run_polygon_geolocation "$shapefile_dir/wwf_global200ecoregions/g200_terr.shp"  "$outdir/g200_terr_hits.tsv" "$geo_crc"



echo "wwf_GLWD  <----------------------------------------------------------"
#wwf_GLWD_level1
shape_file=$shapefile_dir/wwf_GLWD_level1/glwd_1.shp
out_file=$outdir/glwd_1_hits.tsv
run_polygon_geolocation "$shape_file"  "$out_file" "$geo_crc"

shape_file=$shapefile_dir/wwf_GLWD_level2/glwd_2.shp
out_file=$outdir/glwd_2_hits.tsv
run_polygon_geolocation "$shape_file"  "$out_file" "$geo_crc"

echo "marine: Intersect_EEZ_IHO : Intersect_EEZ_IHO  <----------------------------------------------------------"
#marine: Intersect_EEZ_IHO : Intersect_EEZ_IHO
shape_file=$shapefile_dir/Intersect_EEZ_IHO_v4_2020/Intersect_EEZ_IHO_v4_2020.shp
out_file=$outdir/intersect_eez_iho_hits.tsv
run_polygon_geolocation "$shape_file"  "$out_file" "$geo_crc"

#terrestrial: oprvs_watercourse : freshwater use cases ( have no hits, and not currently using)
#shape_file=$shapefile_dir/oprvrs_essh_gb/data/WatercourseLink.shp
#out_file=$outdir/oprvs_hits.tsv
#run_polygon_geolocation "$shape_file"  "$out_file" "EPSG:22700"

#marine: GEBCO_undersea_multiline : GEBCO undersea feature names  (zero hits for multiline with the points - not currently using)
shape_file=$shapefile_dir/features/features-multilinestring.shp
out_file=$outdir/GEBCO_undersea_multiline_hits.tsv
run_line_geolocation "$shape_file"  "$out_file" "$geo_crc"

#marine: : GEBCO_undersea_polyg : ? ( fails during running)
#shape_file=$shapefile_dir/features/features-multipolygon.shp
#out_file=$outdir/GEBCO_undersea_polyg_hits.tsv
#run_polygon_geolocation "$shape_file"  "$out_file" "$geo_crc"

#marine: SeaVoX_sea_areas: if in sea (name of?)
shape_file=$shapefile_dir/SeaVoX_sea_areas_polygons_v18/SeaVoX_sea_areas_polygons_v18.shp
out_file=$outdir/SeaVox_seaareas_hits.tsv
run_polygon_geolocation "$shape_file"  "$out_file" "$geo_crc"

#terrestrial: land-polygons : this for land (may be rivers too)
shape_file=$shapefile_dir/land-polygons-split-4326/land_polygons.shp
out_file=$outdir/land_polygons_hits.tsv
run_polygon_geolocation "$shape_file"  "$out_file" "$geo_crc"

#marine: water_polygons: if in sea
shape_file=$shapefile_dir/water-polygons-split-4326/water_polygons.shp
out_file=$outdir/seawater_polygons_hits.tsv
run_polygon_geolocation "$shape_file"  "$out_file" "$geo_crc"

#terrestrial: world-administrative-boundaries : if in a countries and name of
shape_file=$shapefile_dir/world-administrative-boundaries/world-administrative-boundaries.shp
out_file=$outdir/world-administrative-boundaries_hits.tsv
run_polygon_geolocation "$shape_file"  "$out_file" "$geo_crc"

#terrestrial/freshwater: feow_hydrosheds : if in hydroshed
shape_file=$shapefile_dir/GIS_hs_snapped/feow_hydrosheds.shp
out_file=$outdir/feow_hydrosheds_hits.tsv
run_polygon_geolocation "$shape_file"  "$out_file" "$geo_crc"

#marine: World_EEZ : if in an EEZ and name of
shape_file=$shapefile_dir/World_EEZ_v12_20231025/eez_v12.shp
out_file=$outdir/eez_hits.tsv
run_polygon_geolocation "$shape_file"  "$out_file" "$geo_crc"

#marine: Longhurst_world : types of marine regions
shape_file=$shapefile_dir/longhurst_v4_2010/Longhurst_world_v4_2010.shp
out_file=$outdir/longhurst_v4_hits.tsv
run_polygon_geolocation "$shape_file"  "$out_file" "$geo_crc"

#marine: World_Seas_IHO : if in sea and names of seas
shape_file=$shapefile_dir/World_Seas_IHO_v3/World_Seas_IHO_v3.shp
out_file=$outdir/World_Seas_IHO_v3_hits.tsv
run_polygon_geolocation "$shape_file"  "$out_file" "$geo_crc"
