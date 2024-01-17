#!/usr/bin/env bash
# basic template bash script to run submit the clearinghouse submissions
#
# Peter Woollard, ENA, EMBL-EBI, January 2024
echo " template script to run submit the clearinghouse submissions"
echo "  run: script_name.py dir_path_to_submission_jsons"
echo "  suggestion, before the run: script submission_typescript.log as this will record the output"
echo "  please check the output for an errors, e.g. JSON to fix or resubmit"
echo ""

################################################################
# Functions

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

function submit_2_clearinghouse () {
  export curation_json_file=$1
  echo $curation_json_file
  export bearerkey=`cat $bearer_file`
  export bearer="Authorization: Bearer $bearerkey"
  #echo $bearer
  # -T is needed for big files -d @ is slightly faster and puts it into memory
  cmd=`echo curl -X POST \"${url}\" -H \"accept: */*\"  -H \"Content-Type: application/json\"   -H \"${bearer}\"  -d @${curation_json_file}`
  #could not get to both see the command and execute it, so doing the dirty way via a new file
  echo $cmd
  echo $cmd > run_me.sh
  time sh ./run_me.sh
  echo " "
}

##################################################################################################
##### Configurable portion
# set environment variables and credentials up - this is my local bash (chmod 007 ~/.my_secrets), please contact your IT admin to see whether this is permissible or they have a better solution
#source ~/.my_secrets
source ~/.ayup
#these are the relevant contents of the file
#export my_email_address='great_crested_newt@redbrick.ac.uk'
#export aai_test_user='my_test_username'
#export aai_test_pass='my_test_password'
#export aai_test_creds="${aai_test_user}:${aai_test_pass}"
#export aai_prod_user='my_prod_username'
#export aai_prod_pass='my_prod_password'
#export aai_prod_creds="${aai_prod_user}:${aai_prod_pass}"

submission_dir=$1

TEST=0
if [ $TEST -eq 1 ]; then
  echo "using test credentials and setup"
  url="https://wwwdev.ebi.ac.uk/ena/clearinghouse/api/curations"
  auth_url='https://explore.api.aai.ebi.ac.uk/auth'
  creds=$aai_test2_creds
else
  #PROD
  echo "using production credentials and setup"
  url="https://www.ebi.ac.uk/ena/clearinghouse/api/curations"
  auth_url='https://api.aai.ebi.ac.uk/auth'
  creds=$aai_prod_creds
fi

if [ ! -d $submission_dir ]; then
    echo "${submission_dir}<--is not a valid directory, so exiting"
    exit
fi
echo "submission_dir: -->"${submission_dir}

export bearer_file="bearer_file"
# echo $creds
# if one needs, renew the bearer ( the below is for the test):
#curl 'https://explore.api.aai.ebi.ac.uk/auth'  -u $aai_test2_creds 1> bearer_file 2>/dev/null
#re-running the bearer key frequently as it times out within an hour...

re_run_bearer_file $auth_url $creds
export bearerkey=`cat $bearer_file`
export bearer="Authorization: Bearer $bearerkey"

##################################################################################################
# processing every json file
for file in $submission_dir/*.json
do
    echo $file
    echo $bearer
    submit_2_clearinghouse $file
    sleep 0.1 # wait 0.1 seconds
    re_run_bearer_file $auth_url $creds
done
message_contents="Attempted to process all files in ${submission_dir} . Please do check the logfiles for any errors"
echo ${message_contents} | mail -s "ClearingHouse submission finished" ${my_email_address}
echo "end of script: ${0}"
################################################################################################


