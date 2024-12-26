## CLI

### Usage
The general form of the CLI usage is:

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
The generated HTML looks like the raw PDF file with the following additions:
* Pretty-print dictionary object
* Extract an object contained in an object stream and insert it in the flow like a regular object
* Decompress stream and display a small part of it
* Turn indirect object reference into hyperlink
* Turn offset reference (for example a /Prev entry) into hyperlink
* Put some color on key names (for example /Type)
* Display offset of an object

The command writes on the standard output so you need to redirect to a file that you can open in your browser:

    python3 -m pdfsyntax browse file.pdf > inspection_file.pdf


[This is a link to an EXAMPLE](https://pdfsyntax.dev/simple_text_string.html) of a full inspection output that you can browse.

Here is another example, as a partial screenshot:
![PDFSyntax screenshot](https://raw.githubusercontent.com/desgeeko/pdfsyntax/main/docs/screenshot.png)


> TO BE CONTINUED
