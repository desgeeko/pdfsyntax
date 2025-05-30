## API

This article introduces the principles.

Quick access to specific articles:
- [High-level API](api_high.md)
- [Low-level API](api_low.md) 

### Pure functions

Most functions are pure and are exposed both as basic functions and as instance methods of a Doc object: in the function signatures found in the following sections, a `doc` first argument can read as `self`. For example both samples are equivalent:

```Python
>>> #Function pattern
>>> from pdfsyntax import readfile, metadata
>>> doc = readfile("samples/simple_text_string.pdf")
>>> m = metadata(doc)
```

```Python
>>> #Method pattern
>>> import pdfsyntax as pdf
>>> doc = pdf.readfile("samples/simple_text_string.pdf")
>>> m = doc.metadata()
```

Every time a function is applied to a Doc object, the function returns a new object built as a shallow copy of the input.

### Incremental updates

PDFSyntax tracks document incremental updates made possible by appending new or updated objects at the end of an original PDF file (and the matching XREF section). A revision, if greater than 0, indicates that incremental updates have been appended.
By default, a newly opened document by PDFSyntax is ready to write modifications in the next revision.
The `rewind` function rolls back to the previous revision. The `commit` function closes the current revision and open the next one.


For example this file contains 2 revisions (0 and 1) and PDFSyntax has initialized the doc object to open revision 2:

```Python
>>> import pdfsyntax as pdf
>>> doc = pdf.readfile("samples/add_text_annotation.pdf")
>>> doc
<PDF Doc in revision 2 with 0 modified object(s)>
```

The `rewind` function rolls back to the previous revision. Let's rewind to revision 0:

```Python
>>> doc = pdf.rewind(doc) # to revision 1
>>> doc = pdf.rewind(doc) # to revision 0
>>> doc
<PDF Doc in revision 0 with 7 modified object(s)>
```

After one or several modifications, the `commit` function closes the current revision and opens the next one:

```Python
>>> doc = pdf.rotate(doc)
>>> doc = pdf.commit(doc)
>>> doc
<PDF Doc in revision 1 with 0 modified object(s)>
```

### Squashing

By default incremental updates stack up but it is possible to `squash` a document in order to combine all revisions into a single one. in this example the last document is equivalent to the first one (same appearance), but it is only made of one revision. As this revision is like a document started from scratch, its revision is 0 and all its 7 internal objects look like new ones:

```Python
>>> doc90 = pdf.rotate(doc)
>>> doc90
<PDF Doc in revision 1 with 1 modified object(s)>
>>> docs = pdf.squash(doc90)
>>> docs
<PDF Doc in revision 0 with 7 modified object(s)>
```

### File I/O

The `writefile` function dumps the document with all the incremental updates appended at the end of the original data.

```Python
>>> from pdfsyntax import readfile, writefile
>>> doc = readfile("samples/simple_text_string.pdf")
>>> doc90 = pdf.rotate(doc)
>>> writefile(doc90, "rotated_doc.pdf")
```


> TO BE CONTINUED

