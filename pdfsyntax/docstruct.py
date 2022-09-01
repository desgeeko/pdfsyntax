"""Module pdfsyntax.docstruct: how objects represent a document"""

from .objects import *
from .filestruct import *
from .text import *
from collections import namedtuple


Doc = namedtuple('Doc', 'bdata index cache')

class Doc(Doc):
    def __repr__(self):
        res = ""
        res += f"bdata={self.bdata[:30]}...{self.bdata[-30:]} ({len(self.bdata)} bytes)\n"
        res += f"index=list of list, {len(self.index)} update(s) with {len(self.index[0])} objects\n"
        if self.cache:
            present = [i for i, obj in enumerate(self.cache) if obj is not None]
            res += f"cache=list, {len(present)} / {len(self.cache)} objects loaded\n"
        else:
            res += f"cache=None\n"
        return res

EOL = b'\r\n'
SPACE = EOL + b'\x00\x09\x0c\x20'


def memoize_obj_in_cache(idx: list, bdata: bytes, key: int, cache=None, rev=-1) -> list:
    """Parse indirect object whose number is [key] and return a cache filled at index [key]
    cache argument may be:
    - a list that is updated,
    - or None that is replaced with an empty list
    """
    if cache is None:
        cache = (key + 1) * [None]
    if  cache[key] != None:
        return cache
    if key == 0:
        index = idx[rev][key]
        if type(index) != list:
            indexes = [index]
        else:
            indexes = index
        obj = {}
        for index in indexes:
            i, j, _ = next_token(bdata, index['abs_pos'])
            i, j, _ = next_token(bdata, j)
            text = bdata
            i_obj = parse_obj(text, i)
            if 'stream_def' in i_obj:
                i_obj = i_obj['stream_def']
            obj.update(i_obj)
        cache[key] = obj    
    elif 'env_num' not in idx[rev][key]:
        i, j, _ = next_token(bdata, idx[rev][key]['abs_pos'])
        i, j, _ = next_token(bdata, j)
        i, j, _ = next_token(bdata, j)
        i, j, _ = next_token(bdata, j)
        text = bdata
        obj = parse_obj(text, i)
        if key == 0 and 'stream_def' in obj:
            obj = obj['stream_def']
        cache[key] = obj    
    else:
        container = idx[rev][key]['env_num']
        i, j, _ = next_token(bdata, idx[rev][container]['abs_pos'])
        i, j, _ = next_token(bdata, j)
        i, j, _ = next_token(bdata, j)
        i, j, _ = next_token(bdata, j)
        text = bdata
        c_obj = parse_obj(text, i)
        cache[container] = c_obj
        offset = int(c_obj['stream_def']['/First'])
        nb_obj = int(c_obj['stream_def']['/N'])
        x_array = parse_obj(b'[' + c_obj['stream_content'][:offset] + b']')
        for x in range(nb_obj):
            cache[int(x_array[2 * x])] = parse_obj(c_obj['stream_content'], offset + int(x_array[2 * x + 1]))
        if key == 0 and 'stream_def' in cache[0]:
            cache[0] = cache[0]['stream_def']
    return cache


def get_object(doc: Doc, obj):
    """Return raw object or the target of an indirect reference"""
    if isinstance(obj, complex) == True:
        ref = int(obj.imag)
        res = memoize_obj_in_cache(doc.index, doc.bdata, ref, doc.cache)
        return res[ref]
    else: 
        return obj


def get_pages(doc: Doc, node) -> list:
    """Recursively list the pages of a node"""
    accu = []
    if node['/Type'] == '/Pages':
        for i in node['/Kids']:
            kid = get_object(doc, i)
            accu = accu + get_pages(doc, kid)
        return accu
    elif node['/Type'] == '/Page':
        return[node]


def build_page_list(doc: Doc) -> list:
    """List the pages of a document"""
    trailer = get_object(doc, 0j)
    catalog = get_object(doc, trailer['/Root'])
    pages = get_object(doc, catalog['/Pages'])
    page_index = get_pages(doc, pages)
    return page_index


def build_cache(bdata: bytes, index: list) -> list:
    """Initialize cache with trailer and Root"""
    size = len(index[-1])
    cache = size * [None]
    memoize_obj_in_cache(index, bdata, 0, cache)
    cat = int(cache[0]['/Root'].imag)
    memoize_obj_in_cache(index, bdata, cat, cache)
    return cache


def version(doc: Doc) -> bytes:
    """Return PDF version"""
    ver = doc.bdata[5:8]
    cat = catalog(doc)
    if '/Version' in cat and cat['/Version'] > ver:
            return cat['/Version']
    return ver


def updates(doc: Doc) -> int:
    """Return the number of updates the document received"""
    upd = len(doc.index) - 1
    return upd


def trailer(doc: Doc):
    """Return doc trailer dictionary"""
    return get_object(doc, 0j)


def catalog(doc: Doc):
    """Return doc Root/Catalog dictionary"""
    return get_object(doc, trailer(doc)['/Root'])


def info(doc: Doc):
    """Return doc Info dictionary if present"""
    trail = trailer(doc)
    info = trail.get('/Info')
    if info:
        return get_object(doc, info)


def pages(doc: Doc):
    """Return doc Pages dictionary"""
    return get_object(doc, catalog(doc)['/Pages'])


def number_pages(doc: Doc):
    """Return doc number of pages"""
    return pages(doc)['/Count']


#def get_fonts(doc: Doc, page_num: int) -> dict:
#    """Return the dictionary of fonts used in page number page_num"""
#    page_idx = build_page_list(doc)
#    fonts = {}
#    resources = get_object(doc, page_idx[page_num]['/Resources'])
#    l = get_object(doc, resources['/Font'])
#    for f in l:
#        res = {}
#        font = get_object(doc, l[f])
#        for k in font:
#            res[k] = font[k]
#        if res['/Subtype'] == '/Type1':
#            res['TRANSCO'] = dec_empty
#        else:
#            #toU = get_object(doc, font[b'/ToUnicode'])
#            res['TRANSCO'] = dec_unicode
#        fonts[f] = res
#    return fonts


#def print_page(doc: Doc, page_num: int) -> None:
#    """ """
#    page_idx = build_page_list(doc)
#    f = get_fonts(doc, page_num)
#    c = get_object(doc, page_idx[page_num]['/Contents'])
#    for j in extract_text(c['stream_content']):
#        _, _, font, _, text = j
#        dec_fun = f[font]['TRANSCO']
#        if len(text) == 16:
#            print(dec_fun(text))
#   return None

