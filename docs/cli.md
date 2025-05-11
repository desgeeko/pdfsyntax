## CLI

### Usage
The general form of the CLI usage is:

    pdfsyntax COMMAND FILE

Or this longer form if you installed from source:

    python3 -m pdfsyntax COMMAND FILE

You can get quick insights on a PDF file with these commands:
- `overview` outputs text data about the structure and the metadata. 
- `disasm` outputs a dump of the file structure on the terminal.
- `text` spatially extracts text content on all pages, as if it was a kind of scan.
- `browse` outputs static html data that lets you browse the internal structure of the PDF file: the PDF source is pretty-printed and augmented with hyperlinks.

### `overview`
The output shows information about:
- the structure : Version, Pages, Revisions, etc...
- the metadata : Title, Author, Subject, etc...

### `disasm`
The output shows a terse and greppable view of the file internal structure.
Please refer to the [Disassembler article](https://github.com/desgeeko/pdfsyntax/blob/main/docs/disassembler.md) for details.

### `text`
The output shows a full extract of the text content, with a spatial awareness: the algorithm *tries* to respect the original layout, as if characters of all sizes were approximately rendered on a fixed-size grid.

### `fonts`
The output shows a list of fonts used in the file, with the following tabular data:
- Name
- Type
- Encoding
- Object number and generation number, comma separated
- Number of pages where it occurs

### `browse`
This command generates HTML output that looks like the raw PDF file with additionnal hyperlinks and information that expose its internal structure and relations between its objects.
Redirect the standard output to a file that you can open in your browser:

    pdfsyntax browse file.pdf > inspection_file.html

Please refer to the [Browse article](https://github.com/desgeeko/pdfsyntax/blob/main/docs/browse.md) for details.


> TO BE CONTINUED
