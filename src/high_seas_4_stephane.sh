echo "high_seas_4_stephane"
# for a set of sample accession ids needed to know the
data_dir="/Users/woollard/projects/bluecloud/data/samples/may_2025"

target_access_file="target_sample_accession_ids.txt"
#tail +2  highseas-samples-output.csv  | cut -d, -f 1 > $target_access_file
echo "Total of target sample accs="
wc -l $target_access_file

# cut -f 1,9,10 /Users/woollard/projects/bluecloud/data/samples/sample_much_raw.tsv

cut -f 1,9,10 /Users/woollard/projects/bluecloud/data/samples/sample_much_raw.tsv |  grep -v '\t\t' > all_samples_with_lat_lon.tsv