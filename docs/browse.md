## Browse

### Introduction
Inspecting the internal structure of a PDF file involves a lot of things (decompression, parsing, xref indexing, etc...) in order to make sense of the raw bytes.

PDFSyntax takes care of the processing and proposes a visualization approach that consists in adding information and hyperlinks on top of a text that is a mostly a pretty-print of the PDF data once uncompressed. It respects the physical flow of the file while offering a logical navigation between revisions (incremental updates) and between objects.

### Architecture
PDFSyntax is a self-contained Python package - without any dependency - and is principally a low-level PDF library.
The `browse` command is its highest and most visible part. It produces static HTML content that offers sufficient interactivity: JavaScript may be disabled.

### Demo
Please try the [**LIVE DEMO**](https://pdfsyntax.dev/simple_text_string.html) of a full static HTML output that you can browse, at [https://pdfsyntax.dev/simple_text_string.html](https://pdfsyntax.dev/simple_text_string.html) (hosted on GitHub Pages).

Here is the same example, as a partial screenshot:
![PDFSyntax screenshot](https://raw.githubusercontent.com/desgeeko/pdfsyntax/main/docs/screenshot.png)

NB: this is the output produced for the [_Simple Text String_](https://github.com/desgeeko/pdfsyntax/raw/main/samples/simple_text_string.pdf) example file from the PDF Specification.

### Usage
PDFSyntax can be installed from the GitHub repo (no dependency) or from PyPI:

    pip install pdfsyntax

Redirect the standard output to a file that you can open in your browser:

    python3 -m pdfsyntax browse file.pdf > inspection_file.html

### Features
The generated HTML "looks" like an augmented raw PDF file with the following additional work:
* Add a reverse index: links to where an object is used
* Add a page index in a navigation menu
* Add a physical minimap in a navigation menu
* Indent to pretty-print dictionary objects
* Extract objects contained in object streams and insert them in the flow like regular objects
* Decompress streams and display a small part of it
* Turn indirect object references into hyperlinks
* Turn offset references (for example a /Prev entry) into hyperlinks
* Display file offsets of objects in a left margin
* Put some color on important names (for example /Type)
* Put some color on warnings (for example the presence of /JS)
* Light & dark modes

> WARNING: Encrypted files are not supported yet

> WORK IN PROGRESS: New features are on the roadmap