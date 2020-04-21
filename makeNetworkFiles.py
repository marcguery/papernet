#!/usr/bin/env python3.6
import sys
import json

#JSON file from the builder of this repo, name of node file, name of edge file
assert len(sys.argv)==4

with open(sys.argv[1], "r") as f:
    network=json.load(f)

ext=".tsv"
sep="\t"

nodes="\n".join(sep.join([
    network[identifier]["article"]["title"],
    network[identifier]["article"]["author_list"].split(",")[0],
    network[identifier]["article"]["journal_title"],
    network[identifier]["article"]["html_escaped_title"],
    network[identifier]["article"]["publisher_source"],
    network[identifier]["article"]["publisher"],
    network[identifier]["article"]["pub_class"],
    str(network[identifier]["article"]["aff_country_count"]),
    str(network[identifier]["article"]["aff_org_count"]),
    network[identifier]["article"]["created_in_dimensions"],
    network[identifier]["article"]["doi"],
    network[identifier]["article"]["id"],
    network[identifier]["article"]["issue"] if "issue" in network[identifier]["article"] else "",
    network[identifier]["article"]["pages"] if "pages" in network[identifier]["article"] else "",
    network[identifier]["article"]["pmid"] if "pmid" in network[identifier]["article"] else "",
    network[identifier]["article"]["pub_date"],
    str(network[identifier]["article"]["pub_year"]),
    network[identifier]["article"]["volume"] if "volume" in network[identifier]["article"] else "",
    str(network[identifier]["article"]["times_cited"]),
    str(network[identifier]["article"]["score"]),
    str(network[identifier]["article"]["altmetric_id"]),
    network[identifier]["article"]["source_title"],
    network[identifier]["article"]["pub_class_id"]]) for identifier in network)

edges="\n".join("\n".join(sep.join([network[identifier]["article"]["id"], reference["id"], "1"]) for reference in network[identifier]["references"]) for identifier in network)

with open(sys.argv[2]+ext, "w") as f:
    f.write(nodes)

with open(sys.argv[3]+ext, "w") as f:
    f.write(sep.join(["Source", "Target", "Weigth"])+"\n")
    f.write(edges)
