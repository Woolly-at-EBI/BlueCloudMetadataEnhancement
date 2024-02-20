#!/usr/bin/env bash
# Script of extract_curations_ids.sh is to extract curations_ids from the JSON outputs of all entries in date ranges.
# This was written before attribute specific queries were possible
#
# ___author___ = "woollard@ebi.ac.uk"
# ___start_date___ = 2024-02-14
# __docformat___ = 'reStructuredText'

################################################################
# Functions
set -e

function run_cmd () {
  echo "inside function arg1>>>"$1"<<<"
  mycmd=($1)
  echo "my_cmd="$mycmd"<<<<<<<<<<<<<<<<<<"
  echo "RUNNING &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&"
  # "${mycmd[@]}"
  # bash -c $1
  `echo $1`
  exit
}

js_cmd() {
  echo "inside js_cmd $1 $2 $3"
  file=$1
  attributeField=$2
  outfile=$3
  # remaining array=(EEZ-sovereign-level-1 EEZ-sovereign-level-2 EEZ-sovereign-level-3 EEZ-territory-level-1 EEZ-territory-level-2 EEZ-territory-level-3 )

  case $attributeField in
#    IHO-name)
#    cat $1 | jq -s '.[] | .curations | .[] | select(.attributePost == "IHO-name") | .id' >> $outfile
#    ;;
#    EEZ-IHO-intersect-name)
#    cat $1 | jq -s '.[] | .curations | .[] | select(.attributePost == "EEZ-IHO-intersect-name") | .id' >> $outfile
#    ;;
#    EEZ-name)
#    cat $1 | jq -s '.[] | .curations | .[] | select(.attributePost == "EEZ-name") | .id' >> $outfile
#    ;;
#    intersect_MARREGION:marregion)
#    cat $1 | jq -s '.[] | .curations | .[] | select(.attributePost == "intersect_MARREGION:marregion") | .id' >> $outfile
#    ;;
#    *)
    EEZ-sovereign-level-1)
    cat $1 | jq -s '.[] | .curations | .[] | select(.attributePost == "EEZ-sovereign-level-1") | .id' >> $outfile
    ;;
    EEZ-sovereign-level-2)
    cat $1 | jq -s '.[] | .curations | .[] | select(.attributePost == "EEZ-sovereign-level-2") | .id' >> $outfile
    ;;
    EEZ-sovereign-level-3)
    cat $1 | jq -s '.[] | .curations | .[] | select(.attributePost == "EEZ-sovereign-level-3") | .id' >> $outfile
    ;;
    EEZ-territory-level-1)
    cat $1 | jq -s '.[] | .curations | .[] | select(.attributePost == "EEZ-territory-level-1") | .id' >> $outfile
    ;;
    EEZ-territory-level-2)
    cat $1 | jq -s '.[] | .curations | .[] | select(.attributePost == "EEZ-territory-level-1") | .id' >> $outfile
    ;;
    EEZ-territory-level-3)
    cat $1 | jq -s '.[] | .curations | .[] | select(.attributePost == "EEZ-territory-level-1") | .id' >> $outfile
    ;;
    *)
    echo -n "unknown attribute $attributeField"
    ;;
  esac
  # cat $1 | jq -s '.[] | .curations | .[] | select(.attributePost == "$2") | .id'
  # cat $arg1 | jq -s '.[] | .curations | .[] | .id'
  }

function get_file_curationids() {
  arg1=$1
  # arg1='cho_2023-04-06T07_2023-04-06T08.json'
  # echo $arg1
  array=(EEZ-IHO-intersect-name EEZ-name EEZ-sovereign-level-1 EEZ-sovereign-level-2 EEZ-sovereign-level-3 EEZ-territory-level-1 EEZ-territory-level-2 EEZ-territory-level-3 IHO-name intersect_MARREGION:marregion)
  array=(EEZ-IHO-intersect-name EEZ-name IHO-name intersect_MARREGION:marregion)
  array=(EEZ-sovereign-level-1 EEZ-sovereign-level-2 EEZ-sovereign-level-3 EEZ-territory-level-1 EEZ-territory-level-2 EEZ-territory-level-3)
  # array=(intersect_MARREGION:marregion)
  # cat $arg1 | jq | jq -s '.[] | .curations | .[] | select(.attributePost == "IHO-name") | .id'
  prefix="cat $arg1 | jq -s '.[] | .curations | .[] | select(.attributePost == \""
  # echo $prefix
  suffix="\") | .id'"
  for attributeField in ${array[*]}
  do
    # printf -v my_cmds "ayip  %s\n" $attributeField
    outfile="curationids_$attributeField"".txt"
    if [ ! -f $outfile ]; then
        touch $outfile
    fi
    my_cmds="$prefix$attributeField$suffix >> $outfile"
    # echo "CMD>>>>>>>>>>"$my_cmds"<<<<<<<<<<<"
    echo "ABOUT TO run_cmd:"
    # run_cmd "$my_cmds"
    js_cmd $arg1 $attributeField $outfile
    echo $my_cmds
  done

  }


###

# processing every json file
data_dir='/Users/woollard/projects/bluecloud/clearinghouse/high_seas/past_curations_records'
cd $data_dir
# cat cho_2023-04-06T07_2023-04-06T08.json | jq -s '.[] | .curations | .[] | select(.attributePost == "IHO-name") .id '

pwd
# run_cmd "ls -1" # cat cho_2023-04-06T07_2023-04-06T08.json | jq -s '.[] | .curations | .[] | select(.attributePost == "intersect_MARREGION:marregion") | .id'

for file in *.json
do
    get_file_curationids $file
    echo "####################################################################################"
done

###### end of script #######
