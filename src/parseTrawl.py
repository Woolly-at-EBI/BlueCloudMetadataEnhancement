# parseTrawl
"""Script to extra long and lat coordinates from sample xml
    this has start and end coords

___author___ = "woollard@ebi.ac.uk"
___start_date___ = "2022-12-15"
__docformat___ = 'reStructuredText'

"""

from icecream import ic
from xml.dom.minidom import parse, parseString
import xml.etree.ElementTree as ET
import pandas as pd


def process(sample_dict):
    pd.set_option('display.max_columns', None)
    df = pd.DataFrame.from_dict(sample_dict, orient='index')
    out_file = "/Users/woollard/projects/bluecloud/data/samples/sample_trawl_all_start_ends.tsv"
    ic(out_file)
    df.to_csv(out_file,sep="\t")




def justParse(xml_file_name):
    # document = parse(xml_file_name)

    # create element tree object
    tree = ET.parse(xml_file_name)

    # get root element
    root = tree.getroot()
    sample_trawl= {}

    # iterate news items
    count =0
    for sample in root.findall('./SAMPLE'):
        # ic(sample.tag)
        # ic(sample.get('accession'))
        identifiers = sample.find('IDENTIFIERS')
        # ic(identifiers)
        primary_id = identifiers.find('PRIMARY_ID')
        external_id = identifiers.find('EXTERNAL_ID')
        sample_attributes = sample.find('SAMPLE_ATTRIBUTES')
        local_dict = {}

        for child in sample_attributes:
            tag = child.find('TAG')
            if(tag.text == 'Latitude Start'):
                value_tag = child.find('VALUE')
                local_dict['lat_start'] = value_tag.text
            elif(tag.text == 'Latitude End'):
                value_tag = child.find('VALUE')
                local_dict['lat_end'] = value_tag.text
            elif(tag.text == 'Longitude Start'):
                value_tag = child.find('VALUE')
                local_dict['lon_start'] = value_tag.text
            elif (tag.text == 'Longitude End'):
                value_tag = child.find('VALUE')
                local_dict['lon_end'] = value_tag.text
            elif(tag.text == 'Marine Region'):
                value_tag = child.find('VALUE')
                local_dict['marine_region'] = value_tag.text
        local_dict['external_id'] = external_id.text
        sample_trawl[primary_id.text] = local_dict
        count += 1

    # ic(sample_trawl)
    return sample_trawl

def main():
    xml_file_name: str = "/Users/woollard/projects/bluecloud/data/samples/sample_attributes.xml"
    xml_file_name: str = "/Users/woollard/projects/bluecloud/data/samples/sample_potential_trawls_acc.xml"
    ic(xml_file_name)
    sample_dict = justParse(xml_file_name)
    process(sample_dict)




if __name__ == '__main__':
    main()
