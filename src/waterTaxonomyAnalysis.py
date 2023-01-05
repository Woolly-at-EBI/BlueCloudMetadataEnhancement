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
import warnings
import numpy as np
import matplotlib.pyplot as plt
from matplotlib_venn import venn2

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


def clean_up_df_tax2env(df):
    """ clean_up_df_tax2env
       clean the df_tax2env so that every row has at least one true water species (marine of terrestrial)
       Also forces 1 to True and 0 to False for the  NCBI-to-terrestrial.1 and "NCBI-to-marine.1"
        __params__:
               passed_args: df_tax2env

        __return__: df_tax2env

    """
    # N.B. changed all NaN's to 0. Mapping 1's to True and 0's to False
    warnings.simplefilter('ignore')
    df["NCBI-to-terrestrial.1"] = df["NCBI-to-terrestrial.1"].replace(np.nan, 0).astype(bool)
    df["NCBI-to-marine.1"] = df["NCBI-to-marine.1"].replace(np.nan, 0).astype(bool)
    warnings.resetwarnings()

    #get all those were it is water based and marine inclusive OR  terrestrial
    df = df.loc[(df["NCBI-to-marine.1"] | df["NCBI-to-terrestrial.1"])]

    return(df)

def analyse_all_ena_all_tax2env(plot_dir,df_all_ena_sample_detail, df_tax2env):
    """ analyse_all_ena_all_tax2env
           analyse the taxononmy WRT the GPS coordinates
        __params__:
               passed_args: plot_dir,df_all_ena_sample_detail,df_metag_tax, df_tax2env)

        __return__: df_merged

    """

    ic()
    ic(len(df_all_ena_sample_detail))
    # clean the df_tax2env so that every row has at least one true water species (marine of terrestrial)
    df_tax2env = clean_up_df_tax2env(df_tax2env)
    ic(len(df_tax2env))

    df_merged = pd.merge(df_all_ena_sample_detail, df_tax2env, how='inner',left_on=['tax_id'], right_on=['NCBI taxID'])
    ic(len(df_merged))
    ic(df_merged.head())

    print(f"total ENA samples={len(df_all_ena_sample_detail)}")
    print(f"total Taxonomic entries={len(df_tax2env)}")

    samples_with_marine_tax=len(df_merged)
    samples_without_marine_tax = len(df_all_ena_sample_detail) - samples_with_marine_tax
    print(f"total ENA samples with a marine or freshwater tax_id={samples_with_marine_tax} percentage= {(samples_with_marine_tax * 100)/len(df_all_ena_sample_detail):.2f} %")
    print(f"total ENA samples without a marine or freshwater tax_id={samples_without_marine_tax} percentage= {(samples_without_marine_tax * 100)/len(df_all_ena_sample_detail):.2f} %")

    df = df_merged[["accession","NCBI-to-marine.1","NCBI-to-terrestrial.1","NCBI taxID", "NCBI taxID Type", "NCBI taxID rank", "NCBI taxID Name"]]

    # ic(df.head())
    ic(df["NCBI-to-terrestrial.1"].value_counts())
    ic(df["NCBI-to-marine.1"].value_counts())
    both_true_total = len(df.loc[(df["NCBI-to-marine.1"] & df["NCBI-to-terrestrial.1"])])
    print(f"NCBI-to-marine.1 and NCBI-to-terrestrial.1 ={both_true_total}")
    just_marine_true_total = len(df.loc[(df["NCBI-to-marine.1"] & ~df["NCBI-to-terrestrial.1"])])
    print(f"NCBI-to-marine.1 and not NCBI-to-terrestrial.1 ={just_marine_true_total}")
    just_terr_true_total = len(df.loc[(~df["NCBI-to-marine.1"] & df["NCBI-to-terrestrial.1"])])
    print(f"not NCBI-to-marine.1 and  NCBI-to-terrestrial.1 ={just_terr_true_total}")
    non_true_total = len(df.loc[(~df["NCBI-to-marine.1"] & ~df["NCBI-to-terrestrial.1"])])
    print(f"not NCBI-to-marine.1 and not NCBI-to-terrestrial.1 ={non_true_total}")

    non_true = df.loc[(~df["NCBI-to-marine.1"] & ~df["NCBI-to-terrestrial.1"])]
    ic(non_true.head())

    # Use the venn2 function
    # ic("plotting as venn")
    # # venn2(subsets = (10, 5, 2), set_labels = ('Group A', 'Group B'))
    # venn2(subsets = (just_terr_true_total, both_true_total, just_terr_true_total), set_labels = ('Marine', 'Terrestrial'))
    # plt.title("ENA marine and terrestrial water taxon counts")
    # plt.show()
    # plotfile=plot_dir + 'ENA_marine_terristrial_water_tax_counts.pdf'
    # ic(plotfile)
    # plt.savefig(plotfile)

    return df

def get_all_ena_detailed_sample_info(sample_dir):
    """ get_all_ena_detailed_sample_info
        __params__:
               passed_args:
                  sample_dir
        __return__:
            df_all_ena_sample_detail
    """

    infile = sample_dir + "sample_much_raw.tsv"
    ic(infile)
    df = pd.read_csv(infile, sep = "\t", nrows=100000)
    ic(df.head())

    return df

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

    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir, taxonomy_dir) = get_directory_paths()

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
    ic(" metag get counts of sample rows by NCBI taxid")
    out_file = analysis_dir + 'tax_metag_sample_counts.tsv'
    # df2 = df_merged_ena_metag_tax[["NCBI:taxid", "accession", "NCBI term", "marine (ocean connected)", "freshwater (land enclosed)"]]
    df3 = df_merged_ena_metag_tax.groupby(["NCBI:taxid", "NCBI term", "NCBI metagenome category", "marine (ocean connected)", "freshwater (land enclosed)"]).size().to_frame('count').reset_index()
    ic(df3.head(2))
    ic(out_file)
    df3.to_csv(out_file, sep = '\t')
    ic(df3.head())


    out_file = analysis_dir + 'tax_metag_lat_lon_counts.tsv'
    df2 = df_merged_ena_metag_tax[["NCBI:taxid",  "NCBI term", 'lat', 'lon']].drop_duplicates()
    ic(df2.head(2))
    df3 = df2.groupby(["NCBI:taxid", "NCBI term"]).size().to_frame('count')
    ic(df3.head(2))
    ic(out_file)
    df3.to_csv(out_file, sep = '\t')

    """ want to get samples in sea, sea & land, land"""
    ic(df_merged_ena_metag_tax.head(2))
    ic(df_merged_all_categories.head(2))
    df_mega = pd.merge(df_merged_ena_metag_tax, df_merged_all_categories, how = 'inner', left_on = ['lat', 'lon'],
                                     right_on = ['lat', 'lon'])
    ic(df_mega.head(2))
    ic(df_mega.columns)
    ic(len(df_mega))
    out_file = analysis_dir + 'tax_metag_sample_land_sea_counts.tsv'
    df3 = df_mega.groupby(["NCBI:taxid", "NCBI term",'location_designation', "NCBI metagenome category", "marine (ocean connected)", "freshwater (land enclosed)"]).size().to_frame('count').reset_index()

    ic(df3.head())
    ic(out_file)
    df3.to_csv(out_file, sep = '\t')
    df_tax_metag_sample_land_sea_counts = df3


    plotting(plot_dir,df_tax_metag_sample_land_sea_counts )

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
    ic()
    mark_size = 8

    ic(df_merged_cats_metag_land_sea_counts.head())
    df = df_merged_cats_metag_land_sea_counts
    df['fraction']  =  df['count'] / df.groupby(["NCBI:taxid"])['count'].transform('sum')
    ic()
    ic(df.head(5))

    ic(df.columns)
    title_string = "Marine and Aqua metagenome Counts in ENA having GPS coordinates"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_counts.pdf'
    color_value = 'location_designation'
    fig = px.histogram(df, x = "NCBI term", y = "count",  color = color_value, title = title_string)
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    title_string = "Marine and Aqua metagenome log(Counts) in ENA having GPS coordinates"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_log_counts.pdf'
    color_value = 'location_designation'
    fig = px.histogram(df, x = "NCBI term", y = "count", log_y = True, color = color_value, title = title_string)
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    title_string = "Marine and Aqua metagenome counts in ENA having GPS coordinates - stacked"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_stacked_counts.pdf'
    color_value = 'location_designation'
    fig = px.bar(df, x = "NCBI term", y = "fraction",  color = color_value, title = title_string, barmode = "stack")
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    """get the taxonomic geographical categories changed to boolean
        and also change the location_designation to a more sensible order
        """
    df["marine (ocean connected)"] = df["marine (ocean connected)"].astype(bool)
    df["freshwater (land enclosed)"] = df["freshwater (land enclosed)"].astype(bool)
    category_order = ['sea', 'sea and land', 'land']
    df["location_designation"] = pd.Categorical(df["location_designation"], category_order)
    df = df.sort_values(["location_designation", "fraction"], ascending = [True, False])
    ic(df.head(20))
    quit()
    title_string = "Marine and Aqua metagenome counts in ENA having GPS coordinates - stacked ordered"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_stacked_counts_ordered.pdf'
    color_value = 'location_designation'
    fig = px.bar(df, x = "NCBI term", y = "fraction", color = color_value, title = title_string, barmode = "stack")

    """ creating a single column summary for the taxonomic geographic assignments"""
    def categorise_df(df):
        if(df["marine (ocean connected)"] and df["freshwater (land enclosed)"]):
            return "tax:marine and freshwater"
        elif (df["marine (ocean connected)"] and  not df["freshwater (land enclosed)"]):
            return "tax:marine (ocean connected)"
        elif (not df["marine (ocean connected)"] and df["freshwater (land enclosed)"]):
            return "tax:freshwater (land enclosed)"
    df["marine_freshwater_by_tax"] = df.apply(categorise_df, axis = 1)
    category_order = ['sea','sea and land','land']
    df["location_designation"] = pd.Categorical(df["location_designation"], category_order)
    df = df.sort_values(["location_designation","fraction"], ascending = [True,False])

    ic(df.head(20))
    title_string = "Marine and Aqua metagenome sample counts in ENA having GPS coordinates + taxonomic categorisation" \
                   + "<br><sup>stacked and ordered by the GPS location_designations - "\
                   + "the taxonomic cat are in the patterns</sup>" \
                   + "<br><sup>the numbers are sample counts foreach of the GPS location_designations</sup>"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_tax_cat_stacked_counts_ordered.pdf'
    color_value = 'location_designation'
    fig = px.bar(df, x = "NCBI term", y = "fraction",  color = color_value, title = title_string, barmode = "stack",
                 text= "count", pattern_shape = "marine_freshwater_by_tax")
    # fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    title_string = "Marine and Aqua metagenome sample counts in ENA having GPS coordinates + taxonomic categorisation" \
                   + "<br><sup>stacked and ordered by the GPS location_designations - "\
                   + "the taxonomic cat are in the patterns</sup>" \
                   + "<br><sup>the numbers are sample counts foreach of the GPS location_designations</sup>"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_tax_cat_stacked_counts_ordered_facet.pdf'
    color_value = 'location_designation'
    fig = px.bar(df, x = "NCBI term", y = "fraction",  color = color_value, title = title_string, barmode = "stack",
                 text= "count", pattern_shape = "marine_freshwater_by_tax", facet_row="NCBI metagenome category")
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    df = df.sort_values(["marine (ocean connected)","freshwater (land enclosed)"])
    ic(df.head(20))
    title_string = "Marine and Aqua metagenome sample counts in ENA having GPS coordinates + taxonomic categorisation"\
                   +  "<br><sup>stacked and ordered by the taxonomic geography</sup>"\
                   +  "<br><sup>the numbers are sample counts foreach of the GPS location_designations </sup>"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_tax_cat_stacked_counts_ordered_by_tax_cat.pdf'
    color_value = 'location_designation'
    fig = px.bar(df, x = "NCBI term", y = "fraction",  color = color_value, title = title_string, barmode = "stack",
                 text= "count", pattern_shape = "marine_freshwater_by_tax")
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_tax_cat_stacked_counts_ordered_by_tax_cat_facet.pdf'
    fig = px.bar(df, x = "NCBI term", y = "fraction",  color = color_value, title = title_string, barmode = "stack",
                 text= "count", facet_row = "marine_freshwater_by_tax")
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')

    title_string = "Marine and Aqua metagenome sample counts in ENA having GPS coordinates + taxonomic categorisation" \
                   + "<br><sup>Is an overall (sunburst plot)</sup>"
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_tax_cat_sunburst_LOOKATTHISONE.pdf'
    fig = px.sunburst(
        df,
        title = title_string,
        path=['marine_freshwater_by_tax', 'location_designation','NCBI term'],
        values='count',
    )
    fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_tax_cat_sunburst.html'
    ic(out_graph_file)
    fig.write_html(out_graph_file)

    title_string = "Marine and Aqua metagenome sample counts in ENA having GPS coordinates + taxonomic categorisation" \
                   + "<br><sup>Is an overall (sunburst plot)</sup>"\
                   + "<br><sup>Excluding the land/sea from GPS from plot</sup>"
    out_graph_file = plot_dir + 'merged_cats_metag_tax_cat_exclusive_sunburst.pdf'
    fig = px.sunburst(
        df,
        title = title_string,
        path = ['marine_freshwater_by_tax', 'NCBI term'],
        values = 'count',
    )
    fig.show()
    ic(out_graph_file)
    plotly.io.write_image(fig, out_graph_file, format = 'pdf')
    out_graph_file = plot_dir + 'merged_cats_metag_land_sea_tax_cat_exclusive_sunburst.html'
    ic(out_graph_file)
    fig.write_html(out_graph_file)

def analyse_all_ena_just_metag(plot_dir, analysis_dir, df_all_ena_sample_detail, df_metag_tax, df_tax2env):
    """ analyse_all_ena_just_metag
        __params__: plot_dir, analysis_dir, df_all_ena_sample_detail, df_metag_tax
               passed_args
    """
    df_ena_sample_detail = df_all_ena_sample_detail.drop(columns=['altitude', 'elevation', 'checklist', 'collection_date',
            'collection_date_submitted', 'country', 'taxonomic_classification', 'salinity', 'depth',
            'environment_biome', 'environment_feature'])

    merged_all_categories_file = analysis_dir + "merged_all_categories.tsv"
    df_merged_all_categories = pd.read_csv(merged_all_categories_file, sep = "\t")
    ic(df_merged_all_categories.head(3))

    taxa_with_ena_coords(df_merged_all_categories, df_ena_sample_detail, df_metag_tax, df_tax2env,analysis_dir)

    quit()
    taxa_notin_ena_coords(df_ena_sample_detail, df_metag_tax, df_tax2env, analysis_dir)

    return

def main(passed_args):
    """ main
        __params__:
               passed_args
    """
    (hit_dir, shape_dir, sample_dir, analysis_dir, plot_dir,  taxonomy_dir) = get_directory_paths()
    ic(analysis_dir)
    ic(plot_dir)

    """ This section can be deleted, plotting called elsewhere - is here as to allow plotting without rerrunning everything"""
    # infile = analysis_dir + 'tax_metag_sample_land_sea_counts.tsv'
    # df_merged_cats_metag_land_sea_counts = pd.read_csv(infile, sep = "\t")
    # plotting(plot_dir, df_merged_cats_metag_land_sea_counts)
    #
    # quit()

    """ The section above can be deleted, plotting called else"""

    (df_metag_tax, df_tax2env) = getTaxonomyInfo(taxonomy_dir)
    df_all_ena_sample_detail = get_all_ena_detailed_sample_info(sample_dir)

    # df_tax2env_clean = analyse_all_ena_all_tax2env(plot_dir, df_all_ena_sample_detail,df_tax2env)

    analyse_all_ena_just_metag(plot_dir, analysis_dir, df_all_ena_sample_detail, df_metag_tax,df_tax2env)

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
