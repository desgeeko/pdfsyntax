PDFSyntax
=========

*A Python library to inspect and modify the internal structure of a PDF file*

## Introduction

The project is focused on chapter 7 ("Syntax") of the Portable Document Format (PDF) Specification.

PDFSyntax is lightweight (no dependencies) and written from scratch in pure Python. 

1. CLI: It started as a command-line interface to inspect the internal structure of a PDF file.
2. API: Now the internal functions are being exposed as a toolkit for PDF read/write operations.

## Project status

WORK IN PROGRESS! This is ALPHA quality software. The API may change anytime.
Next on TO-DO list:
- Cut & append pages
- Lossless compression
- More filters
- Improve text extraction
- Augment text extraction with layout detection

## Design

PDFSyntax favors non-destructive edits allowed by the PDF Specification: by default incremental updates are added at the end of the original file.

It is mostly made of simple functions working on built-in types and named tuples. Shallow copying of the Doc object structure performed by pure functions offers some kind of - *experimental* - immutability.

## Installation

You can install from PyPI:

    pip install pdfsyntax

## CLI overview

Please refer to the [CLI README](https://github.com/desgeeko/pdfsyntax/blob/main/docs/cli.md) for details.

The general form of the CLI usage is:

    python3 -m pdfsyntax COMMAND FILE

You can get quick insights on a PDF file with these commands:
- `overview` outputs text data about the structure and the metadata. 
- `browse` outputs static html data that lets you browse the internal structure of the PDF file: the PDF source is pretty-printed and augmented with hyperlinks.
- `text` outputs extracted text spatially, as if it was a kind of scan.

## API overview

Please refer to the [API README](https://github.com/desgeeko/pdfsyntax/blob/main/docs/api.md) for details.

PDFSyntax is mostly made of simple functions. Example:

```Python
>>> from pdfsyntax import readfile, metadata
>>> doc = readfile("samples/simple_text_string.pdf")
>>> metadata(doc) #returns a Python dict whose keys are 'Title', 'Author', 'Subject', etc...
```

The Doc object is probably the only dedicated class you will need to handle. It is a black box that stores all the internal states of a document:
- content that is cached/memoized from an original file,
- modifications that add/modifiy/delete content and that are tracked as incremental updates.

```Python
>>> doc
<PDF Doc with 1 revisions(s), ready to start update/revision 2, cache loaded with 0 / 7 objects>
```

This object exposes as a method the same metadata function, therefore you can get the same result with:

```Python
>>> doc.metadata() #returns a Python dict whose keys are 'Title', 'Author', 'Subject', etc...
```

Low-level functions like `get_object` or `update_object` allow you to directly access and manipulate the inner objects of the document structure.
You may also use higher-level functions like `rotate`:

```Python
>>> from pdfsyntax import rotate, writefile
>>> doc180 = rotate(doc, 180) #rotate pages by 180°
```

The orignal object is unchanged and a new object is created with an incremental update (revision 2) that encloses the ongoing orientation modification:

```Python
>>> doc180
<PDF Doc with 2 revisions(s), current update/revision containing 1 modifications, cache loaded with 3 / 7 objects>
```

You then can write the modified PDF to disk. Note that the resulting file contains a new section appended to the original content. You may cut this section to revert the change.

```Python
>>> writefile(doc180, "rotated_doc.pdf")
```


## Open-Source, not Open-Contribution yet

PDFSyntax is [MIT licensed](https://github.com/desgeeko/pdfsyntax/blob/main/LICENCE) but is currently closed to contributions.
> Personal note: this is a pet projet of mine and my time is limited. First I need to focus on my roadmap (new features and refactoring) and then I will happily accept contributions when everything is a little more stabilised. 


