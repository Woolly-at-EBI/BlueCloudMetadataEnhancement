""" clearinghouse_objects.py
     see the PDF details in https://www.ebi.ac.uk/ena/clearinghouse/api/
     used by generate_clearinghouse_submissions.py

 ___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-17
__docformat___ = 'reStructuredText'

"""
import json

from icecream import ic
import os.path




class Sample:
    """ Sample
        a class for preparing new annotation for submission to the Clearing house
        see the PDF details in https://www.ebi.ac.uk/ena/clearinghouse/api/
      """
    def __init__(self,useENAAutoCurationValues):

        self.assertionAdditionalInfo = ""
        #                           'assertionEvidences': [{'label': ''}],
        self.assertionEvidences = []   #optional free text
        self.assertionSource = ""   #optional Valid URI  e.g. to a publication
        self.assertionMethod = ""    #mandatory child term of ECO_0000217 assertion method
        self.attributeDelete = ""    #optional
        self.attributePost = ""      #optional, but at least one of Post or Pre needed
        self.attributePre = ""       #optional, but at least one of Post or Pre needed
        self.valuePost = ""          #optional
        self.valuePre = ""          #optional
        self.providerName = ""  #Mandatory
        self.providerUrl = "" #optional
        self.recordId = ""              #mandatory
        self.recordType = 'sample'      #mandatory
        self.dataType = ""  #optional , CV
        self.dataIdentifier = ""  # optional, free text
        if useENAAutoCurationValues:
            self.assertionMethod = "automatic assertion"  # mandatory child term of ECO_0000217 assertion method
            self.providerName = "European Nucleotide Archive"  # Mandatory
            self.providerUrl = "https://www.ebi.ac.uk/ena/browser/home"  # optional
            self.addAutoAssertionEvidence()


    def putAssertionEvidence(self, value):
        #identifier is from ECO_0006019 child
        # label is from ECO_0006019 child
        #provide id or label
        evidence = {}
        evidence["identifier"] = value
        self.assertionEvidences.append(evidence)

    def addAutoAssertionEvidence(self):
        # = inference from background scientific knowledge used in manual assertion
        #         - as using GPS coordinates
        self.putAssertionEvidence("ECO:0000306")
        # =biological system reconstruction evidence used in manual assertion
        #       -  as using taxonomic and environment_biome evidence
        self.putAssertionEvidence("ECO:0007746")


    def get_filled_dict(self):
        my_dict = {}
        my_dict['recordId'] = self.recordId
        my_dict['recordType'] = self.recordType
        my_dict['assertionEvidences'] = self.assertionEvidences
        my_dict['assertionAdditionalInfo'] = self.assertionAdditionalInfo
        my_dict['assertionSource'] = self.assertionSource
        my_dict['assertionSource'] = self.assertionMethod
        my_dict['attributePost'] = self.attributePost
        my_dict['providerName'] = self.providerName
        my_dict['providerUrl'] = self.providerUrl

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


def demo_format(test_status):
    sample_dict = _get_template("sample")
    ic(sample_dict['curations'])
    curations = sample_dict['curations']
    ic(curations)
    curation_template_record = curations[0].copy()
    ic(curation_template_record)

    curation_count = 0
    my_record = Sample(useENAAutoCurationValues=True)
    ic(my_record.get_filled_dict())
    sample_id = 'SAMD'
    ic(my_record.attributeDelete)
    my_record.recordId = sample_id
    ic(my_record.get_filled_dict())



def main():
    test_status = False
    demo_format(test_status)


if __name__ == '__main__':
    ic()

    main()