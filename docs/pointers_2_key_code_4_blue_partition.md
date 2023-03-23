# Pointers to Key Code needed for Productionising Blue Partition

## General
[script docs](script_documentation.md)


## Preparation
### get the ENA_sample metadata and in particular lat and lons
* get_ena_ws_data.sh
  * specific_columns_needed = ["accession", "tax_id", "scientific_name", "lat", "lon", "collection_date", "environment_biome"]
    * main filters: includeMetagenomes=true , dataPortal=ena&dccDataOnly=false
  * get unique lat and lons from ena_sample extract
    * tail +2 $infile | cut -f 2,3 | sed '/^\t$/d' | sort | uniq >> $outfile

## Lat and Lon Coordinates mapping to shapefile
 
* getGeoLocationCategorisation.py
  * create_points_geoseries - for the lat and lons, default CRS_format=EPSG:4326
  * read_shape for polygon shapefile - provide CRS_format=EPSG:4326 if none provided in shapefile 
  * automatically check CRS of shapefile and points, auto-reproject shapefile if needed
  * df_with_hits = gpd.tools.sjoin(points_geodf, my_shape, predicate = "within", how = 'left')

## Taxonomy

### Taxonomy Integration

### Taxonomy Rules

## Environment Biome

### ?

### Pointers to regex

## ?