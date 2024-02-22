# script to run submit the clearinghouse submissions
#
# Peter Woollard, ENA, EMBL-EBI, March 2023
echo "script to run submit the clearinghouse submissions"
export usage="  run: script.py -m [test|prod] -d dir_path_to_submission_jsons"
echo "INFO: suggestion, before the run, ensure you capture all the screen output e.g. by: script submission_typescript.log"
echo "#####################################################"

##################################################################################################
##### Configurable portion
# set environment variables and credentials up - this is my local bash (only readable by me), suggest you doing something similar
source bearer_credentials_setup.sh

while getopts m:d: flag
do
    case "${flag}" in
        m) mode=${OPTARG};;
        d) submission_dir=${OPTARG};;
    esac
done

echo "INFO: run_mode=${mode}<--"
echo "INFO: submission_dir=${submission_dir}<--"
original_submission_dir=${submission_dir}
if ! { [ ${mode} = "test" ] || [ ${mode} = "prod" ]; } ; then
  echo "ERROR with the -m parameter: ${usage}"
  exit
fi
if ! { [ ${submission_dir} != "" ] &&  [ -d $submission_dir ]; } ; then
    echo "ERROR with the -d parameter: ${usage}"
    if ! [ -d $submission_dir ]; then
      echo "${submission_dir}<--is not a valid directory, so exiting"
      exit
    fi
    exit
fi
echo "INFO: commandline parameters are apparently correct (well done you!)"

clearinghouse_credentials ${mode}

if [ ${original_submission_dir} != ${submission_dir} ]; then
  echo "WARNING: submission_dir is not what was passed to commandline, currently: ${submission_dir}"
fi

export bearer_file="bearer_file"

# echo $creds
# if need to renew the bearer ( the below is for the test):
#curl 'https://explore.api.aai.ebi.ac.uk/auth'  -u $aai_test2_creds 1> bearer_file 2>/dev/null
#re-running the bearerkey frequently as it times out within an hour

#################################################################################################



function submit_2_clearinghouse () {
  export curation_json_file=$1
  echo $curation_json_file
  export bearerkey=`cat $bearer_file`
  export bearer="Authorization: Bearer $bearerkey"
  #echo $bearer
  # -T is needed for big files -d @ is slightly faster and puts it into memory
  cmd=`echo curl -X POST \"${url}\" -H \"accept: */*\"  -H \"Content-Type: application/json\"   -H \"${bearer}\"  -T ${curation_json_file}`
  # cmd=`echo curl -X POST \"${url}\" -H \"accept: */*\"  -H \"Content-Type: application/json\"   -H \"${bearer}\"  -d @${curation_json_file}`
  #could not get to both see the command and execute it, so doing the dirty way via a new file
  echo $cmd
  run_me_script="run_me_"$$".sh"
  echo $cmd > $run_me_script
  time sh ./$run_me_script
  rm ./$run_me_script
  echo " "
}
#################################################################################################
## starting now to actually run stuff
re_run_bearer_file $auth_url $creds
export bearerkey=`cat $bearer_file`
export bearer="Authorization: Bearer $bearerkey"

file_counter=0
for file in $submission_dir/*.json
do
    echo $file
    echo $bearer
    submit_2_clearinghouse $file
    sleep 0.1 # wait 0.1 seconds to give a break to the curl etc.
    re_run_bearer_file $auth_url $creds
    file_counter=$[$file_counter +1]
done

out_message="submission_dir was ${submission_dir}\ncount of JSON files was: ${file_counter}"
out_message="${out_message}\nsee curation_server_api: ${curation_server_api} and try out some curation ids and also some sample ids you saw in the submission output"
echo ${out_message}
echo $out_message| mail -s "Clearinghouse ${mode} submission finished" woollard@ebi.ac.uk
echo "###########################end of script"


