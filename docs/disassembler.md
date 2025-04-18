## A PDF Disassembler

### Introduction
PDFSyntax is built from the ground up to become a PDF inspection and transformation library/tool. On this path, while debugging,  it is sometimes useful to directly dump the **structure** - and **not the content** - of PDF files on the command line (either files to transform or file produced by a transformation).

This _"Disassembler"_ function is exposed on the command line interface of the library. By design its output is terse and greppable.

As stated by the PDF Specification, _PDF is not a programming language, and a PDF file is not a program._ But there is an analogy: cross-references allow to jump to different portions of a file with absolute (regular indirect objects) or relative addressing (indirect objects embedded in object streams).

### Usage
PDFSyntax can be installed from the GitHub repo (no dependency) or from PyPI:

    pip install pdfsyntax

Then the following command prints a dump on the standard output:

    python3 -m pdfsyntax disasm FILE

### Example
Here is the output produced for the [_Simple Text String_](https://github.com/desgeeko/pdfsyntax/raw/main/samples/simple_text_string.pdf) example file from the PDF Specification:

```
$ python3 -m pdfsyntax disasm samples/simple_text_string.pdf
+ 000 [8  ]               comment                        %PDF-1.4           
+ 008 [1  ]               void                                              
+ 009 [70 ]            @- ind_obj   1,0           dict   /Catalog  !/JS!    
+ 079 [1  ]               void                                              
+ 080 [48 ]            @- ind_obj   2,0           dict   /Outlines  !/JS!   
+ 128 [1  ]               void                                              
+ 129 [62 ]            @- ind_obj   3,0           dict   /Pages  !/JS!      
+ 191 [1  ]               void                                              
+ 192 [183]            @- ind_obj   4,0           dict   /Page  !/JS!       
+ 375 [1  ]               void                                              
+ 376 [121] 100% _     @- ind_obj   5,0           stream !/JS!              
+ 497 [1  ]               void                                              
+ 498 [27 ]            @- ind_obj   6,0           array                     
+ 525 [1  ]               void                                              
+ 526 [119]            @- ind_obj   7,0           dict   /Font  !/JS!       
+ 645 [1  ]               void                                              
+ 646 [198]               xreftable                      !/JS!  /Root=1,0   
-                      -@ xref      0,65535   000 free                      
-                      -@ xref      1,0       009 inuse                     
-                      -@ xref      2,0       080 inuse                     
-                      -@ xref      3,0       129 inuse                     
-                      -@ xref      4,0       192 inuse                     
-                      -@ xref      5,0       376 inuse                     
-                      -@ xref      6,0       498 inuse                     
-                      -@ xref      7,0       526 inuse                     
+ 844 [1  ]               void                                              
+ 845 [13 ]               startxref           646                           
+ 858 [1  ]               void                                              
+ 859 [5  ]               comment                        %%EOF              
+ 864 [1  ]               void                                              
+ 865 [1  ]               void                                              
$
```

This example is very basic because of its xref table and single uncompressed (100%) content stream. Inside a more complex file you would probably find something like this:

```
+ 053123 [461  ] 86%  _Flate        ind_obj   52,0               stream   /XRef  /Root=50,0   
```


### Grep examples
Ignore void spaces (separators) and focus on real objects:

    python3 -m pdfsyntax disasm FILE | grep -v void

List all xref entries of all tables or streams:

    python3 -m pdfsyntax disasm FILE | grep xref

Ignore detail lines:

    python3 -m pdfsyntax disasm FILE | grep "^+"

Search all mentions of an indirect object, both in itself and in xref:

    python3 -m pdfsyntax disasm FILE | grep 52,


### Columns

Most of the columns are collapsable in order to save horizontal space. For example the position (`#2`) may have a maximum width of 10 digits but for small files the unecessary leading zeros are removed.

| Column | Description |
|--------|-------------|
| `1`     | `+` for a region with absolute positionning, `-` for a detail line (xref, /XRef, /ObjStm)|
| `2`     | Position, absolute (`+`) or relative (`-`)|
| `3`     | Size in bytes|
| `4`     | Percentage compressed size / plain size|
| `5`     | Applied filter(s)|
| `6`     | Sequence number of embedded object|
| `7`     | Indirect reference of **envelope** object|
| `8`     | Index check, @ for OK and ? for NOK|
| `9`     | Region type|
| `10`     | Indirect reference of **this** object|
| `11`    | Addressing mode of xref, envelope or absolute|
| `12`    | Address of xref|
| `13`    | Type of PDF object|
| `14`    | Some detail : most important keys for dict, excerpt for comment|


> Warning: Encrypted files are not supported yet. 

