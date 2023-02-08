

# script to get answers to questions best done with bash
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


analyse_all_lat_lon