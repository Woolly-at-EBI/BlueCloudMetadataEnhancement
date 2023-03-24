# Pointers to Key Code needed for Productionising Blue Partition Aspect

**Contents:**
<!-- TOC -->
* [Pointers to Key Code needed for Productionising Blue Partition Aspect](#pointers-to-key-code-needed-for-productionising-blue-partition-aspect)
  * [Related Documentation](#related-documentation)
  * [Preparation](#preparation)
    * [get the ENA_sample metadata and in particular lat and lons](#get-the-enasample-metadata-and-in-particular-lat-and-lons)
  * [Lat and Lon Coordinates mapping to shapefile](#lat-and-lon-coordinates-mapping-to-shapefile)
  * [Taxonomy](#taxonomy)
    * [Taxonomy Integration](#taxonomy-integration)
    * [Taxonomy Rules](#taxonomy-rules)
  * [Environment Biome](#environment-biome)
  * [Comparison Rules](#comparison-rules)
* [Testing](#testing)
<!-- TOC -->
## Related Documentation
* [Overview documentation covering all the scripts](script_documentation.md)
* [Testing sample documentation - albeit testing is limited](./testing_samples.md)


## Preparation
### get the ENA_sample metadata and in particular lat and lons
* get_ena_ws_data.sh
  * specific_columns_needed = ["accession", "tax_id", "scientific_name", "lat", "lon", "collection_date", "environment_biome"]
    * main filters: includeMetagenomes=true , dataPortal=ena&dccDataOnly=false
  * get unique lat and lons from ena_sample extract
    * tail +2 $infile | cut -f 2,3 | sed '/^\t$/d' | sort | uniq >> $outfile

## Lat and Lon Coordinates mapping to shapefile
* Choose the limited number of shapefiles and categorise them as marine or terrestrial. The longhurst is marine, elif coastal is "marine&terrestrial"
* getGeoLocationCategorisation.py
  * create_points_geoseries - for the lat and lons, default CRS_format=EPSG:4326
  * read_shape for polygon shapefile -  CRS_format=EPSG:4326 if none provided in shapefile 
  * automatically check CRS of shapefile and points, auto-reproject shapefile if needed
  * df_with_hits = gpd.tools.sjoin(points_geodf, my_shape, predicate = "within", how = 'left')

## Taxonomy
### Taxonomy Integration
  * waterTaxonomyAnalysis.py
    * taxonomy_map_conf_dictionary = get_taxonomy_mapping_confidence_flags
    * get dataframe of NCBI taxid and get_taxonomy_info(taxonomy_dir)
      * infile looks like this
      CBI,NCBI,Pesant (2022),WoRMS,WoRMS,Pesant (2022),Pesant (2022)
```
NCBI taxID,NCBI taxID Name,rule set description,marine,terrestrial or freshwater,NCBI-to-marine,NCBI-to-terrestrial-or-freshwater
78952,,0.993118099,76011,9311,,
2,Bacteria,[direct match],1,1,[is not exclusively],[is not exclusively]
18,Pelobacter,[direct match],1,1,[is not exclusively],[is not exclusively]
19,Syntrophotalea carbinolica,[direct match],1,-,[may be exclusively],[not flagged as]
22,Shewanella,[direct match],1,-,[may be exclusively],[not flagged as]
23,Shewanella colwelliana,[direct match],1,-,[may be exclusively],[not flagged as]
24,Shewanella putrefaciens,[direct match],1,-,[may be exclusively],[not flagged as]
...
```
### Taxonomy Rules
 * foreach sample's NCBI
   * if determining evidence for sample being marine:
     * use infile/dataframe is marine True or False?
   * if determining evidence for sample being terrestrial/freshwater
     * use infile/dataframe is this domain True or False?
   * if True for the particular domain, plug into the taxonomy_map_conf_dictionary
   to decide how to handle the relative weight

## Environment Biome
 * categorise_environment.py - a set of functions to do high level mappings of the rather variable environment_biome
   * input is a unique list 
   * process_environment_biome(df) - calculate and return a dataframe with 2 new fields: environment_biome_hl and environment_biome_hl2
     * N.B. the regex for doing the high-level(hl) took about 20 mins (my implementation is not the most efficient),
     * So I pickled a data frame of every environment_biome to hl, for each new release of ENA samples, if the pickle file is deleted, it will regenerated itself from scratch
     * The mapping of the terms that mapped tp to hl=="terrestrial" to the subcategories of "land" and "freshwater" is done on the fly.
   * Notes:
     * The above process is hierarchical in that one looks for marine first, then marine&terrestrial and then terrestrial. Partly done that as there is the most variability for terrestrial so more patterns to match.
     * What was helping me with hl2(the sub-categorisation) was to use patterns(e.g. pond|stream) and stop patterns(e.g. |\bsea|sea\b|gulf), as it it provided more specificity. May be worth revisiting for the first hl too,
       * Still limits e.g. after be careful with small substrings so worth using word boundaries e.g. "rock pool" is almost certainly marine&terrestrial, but having "rock" as a stop word for terrestrial only, is obviously wrong.

## Comparison Rules
  * waterTaxonomyAnalysis.py
  * The majority of these rules were done using conditional vector operators for speed.
    * if done conditionally per row that gives more sensitivity and control. Also probably simpler to maintain. Although will be slower, could be mitigated by parallelisation.
  * individually for each major domain: marine, marine&terrestrial and terrestrial a call is made
    * done by creating a score, e.g. for marine
      * highest if sample has marine coordinates + taxonomy rules are true for it being marine
      * zero if no evidence for it being marine
      * N.B. use the environment_biome as a nudge up or down if it matches 
      * the score is then mapped to a confidence: high, medium, low, zero
    * e.g. marine&terrestrial
      * highest if sample has coastal/estuarine coordinates and taxonomy rules are true for it being marine and terrestrial
  * Do a combined call to select a single domain, pick the one with the highest confidence. If a tie, preferred marine.
  * Do a score and confidence for freshwater sub-domain (a subset of terrestrial domain as above)
  * Do Blue Partition call where ( combined_call in "marine" or "marine&terrestrial" ) inclusive or ("freshwater")
    * Decision on which domain/sub-domain based on the confidence, if ALL equal preference to "marine&terrestrial", 
    else preference to "marine"

# Testing
* [link to the testing sample documentation - albeit testing is limited](./testing_samples.md)
