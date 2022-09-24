"""Module pdfsyntax.docstruct: how objects represent a document"""

from .objects import *
from .filestruct import *
from .text import *
from collections import namedtuple
from copy import deepcopy


INHERITABLE_ATTRS = '/Resources /MediaBox /CropBox /Rotate'.split()


Doc = namedtuple('Doc', 'bdata index cache')

class Doc(Doc):
    def __repr__(self):
        res = "<PDF Doc"
        res += f" containing "
        if len(self.index) > 1:
            res += f"{len(self.index)-1} revision(s) and "
        res += f"one current update with {len(changes(self))} modifications"
        if self.cache:
            present = 0
            for i in range(1, len(self.index[-1])-1):
                if self.cache[i] is not None:
                    present += 1 
            res += f", cache loaded with {present} / {len(self.cache)-2} objects>\n"
        else:
            res += f", cache=None>\n"
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


def follow_pages_rec(doc: Doc, num, inherited={}) -> list:
    """Recursively list the pages of a node"""
    accu = []
    node = get_object(doc, num)
    if node['/Type'] == '/Pages':
        for kid in node['/Kids']:
            e = {k: node.get(k) for k in INHERITABLE_ATTRS if node.get(k) is not None}
            inherited.update(e)
            accu = accu + follow_pages_rec(doc, kid, inherited.copy())
        return accu
    elif node['/Type'] == '/Page':
        return[(num, inherited)]


def build_cache(bdata: bytes, index: list) -> list:
    """Initialize cache with trailer and Root"""
    size = len(index[-1])
    cache = size * [None]
    memoize_obj_in_cache(index, bdata, 0, cache)
    return cache


def changes(doc: Doc):
    """ """
    res = []
    current = doc.index[-1]
    if len(doc.index) == 1:
        previous = [None] * len(current)
    else:
        previous = doc.index[-2]
    ver = len(doc.index)-1
    for i in range(1, len(current)-1):
        if previous[i] != None and current[i] == None:
            res.append((i, 'd'))
        elif previous[i] != None and current[i] != previous[i]:
            res.append((i, 'u'))
        else:
            res.append((i, 'a'))
    return res


def version(doc: Doc) -> str:
    """Return PDF version"""
    ver = doc.bdata[5:8]
    cat = catalog(doc)
    if '/Version' in cat and cat['/Version'] > ver.decode('ascii'):
            return cat['/Version'].decode('ascii')
    return ver.decode('ascii')


def updates(doc: Doc) -> int:
    """Return the number of updates the document received"""
    upd = len(doc.index) - 1
    return upd


def trailer(doc: Doc):
    """Return doc trailer dictionary"""
    return get_object(doc, 0j)


def encrypted(doc: Doc):
    """ """
    trail = trailer(doc)
    encrypt = trail.get('/Encrypt')
    if encrypt:
        return True
    else:
        return False


def catalog(doc: Doc):
    """Return doc Root/Catalog dictionary"""
    return get_object(doc, trailer(doc)['/Root'])


def info(doc: Doc):
    """Return doc Info dictionary if present"""
    trail = trailer(doc)
    info = trail.get('/Info')
    if info:
        return get_object(doc, info)


def number_pages(doc: Doc):
    """Return doc number of pages"""
    p = get_object(doc, catalog(doc)['/Pages'])
    return p['/Count']


def collect_inherited_attr_pages(doc: Doc) -> list:
    """ """
    p = get_object(doc, catalog(doc)['/Pages'])
    page_index = follow_pages_rec(doc, p)
    return page_index


def pages(doc: Doc) -> list:
    """ """
    pl = []
    for num, in_attr in collect_inherited_attr_pages(doc):
        temp = deepcopy(get_object(doc, num))
        for a in in_attr:
            if a not in temp:
                temp[a] = in_attr[a]
        pl.append(temp)
    return pl


def add_version(doc: Doc) -> Doc:
    """ """
    if len(changes(doc)) == 0:
        return doc
    ver = len(doc.index)
    current_v = doc.index[-1]
    new_cache = len(current_v) * [None]
    new_trailer = doc.cache[0].copy()
    new_trailer['/Prev'] = current_v[0]['xref_table_pos']
    new_cache[0] = new_trailer
    new_index = doc.index.copy()
    new_trailer = {'o_num': 0, 'o_gen': 0, 'o_ver': ver, 'doc_ver': ver}
    new_v = [new_trailer] + [current_v[i] for i in range(1,len(current_v)-1)] + [None] 
    new_index.append(new_v)
    return Doc(doc.bdata, new_index, new_cache)


def prepare_version(doc: Doc) -> list:
    """ """
    res = b''
    chg = changes(doc)
    fragments = build_fragments(chg, doc.index[-1], doc.cache, len(doc.bdata))
    for f in fragments:
        res += f
    return res


def update_object(doc: Doc, num: int, new_o) -> Doc:
    """ """
    ver = len(doc.index)
    old_i = doc.index[-1][num]
    new_i = {'o_num': num, 'o_gen': old_i['o_gen'], 'o_ver': old_i['o_ver']+1, 'doc_ver': ver-1}
    new_index = doc.index.copy()
    new_index[-1] = doc.index[-1].copy()
    new_index[-1][num] = new_i
    new_cache = doc.cache.copy()
    new_cache[num] = new_o
    return Doc(doc.bdata, new_index, new_cache)


def add_object(doc: Doc, new_o) -> Doc:
    """ """
    ver = len(doc.index)
    num = len(doc.index[-1])-1
    new_i = {'o_num': num, 'o_gen': 0, 'o_ver': 0, 'doc_ver': ver-1}
    new_index = doc.index.copy()
    new_index[-1] = doc.index[-1].copy()
    new_index[-1].append(None)
    new_index[-1][num] = new_i
    new_cache = doc.cache.copy()
    new_cache.append(None)
    new_cache[num] = new_o
    return Doc(doc.bdata, new_index, new_cache)


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

