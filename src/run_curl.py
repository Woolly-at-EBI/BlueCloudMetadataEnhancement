#!/usr/bin/env python3
"""Script of run_curl.py is to curl's

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2024-01-23
__docformat___ = 'reStructuredText'
chmod a+x run_curl.py
"""
import logging
from icecream import ic
import os
import argparse
from retry import retry
import requests
import requests.exceptions as re
from urllib3.util import url
import sys

@retry(exceptions=re.RequestException, tries=3, delay=1)
def submit_curl(url, bearer_key, in_file):
    """

    :param url:
    :param bearer_key:
    :param in_file:
    :return:
    """
    try:
        logging.debug(f'Getting file from {url}')
        # headers = {
        #     'Authorization': 'Bearer ' + bearer_key,
        #     'Content-Type': 'application/json'
        # }
        enc_bearer_key = bearer_key
        logging.debug("##########################################################################")
        bearer_part = "Bearer %s" %enc_bearer_key
        logging.debug(f'bearer_part={bearer_part}')
        #sys.exit()
        headers = {
            'Authorization': bearer_part,
            'Content-Type': 'application/json; charset=utf-8'
        }

        logging.debug("##########################################################################")
        logging.debug("About to do the post request")
        logging.debug(f"URL {url} file {in_file}")
        # logging.debug(f"files {files}")

        # sys.exit()
        logging.debug(f"headers {headers}")
        # r = requests.post(url, files=files, headers=headers)
        # files = {'file': open(in_file, 'rb')}
        with open(in_file, 'rb') as f:
            r = requests.post(url, data=f, headers=headers)
        # r = requests.post(url, headers = headers)
        logging.debug("Finished the post request")
        logging.debug(f"text={r.text}")
        print(f"text={r.text}")
        r.raise_for_status()
        logging.debug(f"count={r.content}")
        logging.debug("##########################################################################")
        # sys.exit()
    except re.HTTPError as e:
        logging.error("Error retrieving mappings: {0}".format(e))
        sys.exit(1)
    except IOError as e:
        logging.error("Error writing to local file: {0}".format(e))
        sys.exit(1)


def main(args):
   logging.basicConfig(level = logging.INFO)
   curl = 'https://www.ebi.ac.uk/ena/clearinghouse/api/curations/SAMEA10025004'
   # curl -X POST "https://www.ebi.ac.uk/ena/clearinghouse/api/curations" -H "accept: */*" -H "Content-Type: application/json" -H "Authorization:
   # Bearer ey JhbGciOiJSUzI1NiJ9.eyJpc3MiOiJodHRwczovL2FhaS5lYmkuYWMudWsvc3AiLCJqdGkiOiJfLW9jVlc1YmYwQVVCaXFtdXc2Z0JnIiwiaWF0IjoxNzA1OTI1MDc1LCJzdWIiOiJ1c3ItNmZlZjc3NWEtNGM5OS00NWE1LThmYzMtMzZjYjMyYmFhZWVhIiwiZW1haWwiOiJ3b29sbGFyZEBlYmkuYWMudWsiLCJuaWNrbmFtZSI6InB3b29sbGFyZF9wcm9kIiwibmFtZSI6IlBldGVyIFdvb2xsYXJkIiwiZG9tYWlucyI6W10sImV4cCI6MTcwNTkyODY3NX0.KnPZnGShWFJDa26vSmwAT9Ovetym8iRXmyr46WDMXSbKt8jLv2BuhuTUif56M7udEHAFjoDRp0Ti5vjI16sxIzVy1ZzQmuMv4MouGaXwd4lbOoZ00NeqxduwErhCdCe8Ogmp2ADG2wOjOO5RAK3JrHWwdBuLLsf3KiGkOmq_oh4aWN-mtlvNXap7JGq-NahwNAtDT0-UC8VzzHOf1n43YbKC5utB-WdsNsWLZV9V33GgumlhXwrUOL9KNkpuwI0ZTH-K3tT4aGkRiHwsjlqRMufYgjAHjAT02ESOl3dVrZVUvC8VqUzIG2eLb3lGPksW7mKjjM4wGlBZ8xFZDlYzaQ"
   # -T /Users/woollard/projects/bluecloud/clearinghouse/high_seas/splits/split_IHO-EEZ:intersect_MARREGION//IHO-EEZ:intersect_MARREGION.json_split_10.json
   # url="https://www.ebi.ac.uk/ena/clearinghouse/api/curations"
   # bearer_key="JhbGciOiJSUzI1NiJ9.eyJpc3MiOiJodHRwczovL2FhaS5lYmkuYWMudWsvc3AiLCJqdGkiOiJfLW9jVlc1YmYwQVVCaXFtdXc2Z0JnIiwiaWF0IjoxNzA1OTI1MDc1LCJzdWIiOiJ1c3ItNmZlZjc3NWEtNGM5OS00NWE1LThmYzMtMzZjYjMyYmFhZWVhIiwiZW1haWwiOiJ3b29sbGFyZEBlYmkuYWMudWsiLCJuaWNrbmFtZSI6InB3b29sbGFyZF9wcm9kIiwibmFtZSI6IlBldGVyIFdvb2xsYXJkIiwiZG9tYWlucyI6W10sImV4cCI6MTcwNTkyODY3NX0.KnPZnGShWFJDa26vSmwAT9Ovetym8iRXmyr46WDMXSbKt8jLv2BuhuTUif56M7udEHAFjoDRp0Ti5vjI16sxIzVy1ZzQmuMv4MouGaXwd4lbOoZ00NeqxduwErhCdCe8Ogmp2ADG2wOjOO5RAK3JrHWwdBuLLsf3KiGkOmq_oh4aWN-mtlvNXap7JGq-NahwNAtDT0-UC8VzzHOf1n43YbKC5utB-WdsNsWLZV9V33GgumlhXwrUOL9KNkpuwI0ZTH-K3tT4aGkRiHwsjlqRMufYgjAHjAT02ESOl3dVrZVUvC8VqUzIG2eLb3lGPksW7mKjjM4wGlBZ8xFZDlYzaQ"
   # file="/Users/woollard/projects/bluecloud/data/tests/IHO-EEZ_test_submission.json"

   logging.debug(args)
   logging.debug(f"url={args.url}")
   logging.debug(f"bearer_key={args.bearer_key}")
   logging.debug(f"in_file={args.in_file}")
   submit_curl(args.url, args.bearer_key, args.in_file)

if __name__ == '__main__':
    ic()
    # Read arguments from command line
    prog_des = "Script to split large Clearinghouse submission JSON files with records into smaller chunks"
    print(prog_des)
    parser = argparse.ArgumentParser(description = prog_des)

    # Adding optional argument, n.b. in debugging mode in IDE, had to turn required to false.
    parser.add_argument("-d", "--debug_status",
                        help = "Debug status i.e.True if selected, is verbose",
                        required = False, action = "store_true")
    parser.add_argument("-u", "--url",
                        help = "url",
                        required = True,
                        )
    parser.add_argument("-b", "--bearer_key",
                        help = "An up to date bearer_key",
                        required = True
                        )
    parser.add_argument("-i", "--in_file",
                        help = "full path of json input file.",
                        required = True
                        )
    parser.parse_args()
    args = parser.parse_args()
    ic(args)

    main(args)
