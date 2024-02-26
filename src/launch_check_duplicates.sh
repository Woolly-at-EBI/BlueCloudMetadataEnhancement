#!/usr/bin/env bash
# Script of launch_check_duplicates.sh  runs sample ids throuh analyse_sample_in_clearinghouse.sh
# It is run from check_duplicates_in_all_categories.sh 
# launch_check_duplicates.sh takes as input a file of sample ids and a text file to put the clearinghouse curation ids in.
# By having launch_check_duplicates.sh as a separate script it allows one to run many analyse_sample_in_clearinghouse.sh searches in parallel.
# a key things is that the extra_curations2supress_file[sic] full file path is provided. This and the derived log file is where the curations are put 
# 
#  launch_check_duplicates.sh -i file_of_ids -f extra_curations2supress_file
# ___author___ = "woollard@ebi.ac.uk"
# ___start_date___ = 2024-02-22
# __docformat___ = 'reStructuredText'


usage() { echo "Usage: $0 [-i <sample_ids_2_check_file>] [-f <extra_curations2supress_file>]" 1>&2; exit 1; }


while getopts "i:f:" flag
do
    case "${flag}" in
        i) sample_ids_2_check_file=${OPTARG}
          #echo "sample_ids_2_check_file"
          ((${#sample_ids_2_check_file}  > 2)) || echo "sample_id too short" usage;;
        f) extra_curations2supress_file=${OPTARG}
          #echo "extra_curations2supress_file"
          ((${#extra_curations2supress_file} > 3)) || echo "file name too short" usage;;
        *)
            echo "Unrecognized option '$1'"
            usage ;;
    esac
done


if [ -z "${sample_ids_2_check_file}" ] || [ -z "${extra_curations2supress_file}" ]; then
        echo 'Missing -i or -f' >&2
        usage
fi

function launch_sample_id_check () {
 echo "in launch_sample_id_check"
 echo "file="${sample_ids_2_check_file}
 if ! [ -e ${file} ]; then
    echo "ERROR: $file does not exist"
    exit 1
 fi
 input=${sample_ids_2_check_file}
 total_sample_ids=`wc -l ${sample_ids_2_check_file} | sed 's/^ *//' | cut -d" " -f 1`
 echo ${total_sample_ids}
 count=0
 while IFS= read -r sample_id
   do
     echo "#${count}/${total_sample_ids} ${sample_id}"
     echo "./analyse_sample_in_clearinghouse.sh -i ${sample_id} -f ${extra_curations2supress_file}"
     ./analyse_sample_in_clearinghouse.sh -i ${sample_id} -f ${extra_curations2supress_file}
     count=$((count + 1))
   done < "$input"
}

launch_sample_id_check

