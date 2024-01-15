# script with setup and functions ENA web services to get the data for much of the analysis
# gets called from different scripts
# Peter Woollard, ENA, EMBL-EBI, January 2024

echo "--------------------------------------------------------------------------------------"
echo "                inside ena_ws_functions.sh                      "
date
sample_dir="../data/samples/downloads"
src_dir="/Users/woollard/projects/bluecloud/src"

endpoint="https://www.ebi.ac.uk/ena/portal/api/search?dataPortal=ena"
base_search_prefix="${endpoint}&dccDataOnly=false&download=false"
echo "base_search_prefix="$base_search_prefix

base_search_suffix='&includeMetagenomes=true&result=sample'
echo "base_search_suffix="$base_search_suffix

fieldArray=( "accession"  "secondary_sample_accession"  "description"  "checklist"  "collection_date"  "first_public"  "tax_id"  "taxonomic_classification"  "lat"  "lon"  "country"  "depth"  "altitude"  "elevation"  "salinity"  "environment_biome"  "environment_feature"  "environment_material" )
# fieldArray=( "accession"  "first_public" )

function txt2pa_ext() {
   my_filename=$1
   returnVal=`echo $my_filename | sed 's/tsv$/pa/'`
   echo $returnVal
}
function to_parquet() {
  By default, runns the python convertor in the background
  infile=$1
  txt2pa_ext $outfile
  outfile=$returnVal
  echo "creating "$outfile" from "$infile
  python3 $src_dir/convertCSV2parquet.py -i $infile -o $outfile &
}

function ARRAY2URlEncodeString()  {
  # echo "inside ARRAY2URlEncodeString"
  fieldArray=("$@")
#  echo "FIRST:"${fieldArray[@]}
#  echo "SECOND:"${fieldArray[0]}
  bigString=""
  arrayLen=${#fieldArray[@]}
  count=0
  for field in ${fieldArray[@]}; do
     (( count++ ))
     bigString+=${field}
     if [ ${count} -lt ${arrayLen}  ]
        then
         bigString+="%2C%20"    # don't want to append this to the last one
     fi
  done
  returnVal=${bigString}
}
function DateStartEndSearchString()  {
  start="$1"
  end="$2"
  #curl -X POST -H "Content-Type: application/x-www-form-urlencoded" -d 'result=sample
  #&query=first_public%3E%3D2024-01-01%20AND%20first_public%3C%3D2024-01-02&fields=sample_accession%2Csample_description%2Cfirst_public
  #&format=tsv' "https://www.ebi.ac.uk/ena/portal/api/search"
  date_search="first_public%3E%3D"${start}"%20AND%20first_public%3C%3D"${end}
  returnVal=${date_search}
}

function FullSearchString()  {
  limit="$1"
  start="$2"
  end="$3"

  if [ -z "$limit" ]; then  # i.e. no parameter provided
    limit=0
  fi

  # echo "array=""${fieldArray[@]}"
  ARRAY2URlEncodeString "${fieldArray[@]}"
  fieldString=$returnVal
  fieldString=$returnVal
  echo "------------------------------------------------------------------------------"
  echo ${fieldString}

  if [ -n "$start" ]; then
    DateStartEndSearchString "${start_date}" "${end_date}"
    date_search_string="&query="${returnVal}
  else
    date_search_string=""
    echo "warning no date range provided"
  fi

  format="&limit=${limit}&format=tsv"
  # echo ${date_search_string}
  bigString=${base_search_prefix}${date_search_string}"&fields="${fieldString}${base_search_suffix}${format}
  # echo $bigString
  returnVal=${bigString}
}

function searchLastMonthString () {
  limit=$1
  if [ -z "$limit" ]; then  # i.e. no parameter provided
    limit=10
  fi
  echo "limit=$limit"
  start_date=`date -v1d -v-1m "+%Y-%m-%d"`
  end_date=`date -v1d -v-1d "+%Y-%m-%d"`
  echo "searchLastMonth start_date=${start_date} end_date=${end_date}"
  FullSearchString $limit $start_date $end_date
  returnVal=$returnVal
}

function fileRowCount () {
    # returns number of "rows" as in one less than the file line count
    file=$1
    if ! [ -f $file ]; then  # i.e. no parameter provided
       echo "Error: No valid file provided to fileRowCount provided value=${file}"
       exit
    fi
    line_total=`wc -l $file | sed 's/^ *//;s/ .*//'`
    row_total=$(($line_total - 1))
    returnVal=$row_total
}
echo "--------------------------------------------------------------------------------------"