"""Script of hitDataInfoClasses.py is to store and provide information about the hit data sets.

If using outwith the analyseHits.py use this is as it reads in the info. from the JSON file:
    hit_cats_info = MyHitDataInfo(hit_dir)
    hit_cats_info.read_category_info_dict_json()

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-03-17
__docformat___ = 'reStructuredText'

"""

from icecream import ic
import json


class MyHitDataInfo:
    """
    These are a small set of methods for dealing with  complexity of dynamically having non-exclusive categories.
    extensive use is made of dictionaries, probably could have broken them down as their own classes.
    N.B. the most important data in this is stored as json to allow the metadata to be used elsewhere
    """
    hit_dir = ""

    def __init__(self, hit_dir):
        MyHitDataInfo.hit_dir = hit_dir
        self.read_category_info_dict_json()
        ic()

    def put_category_info_dict(self, category_info_dict):
        """
        This has possibly too many jobs:
            1) store the category_info_dict
            2) determine and populate domain_dict[domain], where domain is e.g. freshwater
            3) determine and populate "shapefile_type" , n.b. dependent on category naming
            4) stores the dict as a JSON so that it can be used elsewhere in other scripts.
        :param category_info_dict:
        :return: nowt
        """
        self._category_info_dict = category_info_dict
        domain_dict = {}

        for key in category_info_dict:
            for domain in category_info_dict[key]["domains"]:
                if domain not in domain_dict:
                    ic(domain)
                    domain_dict[domain] = []
                domain_dict[domain].append(key)

            # use category naming convention; assumption: is a polygon shapefile by default
            if "_line" in key:
                self._category_info_dict[key]["shapefile_type"] = "line"
            else:  # assumption: is a polygon shapefile by default
                self._category_info_dict[key]["shapefile_type"] = "polygon"

        self._domain_cat_dict = domain_dict
        self.write_category_info_dict_json()

    def get_category_info_dict(self):
        """
        :return:
         category_info_dict: { 'eez_category': {'category': 'eez_category',
                                          'domains': ['marine'],
                                          'hitfile': '/Users/woollard/projects/bluecloud/data/hits/eez_hits.tsv',
                                          'shapefile_type': 'polygon',
                                          'short': 'eez'},
                                          ...
                             }

        """
        return self._category_info_dict

    def write_category_info_dict_json(self):
        """

        :return:
        """
        f = open(MyHitDataInfo.hit_dir + "hit_category_info_dict.json", "w")
        json_object = json.dumps(self._category_info_dict, indent = 4)
        f.write(json_object)
        f.close()

    def read_category_info_dict_json(self):
        """
        reads the JSON for the hit categories and initialises populating the class.
        this is typically called outwith analyseHits.py
        if this JSON file is missing, then analyseHits.py needs to be run
        :return: nowt
        """
        filename = MyHitDataInfo.hit_dir + "hit_category_info_dict.json"
        try:
            json_file = open(filename)
        except FileNotFoundError as e:
            print('File does not exist:', e)
            print('If this is in analyseHits.py, just populate it first! Else run analyseHits.py')
        except Exception as e:
            print('An error occurred:', e)
        else:
            category_info_dict = json.load(json_file)
            self.put_category_info_dict(category_info_dict)
            json_file.close()

    def get_category_list(self):
        """

        :return:
        """
        return list(self._category_info_dict)

    def get_domain_cat_dict(self):
        """

        :return:
        domain_cat_dict: {'freshwater': ['g200_fw_category',
                                         'g200_marine_category',
                                         'g200_terr_category',
                                         'glwd_1_category',
                                         'glwd_2_category',
                                         'ne_10m_lake_category',
                                         'feow_category'],
                          'marine': ['IHO_category', 'longhurst', 'eez_category'],
                          'terrestrial': ['feow_category',
                                          'eez_iho_intersect_category',
                                          'sea_category',
                                          'land_category',
                                          'worldAdmin_category']}
        """
        return self._domain_cat_dict

    def get_freshwater_cats(self):
        return self._domain_cat_dict['freshwater']

    def get_freshwater_cats_narrow(self):
        """
        essentially freshwater cats except for hydrosheds
        :return:
        """
        tmp_dict = self._domain_cat_dict['freshwater']
        key = 'feow_category'
        if key in tmp_dict:
            tmp_dict.remove(key)
        else:
            ic(f"Warning {key} not found in dict, not crucial, but unexpected")
        return tmp_dict
