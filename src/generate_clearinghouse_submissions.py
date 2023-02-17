""" generate_clearinghouse_submissions.py

 ___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-16
__docformat___ = 'reStructuredText'

"""
import json

from icecream import ic
import os.path

SavedDataStructures = {}


class Sample:
  def __init__(self):

    self.assertionAdditionalInfo = None
    #                           'assertionEvidences': [{'label': ''}],
    self.assertionEvidences = None
    self.assertionSource = None
    self.attributeDelete = "true"
    self.attributePost = None
    self.attributePre = None
    self.providerName = "European Nucleotide Archive"
    self.providerUrl = "https://www.ebi.ac.uk/ena/browser/home"
    self.recordId = None
    self.recordType = 'sample'


  def get_filled_dict(self):
    my_dict = {}
    my_dict['assertionAdditionalInfo'] = self.assertionAdditionalInfo
    my_dict['assertionSource'] = self.assertionSource
    my_dict['attributeDelete'] = self.attributeDelete
    my_dict['attributePost'] = self.attributePost
    my_dict['attributePre'] = self.attributePre
    my_dict['providerName'] = self.providerName
    my_dict['providerUrl'] = self.providerUrl
    my_dict['recordId'] = self.recordId
    my_dict['recordType'] = self.recordType

    return my_dict





def _get_template(template_type):
    """

    :return: empty_dict
    """
    template_file = ""
    if (template_type == "sample"):
        template_file = "empty_clearinghouse_submission_template.json"

    empty_dict = {}
    if os.path.isfile(template_file):
        f = open(template_file)
        empty_dict = json.load(f)
        f.close()
        type(empty_dict)
        ic(empty_dict)
    else:
        ic(f"ERROR: {template_file} dies not exist")
        quit(1)

    return(empty_dict)


def do_format(test_status):
    sample_dict = _get_template("sample")
    ic(sample_dict['curations'])
    curations = sample_dict['curations']
    ic(curations)
    curation_template_record = curations[0].copy()
    ic(curation_template_record)

    curation_count = 0
    record = Sample()
    ic(record.get_filled_dict())



def main():
    test_status = False
    do_format(test_status)


if __name__ == '__main__':
    ic()

    main()