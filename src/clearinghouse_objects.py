""" clearinghouse_objects.py  are curation objects used by generate_clearinghouse_submissions.py
     see the PDF details in https://www.ebi.ac.uk/ena/clearinghouse/api/
     used by generate_clearinghouse_submissions.py

 ___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-17
__docformat___ = 'reStructuredText'

"""
import json

from icecream import ic
import os.path
import sys

class NewSampleCuration:
    """ NewSampleCuration
        a class for preparing new annotation for submission to the Clearing house
        see the PDF details in https://www.ebi.ac.uk/ena/clearinghouse/api/
      """
    def __init__(self,useENAAutoCurationValues):
        ic()
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
            self.addAutoAssertionEvidence("void")


    def emptyAssertionEvidence(self):
        self.assertionEvidences = []

    def putAssertionEvidence(self, identifier_value, label_value):
        """ putAssertionEvidence
        https://www.ebi.ac.uk/ols/ontologies/eco
        :param identifier_value:
        :param label_valye:
        :return:
        """
        #identifier is from ECO_0006019 child
        # label is from ECO_0006019 child
        #provide id or label
        evidence = {}
        evidence["identifier"] = identifier_value
        evidence["label"] = label_value
        self.assertionEvidences.append(evidence)

    def addAutoAssertionEvidence(self, extra_evidence):
        """addAutoAssertionEvidence adds the identifier and label for the evidence.
        the identifier and label are from https://www.ebi.ac.uk/ols/ontologies/eco native=https://www.evidenceontology.org/
        multiple of these pairs are allowed per curation
        :return:
        """
        identifier = "ECO:0000203"
        label = "An assertion method that does not involve human review."
        self.putAssertionEvidence(identifier, label)

        # currently all evidence is based on GPS coordinate hits to shapefiles or taxonomy inference
        # it would be useful if there was evidence code from spatial coordinates
        identifier = "ECO:0000366"
        label = "A type of evidence based on logical inference from an automatically curated annotation that is used in an automatic assertion."
        self.putAssertionEvidence(identifier, label)

        # ic(extra_evidence)
        if extra_evidence == "combinatorial":
            # for the marine/terrestrial
            #         - as using GPS coordinates
            identifier = "ECO:0007653"
            label = "automatically integrated combinatorial computational evidence used in automatic assertion"
            self.putAssertionEvidence(identifier, label)

        return

    def get_filled_dict(self):
        """get_filled_dict

        :return: a dictionary of the new curation record
        """
        my_dict = {}
        my_dict['recordId'] = self.recordId
        my_dict['recordType'] = self.recordType
        my_dict['assertionEvidences'] = self.assertionEvidences
        my_dict['assertionAdditionalInfo'] = self.assertionAdditionalInfo
        my_dict['assertionSource'] = self.assertionSource
        my_dict['assertionMethod'] = self.assertionMethod
        my_dict['attributePost'] = self.attributePost
        my_dict['valuePost'] = self.valuePost
        my_dict['providerName'] = self.providerName
        my_dict['providerUrl'] = self.providerUrl

        return my_dict

    def get_filled_json(self):
        """  get_filled_json
        calls converts the dictionary to JSON string
        :return: json
        """""

        return json.dumps(self.get_filled_dict(), indent = 4)




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
    ic(sample_dict)
    curations = sample_dict['curations']
    ic(curations)
    curation_template_record = curations[0].copy()
    ic(curation_template_record)

    curation_count = 0
    my_record = NewSampleCuration(useENAAutoCurationValues=True)
    ic(my_record.get_filled_dict())
    sample_id = 'SAMD'
    ic(my_record.attributeDelete)
    my_record.recordId = sample_id
    ic(my_record.get_filled_dict())



def main():
    test_status = True
    demo_format(test_status)

    #environment_biome.pickle



if __name__ == '__main__':
    ic()

    main()