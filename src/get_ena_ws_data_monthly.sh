#script to run ENA web services to get the data for much of the analysis
#The data is returned as TSV files in the "sample_dir"
#Peter Woollard, ENA, EMBL-EBI, January 2023


source ./ena_ws_functions.sh

echo "running script=$0"
echo $sample_dir
cd $sample_dir || exit

# limit is the maximum number of samples to return, if limit is 0 or undefined, returns all
limit=5
searchLastMonthString $limit
echo "______________________________"
curlString=$returnVal
# the start_date and end_date variables are created in the searchLastMonthString function
outfile="sample_much_raw${start_date}_${end_date}.tsv"
echo "${curlString} ${outfile}"
echo "searchLastMonth start_date=${start_date} end_date=${end_date}"
curl -s -X POST -H "Content-Type: application/x-www-form-urlencoded" ${curlString} > $outfile
fileRowCount $outfile
row_count=$returnVal
echo "row_count=${row_count} in ${outfile}"

echo "generating parquet file in the background"
to_parquet $outfile




exit