# script to run submit the clearinghouse submissions
# set environment variables and credentials up
source ~/.ayup
url="https://www.ebi.ac.uk/ena/clearinghouse/api/curations"
url="https://wwwdev.ebi.ac.uk/ena/clearinghouse/api/curations"
# if meed to renew the bearer ( the below is for the test):
bearer_file="bearer_file"
curl 'https://explore.api.aai.ebi.ac.uk/auth'  -u $aai_test2_creds 1> bearer_file 2>/dev/null
export bearerkey=`cat $bearer_file`
#echo $bearerkey

submission_dir="/Users/woollard/projects/bluecloud/clearinghouse/submission_data/full/"
submission_dir="/Users/woollard/projects/bluecloud/clearinghouse/submission_data/test/"

function submit_2_clearinghouse () {

  export curation_json_file=$1
  echo $curation_json_file
  export bearer="Authorization: Bearer $bearerkey"
  #echo $bearer

  # would not run bre
  cmd=`echo curl -X POST \"${url}\" -H \"accept: */*\"  -H \"Content-Type: application/json\"   -H \"${bearer}\"  -T ${curation_json_file}`
  # cmd=`echo echo "ayup"`
  echo $cmd
  echo $cmd > run_me.sh
  time sh ./run_me.sh
  echo ""

}

for file in $submission_dir*.json
do
echo $file
echo $bearer
submit_2_clearinghouse $file
done


curation_json_file="/Users/woollard/projects/bluecloud/clearinghouse/submission_data/IHO-EEZ:intersect_MARREGION.json"


