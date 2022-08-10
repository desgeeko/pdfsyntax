"""Module pdfsyntax.api: Application Programming Interface"""

from .docstruct import *
from .filestruct import *

def init_doc(bdata: bytes) -> tuple:
    """ """
    chrono = build_chrono_from_xref(bdata)
    index = build_index_from_chrono(chrono)
    cache = build_cache(bdata, index)
    doc = Doc(bdata, index, cache)
    return doc, chrono

def load(fp) -> Doc:
    """ """
    bdata = fp.read()
    doc, _ = init_doc(bdata)
    return doc

def loads(bdata) -> Doc:
    """ """
    doc, _ = init_doc(bdata)
    return doc

def read_pdf(filename: str) -> Doc:
    """ """
    bfile = open(filename, 'rb')
    bdata = bfile.read()
    bfile.close()
    doc, _ = init_doc(bdata)
    return doc

def info(doc: Doc) -> dict:
    """ """
    ret = {}
    ret['version'] = version(doc)
    return ret


