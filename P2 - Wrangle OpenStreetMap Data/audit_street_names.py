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
Adapted code from 'Quiz: Improving Street Names' to get a dictionary of all Street Names that
aren't in 'exptected'. Added some Street Names to the 'exptected' set that are real types
of streets in SLC, i.e. North, Sout, East, West, Way, Temple. Will use this information to cleanse
the street names and map abbreviations to full street types.
''' 


osmfilename = 'SLC.osm'
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Broadway", "Circle", "North", "East", "South", "West",
            "Way", "Temple"]

def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)
            
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "way" or elem.tag == "node":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types

audit(osmfilename)