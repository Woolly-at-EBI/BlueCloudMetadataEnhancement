
import os
def get_directory_paths():
    """ get_directory_paths
             takes a base directory, checks this exists
             also sets the directory paths for analysis and plots etc. and checks that these all exist
        __params__:
               passed_args:
        __returns__:
            hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir,  taxonomy_dir)
    """
    base_dir = "/Users/woollard/projects/bluecloud/"
    analysis_dir = base_dir + "analysis/"
    plot_dir = base_dir + "analysis/plots/"
    hit_dir = base_dir + "data/hits/"
    sample_dir = base_dir + 'data/samples/'
    shape_dir = base_dir + 'data/shapefiles/'
    taxonomy_dir = base_dir + 'data/taxonomy/'

    dir_list = [base_dir, hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir]
    dir_err = False
    for my_dir in dir_list:
        if not os.path.isdir(my_dir):
            print(f"This directory path does not exist, please create it: {my_dir}")
            dir_err = True
    if dir_err:
        print("Please fix all this configuration")
        quit()

    return hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir
