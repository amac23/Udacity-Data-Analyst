# Wrangle OpenStreetMap Data Project

*Udacity Description: You will choose any area of the world in https://www.openstreetmap.org and use data munging techniques, such as assessing the quality of the data for validity, accuracy, completeness, consistency and uniformity, to clean the OpenStreetMap data for a part of the world that you care about. Finally, you will choose either MongoDB or SQL as the data schema to complete your project.*

---

### Write-Up Files:
* Wrangle+OpenStreetMap+Data+Project+Write-Up.html
    * This is the document containing answers to the rubric questions

### Map Files:
* SLC.osm
    * This is the OpenStreetMap data file
* SLC_sample.osm
    * This is a sample of the OpenStreetMap data file 

### Python Code Files:
* Wrangle OpenStreetMap Data Project Write-Up.ipynb
    * Jupyter Notebook file containing the write-up
* audit_postcodes.py
    * This file looks at all postcodes and returns those that aren't in the right format (##### or #####-####)
* audit_state_names.py
    * This file looks at all the state names and returns those that aren't UT
* audit_street_names.py
    * This file looks at all the street names and returns those not in the list of expected street names
* data_cleansing_conversion.py
    * This file cleanses the 3 fields that were audited while loading all data into csv files
* sql_data_load_and_queries.py
    * This file loads the csv files into a sqlite database and runs queries to explore the data

### SQL Schema Files:
* data_wrangling_schema.sql
    * This file is used to create the tables in the sqlite database
