%matplotlib inline
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

# Creates the tables and the SLC.db
fd = open('data_wrangling_schema.sql','r')
sqlFile = fd.read()
fd.close()
sqlCommands = sqlFile.split(';')


conn = sqlite3.connect('SLC.db')
cursor = conn.cursor()


for i in sqlCommands:
    cursor.execute(i)
    conn.commit()

conn.close()


# imports csv files into the tables in the database
conn = sqlite3.connect('SLC.db')

for i in ['nodes','nodes_tags','ways','ways_nodes','ways_tags']:
    df = pandas.read_csv(i + '.csv',encoding='utf_8')
    df.to_sql(i,con=conn,if_exists='append',index=False)

conn.close()


# queries into df and prints them out
conn = sqlite3.connect('SLC.db')

query = '''select count(distinct user) as total_users from
(
select user from nodes
union all
select user from ways
) a
'''
total_users_df = pandas.read_sql_query(query,conn)
print('There are ' + str(total_users_df['total_users'][0]) + ' unique users.')

query = '''select count(user) as total_edits from
(
select user from nodes
union all
select user from ways
) a
'''
total_edits_df = pandas.read_sql_query(query,conn)
print('There were ' + str(total_edits_df['total_edits'][0]) + ' total edits.')    
    
query = '''
SELECT nodes.user
    ,node_edits
    ,way_edits
    ,node_edits + way_edits AS total_edits
    ,(node_edits + way_edits) * 1.0 / 
        (SELECT COUNT(user) FROM (SELECT user FROM nodes UNION ALL SELECT user FROM ways)) * 100 
     AS percent_of_total
FROM (SELECT user, count(*) node_edits FROM nodes GROUP BY user) nodes
JOIN (SELECT user, count(*) way_edits FROM ways GROUP BY user) ways
ON nodes.user = ways.user
ORDER BY total_edits DESC;
'''
edits_df = pandas.read_sql_query(query,conn,index_col='user')
pprint.pprint(edits_df.round(2).head())
    
conn.close()


# graph of edits by user
# % of total edits made by the top 5 users - 70% of edits came from them, 38% from the top user
edits_df.sort_values('percent_of_total',ascending=False)['percent_of_total'].head().plot(kind='bar')

# final queries
conn = sqlite3.connect('SLC.db')

query = '''
SELECT value as amenity, COUNT(*) as [count]
FROM nodes_tags
WHERE key = 'amenity'
GROUP BY value
ORDER BY [count] DESC
LIMIT 10;
'''
df = pandas.read_sql_query(query,conn,index_col='amenity')
pprint.pprint(df)

query = '''
SELECT nodes_tags.value as restaurant, COUNT(*) as [count]
FROM nodes_tags 
    JOIN (SELECT DISTINCT(id) FROM nodes_tags WHERE value='restaurant') i
    ON nodes_tags.id=i.id
WHERE nodes_tags.key='name'
GROUP BY nodes_tags.value
HAVING [count] > 2
ORDER BY [count] DESC;
'''
df = pandas.read_sql_query(query,conn,index_col='restaurant')
pprint.pprint(df)
    
conn.close()