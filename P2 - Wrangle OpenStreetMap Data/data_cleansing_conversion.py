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
Adapted code from 'Quiz: Preparing for Database' to take xml file and turn into csv files ready to be 
loaded into database. 
Also does data cleansing of street names, postcodes, and states using the update_name function
''' 

OSM_PATH = "SLC.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


# ================================================== #
#               Data Cleansing Function              #
# ================================================== #
'''
Adapted code from 'Quiz: Improving Street Names', used to cleanse street name, state, and postcode data
'''

street_mapping = { "Ave": "Avenue",
            "Ave.": "Avenue",
            "Blvd": "Boulevard",
            "Dr": "Drive",
            "E": "East",
            "N": "North",
            "Pl": "Place",
            "S": "South",
            "St": "Street",
            "W": "West",
            "W.": "West"
            }

state_mapping = { "Utah": "UT",
                "Ut": "UT",
                "ut": "UT"
                }

postcode_check = re.compile('\d{5}(-\d{4})?')

def update_name(name, tag_key, tag_type):
    if tag_key == 'street' and tag_type == 'addr':
        name = name.split(' ')
        if name[len(name)-1] in street_mapping.keys():
            name[len(name)-1] = street_mapping[name[len(name)-1]]
        name =  ' '.join(name)
        return name
    elif tag_key == 'state' and tag_type == 'addr':
        if name in state_mapping.keys():
            name = state_mapping[name]
        return name
    elif tag_key == 'postcode' and tag_type == 'addr':
        m = postcode_check.search(name)
        name = m.group()
        return name
    else:
        return name


# ================================================== #
#               Data Shaping                         #
# ================================================== #


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    tagtype = ''
    
    # Loops through tags and loads to the different dictionaries
    if element.tag == 'node':
        for i in node_attr_fields:
            node_attribs[i] = element.attrib[i]
        for tag in element.iter('tag'):
            if tag.attrib['k'].find(":")>0:
                tagtype = tagtype = tag.attrib['k'].split(':')[0]
                tag.attrib['k'] = tag.attrib['k'][tag.attrib['k'].find(":")+1:]
            else:
                tagtype = 'regular'
                tagtype = 'regular'
            # uses the update_name function to clean any street names or states or zip codes in the mapping dictionaries
            tags.append({'id':element.attrib['id'],'key':tag.attrib['k'],'value':update_name(tag.attrib['v'],tag.attrib['k'],tagtype),'type':tagtype})
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        for i in way_attr_fields:
            way_attribs[i] = element.attrib[i]
        for tag in element.iter('nd'):
            way_nodes.append({'id':element.attrib['id'],'node_id':tag.attrib['ref'],'position':len(way_nodes)})
        for tag in element.iter('tag'):
            if tag.attrib['k'].find(":")>0:
                tagtype = tagtype = tag.attrib['k'].split(':')[0]
                tag.attrib['k'] = tag.attrib['k'][tag.attrib['k'].find(":")+1:]
            else:
                tagtype = 'regular'
            # uses the update_name function to clean any street names or states or zip codes in the mapping dictionaries
            tags.append({'id':element.attrib['id'],'key':tag.attrib['k'],'value':update_name(tag.attrib['v'],tag.attrib['k'],tagtype),'type':tagtype})
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])
					
					
process_map(OSM_PATH, validate=True)