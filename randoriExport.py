#!/usr/bin/python3
"""
Example API module for exporting Randori data to CSV for all medium or higher
confidence and medium or higher target tempation assets.
Prior to running this code, ensure the environment variable
RANDORI_API_KEY is set to the path to the API file.
"""
import requests
import json
import os
import csv
from base64 import b64encode

APItoken="";
limit = 0;  # initially we may set the limit to 0 to get the total records
offset = 0;  # initial number of records to skip.

def getApiKey():
    api_token = os.getenv("RANDORI_API_KEY")
    #print("test: "+api_token)
    if api_token is None:
        print("Missing environment variable RANDORI_API_KEY.")
        print("Please export RANDORI_API_KEY=$RANDORI_API_TOKEN first.")
        exit(1)
    elif len(api_token) < 100:
        print("Len="+str(len(api_token)))
        print("This token appears too short. Please ensure the entire token"
              "added as an environment variable.")
        exit(1)
    return api_token

def getCsvData(endpoint, csvname):
    # Construct the full endpoint URL for use by requests
    global url
    url = RANDORI_PLATFORM_URL + endpoint
    try:
        response = requests.get(url, params=params, headers=headers)
        # check the server response code for success
        print("response.status_code: "+str(response.status_code))
        result = response.json()
        print("offset="+str(result['offset'])+" total="+str(result['total']))
    except Exception as e:    
        print("Response OR Result failed! Exception: "+e.message)
    return result   

def generateCSV(result):        
    if ('x' in locals()) and ('total' not in result or 'data' not in result):
        print("The server returned an unexpected response.")
        exit(1)

    # get the total number of records in the set to display to the user
    total_records = result['total']
    entity = endpoint.split('/')[-1]  # for the example endpoints, the last
    # component of the path is the type of entity we are querying.
    #print(f"Requesting data about {total_records} {entity}s from Randori")
    if total_records == 0:
        print('No records for entity, skipping')
        return
    # make further requests for records 10 at a time. Max value is 2000
    # Please update this value
    offset = 0  # initial number of records to skip.
    params['limit'] = 10
    print("url="+url+" total_records="+str(total_records))
    all_entities = []
    while offset <= total_records:
        try:
            # make the request for the next 10 records
            response = requests.get(
                url,
                params=params,
                headers=headers)
            # verify the result, if we ever get a non-200 response
            # something has gone wrong and we should stop making requests
            if response.status_code != 200:
                print("The server returned an unexpected reponse. "
                      "We got HTTP status code: {response.status_code}")
                exit(1)
            result = response.json()
            print("Gen: offset="+str(result['offset'])+" count="+str(result['count']))
            records = result['data']
            if result['count'] == 0:
                params['offset'] = 0
                break
            for record in records:
                all_entities.append(record)
            offset = offset + result['count']
            params['offset'] = offset
        except Exception as e:
            print('Offset/TotalRecords Exception was '+e.message)
    # finally, write out the data to a CSV file
    with open(csvname, 'w') as csvfile:
        # Dynamically get names of columns based on dictionary keys
        #print("entity[0]="+str(all_entities[0].values()))
        columns = all_entities[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        for entity in all_entities:
            writer.writerow(entity)
    print("Completed writing "+csvname)


try:
    APItoken = getApiKey()        
except Exception as e:
    print('APItoken Exception was '+e.message)

# Construct headers which send our API token
headers = {'Authorization': APItoken,
           "Content-Type": "application/json"}

RANDORI_PLATFORM_URL = "https://alpha.randori.io/"
# Randori Recon entity types (excluding service)
endpoints = ['recon/api/v1/hostname',
             'recon/api/v1/ip',
             'recon/api/v1/target',
             'recon/api/v1/service',
             'recon/api/v1/network'
             ]  

# Construct our complex query in JQuery querybuilder
query = {
    "condition": "AND",
    "rules": [
        {
            "field": "table.target_temptation",
            "operator": "greater_or_equal",
            "value": 25  # medium or higher target temptation
} ]
}

# We need the query to be a string in order to base64 encode it easily
query = json.dumps(query)
# Randori expects the 'q' query string to be base64 encoded
query = b64encode(query.encode()) 

# sort from highest to lowest             
params = {
        'q': query,
        'offset': offset,
        'limit': limit,
        'sort': '-target_temptation'}  


if __name__ == "__main__":
    try:
        for endpoint in endpoints:
            entity = endpoint.split('/')[-1]
            csvname = entity + '_randori_export.csv'
            print("endpoint="+endpoint+" csvname="+csvname)
            csvData = getCsvData(endpoint, csvname)
            if csvData:
                    generateCSV(csvData)
    except Exception as e:
        print('csvData Exception was '+e.message)

