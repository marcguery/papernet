# papernet

I used the [Dimensions](https://app.dimensions.ai/discover/publication) database to build networks of articles based on their references so you can target key articles in a field of interest you are discovering.

The input CSV file is obtained using [Zotero](https://www.zotero.org/) export tool.

You may want to change the Python interpreter.

# Usage

```bash
buildNetwork.py <input.csv> output.json
makeNetworkFiles.py output.json nodes edges
```

# Example

Using the node and edge files generated by 17 published articles (and some analytic tools from [Cytoscape](https://cytoscape.org/)), we have a clear indication of which article is not yet included in your bibliography (black circles) and which one is the most cited (biggest nodes).

<img src="pics/network-example.png" style="zoom:100%;" />