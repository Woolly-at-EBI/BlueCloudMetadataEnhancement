#!/usr/bin/env bash
# """Script of check_duplicates_in_all_categories.sh is to get all the sample ids
# and check which are in the clearinghouse and which are not.
# if the sample id is in the clearinghouse then call the script to check if has unsuppressed duplicates
# these are captured as pure curation ids in one file and more descriptive info. in a logged file
#
# input are JSON dumps of particular categories from the clearinghouse
#
# This script has been parallelised for ./launch_check_duplicates.sh , to do this need to put the ids into multiple files in a dir.
# Could be automated, but may not need to do it again. Below using 35 input files worked nicely
#  work out how many lines per file needed to split into about 35 streams to run in parallel: bc  532981/35 =15228 lines
# split -l 15228 ../all_sample_ids_2_check.txt ids_
#
# ___author___ = "woollard@ebi.ac.uk"
# ___start_date___ = 2024-02-23
# __docformat___ = 'reStructuredText'

# """
#configuration

set -u
################################################################
# configurations

src_dir="/Users/woollard/projects/bluecloud/src"
dir="/Users/woollard/projects/bluecloud/clearinghouse/high_seas"
dir="/Users/woollard/projects/bluecloud/clearinghouse/high_seas/past_curations_records"
all_sample_ids_2_check_file=${dir}"/curation_ids_2_supress/all_sample_ids_2_check.txt"
all_sample_ids_2_check_tmpfile=${all_sample_ids_2_check_file%.*}"_tmp.txt"

# needed when running first parts of script!
#for file in ${dir}/*.json
#  do
#    echo $file
#  done

echo "logfile="${all_sample_ids_2_check_file}
echo "inside ${dir}"

# Functions

function generate_sample_ids_2_check () {
  json_file=$1
  echo ${json_file}
  cat ${json_file} | jq -s '.[][][]? | .recordId'  | wc -l
  echo "writing sample_ids to ${all_sample_ids_2_check_tmpfile}"
  cat ${json_file} | jq -s '.[][][]? | .recordId' | sed 's/^"//;s/"$//' >> ${all_sample_ids_2_check_tmpfile}

  }

function prepare2generate_sample_ids_2_check () {
  for file in *.json
  do
      generate_sample_ids_2_check $file ${all_sample_ids_2_check_file}
  done
  echo "Ensuring that the ${all_sample_ids_2_check_file} will have unique sample_ids"
  sort --parallel=4  ${all_sample_ids_2_check_tmpfile} | uniq > ${all_sample_ids_2_check_file}
}


function launch_all_sample_id_checks () {
  dir_w_id_files="/Users/woollard/projects/bluecloud/clearinghouse/high_seas/past_curations_records/curation_ids_2_supress/split_all_sample_ids_2_check"
  dir_for_logs=${dir_w_id_files}"/logs"

  if ! [ -d ${dir_for_logs} ]; then
    echo "ERROR: ${dir_for_logs} is not a directory or does not exist"
    exit
  fi

  echo "process all these id files "${dir_w_id_files}
  for file in ${dir_w_id_files}/ids_*
    do
      echo "id_file="${file}
      local_basename="$(basename "${file}")"
      logfile=${dir_for_logs}/${local_basename}".txt"
      echo log=${logfile}
      echo "++++++++++++++++++++++++++++++++++"
      echo ./launch_check_duplicates.sh -i ${file} -f ${logfile}
      echo "++++++++++++++++++++++++++++++++++"
      ./launch_check_duplicates.sh -i ${file} -f ${logfile} &
    done

# echo "in launch_sample_id_check"
# head -100 ${all_sample_ids_2_check_file} > ${all_sample_ids_2_check_tmpfile}
# input=${all_sample_ids_2_check_tmpfile}
# input=${all_sample_ids_2_check_file}
# total_sample_ids=`wc -l ${all_sample_ids_2_check_file} | sed 's/^ *//' | cut -d" " -f 1`
# # echo ${total_sample_ids}
# count=0
# while IFS= read -r sample_id
#   do
#     echo "#${count}/${total_sample_ids} ${sample_id}"
#     # echo "${src_dir}/analyse_sample_in_clearinghouse.sh -i ${sample_id}"
#     ${src_dir}/analyse_sample_in_clearinghouse.sh -i ${sample_id}
#     count=$((count + 1))
#   done < "$input"
}
###



 # cat IHO-EEZ:intersect_MARREGION.json | jq -s '.[][][]? | .recordId'
# processing every json file
# prepare2generate_sample_ids_2_check
launch_all_sample_id_checks