
# Testing Samples

<!-- TOC -->
* [Testing Samples](#testing-samples)
  * [Introduction](#introduction)
  * [Description](#description)
  * [Example sample JSON](#example-sample-json)
<!-- TOC -->

## Introduction
In the BlueCloud exploratory project different types of metadata evidence were investigated. 
Automatic calls were made to assign ENA samples to be part of the Blue Partition or not. Information from this will be useful for 
developing and testing the BlueCloud partition production.

N.B. These are not gold standard, so there may be some slippage with assignments, but it would be rather surprising if it s very wrong.

## Description

There are ENA accession(biosample) ids for each blue partition constituent categories or not. For each of the constituents, 
there are usually 100 accession ids for each confidence level. These accession ids are pseudo randomly selected.

Additionally, at the top level all accession ids can be grabbed from the 'all_test_accessions'

The information is located in this JSON file: testing/data/my_test_samples.json

## Example sample JSON
It is a cut down example, where there are 3 accessions selected 

```{
    "blue_partition_category": {
        "unclassified": {
            "part_of": false,
            "confidence_level": {
                "zero": {
                    "accession": [
                        "SAMD00011717",
                        "SAMD00014583",
                        "SAMD00039177"
                    ]
                }
            }
        },
        "land": {
            "part_of": false,
            "confidence_level": {
                "zero": {
                    "accession": [
                        "SAMD00048681",
                        "SAMD00019803",
                        "SAMD00045854"
                    ]
                }
            }
        },
        "marine": {
            "part_of": true,
            "confidence_level": {
                "low": {
                    "accession": [
                        "SAMD00019677",
                        "SAMD00028058",
                        "SAMD00003712"
                    ]
                },
                "high": {
                    "accession": [
                        "SAMD00028081",
                        "SAMD00028113",
                        "SAMD00028085"
                    ]
                },
                "medium": {
                    "accession": [
                        "SAMD00047113",
                        "SAMD00024460",
                        "SAMD00049107"
                    ]
                }
            }
        },
        "marine_and_terrestrial": {
            "part_of": true,
            "confidence_level": {
                "medium": {
                    "accession": [
                        "SAMD00020282",
                        "SAMD00056745",
                        "SAMD00013050"
                    ]
                },
                "high": {
                    "accession": [
                        "SAMD00056315",
                        "SAMD00020009",
                        "SAMD00020111"
                    ]
                }
            }
        },
        "freshwater": {
            "part_of": true,
            "confidence_level": {
                "medium": {
                    "accession": [
                        "SAMD00053070",
                        "SAMD00052955",
                        "SAMD00053028"
                    ]
                },
                "high": {
                    "accession": [
                        "SAMD00045679",
                        "SAMD00045650",
                        "SAMD00045672"
                    ]
                }
            }
        }
    },
    "all_test_accessions": [
        "SAMD00011717",
        "SAMD00014583",
        "SAMD00039177",
        "SAMD00048681",
        "SAMD00019803",
        "SAMD00045854",
        "SAMD00019677",
        "SAMD00028058",
        "SAMD00003712",
        "SAMD00028081",
        "SAMD00028113",
        "SAMD00028085",
        "SAMD00047113",
        "SAMD00024460",
        "SAMD00049107",
        "SAMD00020282",
        "SAMD00056745",
        "SAMD00013050",
        "SAMD00056315",
        "SAMD00020009",
        "SAMD00020111",
        "SAMD00053070",
        "SAMD00052955",
        "SAMD00053028",
        "SAMD00045679",
        "SAMD00045650",
        "SAMD00045672"
    ]
}
```