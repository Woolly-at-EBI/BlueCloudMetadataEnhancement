#!/usr/bin/env python3
"""Script of test_checklist_term_regex.py is to test_checklist_term_regex.py

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2024-02-27
__docformat___ = 'reStructuredText'
chmod a+x test_checklist_term_regex.py
"""

from icecream import ic
import re


def get_term_regex_dict():
    term_regex_dict = {
        "simple_int": "[0-9]+",
        "broken_int": "[",
        "elevation": "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?",
        "elevation_new": "([+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?)|((^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$))",
        "test_regex": "([+-]?",
        "altitude": "((0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?)|((^not collected$)|(^not provided$)|("
                    "^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic "
                    "construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement "
                    "established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$))",
        "depth": "((0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?)|((^not collected$)|(^not provided$)|("
                 "^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic "
                 "construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement "
                 "established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$))"
    }
    return term_regex_dict


def test_regexes(term_regex_dict):
    """"""

    def is_valid_regex(test_regex):
        try:
            re.compile(test_regex)
            is_valid = True
        except re.error:
            is_valid = False

        return is_valid

    def simple_test(test_regex, test_string):
        if not is_valid_regex(test_regex):
            print(f"\tFalse : ->{test_string}<-  INVALID REGEX {test_regex}")
            return False

        x = re.search(test_regex, test_string)
        print(f"\t{bool(x)} : ->{test_string}<- in {test_regex}")

        return bool(x)

    for term in term_regex_dict:
        print(f"{term}")

        if term == "simple_int":
            simple_test(term_regex_dict[term], "99")
            simple_test(term_regex_dict[term], "ABC")
        elif term == "broken_int":
            simple_test(term_regex_dict[term], "99")
        elif term == "elevation":
            simple_test(term_regex_dict[term], "99")
            simple_test(term_regex_dict[term], "ABC")
        elif term == "elevation_new":
            simple_test(term_regex_dict[term], "99")
            simple_test(term_regex_dict[term], "missing: third party data")
            simple_test(term_regex_dict[term], "missing: third party data ")
        elif term == "altitude":
            simple_test(term_regex_dict[term], "99")
            simple_test(term_regex_dict[term], "missing: third party data")
        elif term == "depth":
            simple_test(term_regex_dict[term], "99")
            simple_test(term_regex_dict[term], "missing: third party data")
        else:
            if is_valid_regex(term_regex_dict[term]):
                print(f"\tTrue: ->{term}<-  VALID REGEX {term_regex_dict[term]}")
            else:
                print(f"\tFalse: ->{term}<-  INVALID REGEX {term_regex_dict[term]}")

        ic("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

    ic()


def main():
    term_regex_dict = get_term_regex_dict()
    test_regexes(term_regex_dict)


if __name__ == '__main__':
    ic()
    main()
