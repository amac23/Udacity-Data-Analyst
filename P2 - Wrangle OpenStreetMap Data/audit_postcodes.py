import xml.etree.cElementTree as ET
import pprint
import pandas
import matplotlib.pyplot as plt
import numpy as np
import re
from collections import defaultdict
import csv
import codecs
import cerberus
import schema
import sqlite3

'''
Adapted code from 'Quiz: Improving Street Names' to see all postcodes that
aren't in the correct format. Will use this info to cleanse the data.
''' 

osmfilename = 'SLC.osm'
postcode_re = re.compile('^\d{5}(-\d{4})?$')

def audit_postcode(postcodes, postcode):
    if postcode_re.match(postcode) is None:
        postcodes[postcode].add(postcode)
            
def is_postcode(elem):
    return (elem.attrib['k'] == "addr:postcode")

def audit(osmfile):
    osm_file = open(osmfile, "r")
    postcodes = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "way" or elem.tag == "node":
            for tag in elem.iter("tag"):
                if is_postcode(tag):
                    audit_postcode(postcodes, tag.attrib['v'])
    osm_file.close()
    return postcodes

audit(osmfilename)