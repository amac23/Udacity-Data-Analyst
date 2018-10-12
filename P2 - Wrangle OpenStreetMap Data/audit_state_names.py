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
Adapted code from 'Quiz: Improving Street Names' to get a dictionary of all State Names that
aren't in 'exptected'. Will use this information to cleanse the state names to the abbreviation UT.
''' 

osmfilename = 'SLC.osm'

expected = ["UT"]

def audit_state(states, state):
    if state not in expected:
        states[state].add(state)
            
def is_state(elem):
    return (elem.attrib['k'] == "addr:state")

def audit(osmfile):
    osm_file = open(osmfile, "r")
    states = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "way" or elem.tag == "node":
            for tag in elem.iter("tag"):
                if is_state(tag):
                    audit_state(states, tag.attrib['v'])
    osm_file.close()
    return states

audit(osmfilename)