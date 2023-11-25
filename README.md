# ZTM_data_parser
Parser for the ZTM public data.

Most importantly exposes two functions: `parse_file` and `get_connections`. First one returns the whole data file parsed into dictionaries and lists with the same structure as the original file. All data is stored as strings. The second one returns a list of tuples with the names of communication line and the `networkx.DiGraph`, where last pair is the whole graph of the public communication. The `networkx` package is the only requirement for this parser.

```
from ztm_parser import parse_file, get_connections

path = 'path\to\your\file.TXT'
ztm_data = parse_file(path)
line_type_graphs = get_connections(ztm_data)
```
