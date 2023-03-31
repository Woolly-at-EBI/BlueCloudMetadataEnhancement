# script to run review some of the clearinghouse submissions
#
# Peter Woollard, ENA, EMBL-EBI, March 2023

typescript_file="typescript.test_submission.txt"
output=`egrep -E '(.json|time)' $typescript_file | grep -v "curl" | uniq | cut -d "," -f 1,7,16,27,32,45,97,101,123,175,256,325,401,555,595,689,723,777,825,968,979 | paste -s -d' \n' - | sed 's/{"timestamp[^,]*//' | sed 's/^[^ ]*\///' | sed 's/[ "]//g;'`
echo $output | grep "split_1\." > ~/tmpdir/hits.csv


while IFS= read -r line
do
    arr_csv+=("$line")
done < ~/tmpdir/hits.csv

echo "Displaying the contents of array mapped from csv file:"
index=0
for record in "${arr_csv[@]}"
do
    #echo "Record at index-${index} : $record"
    echo "echo \"name="`echo $record | cut -d"," -f1`"\""
    rest=`echo $record | cut -d"," -f5,11`
    #echo $rest
    prefix="https://wwwdev.ebi.ac.uk/ena/clearinghouse/api/curations/"
    echo $rest | tr ',' '\n' | awk '{print "curl https://wwwdev.ebi.ac.uk/ena/clearinghouse/api/curations/"$0" 2>/dev/null | jq"}'
    echo " "

	((index++))
done