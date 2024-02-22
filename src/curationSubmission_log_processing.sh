#!/usr/bin/env bash
#"""Script of curationSubmission_log_processing.sh is to process the curation Submission log
# moves the error free JSON submission files to another directory. So that one can then rerun the submission on
# remaining ones.
# usage example: ./curationSubmission_log_processing.sh -f  archive/the_terroritories.script
#
#___author___ = "woollard@ebi.ac.uk"
#___start_date___ = 2024-02-21
#__docformat___ = 'reStructuredText'
#chmod a+x curationSubmission_log_processing.sh
#"""
set -e
################################################################
while getopts f: flag
do
    case "${flag}" in
        f) log_file=${OPTARG};;
    esac
done

################################################################
# Functions
function if_not_dir_create () {
  dir_to_create=$1
  if [ ! -w "$dir_to_create" ]; then
      mkdir $dir_to_create
      echo "created "$dir_to_create
  else
       echo "already exists "$dir_to_create
  fi

  if [ ! -w "$dir_to_create" ]; then
      echo "cannot create "$dir_to_create
      exit
  fi
}


function process () {
  ffn=$1
  echo "####### Processing: "$ffn

  DIR="$(dirname "${ffn}")" ; FILE="$(basename "${ffn}")"
  # echo "[${DIR}] [${FILE}]"
  sa_dir=${DIR}"/submitted_accepted"
  # echo ${sa_dir}
  if_not_dir_create ${sa_dir}
  echo "++++++++++++++++++++++++++++++++++++++"
  # echo $ffn
  file_list=`cat $ffn | sed 's/\r//g' | grep -B1 '"errors":\[\]' | grep -v '"errors":\[\]' |  grep -v '^--' | sed 's/^.*-T //' | tr '\n' ' '`
  # echo $file_list
  echo "file_array:"
  file_array=($file_list)

  # want to move the JSON curation files that had no errors to  ${sa_dir}
  for f in ${file_array[@]}; do
    local_basename="$(basename "${f}")"
    # echo "# examining: ${sa_dir}/${local_basename}"
    if [ ! -e "${sa_dir}/${local_basename}" ]; then
         echo "mv ${f} ${sa_dir}/"
         mv $f ${sa_dir}/
    else
        echo "# already ${f}  in ${sa_dir}/"
    fi
  done
  echo ""
  echo "++++++++++++++++++++++++++++++++++++++"

  }


###

# processing every json file
if [ ! -w "$log_file" ]; then
  echo "$log_file does not exist."
  exit
fi
process $log_file

