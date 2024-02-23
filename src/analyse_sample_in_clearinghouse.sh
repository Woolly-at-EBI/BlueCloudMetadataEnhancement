#!/usr/bin/env bash
# """Script of /Users/woollard/analyse_sample_in_clearinghouse.sh is
# to evaluate a single sample id. If this has curations it then goes on to
# see if these are duplicated for an attribute, and then creates a file of all the curation ids to suppress.
# in theory there should never be duplicates allowed in the clearinghouse, but... I keep finding them in stuff I have submitted. mea culpa?
#
#  ./analyse_sample_in_clearinghouse.sh -i SAMEA7015079
# ___author___ = "woollard@ebi.ac.uk"
# ___start_date___ = 2024-02-22
# __docformat___ = 'reStructuredText'

# """
#configuration
while getopts di: flag
do
    case "${flag}" in
        d) directory=${OPTARG};;
        i) input_sample_id=${OPTARG};;
    esac
done

# trivial QC test...
if [ ${#input_sample_id} -lt 10 ]; then
  echo "It is unlikely that your sample id is valid: ${input_sample_id}"
  exit
fi


curation_prefix="https://www.ebi.ac.uk/ena/clearinghouse/api/curations/"
extra_curations2supress_file="/Users/woollard/projects/bluecloud/clearinghouse/high_seas/extra_curations2_suppress/suppress_todo_from_checking.txt"
extra_curations2supress_logfile=$extra_curations2supress_file".log"
logged_fmt_date=`date '+%Y-%m-%d:%H:%M'`
# echo "logged_fmt_date=${logged_fmt_date}"

################################################################
# Functions
function log_curation_information () {
  loc_sample_id=${1}
  loc_curation_message=${2}
  loc_curation_id=${3}
  loc_dup_attr=${4}
  loc_logged_fmt_date=${5}
  tab="\t"
  # echo -e "${loc_sample_id}${tab}${loc_curation_message}${tab}${loc_curation_id}${tab}${loc_dup_attr}${tab}${loc_logged_fmt_date}"
  echo -e "${loc_sample_id}${tab}${loc_curation_message}${tab}${loc_curation_id}${tab}${loc_dup_attr}${tab}${loc_logged_fmt_date}" >> ${extra_curations2supress_logfile}
}

function add2_suppress_curation_file () {
  curation_id=$1
  echo ${curation_id} >> ${extra_curations2supress_file}
  # echo "adding ${curation_id} to ${extra_curations2supress_file}"
}

function get_provider_names () {
  echo "in get_provider_names"
  # tmp_json=$1
  echo ${tmp_json}| jq -s '.[][][]? | .providerName' | sort | uniq -c | sort -n

}

function get_attribute_post_counts () {
  echo "in get_attribute_post_counts"
  # tmp_json=$1
  # echo $tmp_json
  echo "all"
  echo ${tmp_json}| jq -s '.[][][]? | .attributePost' | sort | uniq -c | sort -n

  echo "not suppressed"
  echo ${tmp_json}| jq -s '.[][][]? | select(.suppressed==false) | .attributePost' | sort | uniq -c | sort -n
}

function get_suppressed_fields () {
  # echo "in get_suppressed_fields"
  # tmp_json=$1
  ret_val=`echo ${tmp_json}| jq -s '.[][][]?' |  jq '. | select(.suppressed==true) | { attributePost, submittedTimestamp, id }'`
}

function get_not_suppressed_fields () {
  # echo "in get_not_suppressed_fields"
  # tmp_json=$1
  # the id is the curation id!
  ret_val=`echo ${tmp_json}| jq -s '.[][][]?' |  jq '. | select(.suppressed==false) | { attributePost, submittedTimestamp, id }'`
  # echo ${ret_val} | jq
}

function get_not_suppressed_duplicates () {
  # ret_val_boolean=true if duplicates else false
  # ret_val = space delimited string of duplicated attributes
  # echo "+++++++++++++++++++++++++++++++++++++++++++++++++++"
  # echo "in get_not_suppressed_duplicates"
  get_not_suppressed_fields ${tmp_json}
  # echo ${ret_val} | jq
  #echo ${ret_val} | jq '. | .attributePost' | uniq -d
  #echo ${ret_val} | jq '. | .attributePost' | uniq -u
  ret_val=`echo ${ret_val} | jq '. | .attributePost' | sort | uniq -d | sed 's/^"//;s/"$//' | tr '\n' ';' `
  if [[ `echo ${#ret_val}` > 5 ]]; then
      ret_val_boolean=true
  else
      ret_val_boolean=false
  fi
  #echo "  ret_val=${ret_val}"
  #echo "  ret_val_boolean=${ret_val_boolean}"
}

function get_array_curation_ids_2_suppress () {
  # tmp_json=$1
  # echo "+++++++++++++++++++++++++++++++++++++++++++++++++++"
  # echo "  in get_array_curation_ids_2_suppress"
  # get_not_suppressed_fields
  get_not_suppressed_duplicates
  # echo "ret_val_boolean:${ret_val_boolean} "
  if [ ${ret_val_boolean} = true ]; then
    # echo "duplicates are:${ret_val}<---"
    arrIN=(${ret_val//;/ })    # split string in ; to create na array
    if [ ${#arrIN[@]} = 1 ]; then
      # should not actually happen...
      log_curation_information ${sample_id} "unduplicated_curations" ${id} "" ${logged_fmt_date}
    else
      for item in ${arrIN[@]}
         do
           # echo "+++++++++++++++++++++++ ${item} ++++++++++++++++++++++++++++++++++++++++++++"
           # echo $item
           # echo ${tmp_json}| jq --arg dupattr $item  -s '.[][][]? | select(.suppressed==false) | select(.attributePost==$dupattr) | { id, updatedTimestamp}'

           # echo ${tmp_json}| jq -s '.[][][]?' |  jq  --arg dupattr $item '. | select(.suppressed==false) | select(.attributePost==$dupattr) | { id, updatedTimestamp}  '
           dup_attr_json=`echo ${tmp_json}| jq -s '.[][][]?' |  jq --arg dupattr $item '. | select(.suppressed==false) | select(.attributePost==$dupattr) | { id, updatedTimestamp}'`
           # will sort in ascending data order, so the one to keep will be at list bottom
           # echo ${dup_attr_json}  | jq -s 'sort_by(.updatedTimestamp) |  .[].id'
           #           exit
           id_list=`echo ${dup_attr_json} | jq -s 'sort_by(.updatedTimestamp) |  .[].id' | sed 's/^"//;s/"$//' | tr '\n' ';'`
           arrID=(${id_list//;/ })
           if [ ${#arrID[@]} = 1 ]; then
               msg="unduplicated_curation"
               echo "${sample_id} ${msg} ${id} ${item} ${logged_fmt_date}"
               log_curation_information ${sample_id} ${msg} ${id} ${item} ${logged_fmt_date}
           else
             #want to keep just the newest curation_id, so removing it from the array. previous used jq to alphanumerically sort
             index=( "${!arrID[@]}" )
             unset "arrID[  ${index[${#index[@]}-1]}  ]"
             msg="has_duplicate_curations"
             for id in ${arrID[@]}
               do
                 # echo "_______________________________________________"
                 add2_suppress_curation_file ${id}
                 # echo "input: sample_id=${sample_id} id=${id} dupattr=${item} date=${logged_fmt_date}"
                 echo "${sample_id} ${msg} ${id} ${item} ${logged_fmt_date}"
                 log_curation_information ${sample_id} ${msg} ${id} ${item} ${logged_fmt_date}
               done
             fi
        done
      fi
  else
    # echo "no unsuppressed curations"
    log_curation_information ${sample_id} "unduplicated_curations" ${id} "" ${logged_fmt_date}
  fi
}

function does_id_have_curations () {
  # echo "in does_id_have_curations"
  tmp_res=`echo $tmp_json | grep '"success": false'`
  # echo -e "+++++++++++++++++++++"
  ret_result=true
  if [ ${#tmp_res} -gt 1 ]; then
    # echo "is false"
    ret_result=false
  fi

  # echo ${ret_res}
}



function log_and_exit_if_no_curations () {
  does_id_have_curations
  # echo "ret_result=${ret_result}<-----"
  if  [ ${ret_result} = false ]; then
    msg="has_no_curations"
    log_curation_information ${sample_id} ${msg} "" "" ${logged_fmt_date}
    echo "${msg} ${sample_id} so exiting; but still logging"
    exit
  fi
  # echo "  does have curations!"
  }

function process_analysis () {
  sample_id=$1
  # echo "About to analyse CH record for sample_id="${sample_id}
  curation_url=${curation_prefix}${sample_id}
  # echo ${curation_url}
  #  tmp_json="/tmp/curl_tmp_json_"$$
  #  echo "writing to ${tmp_json}"
  # Doing this once, then repeatedly reuse the output
  tmp_json=`curl -s ${curation_url} | jq `
  # echo $tmp_json | jq
  log_and_exit_if_no_curations

  # tmp_json="/tmp/curl_tmp_json_11464"
  # get_attribute_post_counts
  #  get_provider_names
  #  get_suppressed_fields
  get_not_suppressed_fields
  # get_not_suppressed_duplicates
  get_array_curation_ids_2_suppress
  #working example that at the time had duplicated entries"https://www.ebi.ac.uk/ena/clearinghouse/api/curations/SAMEA7015079"
  }


###

# processing every json file
process_analysis $input_sample_id
