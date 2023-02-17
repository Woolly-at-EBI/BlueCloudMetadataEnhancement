""" project_utils
     some utilities needed in several projects

 ___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2023-02-17
__docformat___ = 'reStructuredText'

"""

import os.path
import pickle
from icecream import ic

def put_pickleObj2File(obj,pickle_file):
    """

    :param obj:
    :param pickle_file
    :return:
    """
    with open(pickle_file, 'wb') as handle:
        pickle.dump(obj, handle, protocol = pickle.HIGHEST_PROTOCOL)
def get_pickleObj(pickle_file):
    """

    :param pickle_file:
    :return:
    """
    if os.path.isfile(pickle_file):
        ic(pickle_file + " exists, so using it")
        with open(pickle_file, 'rb') as handle:
            obj = pickle.load(handle)
    else:
        ic(pickle_file + " does not exist")
    return obj

def obj_size_fmt(num):
    """

    :param num:
    :return: object size with units
    """
    if num < 10**3:
        return "{:.2f}{}".format(num, "B")
    elif ((num>=10**3)&(num<10**6)):
        return "{:.2f}{}".format(num/(1.024*10**3), "KB")
    elif ((num>=10**6)&(num<10**9)):
        return "{:.2f}{}".format(num/(1.024*10**6), "MB")
    else:
        return "{:.2f}{}".format(num/(1.024*10**9), "GB")

def memory_usage():
    """

    :return: memory_usage_by_variable
    """
    memory_usage_by_variable= pd.DataFrame({k:sys.getsizeof(v)\
    for (k,v) in globals().items()}, index=['Size'])
    memory_usage_by_variable = memory_usage_by_variable.T
    memory_usage_by_variable = memory_usage_by_variable.sort_values(by='Size', ascending=False).head(10)
    memory_usage_by_variable['Size'] = memory_usage_by_variable['Size'].apply(lambda x: obj_size_fmt(x))
    return memory_usage_by_variable
