PDFSyntax
=========

*A Python PDF parsing library and tool built on top to browse the internal structure of a PDF file*

## Introduction

The project is focused on chapter 7 ("Syntax") of the Portable Document Format (PDF) Specification.

PDFSyntax is lightweight (no dependencies) and written from scratch in pure Python. 

1. CLI: It started as a command-line interface to inspect the internal structure of a PDF file.
2. API: Now the internal functions are being exposed as a tooklit for PDF read/write operations.

## Project status

WORK IN PROGRESS! This is ALPHA quality software.

# Design

PDFSyntax favors non-destructive edits allowed by the PDF Specification: by default incremental updates are added at the end of the original file.

It is mostly made of simple functions working on built-in types and named tuples. Shallow copying of the Doc object structure performed by pure functions offers some kind of - *experimental* - immutability.

## Installation

You can install from PyPI:

    pip install pdfsyntax


## CLI

You can get quick insights on a PDF file with commands:
- `overview` outputs text data about the structure and the metadata. 
- `inspect` outputs static html data that lets you browse the internal structure of the PDF file: the PDF source is pretty-printed and augmented with hyperlinks.

The general form of the CLI usage is:

    python3 -m pdfsyntax COMMAND FILE

Please refer to the [CLI README](https://github.com/desgeeko/pdfsyntax/blob/main/docs/cli.md) for details.

## API

Please refer to the [API README](https://github.com/desgeeko/pdfsyntax/blob/main/docs/api.md) for details.


> TO BE CONTINUED

