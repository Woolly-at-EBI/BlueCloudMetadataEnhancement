
# script to get answers to questions best done with bash e.g. latitude and longitude granularity, as panda converts numbers
#
# Peter Woollard, ENA, EMBL-EBI, February

#usage:   ./general_analysis.sh [-b basedir]
#if not argument will use the default basedir as below
basedir='/Users/woollard/projects/bluecloud'

while getopts b: flag
do
    case "${flag}" in
        b) basedir=${OPTARG};;
    esac
done

prog=$basedir/src/getGeoLocationCategorisation.py
samples_dir=$basedir/data/samples/
raw_sample_file=$samples_dir/sample_much_raw.tsv
coordinates_file=$samples_dir/all_sample_lat_longs_present.tsv


function analyse_collection_dates () {
  echo "Granularity of GPS coordinates"
  echo "Total number of ENA samples in $raw_sample_file"
  #tail +2 $raw_sample_file | wc -l

  field="collection_date"
  echo " For sample $field"
  echo ""
  tmp_dates_file=$samples_dir"tmp_dates.txt"
  echo $tmp_dates_file
  #cut -f5 $raw_sample_file | tail +2 | sed '/^$/d' > $tmp_dates_file
  echo "Total number of non-null for "$field
  wc -l $tmp_dates_file
  echo "total samples <1900-01-01 in "$tmp_dates_file
  awk '$1<1900-01-01' $tmp_dates_file| wc -l
  echo "  examples"
  awk '$1<1900-01-01' $tmp_dates_file| uniq| head -5
  echo "total samples >2024-01-01 in "$tmp_dates_file
  awk '$1>2024-01-01' $tmp_dates_file | wc -l
  echo "  examples"
  awk '$1>2024-01-01' $tmp_dates_file| uniq| grep -Ev '(2022|2023)' | head -5

  #investigating a few
  #head -1 sample_much_raw.tsv > dodgy_dates_tmp.tx
  #egrep -E '(1897-10-01|0201-03-03|0514-01-01|1300-01-01|1777-08-03)' $raw_sample_file >> dodgy_dates_tmp.txt
}

function analyse_all_lat_lon () {
  echo "Granularity of GPS coordinates"
  echo "Total number of ENA samples:"
  cat $raw_sample_file | wc -l
  echo "Total number of unique coordinates:"
  cat $coordinates_file | wc -l

  echo "For latitude"
  cut -f2 $coordinates_file | tail +2 | sed 's/^[0-9]*\.//' | awk '{print length}' | sort -n | uniq -c
  echo "Median for latitude"
  cut -f2 $coordinates_file| tail +2 | sed 's/^[0-9]*\.//' | awk '{print length}' | sort -n | awk ' { a[i++]=$1; } END { print a[int(i/2)]; }'
  echo "--------"
  echo "For longitude"
  cut -f3 $coordinates_file | tail +2 | sed 's/^[0-9]*\.//' | awk '{print length}' | sort -n | uniq -c
  echo "Median for longitude"
  cut -f3 $coordinates_file | tail +2 | sed 's/^[0-9]*\.//' | awk '{print length}' | sort -n | awk ' { a[i++]=$1; } END { print a[int(i/2)]; }'

}

analyse_collection_dates

# analyse_all_lat_lon