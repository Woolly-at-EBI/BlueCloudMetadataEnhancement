"""Script of waterTaxonomyAnalysis.py is to


___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2022-12-21
__docformat___ = 'reStructuredText'

"""
from get_directory_paths import get_directory_paths
import pandas as pd
from icecream import ic

import plotly.express as px
import plotly

import argparse

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

def getTaxonomyInfo(taxonomy_dir):
    """ getTaxonomyInfo
     read in the relevant marine taxonomic terms.
    These cam from Stephane Pesant
        __params__:
             taxonomy_dir
        __returns__:
                df_metag_tax, df_tax2env
    """
    ic()

    metagenomes_file = taxonomy_dir + "NCBI-metagenomes-to-environment.csv"
    df_metag_tax = pd.read_csv(metagenomes_file)
    ic(df_metag_tax.head(10))

    taxa_env_file = taxonomy_dir  + "NCBI-taxa-to-environment.csv"
    df_tax2env = pd.read_csv(taxa_env_file)
    ic(df_tax2env.head(10))
   
    return (df_metag_tax, df_tax2env)

def get_ena_detailed_sample_info(sample_dir):
    """ get_ena_detailed_sample_info
        __params__:
               passed_args:
                  sample_dir
        __return__:
            df_ena_sample_detail
    """
    ic()
    infile = sample_dir + "sample_much_lat_filtered.tsv"
    df_ena_sample_detail = pd.read_csv(infile, sep = "\t", nrows=10000000)
    ic(df_ena_sample_detail.head())

    return df_ena_sample_detail

def taxa_notin_ena_coords(df_ena_sample_detail, df_metag_tax, df_tax2env, analysis_dir):
    """ taxa_notin_ena_coords
    NCBI Taxa from samples that have at least 1 coordinate at ENA.

    For each taxon, please inform the following fields:

    NCBI taxID
    #samples in sea, sea & land, land
    #of associated runs in sea, sea & land, land (if possible, to assess relevance/importance)


        __params__:
               passed_args
               df_ena_sample_detail, df_metag_tax, df_tax2env
        __return__:
    """
    ic(len(df_ena_sample_detail))

    df_metag_not_in_ena_latlon =df_metag_tax[~df_metag_tax['NCBI:taxid'].isin(df_ena_sample_detail['tax_id'])]
    ic(df_metag_not_in_ena_latlon.head(10))
    ic(len(df_metag_tax))
    ic(len(df_metag_not_in_ena_latlon))
    out_file = analysis_dir + 'tax_metag_notin_ena_latlon.tsv'
    ic(out_file)
    df_metag_not_in_ena_latlon.to_csv(out_file, sep = '\t')

    df_metag_is_in_ena_latlon =df_metag_tax[df_metag_tax['NCBI:taxid'].isin(df_ena_sample_detail['tax_id'])]
    ic(df_metag_is_in_ena_latlon.head(2))
    ic(len(df_metag_tax))
    ic(len(df_metag_is_in_ena_latlon))
    out_file = analysis_dir + 'tax_metag_is_in_ena_latlon.tsv'
    ic(out_file)
    df_metag_is_in_ena_latlon.to_csv(out_file, sep = '\t')

    # how many runs are for these samples
    sample_acc = ["SAMN18146923", "SAMN18146924", "SAMN18146925", "SAMN18146926", "SAMN18146927", "SAMN18146928", "SAMN18146929", "SAMN18146930", "SAMN18146931", "SAMN18146932", "SAMN18146933", "SAMN18146934", "SAMN18146935", "SAMN18146936", "SAMN18146937", "SAMN18146938", "SAMN18146939", "SAMN18146940", "SAMN18146941", "SAMN18146942", "SAMN18146943", "SAMN18146944", "SAMN18146945", "SAMN18146946", "SAMN18146947", "SAMN18146948", "SAMN18146949", "SAMN18146950", "SAMN18146951", "SAMN18146952", "SAMN18146953", "SAMN18146954", "SAMN18146955", "SAMN18146956", "SAMN18146957", "SAMN18146958", "SAMN18146959", "SAMN18146960", "SAMN18146961", "SAMN18146962", "SAMN18146963", "SAMN18146964", "SAMN18146965", "SAMN18146966", "SAMN18146967", "SAMN18146968", "SAMN18146969", "SAMN18146970", "SAMN18146971", "SAMN18146972", "SAMN18146973", "SAMN18146974", "SAMN18146975", "SAMN18146976", "SAMN21876556"]
    ic(len(sample_acc))


    return

def taxa_with_ena_coords(df_merged_all_categories, df_ena_sample_detail, df_metag_tax, df_tax2env, analysis_dir):
    """ taxa_with_ena_coords
    NCBI Taxa from samples that have at least 1 coordinate at ENA.

    For each taxon, please inform the following fields:

    NCBI taxID
    #samples in sea, sea & land, land
    #of associated runs in sea, sea & land, land (if possible, to assess relevance/importance)


        __params__:
               passed_args
               df_merged_all_categories
               df_ena_sample_detail,
                df_metag_tax, df_tax2env
        __return__:
    """
    ic(len(df_ena_sample_detail))
    df_merged_ena_metag_tax = pd.merge(df_ena_sample_detail, df_metag_tax, how='inner',left_on=['tax_id'],
                                right_on=['NCBI:taxid'])
    ic(df_merged_ena_metag_tax.head())
    ic(len(df_merged_ena_metag_tax))

    df_tax2env = df_tax2env.rename({'NCBI taxID': "NCBI:taxid", "NCBI taxID Name": "NCBI term"})
    df_merged_ena_tax2env = pd.merge(df_ena_sample_detail, df_metag_tax, how='inner',left_on=['tax_id'],
                                right_on=['NCBI:taxid'])
    ic(df_merged_ena_tax2env.head())
    ic(len(df_merged_ena_tax2env))

    """ metag get counts of sample rows by NCBI taxid"""
    out_file = analysis_dir + 'tax_metag_sample_counts.tsv'
    df2 = df_merged_ena_metag_tax[["NCBI:taxid", "accession", "NCBI term"]]
    df3 = df2.groupby(["NCBI:taxid", "NCBI term"]).size().to_frame('count')
    ic(df3.head(2))
    ic(out_file)
    df3.to_csv(out_file, sep = '\t')

    out_file = analysis_dir + 'tax_metag_lat_lon_counts.tsv'
    df2 = df_merged_ena_metag_tax[["NCBI:taxid",  "NCBI term", 'lat', 'lon']].drop_duplicates()
    ic(df2.head(2))
    df3 = df2.groupby(["NCBI:taxid", "NCBI term"]).size().to_frame('count')
    ic(df3.head(2))
    ic(out_file)
    df3.to_csv(out_file, sep = '\t')

    """ wnat to get samples in sea, sea & land, land"""
    ic(df_merged_ena_metag_tax.head(2))
    ic(df_merged_all_categories.head(2))
    df_mega = pd.merge(df_merged_ena_metag_tax, df_merged_all_categories, how = 'inner', left_on = ['lat', 'lon'],
                                     right_on = ['lat', 'lon'])
    ic(df_mega.head(2))
    ic(len(df_mega))

    out_file = analysis_dir + 'tax_metag_sample_land_sea_counts.tsv'
    df2 = df_mega[['NCBI:taxid', 'NCBI term','location_designation']]
    ic(df2.head(2))
    df3 = df2.groupby(["NCBI:taxid", "NCBI term",'location_designation']).size().to_frame('count')

    ic(df3)
    ic(out_file)
    quit()
    df3.to_csv(out_file, sep = '\t')
    plotting(df3)

    # """ tax2env get counts of sample rows by NCBI taxid"""
    # out_file = analysis_dir + 'tax2env_sample_counts.tsv'
    # df2 = df_merged_ena_tax2env[["NCBI:taxid", "accession", "NCBI term"]]
    # df3 = df2.groupby(["NCBI:taxid", "NCBI term"]).size().to_frame('count')
    # ic(df3.head(2))
    # ic(out_file)
    # df3.to_csv(out_file, sep = '\t')
    #
    # out_file = analysis_dir + 'tax2env__lat_lon_counts.tsv'
    # df2 = df_merged_ena_tax2env[["NCBI:taxid",  "NCBI term", 'lat', 'lon']].drop_duplicates()
    # ic(df2.head(2))
    # df3 = df2.groupby(["NCBI:taxid", "NCBI term"]).size().to_frame('count')
    # ic(df3.head(2))
    # ic(out_file)
    # df3.to_csv(out_file, sep = '\t')

    return

def plotting(plot_dir,df_merged_cats_metag_land_sea_counts):
    """ plotting
        __params__:
               passed_args
               df_merged_cats_metag_land_sea_counts
    """
    ic(df_merged_cats_metag_land_sea_counts.head())
    df = df_merged_cats_metag_land_sea_counts
    df['fraction']  =  df['count'] / df.groupby(["NCBI:taxid"])['count'].transform('sum')
    ic(df.head(10))

    title_string = "Marine and Aqua metagenome Counts in ENA having GPS coordinates"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_counts.pdf'
    mark_size = 8
    color_value = 'location_designation'
    fig = px.histogram(df, x = "NCBI term", y = "count",  color = color_value, title = title_string)
    fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    title_string = "Marine and Aqua metagenome log(Counts) in ENA having GPS coordinates"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_log_counts.pdf'
    mark_size = 8
    color_value = 'location_designation'
    fig = px.histogram(df, x = "NCBI term", y = "count", log_y = True, color = color_value, title = title_string)
    fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    title_string = "Marine and Aqua metagenome counts in ENA having GPS coordinates - stacked"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_stacked_counts.pdf'
    mark_size = 8
    color_value = 'location_designation'
    fig = px.bar(df, x = "NCBI term", y = "fraction",  color = color_value, title = title_string, barmode = "stack")
    fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

def main(passed_args):
    """ main
        __params__:
               passed_args
    """
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir,  taxonomy_dir) = get_directory_paths()
    ic(analysis_dir)
    ic(plot_dir)

    """ This section can be deleted, plotting called else"""
    infile = analysis_dir + 'tax_metag_sample_land_sea_counts.tsv'
    df_merged_cats_metag_land_sea_counts = pd.read_csv(infile, sep = "\t")
    plotting(plot_dir, df_merged_cats_metag_land_sea_counts)

    quit()

    """ The section above can be deleted, plotting called else"""

    df_ena_sample_detail = get_ena_detailed_sample_info(sample_dir)
    df_ena_sample_detail = df_ena_sample_detail.drop(columns=['altitude', 'elevation', 'checklist', 'collection_date',
            'collection_date_submitted', 'country', 'taxonomic_classification', 'salinity', 'depth',
            'environment_biome', 'environment_feature'])

    (df_metag_tax, df_tax2env) = getTaxonomyInfo(taxonomy_dir)
    merged_all_categories_file = analysis_dir + "merged_all_categories.tsv"
    df_merged_all_categories = pd.read_csv(merged_all_categories_file, sep = "\t")
    ic(df_merged_all_categories.head(3))

    taxa_with_ena_coords(df_merged_all_categories, df_ena_sample_detail, df_metag_tax, df_tax2env,analysis_dir)
    taxa_notin_ena_coords(df_ena_sample_detail, df_metag_tax, df_tax2env, analysis_dir)


    return ()


if __name__ == '__main__':
    ic()
    # Read arguments from command line
    prog_des = "Script to get the marine zone classification for a set of longitude and latitude coordinates"
    parser = argparse.ArgumentParser(description = prog_des)

    # Adding optional argument, n.b. in debugging mode in IDE, had to turn required to false.
    parser.add_argument("-v", "--verbosity", type = int, help = "increase output verbosity", required = False)
    parser.add_argument("-o", "--outfile", help = "Output file", required = False)

    parser.parse_args()
    args = parser.parse_args()
    ic(args)
    print(args)
    if args.verbosity:
        print("verbosity turned on")


    main(args)
