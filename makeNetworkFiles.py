#!/usr/bin/env python3.6
import re
import sys
import json
import csv

def clean_text(raw_text, cleanr):
    raw_text=re.sub(r'\s+',' ', raw_text).strip()
    cleantext = re.sub(cleanr, '', raw_text)
    return cleantext

#JSON file from the builder of this repo, name of node file, name of edge file
assert len(sys.argv)==4

with open(sys.argv[1], "r") as f:
    network=json.load(f)

ext=".tsv"
sep="\t"
quoteStatus=csv.QUOTE_NONE

with open(sys.argv[2]+ext, 'w') as nodefile:
    fieldnames = [
        "title", "author_list", "journal_title",
        "html_escaped_title", "publisher_source", "pub_class",
        "doi", "id", "pub_year", 
        "times_cited", "altmetric", "source_title"]
    writer = csv.DictWriter(nodefile, fieldnames=fieldnames, extrasaction="ignore", delimiter=sep, quoting=quoteStatus)

    writer.writeheader()
    cleanr = re.compile('(<.*?>|\")')
    for identifier in network:
        lineToWrite={key:clean_text(str(item), cleanr) for key, item in network[identifier]["article"].items() if key in fieldnames}
        try:
            writer.writerow(lineToWrite)
        except:
            print(lineToWrite)
            exit(1)

with open(sys.argv[3]+ext, "w") as edgefile:
    writer = csv.writer(edgefile, delimiter=sep,quoting=quoteStatus)
    writer.writerow(["Source", "Target", "Weigth"])
    for identifier in network:
        if network[identifier]["references"]!=[]:
            for reference in network[identifier]["references"]:
                writer.writerow([network[identifier]["article"]["id"], reference["id"], "1"])
