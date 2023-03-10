
# High Level Script Documentation

## Philosophy
Smaller scripts/utilities focused on different aspects 
* get ENA sample data
* run latitude and longitude points against shapefiles to generate hit files
  * multiple shapefile each with specific attributes
  * some "category" overlaps e.g. 4 different ones inform on 
* analysis scripts to merge and combine the above attributes
*  a script to read files generated above to create formatted metadata for submission to the clearinghouse.

These scripts were also used to explore the data and space, hence there were dead-end, thus deprecated scripts as well functions, sorry.

## Table of documentation, the high level docs from pydocs for each script 
| Script                                       | Language | Description                                                                                                                                                                                                                                                                                                      |
|----------------------------------------------|----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| analyseHits.py                               | python   | Script to merge, analyse and plot the hits from getGeoLocationCategorisation.py directories for the hits, samples, analysis, plot etc. are set in "def get_directory_paths" The hits and plot files are additionally manually copied to a google drive shared with Stephane and Josie.                           |
| analysis_count_stats.py                      | python   | Script of analysis_count_stats.py is to analysis the combined output count file from the waterTaxonomyAnalysis.py It is doing some basic stats and comparisons.                                                                                                                                                  |
| categorise_environment.py                    | python   | a set of functions to do high level mappings of the rather variable environment_biome.         The main one to use is:     - process_environment_biome(df)                                                                                                                                                       |
| clearinghouse_objects.py                     | python   | clearinghouse_objects.py  are curation objects used by generate_clearinghouse_submissions.py see the PDF details in https://www.ebi.ac.uk/ena/clearinghouse/api/                                                                                                                                                 |
| convertCSV2parquet.py                        | python   | script to convert tab separated files to parquet format                                                                                                                                                                                                                                                          |
| ena_samples.py                               | python   | a bunch of ena_sample related methods  - get_all_ena_detailed_sample_info  - get_ena_species_count  - get_ena_species_info                                                                                                                                                                                       |
| find_all_gps_samples.py                      | python   | Script to do quick search of ena data warehouse for all samples with GEO locations NOT USED                                                                                                                                                                                                                      |
| generate_clearinghouse_submissions.py        | python   | generating submission JSON from merge of shape hit files and also from waterTaxonomyAnalysis.p       see the PDF details in https://www.ebi.ac.uk/ena/clearinghouse/api/                                                                                                                                         |
| extra_comparisons.py                         | python   | comparisons(venn) and other plots of the combined_designation                                                                                                                                                                                                                                                    |
| getGeoLocationCategorisation.py              | python   | Script to get the e.g. EEZ classification for a set of longitude and latitude coordinates  is using GDAL via geopandas                                                                                                                                                                                           |
| get_directory_paths.py                       | python   | takes a base directory, checks this exists              also sets the directory paths for analysis and plots etc. and checks that these all exist                                                                                                                                                                |
| parseTrawl.py                                | python   | Script to extra long and lat coordinates from sample xml     this has start and end coords                                                                                                                                                                                                                       |
| project_utils.py                             | python   | some utilities needed in several projects                                                                                                                                                                                                                                                                        |
| waterTaxonomyAnalysis.py                     | python   | Script to take the taxonomy environment assignments    and combine them with the output from analyseHits.py    to allow one to get analysis of what is marine or terrestrial/freshwater from different methods                                                                                                   |
| general_analysis.sh                          | bash     | script to get answers to questions best done with bash e.g. latitude and longitude granularity, as panda converts numbers                                                                                                                                                                                        |
| get_ena_ws_data.sh                           | bash     | script to run ENA web services to get the data for much of the analysis #The data is returned as TSV files in the "sample_dir"                                                                                                                                                                                   |
| run_all.sh                                   | bash     | script to run the lat lon coordinates against various shapefiles, using geopandas - the script automatically re-projects if different coordinate reference systems(CRS) are used. # it returns a file one row per coordinate. Additionally annotation from the shapefile is only added if a hit else nowt (NaN). |
| empty_clearinghouse_submission_template.json | json     | empty_clearinghouse_submission_template                                                                                                                                                                                                                                                                          |


## To have new versions of ena_data including new lat and longs
Get the latest data from the ENA portal by running  
* get_ena_ws_data.sh 
Run the coordinates against all the shapefiles
* run_all.sh 
and get the biome regex's all run
* rm $analysis_dir/environment_biome.pickle
* python3 ./categorise_environment.py  

Then run these scripts
* python3 ./analyseHits.py
* python3 ./waterTaxonomyAnalysis.py
* python3 ./extra_comparisons.py 

## Notes about the scripts
Many of the scripts e.g. get_directory_paths.py are utility scripts