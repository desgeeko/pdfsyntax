"""Module pdfsyntax.docstruct: how objects represent a document"""

from .objects import *
from .filestruct import *
from .text import *
import re
import zlib
from collections import namedtuple

Doc = namedtuple('Doc', 'bdata index cache')

EOL = b'\r\n'
SPACE = EOL + b'\x00\x09\x0c\x20'

def isRef(obj):
    """ """
    if isinstance(obj, dict) == True and '_REF' in obj:
        return obj['_REF']
    else:
        return False

def get_nodes(dict_or_list):
    """ """
    if isinstance(dict_or_list, dict) == True:
        return [dict_or_list]
    else:
        return dict_or_list

def memoize_obj_in_cache(idx, bdata, key, cache, rev=-1):
    """ """
    #print(idx[rev][key])
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
            i = beginning_next_non_empty_line(bdata, index['abs_pos'])
            text = bdata
            i_obj = parse_obj(text, i)
            if 'stream_def' in i_obj:
                i_obj = i_obj['stream_def']
            obj.update(i_obj)
        cache[key] = obj    
    elif 'env_num' not in idx[rev][key]:
        i = beginning_next_non_empty_line(bdata, idx[rev][key]['abs_pos'])
        text = bdata
        obj = parse_obj(text, i)
        if key == 0 and 'stream_def' in obj:
            obj = obj['stream_def']
        cache[key] = obj    
    else:
        container = idx[rev][key]['env_num']
        #print(key)
        #print(container)
        i = beginning_next_non_empty_line(bdata, idx[rev][container]['abs_pos'])
        text = bdata
        c_obj = parse_obj(text, i)
        cache[container] = c_obj
        #print(c_obj)
        offset = int(c_obj['stream_def'][b'/First'])
        nb_obj = int(c_obj['stream_def'][b'/N'])
        x_array = parse_obj(b'[' + c_obj['stream_content'][:offset] + b']')
        for x in range(nb_obj):
            cache[int(x_array[2 * x])] = parse_obj(c_obj['stream_content'], offset + int(x_array[2 * x + 1]))
        if key == 0 and 'stream_def' in cache[0]:
            cache[0] = cache[0]['stream_def']
    return cache

def follow_node(idx, bdata, obj, cache):
    """ """
    if isinstance(obj, dict) == True and '_REF' in obj:
        ref = int(obj['_REF'])
        memoize_obj_in_cache(idx, bdata, ref, cache)
        return cache[ref]
    else: return obj

def get_pages(idx, bdata, node, cache):
    """ """
    accu = []
    #print(node)
    if node[b'/Type'] == b'/Pages':
        for i in node[b'/Kids']:
            #print(i)
            ref = isRef(i)
            if ref:
                memoize_obj_in_cache(idx, bdata, int(ref), cache)
                accu = accu + get_pages(idx, bdata, cache[int(ref)], cache)
        return accu
    elif node[b'/Type'] == b'/Page':
        return[node]

def build_page_list(doc):
    """ """
    bdata, idx, cache = doc
    cache = memoize_obj_in_cache(idx, bdata, 0, cache)
    cat = int(cache[0][b'/Root']['_REF'].split()[0])
    cache = memoize_obj_in_cache(idx, bdata, cat, cache)
    pages = follow_node(idx, bdata, cache[cat][b'/Pages'], cache)
    page_index = get_pages(idx, bdata, pages, cache)
    return page_index

def build_cache(bdata, index):
    """ """
    size = len(index[-1])
    cache = memoize_obj_in_cache(index, bdata, 0, size * [None])
    cat = int(cache[0][b'/Root']['_REF'].split()[0])
    cache = memoize_obj_in_cache(index, bdata, cat, cache)
    return cache

def init_doc(bdata):
    """ """
    chrono = build_chrono_from_xref(bdata)
    index = build_index_from_chrono(chrono)
    cache = build_cache(bdata, index)
    doc = Doc(bdata, index, cache)
    return doc, chrono

def get_fonts(doc, page_num):
    """ """
    bdata, idx, cache = doc
    page_idx = build_page_list(doc)
    fonts = {}
    r = follow_node(idx, bdata, page_idx[page_num][b'/Resources'], cache)
    l = follow_node(idx, bdata, r[b'/Font'], cache)
    for f in l:
        res = {}
        font = follow_node(idx, bdata, l[f], cache)
        for k in font:
            res[k] = font[k]
        if res[b'/Subtype'] == b'/Type1':
            res['TRANSCO'] = dec_empty
        else:
            toU = follow_node(idx, bdata, font[b'/ToUnicode'], cache)
            res['TRANSCO'] = dec_unicode
        fonts[f] = res
    return fonts

def print_page(doc, page_num):
    """ """
    bdata, idx, cache = doc
    page_idx = build_page_list(doc)
    f = get_fonts(doc, page_num)
    c = follow_node(idx, bdata, page_idx[page_num][b'/Contents'], cache)
    for j in extract_text(c['stream_content']):
        _, _, font, _, text = j
        dec_fun = f[font]['TRANSCO']
        if len(text) == 16:
            print(dec_fun(text))
    return None

def load(fp):
    """ """
    bdata = fp.read()
    doc, _ = init_doc(bdata)
    return doc

def loads(bdata):
    """ """
    doc, _ = init_doc(bdata)
    return doc

def read_pdf(filename):
    """ """
    bfile = open(filename, 'rb')
    bdata = bfile.read()
    bfile.close()
    doc, _ = init_doc(bdata)
    return doc


