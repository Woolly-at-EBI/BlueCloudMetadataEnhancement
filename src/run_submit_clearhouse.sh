# script to run submit the clearinghouse submissions
# set environment variables and credentials up
source ~/.ayup
url="https://www.ebi.ac.uk/ena/clearinghouse/api/curations"
url="https://wwwdev.ebi.ac.uk/ena/clearinghouse/api/curations"
# if meed to renew the bearer ( the below is for the test):
# curl 'https://explore.api.aai.ebi.ac.uk/auth'  -u $aai_test2_creds > aai_test2_bearer
export aai_test2_bearer_val=`cat /Users/woollard/projects/bluecloud/clearinghouse/docs/aai_test2_bearer`

bearer="Authorization: Bearer $aai_test2_bearer_val"
curation_json_file="/Users/woollard/projects/bluecloud/clearinghouse/submission_data/EEZ:TERRITORY1.json"

echo "bearer: " $bearer

# would not run bre
cmd=`echo curl -X POST \"${url}\" -H \"accept: */*\"  -H \"Content-Type: application/json\"   -H \"${bearer}\"  -d @${curation_json_file}`
echo $cmd
echo $cmd > run_me.sh
sh ./run_me.sh

