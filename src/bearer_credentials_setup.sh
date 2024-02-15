#!/usr/bin/env bash
#"""Script of bearer_credentials_setup.sh is to set up the bearere credentials
#
#___author___ = "woollard@ebi.ac.uk"
#___start_date___ = 2024-02-14
#__docformat___ = 'reStructuredText'

#"""
# set environment variables and credentials up
source ~/.ayup

################################################################
# Functions

function clearinghouse_credentials () {
  mode=$1
  if [ ${mode} == "test" ]; then
  echo "INFO: using -->test<--- credentials etc."
  url="https://wwwdev.ebi.ac.uk/ena/clearinghouse/api/curations"
  curation_server_api="https://wwwdev.ebi.ac.uk/ena/clearinghouse/api/swagger-ui/index.html"
  auth_url='https://explore.api.aai.ebi.ac.uk/auth'
  creds=$aai_test2_creds
  # submission_dir="/Users/woollard/projects/bluecloud/clearinghouse/submission_data/test/splits/"
  # submission_dir="/Users/woollard/projects/bluecloud/clearinghouse/submission_data/full/splits/"
else
  #PROD
  echo "using production credentials and setup"
  url="https://www.ebi.ac.uk/ena/clearinghouse/api/curations"
  curation_server_api="https://www.ebi.ac.uk/ena/clearinghouse/api/swagger-ui/index.html"
  auth_url='https://api.aai.ebi.ac.uk/auth'
  creds=$aai_prod_creds
#  submission_dir="/Users/woollard/projects/bluecloud/clearinghouse/submission_data/full/splits/"
#  submission_dir="/Users/woollard/projects/bluecloud/clearinghouse/submission_data/full/splits/IHO:IHO_category/"
#  submission_dir="/Users/woollard/projects/bluecloud/clearinghouse/submission_data/full/splits/redo_IHO:IHO_category/split_100/"
#  submission_dir="/Users/woollard/projects/bluecloud/clearinghouse/corrections/splits/remainder/"
#  submission_dir=$1
 fi
}

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



