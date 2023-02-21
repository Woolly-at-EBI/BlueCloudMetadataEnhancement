
# BlueCloud
"""Script to do quick search of ena data warehouse for all samples with GEO locations
NOT USED
___author___ = "woollard@ebi.ac.uk"
___start_date___ = "2023-01-13"
__docformat___ = 'reStructuredText'

"""
import requests

from icecream import ic

def find_samples_with_gps():
    url = 'https://www.ebi.ac.uk/ena/data/warehouse/search?query=geo_loc_name:*&result=sequence_release' +\
        '&fields=accession,geo_loc_name'
    ic(url)
    response = requests.get(url)
    data = response.json()
    return data


if __name__ == '__main__':
    samples = find_samples_with_gps()
    print(samples)
