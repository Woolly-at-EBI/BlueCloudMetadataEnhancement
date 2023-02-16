""" generate_clearinghouse_submissions.py

 ___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-16
__docformat___ = 'reStructuredText'

"""
import json

from icecream import ic
import os.path



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
    ic(curations[0].keys())

    curations[0]['providerName'] = 'EBI ENA'
    'providerUrl': '',





def main():
    test_status = False
    do_format(test_status)


if __name__ == '__main__':
    ic()

    main()