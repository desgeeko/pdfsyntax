## API

### Principles

#### Pure functions

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

#### Incremental updates

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

#### Squashing

By default incremental updates stack up but it is possible to `squash` a document in order to combine all revisions into a single one. in this example the last document is equivalent to the first one (same appearance), but it is only made of one revision. As this revision is like a document started from scratch, its revision is 0 and all its 7 internal objects look like new ones:

```Python
>>> doc90 = pdf.rotate(doc)
>>> doc90
<PDF Doc in revision 1 with 1 modified object(s)>
>>> docs = pdf.squash(doc90)
>>> docs
<PDF Doc in revision 0 with 7 modified object(s)>
```

#### File I/O

The `writefile` function dumps the document with all the incremental updates appended at the end of the original data.

```Python
>>> from pdfsyntax import readfile, writefile
>>> doc = readfile("samples/simple_text_string.pdf")
>>> doc90 = pdf.rotate(doc)
>>> writefile(doc90, "rotated_doc.pdf")
```

### File information

`structure` and `metadata` are functions showing general information about the document.

```Python
>>> #File structure
>>> structure(doc)
{'Version': '1.4', 'Pages': 1, 'Revisions': 1, 'Encrypted': False, 'Paper of 1st page': '215x279mm or 8.5x11.0in (US Letter)'}

>>> #File metadata
>>> metadata(doc)
{'Title': None, 'Author': None, 'Subject': None, 'Keywords': None, 'Creator': None, 'Producer': None, 'CreationDate': None, 'ModDate': None}
```

### High-level transformation

`rotate` turns pages relatively to their current position by multiples of 90 degrees clockwise. NB: It takes into account the inherited attributes from the page hierarchy.

```Python
>>> #Default rotation applies 90 degrees to all pages
>>> doc90 = rotate(doc)

>>> #Apply 180 degrees to first two page
>>> doc180 = doc.rotate(180, [0, 1])
```

_WARNING_: To REMOVE something means it still exists but it is hidden.

`remove_pages` cuts a set of pages from the document as incremental update: they are not permanently deleted because it is still possible to revert to the previous revision.

```Python
>>> #Remove first 3 pages of a 6-page doc
>>> second_half_doc = pdf.remove_pages(doc, {0, 1, 2})
```

`keep_pages` does the opposite:

```Python
>>> #Keep last 3 pages of a 6-page doc
>>> second_half_doc = pdf.keep_pages(doc, {3, 4, 5})
```

`concat` merges documents:

```Python
>>> #Concatenate doc2 pages after doc1 pages into a new doc
>>> doc = pdf.concat(doc1, doc2)
```

A Doc object can also be seen as a virtual list of pages. It is possible to use operators to slice or concatenate:

```Python
>>> #Equivalent to pdf.keep_pages(doc, {3, 4, 5})
>>> last_3_pages = doc[3:]

>>> #Equivalent to pdf.concat(doc1, doc2)
>>> doc = doc1 + doc2
```

`add_text_annotation` inserts a simple text annotation in a page.

```Python
>>> annotated_doc = add_text_annotation(doc, 0, "abcdefg", [100, 100, 100, 100])
```

### Low-level access and modification

#### Objects

`trailer` and `catalog` give access to the starting point of the object tree. 

```Python
>>> #Access to document trailer
>>> doc.trailer()
{'/Root': 1j, '/Size': 8, '/Prev': 603}

>>> #Access to document catalog as specified in the /Root entry of the trailer
>>> doc.catalog()
{'/Pages': 3j, '/Outlines': 2j, '/Type': '/Catalog'}
```

`1j` is a complex number (!) representing indirect reference `1 0 R`. Why? Because the approach is to map PDF object types to Python basic built-in types as much as possible, and it is a concise way to show both the object number (as the imaginary part) and the generation number (as the real part). Moreover the generation is very often equal to zero, so the real part is not shown.
You may think of the `j` as a "jump" to another object :)

`get_object` gives direct access to indirect objects.

```Python
>>> #Access to document catalog, given that the trailer redirects to 1j for root
>>> #(equivalent to catalog fonction)
>>> doc.get_object(1j)
{'/Pages': 3j, '/Outlines': 2j, '/Type': '/Catalog'}
```

#### Pages

Page index is a tree structure where attributes can be inherited from parent nodes. For convenience `flat_page_tree` returns an ordered list of document pages and specifies inherited attributes that should apply to each page.

```Python
>>> #Each item of the list is a tuple with the page object reference and its inherited attributes
>>> doc = pdf.readfile("samples/simple_text_string.pdf")
>>> pdf.flat_page_tree(doc)
[(4j, {})]
>>> #(In this example, nothing is inherited from upper nodes)
```

The `page` function goes further by merging inherited attributes with local attributes of each page and giving the result in a list.

```Python
>>> #Equivalent list with computed page attribues
>>> pdf.pages(doc)
[{'/Resources': {'/Font': {'/F1': 7j}, '/ProcSet': 6j},
  '/Contents': 5j,
  '/MediaBox': [0, 0, 612, 792],
  '/Parent': 3j,
  '/Type': '/Page'}]
```


> TO BE CONTINUED

