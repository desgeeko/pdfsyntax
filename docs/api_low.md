## Low-level API

### Objects

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


> TO BE CONTINUED


