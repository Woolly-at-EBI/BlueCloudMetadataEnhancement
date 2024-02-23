#!/usr/bin/env bash
# """Script of check_duplicates_in_all_categories.sh is to get all the sample ids
# and check which are in the clearinghouse and which are not.
# if the sample id is in the clearinghouse then call the script to check if has unsuppressed duplicates
# these are captured as pure curation ids in one file and more descriptive info. in a logged file
#
# input are JSON dumps of particular categories from the clearinghouse

#
# ___author___ = "woollard@ebi.ac.uk"
# ___start_date___ = 2024-02-23
# __docformat___ = 'reStructuredText'

# """
#configuration

set -e
################################################################
# configurations
src_dir="/Users/woollard/projects/bluecloud/src"
dir="/Users/woollard/projects/bluecloud/clearinghouse/high_seas"
dir="/Users/woollard/projects/bluecloud/clearinghouse/high_seas/past_curations_records"
all_sample_ids_2_check_file=${dir}"/curation_ids_2_supress/all_sample_ids_2_check.txt"
all_sample_ids_2_check_tmpfile=${dir}"/curation_ids_2_supress/all_sample_ids_2_check_tmp.txt"

echo "logfile="${all_sample_ids_2_check_file}
cd $dir
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


function launch_sample_id_check () {
 echo "in launch_sample_id_check"
 head -100 ${all_sample_ids_2_check_file} > ${all_sample_ids_2_check_tmpfile}
 input=${all_sample_ids_2_check_tmpfile}
 input=${all_sample_ids_2_check_file}
 total_sample_ids=`wc -l ${all_sample_ids_2_check_file} | sed 's/^ *//' | cut -d" " -f 1`
 # echo ${total_sample_ids}
 count=0
 while IFS= read -r sample_id
   do
     echo "#${count}/${total_sample_ids} ${sample_id}"
     # echo "${src_dir}/analyse_sample_in_clearinghouse.sh -i ${sample_id}"
     ${src_dir}/analyse_sample_in_clearinghouse.sh -i ${sample_id}
     count=$((count + 1))
   done < "$input"
}
###



 # cat IHO-EEZ:intersect_MARREGION.json | jq -s '.[][][]? | .recordId'
# processing every json file
# prepare2generate_sample_ids_2_check
launch_sample_id_check