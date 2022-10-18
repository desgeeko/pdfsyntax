PDFSyntax
=========

*A Python PDF parsing library and tool built on top to browse the internal structure of a PDF file*

## Introduction

The project is focused on chapter 7 ("Syntax") of the Portable Document Format (PDF) Specification.

PDFSyntax is lightweight (no dependencies) and written from scratch in pure Python. 

It is mostly made of simple functions working on built-in types and named tuples. Shallow copying of the Doc object structure performed by pure functions offers some kind of - *experimental* - immutability.

PDFSyntax favors non-destructive edits allowed by the PDF Specification: by default incremental updates are added at the end of the original file.

WORK IN PROGRESS!


## CLI

### Features
The generated HTML looks like the raw PDF file with the following additions:
* Pretty-print dictionary object
* Extract an object contained in an object stream and insert it in the flow like a regular object
* Decompress stream and display a small part of it
* Turn indirect object reference into hyperlink
* Turn offset reference (for example a /Prev entry) into hyperlink
* Put some color on key names (for example /Type)
* Display offset of an object

### Screenshot
![PDFSyntax screenshot](https://raw.githubusercontent.com/desgeeko/pdfsyntax/main/screenshot.png)

### Usage
Generate the HTML file and open it in your browser:

    python3 -m pdfsyntax inspect file.pdf > inspection.html

## API

### Usage

Most functions are pure and are exposed both as basic functions and as instance methods of a Doc object: in the function signatures found in the following sections, a `doc` first argument can read as `self`.
For example both samples are equivalent:

```Python
#Function pattern
m = metadata(doc)
```

```Python
#Method pattern
m = doc.metadata()
```

### I/O Functions

| Function | Description |
| --- | --- |
| `read(filename: str) -> Doc` | Loads a PDF from the filesystem into a Doc object |
| `write(doc: Doc, filename: str) -> None` | Writes a Doc object to the filesystem into a PDF file |

### Versioning Functions

| Function | Description |
| --- | --- |
| `rewind(doc: Doc) -> Doc` | Cancels current changes and go back to previous revision |

### Inspection Functions

| Function | Description |
| --- | --- |
| `metadata(doc: Doc) -> Dict` | Returns the document metadata (title, author, ...) |
| `structure(doc: Doc) -> Dict` | Returns the document structure (PDF version, nb of pages, nb of revisions, encryption, paper format) |



