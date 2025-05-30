## High-level API

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

### Basic text extraction

The function outputs a full extract of the text content, with a spatial awareness: the algorithm tries to respect the original layout, as if characters of all sizes were approximately rendered on a fixed-size grid.

```Python
>>> #Extracting text of first page
>>> text = pdf.extract_page_text(doc, 0)
>>> print(text)
Hello World
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


> TO BE CONTINUED


