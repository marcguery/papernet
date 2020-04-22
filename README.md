# papernet

I used the [Dimensions](https://app.dimensions.ai/discover/publication) database to build networks of articles based on their references.

The input CSV file is obtained using [Zotero](https://www.zotero.org/) export tool.

You may want to change the Python interpreter.

# Usage

```bash
buildNetwork.py <input.csv> output.json
makeNetworkFiles.py output.json nodes edges
```
