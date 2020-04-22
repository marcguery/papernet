#!/usr/bin/env python3.6
import sys
import pandas as pd
import re
import requests
import json

def clean_html(raw_html, cleanr):
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

def get_article(title, year):
    articleSearchUrl='https://app.dimensions.ai/discover/publication/results.json?search_text="%s"&search_type=kws&search_field=text_search&and_facet_year=%i'%(title.replace(" ", "%20"), year)
    articleSearchResponse = requests.get(articleSearchUrl)
    article=articleSearchResponse.json()["docs"][0]
    return article


def get_references(dimensionsId):
    referenceSearchResponse = requests.get(
    'https://app.dimensions.ai/details/sources/publication/%s/related_citations.json'%dimensionsId)
    referenceSearchResponse=referenceSearchResponse.json()
    totalReferences=referenceSearchResponse["count"] if "count" in referenceSearchResponse else 0
    articleReferences=referenceSearchResponse["docs"] if "docs" in referenceSearchResponse else []

    print("Retrieving "+ str(totalReferences) + " references...")
    #5 references at a time, I could not find another way
    while len(articleReferences) < totalReferences:
        try:
            cursor=referenceSearchResponse["navigation"]["more.json"].split("?")[-1]
        except:
            print("Cannot go further than " + str(len(articleReferences)))
            break
        referenceSearchResponse = requests.get(
        'https://app.dimensions.ai/details/sources/publication/%s/related_citations.json?%s'%(dimensionsId, cursor))
        referenceSearchResponse=referenceSearchResponse.json()
        try:
            assert len(referenceSearchResponse["docs"]) > 0
        except:
            print("Empty references, stopped searching at " + str(len(articleReferences)))
            break
        articleReferences.extend(referenceSearchResponse["docs"])
    return articleReferences

def fill_references(references, article, articleReferences, degree):
    if degree > 0:
        degree-=1
        articleReferences=get_references(article["id"])
        nRef=0
        for reference in articleReferences:
            nRef+=1
            if degree > 0:
                print(str(nRef)+"/"+str(len(articleReferences))+"...")
            if reference["id"] not in references or (degree==1 and references[reference["id"]]["references"]==[]) or degree > 1:
                fill_references(references, reference, [], degree)
            else:
                print("Skipping " + reference["id"] + " at leaf+" + str(degree))
    references[article["id"]]={"article":article, "references":articleReferences}
    return references

#CSV file from Zotero, name of JSON file
assert len(sys.argv)==3

cleanr = re.compile('<.*?>')

with open(sys.argv[1], "r") as f:
    rawArticles=pd.read_csv(f)

references={}
#TO DO : parallelize cause it takes forever
for index, rawArticle in rawArticles.iterrows():
    print("Processing " + rawArticle["Key"] + " article...")
    cleanedTitle=clean_html(rawArticle["Title"], cleanr)
    year=int(rawArticle["Publication Year"])

    article=get_article(cleanedTitle, year)

    references=fill_references(references, article, [], 2)

with open(sys.argv[2], 'w', encoding='utf-8') as f:
    json.dump(references, f, ensure_ascii=False, indent=4)
