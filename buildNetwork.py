#!/usr/bin/env python3.6
import sys
import pandas as pd
import re
import requests
import json

#CSV file from Zotero, name of JSON file
assert len(sys.argv)==3

def cleanhtml(raw_html, cleanr):
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

cleanr = re.compile('<.*?>')

with open(sys.argv[1], "r") as f:
    rawArticles=pd.read_csv(f)

references={article["Key"]:{"article":{}, "references":[]} for index, article in rawArticles.iterrows()}
#TO DO : parallelize cause it takes forever
for index, article in rawArticles.iterrows():
    print("Processing " + article["Key"] + " article...")
    cleanedTitle=cleanhtml(article["Title"], cleanr)
    articleSearchUrl="https://app.dimensions.ai/discover/publication/results.json?search_text=%s&search_type=kws&search_field=text_search"%(cleanedTitle.replace(" ", "%20"))
    articleSearchResponse = requests.get(
    articleSearchUrl)
    identifier=articleSearchResponse.json()["docs"][0]["id"]
    referenceSearchResponse = requests.get(
    'https://app.dimensions.ai/old/details/publication/%s/related_citations.json'%identifier)
    referenceSearchResponse=referenceSearchResponse.json()
    totalReferences=referenceSearchResponse["count"]
    articleReferences=referenceSearchResponse["docs"]
    cursor=referenceSearchResponse["navigation"]["more.json"].split("?")[-1]

    print("Retrieving "+ str(totalReferences) + " references...")
    #5 references at a time, I could not find another way
    while len(articleReferences) < totalReferences:
        referenceSearchResponse = requests.get(
        'https://app.dimensions.ai/old/details/publication/%s/related_citations.json?%s'%(identifier, cursor))
        referenceSearchResponse=referenceSearchResponse.json()
        articleReferences.extend(referenceSearchResponse["docs"])
        cursor=referenceSearchResponse["navigation"]["more.json"].split("?")[-1]
    
    references[article["Key"]]["article"]=articleSearchResponse.json()["docs"][0]
    references[article["Key"]]["references"]=articleReferences

with open(sys.argv[2], 'w', encoding='utf-8') as f:
    json.dump(references, f, ensure_ascii=False, indent=4)
