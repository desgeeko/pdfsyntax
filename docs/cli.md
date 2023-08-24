## CLI

### Usage
The general form of the CLI usage is:

    python3 -m pdfsyntax COMMAND FILE

You can get quick insights on a PDF file with these commands:
- `overview` outputs text data about the structure and the metadata. 
- `inspect` outputs static html data that lets you browse the internal structure of the PDF file: the PDF source is pretty-printed and augmented with hyperlinks.

### `overview`
The output shows information about:
- the structure : Version, Pages, Revisions, etc...
- the metadata : Title, Author, Subject, etc...

### `inspect`
The generated HTML looks like the raw PDF file with the following additions:
* Pretty-print dictionary object
* Extract an object contained in an object stream and insert it in the flow like a regular object
* Decompress stream and display a small part of it
* Turn indirect object reference into hyperlink
* Turn offset reference (for example a /Prev entry) into hyperlink
* Put some color on key names (for example /Type)
* Display offset of an object

The command writes on the standard output so you need to redirect to a file that you can open in your browser:

    python3 -m pdfsyntax inspect file.pdf > inspection_file.pdf

#### Screenshot
![PDFSyntax screenshot](https://raw.githubusercontent.com/desgeeko/pdfsyntax/main/docs/screenshot.png)


> TO BE CONTINUED
