"""Module pdfsyntax.api: Application Programming Interface"""

from .docstruct import *
from .filestruct import *
from .objects import *
from .text import *


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
    ret['Pages'] = number_pages(doc)
    ret['Updates'] = updates(doc)

    i = info(doc) or {}
    entries = '/Title /Author /Subject /Keywords /Creator /Producer'.split()
    for entry in entries:
        ret[entry[1:]] = text_string(i.get(entry)) or None    

    ret['CreationDate'] = text_string(i.get('/CreationDate')) or None
    ret['ModDate'] = text_string(i.get('/ModDate')) or None
    return ret


