#!/usr/bin/env python3
import sys
import os.path
import pandas as pd
import re
import requests
import json
import csv
import subprocess

def clean_text(raw_text, cleanr):
    raw_text=re.sub(r'\s+',' ', raw_text).strip()
    cleantext = re.sub(cleanr, '', raw_text)
    return cleantext

def get_article(title, year):
    articleSearchUrl='https://app.dimensions.ai/discover/publication/results.json?search_text="%s"&search_type=kws&search_field=text_search&and_facet_year=%i'%(title.replace(" ", "%20"), year)
    articleSearchResponse = requests.get(articleSearchUrl)
    try:
    	article=articleSearchResponse.json()["docs"][0]
    except:
    	print("""!!The article %s from %s was not found in Dimensions,
    		You may need to edit the CSV file!!!"""%(title, year), file=sys.stderr)
    	return None
    return article

def get_referings(dimensionsId, distance):
    referingsSearchResponse = requests.get(
    'https://app.dimensions.ai/discover/publication/results.json?or_subset_publication_citations=%s'%dimensionsId)
    try:
        referingsSearchResponse=referingsSearchResponse.json()
    except:
        print("Unexpected document, it may be empty:", file=sys.stderr)
        print(referingsSearchResponse, file=sys.stderr)
        return []
    totalReferings=referingsSearchResponse["count"] if "count" in referingsSearchResponse else 0
    articleReferings=referingsSearchResponse["docs"] if "docs" in referingsSearchResponse else []
    
    print("\t"*distance+"Retrieving "+ str(totalReferings) + " referings...")
    while len(articleReferings) < totalReferings:
        try:
            cursor=referingsSearchResponse["navigation"]["results_json"].split("?")[-1]
        except:
            print("Cannot go further than " + str(len(articleReferings)), file=sys.stderr)
            break
        referingsSearchResponse = requests.get(
        'https://app.dimensions.ai/discover/publication/results.json?or_subset_publication_citations=%s&%s'%(dimensionsId, cursor))
        referingsSearchResponse=referingsSearchResponse.json()
        try:
            assert len(referingsSearchResponse["docs"]) > 0
        except:
            print("Empty referings, stopped searching at " + str(len(articleReferings)), file=sys.stderr)
            break
        articleReferings.extend(referingsSearchResponse["docs"])
    return articleReferings

def get_references(dimensionsId, distance):
    referenceSearchResponse = requests.get(
    'https://app.dimensions.ai/discover/publication/results.json?or_subset_publication_references=%s'%dimensionsId)
    try:
    	referenceSearchResponse=referenceSearchResponse.json()
    except:
        print("Unexpected document, it may be empty:", file=sys.stderr)
        print(referenceSearchResponse, file=sys.stderr)
        return []
    totalReferences=referenceSearchResponse["count"] if "count" in referenceSearchResponse else 0
    articleReferences=referenceSearchResponse["docs"] if "docs" in referenceSearchResponse else []

    print("\t"*distance+"Retrieving "+ str(totalReferences) + " references...")
    #5 references at a time, I could not find another way
    while len(articleReferences) < totalReferences:
        try:
            cursor=referenceSearchResponse["navigation"]["results_json"].split("?")[-1]
        except:
            print("Cannot go further than " + str(len(articleReferences)), file=sys.stderr)
            break
        referenceSearchResponse = requests.get(
        'https://app.dimensions.ai/discover/publication/results.json?or_subset_publication_references=%s&%s'%(dimensionsId, cursor))
        referenceSearchResponse=referenceSearchResponse.json()
        try:
            assert len(referenceSearchResponse["docs"]) > 0
        except:
            print("Empty references, stopped searching at " + str(len(articleReferences)), file=sys.stderr)
            break
        articleReferences.extend(referenceSearchResponse["docs"])
    return articleReferences

def fill_citations(citations, article, distance, articleReferences=[], articleReferings=[], inlibrary=False):
    assert distance >= 0
    if article["id"] in citations and citations[article["id"]]["level"] > 0:
        if distance <= citations[article["id"]]["level"]:
            print("\t"*distance+article["id"]+"[S]")
            return citations
        else:
            articleCitations={
                "references":[citations[refId]["article"] for refId in citations[article["id"]]["references"]],
                "referings":[citations[refId]["article"] for refId in citations[article["id"]]["referings"]]}
    elif distance > 0:
        articleCitations={
            "references":get_references(article["id"], distance),
            "referings":get_referings(article["id"], distance)}
    elif distance == 0:
        articleCitations={
            "references":[],
            "referings":[]}
    articleReferences=articleCitations["references"]
    articleReferings=articleCitations["referings"]
    
    print("\t"*distance+article["id"])
    for citationType in articleCitations:
        nRef=0
        for citation in articleCitations[citationType]:
            nRef+=1
            fill_citations(citations, citation, distance-1)
    citations[article["id"]]={
        "article":article, 
        "references":[reference["id"] for reference in articleReferences], 
        "referings":[refering["id"] for refering in articleReferings], 
        "level":distance,
        "inlibrary":inlibrary}
    return citations

def write_network(network, filename):
    with open(filename+".json", 'w', encoding='utf-8') as f:
        json.dump(network, f, ensure_ascii=False, indent=4)

def write_nodes(network, filename, ext, sep="\t", quotes=csv.QUOTE_NONE):
    with open(filename+ext, 'w') as nodefile:
        fieldnames = [
            "title", "author_list", "journal_title",
            "html_escaped_title", "publisher_source", "pub_class",
            "doi", "id", "pub_year", 
            "times_cited", "altmetric", "source_title"]
        writer = csv.DictWriter(nodefile, fieldnames=fieldnames+["inlibrary"], extrasaction="ignore", delimiter=sep, quoting=quotes)

        writer.writeheader()
        for identifier in network:
            lineToWrite={key:clean_text(str(item), cleanr) for key, item in network[identifier]["article"].items() if key in fieldnames}
            lineToWrite["inlibrary"]=network[identifier]["inlibrary"]
            try:
                writer.writerow(lineToWrite)
            except:
                print("There is a problem with the line:")
                print(lineToWrite)

def write_edges(network, filename, ext, sep="\t", quotes=csv.QUOTE_NONE):
    with open(filename+ext, "w") as edgefile:
        writer = csv.writer(edgefile, delimiter=sep, quoting=quotes)
        writer.writerow(["Source", "Target", "Weigth"])
        for identifier in network:
            for referenceId in network[identifier]["references"]:
                writer.writerow([network[identifier]["article"]["id"], referenceId, "1"])
            for referingId in network[identifier]["referings"]:
                writer.writerow([referingId, network[identifier]["article"]["id"], "1"])

if __name__ == "__main__":
    sys.stderr = open('err.log', 'w')
    cleanr = re.compile('(<.*?>|\")')
    ext=".tsv"

    #CSV file from Zotero, name of network
    assert len(sys.argv)==3

    if os.path.isfile(sys.argv[2]+".json"):
        with(open(sys.argv[2]+".json", "r")) as netf:
            citations=json.load(netf)
    else:
        citations={}
    
    with open(sys.argv[1], "r") as f:
        rawArticles=pd.read_csv(f)
    #TO DO : parallelize cause it takes forever
    for index, rawArticle in rawArticles.iterrows():
        print("Processing " + rawArticle["Key"] + " article...")
        cleanedTitle=clean_text(rawArticle["Title"], cleanr)
        year=int(rawArticle["Publication Year"])

        article=get_article(cleanedTitle, year)
        if article is not None:
        	citations=fill_citations(citations, article, 1, inlibrary=True)
    write_network(citations, sys.argv[2])
    write_nodes(citations, sys.argv[2]+"-nodes", ext)
    write_edges(citations, sys.argv[2]+"-edges", ext)
    subprocess.check_call(['./remove-dup-edges.sh', sys.argv[2]+"-edges"+ext])
