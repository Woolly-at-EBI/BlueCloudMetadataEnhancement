#script to run ENA web services to get the data for much of the analysis
#The data is returned as TSV files in the "sample_dir"
#Peter Woollard, ENA, EMBL-EBI, January 2023

sample_dir="../data/samples/downloads"
cd $sample_dir || exit

#the most important fields

#the most used file
outfile="sample_much_raw.tsv"
echo "From ENA, extract lots of useful columns of data as well as lat lon column: " $outfile
curl -X GET "https://www.ebi.ac.uk/ena/portal/api/search?dataPortal=ena&dccDataOnly=false&download=false&fields=accession%2C%20secondary_sample_accession%2C%20description%2C%20checklist%2C%20collection_date%2C%20collection_date_submitted%2C%20tax_id%2C%20taxonomic_classification%2C%20lat%2C%20%20lon%2C%20country%2C%20depth%2C%20altitude%2C%20elevation%2C%20salinity%2C%20environment_biome%2C%20environment_feature%2C%20environment_material&includeMetagenomes=true&limit=0&result=sample&sortDirection=asc" -H "accept: */*" > $outfile

exit
outfile="all_sample_lat_lon_country.tsv"
echo "From ENA, extract all lat lon column needed for the shapefile: " $outfile
#curl -X GET "https://www.ebi.ac.uk/ena/portal/api/search?dataPortal=ena&dccDataOnly=false&download=false&fields=lon%2Clat%2Ccountry&includeMetagenomes=true&limit=0&result=sample&sortDirection=asc" -H "accept: */*" > $outfile
infile=$outfile
echo "creating "$outfile" from "$infile
outfile="all_sample_lat_longs_present_uniq.tsv"
head -1 $infile | cut -f 2,3 > $outfile
tail +2 $infile | cut -f 2,3 | sed '/^\t$/d' | sort | uniq >> $outfile

#informative fields
outfile="all_sample_rtn_fields.txt"
echo "all the returned fields for samples: " $outfile
curl 'https://www.ebi.ac.uk/ena/portal/api/returnFields?result=sample'  > $outfile

outfile="all_sample_searchable_fields.txt"
echo "all the searchable fields for samples: " $outfile
curl -X GET "https://www.ebi.ac.uk/ena/portal/api/searchFields?result=sample" -H "accept: */*" > $outfile

outfile="all_study_searchable_fields.txt"
echo "all the searchable fields for study: " $outfile
curl -X GET 'https://www.ebi.ac.uk/ena/portal/api/returnFields?result=study'  -H "accept: */*" > $outfile


outfile="ena_sample_species.txt"
echo "All the species in ENA tax id and scientific_name"
curl -X GET "https://www.ebi.ac.uk/ena/portal/api/search?dataPortal=ena&dccDataOnly=false&download=false&fields=tax_id%2Cscientific_name&includeMetagenomes=true&result=sample&sortDirection=asc" -H "accept: */*" | cut -f 2-3 | uniq | sort | uniq > $outfile