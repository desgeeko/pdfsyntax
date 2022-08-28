"""Module pdfsyntax.api: Application Programming Interface"""

from .docstruct import *
from .filestruct import *

def init_doc(bdata: bytes, use_cache=True) -> tuple:
    """ """
    chrono = build_chrono_from_xref(bdata)
    index = build_index_from_chrono(chrono)
    if use_cache == False:
        cache = None
    else:
        cache = build_cache(bdata, index)
    doc = Doc(bdata, index, cache)
    return doc, chrono

def load(fp, use_cache=True) -> Doc:
    """ """
    bdata = fp.read()
    doc, _ = init_doc(bdata, use_cache)
    return doc

def loads(bdata, use_cache=True) -> Doc:
    """ """
    doc, _ = init_doc(bdata, use_cache)
    return doc

def read_pdf(filename: str, use_cache=True) -> Doc:
    """ """
    bfile = open(filename, 'rb')
    bdata = bfile.read()
    bfile.close()
    doc, _ = init_doc(bdata, use_cache)
    return doc

def metadata(doc: Doc) -> dict:
    """ """
    ret = {}
    #ret['version'] = version(doc)
    ret['pages'] = number_pages(doc)
    ret['updates'] = updates(doc)
    i = info(doc) or {}
    ret['title'] = i.get('/Title', "N/A")
    ret['author'] = i.get('/Author', "N/A")
    ret['subject'] = i.get('/Subject', "N/A")
    ret['keywords'] = i.get('/Keywords', "N/A")
    ret['creator'] = i.get('/Creator', "N/A")
    ret['producer'] = i.get('/Producer', "N/A")
    ret['creationdate'] = i.get('/CreationDate', "N/A")
    ret['moddate'] = i.get('/ModDate', "N/A")
    return ret


