## API

### Usage

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

### Low-level access to object tree

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

### Pages

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

### Incremental updates

PDFSyntax tracks document incremental updates made possible by appending new or updated objects at the end of an original PDF file (and the matching XREF section). The `Revisions` entry of the `structure` function result, if greater than 1, indicates that incremental updates have been appended.
By default, a newly opened document by PDFSyntax is ready to write modifications in the next revision.
The `rewind` function rolls back to the previous revision. The `commit` function closes the current revision and open the next one.

```Python
>>> import pdfsyntax as pdf
>>> doc = pdf.readfile("samples/add_text_annotation.pdf")
>>> doc.structure()
{'Version': '1.4', 'Pages': 1, 'Revisions': 2, 'Encrypted': False, 'Paper of 1st page': '215x279mm or 8.5x11.0in (US Letter)'}

>>> #This file contains 2 revisions and PDFSyntax has initialized the doc object for a future revision 3

>>> doc.get_object(4j)
{'/Annots': 8j, '/Resources': {'/Font': {'/F1': 7j}, '/ProcSet': 6j}, '/Contents': 5j, '/MediaBox': [0, 0, 612, 792], '/Parent': 3j, '/Type': '/Page'}

>>> #In its current state, the page (object 4) contains an annotation
>>> #Let's rewind to revision 1

>>> doc = doc.rewind() # to revision 2
>>> doc = doc.rewind() # to revision 1

>>> doc.get_object(4j)
{'/Resources': {'/Font': {'/F1': 7j}, '/ProcSet': 6j}, '/Contents': 5j, '/MediaBox': [0, 0, 612, 792], '/Parent': 3j, '/Type': '/Page'}

>>> #The annotation was not present in the initial revision of the file
```

### High-level transformation

`add_text_annotation` inserts a simple text annotation in a page.

```Python
>>> annotated_doc = add_text_annotation(doc, 0, "abcdefg", [100, 100, 100, 100])
```

`rotate` turns pages relatively to their current position by multiples of 90 degrees clockwise. NB: It takes into account the inherited attributes from the page hierarchy.

```Python
>>> #Default rotation applies 90 degrees to all pages
>>> doc90 = rotate(doc)

>>> #Apply 180 degrees to first two page
>>> doc180 = doc.rotate(180, [1, 2])
```

> TO BE CONTINUED

