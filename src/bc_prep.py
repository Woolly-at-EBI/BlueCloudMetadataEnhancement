# a single comment
"""Script to try out some likely tasks for the BlueCloud
restAPI conusming
geographic

___author___ = "woollard@ebi.ac.uk"
___start_date___ = "2022-11-23"
__docformat___ = 'reStructuredText'

"""

from icecream import ic
import subprocess
import sys
import getopt
import requests
from requests.structures import CaseInsensitiveDict

import os
from os.path import join, dirname
import json
from jsonschema import validate
import pandas as pd



def getDataFromWebService(api_url):
    '''Function to do a RESTFull API query and handle errors.
       Parameters:
       arg1 (string) : a URL

       Returns
       arg1 (string): results. Is undefined if there was an error message.
       arg2 (string): error message. Is undefined if no error message.
    
    '''

    results = None
    err_msg = None
    ic(":input_Vars: " + api_url)


    #response = requests.get(api_url, headers=headers)
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"


    try:
        response = requests.get(api_url, headers=headers)
        #ic(response.json())
    except requests.exceptions.RequestException as err:
        ic(err)
        err_msg = err
    else:
        results = response.json()
        ic('DICTIONARY RESULTS:',results)
        #err = None
    return(results,err_msg)


def comCurl(api_url):
    ic(api_url)
    cmd_line = "curl -X GET --header 'Accept: application/json' '" + api_url + "'"
    ic(cmd_line)
    print(cmd_line)

    stream = os.popen(cmd_line)
    output = stream.read()
    ic(output)

def addGazettaData(record,df):
    # ic(record)
    # ic(record["MRGID"])
    # ic(record["preferredGazetteerName"])
    # ic(record["placeType"])
    # ic(record["latitude"])
    # ic(record["longitude"])
    #for field in record:
    #    df[field] = record[field]
    #df = df.append(record, ignore_index = True)
    allColumns = list(record.values())

    # record = [{'area': 'new-hills', 'rainfall': 100, 'temperature': 20},
    #      {'area': 'cape-town',  'rainfall': 70, 'temperature': 25},
    #      {'area': 'mumbai',  'rainfall': 200,  'temperature': 39 }]
    #record = '{"a":54, "b": 28}'
    ic(type(record))
    #record = json.loads(record)
    ic(record)
    ic(type(record))
    new_df_row = pd.DataFrame([record])
    ic(new_df_row)
    df = pd.concat([df, new_df_row], ignore_index=True)
    ic(df)
    return(df)

def main():
    ic("'afternoon")
    df = pd.DataFrame()

    # api_url = "https://jsonplaceholder.typicode.com/todos/1"
    # getDataFromWebService(api_url)
    # api_url = "https://jsonplaceholder.madeup/"
    # getDataFromWebService(api_url)
    # api_url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/fields?format=json'
    # getDataFromWebService(api_url)
    # api_url = 'https://www.ebi.ac.uk/europepmc/annotations_api/annotationsByArticleIds?articleIds=PMC%3APMC9561433&type=Gene_Proteins&type=Organisms&type=Chemicals&type=Gene%20Ontology&format=JSON'
    # getDataFromWebService(api_url)


    api_url = "https://www.marineregions.org/gazetteer.php?p=details&id=5677"
    api_url = "https://www.marineregions.org/rest/getGazetteerRecordByMRGID.json/5677/"
    (data,err_msg) = getDataFromWebService(api_url)
    df = addGazettaData(data,df)
    #comCurl(api_url)
    api_url = "https://www.marineregions.org/rest/getGazetteerRecordByMRGID.json/1111/"
    (data,err_msg) = getDataFromWebService(api_url)
    df = addGazettaData(data,df)

    api_url = "https://www.marineregions.org/rest/getGazetteerRecordByMRGID.json/3333/"
    (data,err_msg) = getDataFromWebService(api_url)
    df = addGazettaData(data,df)

    api_url = "https://www.marineregions.org/rest/getGazetteerRecordByMRGID.json/5666/"
    (data,err_msg) = getDataFromWebService(api_url)
    df = addGazettaData(data,df)
    







if __name__ == '__main__':
    main()
