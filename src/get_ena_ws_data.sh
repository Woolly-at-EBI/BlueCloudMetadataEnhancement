# script to run ENA web services to get the data for much of the analysis
# This script does a full update! There is an alternative that just does a periodic update
# The data is returned as TSV files in the "sample_dir"
# Peter Woollard, ENA, EMBL-EBI, January 2023


source ./ena_ws_functions.sh

echo "running script=$0"
echo $sample_dir
cd $sample_dir || exit

# curl -X POST -H "Content-Type: application/x-www-form-urlencoded" -d 'result=sample&query=first_public%3E%3D2024-01-01%20AND%20first_public%3C%3D2024-01-02&fields=sample_accession%2Csample_description%2Cfirst_public&limit=10&format=tsv' "https://www.ebi.ac.uk/ena/portal/api/search"
#&fields=accession%2C%20secondary_sample_accession%2C%20description%2C%20checklist%2C%20collection_date%2C%20first_public%2C%20tax_id%2C%20taxonomic_classification%2C%20lat%2C%20%20lon%2C%20country%2C%20depth%2C%20altitude%2C%20elevation%2C%20salinity%2C%20environment_biome%2C%20environment_feature%2C%20environment_material&includeMetagenomes=true&limit=0&result=sample" -H "accept: */*" > $outfile
#echo "accession%2C%20secondary_sample_accession%2C%20description%2C%20checklist%2C%20collection_date%2C%20first_public%2C%20tax_id%2C%20taxonomic_classification%2C%20lat%2C%20%20lon%2C%20country%2C%20depth%2C%20altitude%2C%20elevation%2C%20salinity%2C%20environment_biome%2C%20environment_feature%2C%20environment_material" | sed 's/%2C%20/£/g;s/%20//g' | tr '£' '\n' | sed 's/^/ "/g;s/$/"/g' | tr '\n' ' '

#the most important fields

#the most used file N.B. this takes 90 minutes to download
#outfile="sample_much_raw.tsv"
#echo "From ENA, extract lots of useful columns of data as well as lat lon column: " $outfile
#curl -X GET "https://www.ebi.ac.uk/ena/portal/api/search?dataPortal=ena&dccDataOnly=false&download=false&fields=accession%2C%20secondary_sample_accession%2C%20description%2C%20checklist%2C%20collection_date%2C%20first_public%2C%20tax_id%2C%20taxonomic_classification%2C%20lat%2C%20%20lon%2C%20country%2C%20depth%2C%20altitude%2C%20elevation%2C%20salinity%2C%20environment_biome%2C%20environment_feature%2C%20environment_material&includeMetagenomes=true&limit=0&result=sample" -H "accept: */*" > $outfile
#FullSearchString 10
#curlString=${returnVal}
#echo ${curlString}
#curl -s -X POST -H "Content-Type: application/x-www-form-urlencoded" ${curlString} > $outfile
#to_parquet $outfile &

# cat ../data/samples/downloads/sample_much_raw.tsv | awk -F ',' 'NR == 1 || $9 != "" {print}' | head -3  | cat -n
outfile="all_sample_lat_lon_country.tsv"
echo "From ENA, extract all lat lon column needed for the shapefile: " $outfile
curl -X GET "https://www.ebi.ac.uk/ena/portal/api/search?dataPortal=ena&dccDataOnly=false&download=false&fields=lon%2Clat%2Ccountry&includeMetagenomes=true&limit=0&result=sample" -H "accept: */*" > $outfile
infile=$outfile
outfile="all_sample_lat_longs_present_uniq.tsv"
echo "creating "$outfile" from "$infile
head -1 $infile | cut -f 1,2 > $outfile
# the first uniq reduces the number of lines that need to be sorted
tail +2 $infile | cut -f 1,2 | sed '/^\t$/d' | awk '{if ($1) print $0;}' | awk '{if ($2) print $0;}' | uniq | sort | uniq >> $outfile

outfile="ena_sample_species.txt"
echo "All the species in ENA tax id and scientific_name"
# n.b. did the initial uniq to get rid of many identical rows next to each other, it made the subsequent sort less onerous
curl -X GET "https://www.ebi.ac.uk/ena/portal/api/search?dataPortal=ena&dccDataOnly=false&download=false&fields=tax_id%2Cscientific_name&includeMetagenomes=true&result=sample" -H "accept: */*" | cut -f 1-2 | uniq | sort | uniq > $outfile
to_parquet $outfile &

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


# ---------------------------------------------------------------------------------------------------------
echo "${0}\n script has completed to the end" | mail -s ${0}" has completed" ${emailaddress}
