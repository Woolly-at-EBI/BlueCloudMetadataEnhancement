# script to run submit the clearinghouse submissions
#
# Peter Woollard, ENA, EMBL-EBI, March 2023
echo "script to run submit the clearinghouse submissions"

##################################################################################################
##### Configurable portion
# set environment variables and credentials up - this is my local bash (only readable by me), suggest you doing something similar
source ~/.ayup

TEST=0
if [ $TEST -eq 1 ]; then
  echo "using test credentials and setup"
  url="https://wwwdev.ebi.ac.uk/ena/clearinghouse/api/curations"
  auth_url='https://explore.api.aai.ebi.ac.uk/auth'
  creds=$aai_test2_creds
  submission_dir="/Users/woollard/projects/bluecloud/clearinghouse/submission_data/test/splits/"
  submission_dir="/Users/woollard/projects/bluecloud/clearinghouse/submission_data/full/splits/"
else
  #PROD
  echo "using production credentials and setup"
  url="https://www.ebi.ac.uk/ena/clearinghouse/api/curations"
  auth_url='https://api.aai.ebi.ac.uk/auth'
  creds=$aai_prod_creds
  submission_dir="/Users/woollard/projects/bluecloud/clearinghouse/submission_data/full/splits/"
fi
export bearer_file="bearer_file"
# echo $creds
# if meed to renew the bearer ( the below is for the test):
#curl 'https://explore.api.aai.ebi.ac.uk/auth'  -u $aai_test2_creds 1> bearer_file 2>/dev/null
#re-running the bearerkey frequently as it times out within an hour


##################################################################################################
echo "submission_dir: "$submission_dir

function re_run_bearer_file () {
  auth_url=$1
  credentials=$2
  echo "curl $auth_url" -u "$credentials"
  echo $bearer_file
  curl "$auth_url" -u "$credentials" 1> $bearer_file 2>/dev/null
  bearerkey=`cat $bearer_file`
  len=${#bearerkey}
  if [ $len -lt 100 ]; then
    echo "Invalid bearer key, so exiting script, try later."
    exit
  fi
  }

re_run_bearer_file $auth_url $creds
export bearerkey=`cat $bearer_file`
export bearer="Authorization: Bearer $bearerkey"

function submit_2_clearinghouse () {
  export curation_json_file=$1
  echo $curation_json_file
  export bearerkey=`cat $bearer_file`
  export bearer="Authorization: Bearer $bearerkey"
  #echo $bearer
  # -T is needed for big files -d @ is slightly faster and puts it into memoru
  cmd=`echo curl -X POST \"${url}\" -H \"accept: */*\"  -H \"Content-Type: application/json\"   -H \"${bearer}\"  -T ${curation_json_file}`
  cmd=`echo curl -X POST \"${url}\" -H \"accept: */*\"  -H \"Content-Type: application/json\"   -H \"${bearer}\"  -d @${curation_json_file}`
  #could not get to both see the command and execute it, so doing the dirty way via a new file
  echo $cmd
  echo $cmd > run_me.sh
  time sh ./run_me.sh
  echo " "

}

for file in $submission_dir/*.json
do
    echo $file
    echo $bearer
    submit_2_clearinghouse $file
    sleep 0.1 # wait 0.1 seconds
    re_run_bearer_file $auth_url $creds
done

#end of script


