"""Module pdfsyntax.docstruct: how objects represent a document"""

from typing import Callable
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
        res += f" with "
        i = len(self.index)
        if not changes(self):
            i -= 1
        res += f"{i} revisions(s)"
        if not changes(self):
            res += f", ready to start update/revision {len(self.index)}"
        else:
            res += f", current update/revision containing {len(changes(self))} modifications"
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


def memoize_obj_in_cache(idx: list, fdata: Callable, key: int, cache=None, rev=-1) -> list:
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
            bdata, a0, _ = fdata(index['abs_pos'], index['abs_next'] - index['abs_pos'])
            i, j, _ = next_token(bdata, a0)
            i, j, _ = next_token(bdata, j)
            if 'xref_stream' in index:
                i, j, _ = next_token(bdata, j)
                i, j, _ = next_token(bdata, j)
            text = bdata
            i_obj = parse_obj(text, i)
            if type(i_obj) == Stream:
                i_obj = i_obj['entries']
            obj.update(i_obj)
        cache[key] = obj    
    elif 'env_num' not in idx[rev][key]:
        bdata, a0, _ = fdata(idx[rev][key]['abs_pos'], idx[rev][key]['abs_next'] - idx[rev][key]['abs_pos'])
        i, j, _ = next_token(bdata, a0)
        i, j, _ = next_token(bdata, j)
        i, j, _ = next_token(bdata, j)
        i, j, _ = next_token(bdata, j)
        text = bdata
        obj = parse_obj(text, i)
        if key == 0 and type(obj) == Stream:
            obj = obj['entries']
        cache[key] = obj    
    else:
        container = idx[rev][key]['env_num']
        bdata, a0, _ = fdata(idx[rev][container]['abs_pos'], idx[rev][container]['abs_next'] - idx[rev][container]['abs_pos'])
        i, j, _ = next_token(bdata, a0)
        i, j, _ = next_token(bdata, j)
        i, j, _ = next_token(bdata, j)
        i, j, _ = next_token(bdata, j)
        text = bdata
        c_obj = parse_obj(text, i)
        cache[container] = c_obj
        offset = int(c_obj['entries']['/First'])
        nb_obj = int(c_obj['entries']['/N'])
        x_array = parse_obj(b'[' + c_obj['stream'][:offset] + b']')
        for x in range(nb_obj):
            cache[int(x_array[2 * x])] = parse_obj(c_obj['stream'], offset + int(x_array[2 * x + 1]))
        if key == 0 and type(cache[0]) == Stream:
            cache[0] = cache[0]['entries']
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


def build_cache(bdata: Callable, index: list) -> list:
    """Initialize cache with trailer and Root"""
    size = len(index[-1])
    cache = size * [None]
    memoize_obj_in_cache(index, bdata, 0, cache)
    return cache


def changes(doc: Doc, rev: int=-1):
    """List deleted/updated/added objects"""
    res = []
    current = doc.index[rev]
    if len(doc.index) == 1:
        previous = [None] * len(current)
    else:
        previous = doc.index[rev-1]
    ver = len(doc.index)-1
    for i in range(1, len(current)-1):
        if i < len(previous) - 1 and previous[i] == current[i]:
            continue
        elif previous[i] != None and current[i] == None:
            res.append((i, 'd'))
        elif previous[i] != None and current[i] != previous[i]:
            res.append((i, 'u'))
        else:
            res.append((i, 'a'))
    return res


def group_obj_into_stream(doc: Doc):
    """Provision a ObjStm object and tag all changes to target this envelope"""
    doc2 = add_object(doc, b'')
    current = doc2.index[-1]
    o_num = current[-2]['o_num']
    chgs = changes(doc)
    for i, _ in chgs:
        if i == o_num:
            print("continue")
            continue
        current[i]['env_num'] = o_num
    d = {'/Type': '/ObjStm', '/Length': 0, '/N': 0, '/First': 0, '/FirstLine': []}
    doc2.cache[o_num] = Stream(d, b'')
    return doc2


def version(doc: Doc) -> str:
    """Return PDF version"""
    bdata, a0, _ = doc.bdata(5, 3)
    ver = bdata[a0:a0+3]
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


def encrypted(doc: Doc) -> bool:
    """Detect if doc is encrypted"""
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
    """List pages with applied inherited attributes"""
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


def add_revision(doc: Doc) -> Doc:
    """Add new index for incremental update"""
    if len(changes(doc)) == 0:
        return doc
    ver = len(doc.index)
    current_v = doc.index[-1]
    new_cache = len(current_v) * [None]
    new_trailer = doc.cache[0].copy()
    new_trailer['/Prev'] = current_v[0].get('xref_table_pos') or current_v[0].get('xref_stream_pos')
    new_cache[0] = new_trailer
    new_index = doc.index.copy()
    new_trailer = {'o_num': 0, 'o_gen': 0, 'o_ver': ver, 'doc_ver': ver}
    new_v = [new_trailer] + [current_v[i] for i in range(1,len(current_v)-1)] + [None] 
    new_index.append(new_v)
    return Doc(doc.bdata, new_index, new_cache)


def prepare_revision(doc: Doc, rev:int = -1, idx:int = 0) -> bytes:
    """Build bytes representing incremental update"""
    res = b''
    chg = changes(doc, rev)
    if doc.index[rev][-1] or not chg:
        return res
    for num, _ in chg:
        memoize_obj_in_cache(doc.index, doc.bdata, num, doc.cache, rev=-1)
    fragments = build_fragments_and_xref(chg, doc.index[rev], doc.cache, idx, version(doc))
    for f in fragments:
        res += f
    return res


def rewind(doc: Doc) -> Doc:
    """Go back to previous revision"""
    if len(doc.index) == 1:
        return doc
    new_index = doc.index.copy()
    new_index.pop()
    new_current = new_index[-1].copy()
    #new_current[-1] = None
    new_index[-1] = new_current
    new_cache = build_cache(doc.bdata, new_index)
    return Doc(doc.bdata, new_index, new_cache)


def update_object(doc: Doc, num: int, new_o) -> Doc:
    """Update object in the current revision"""
    #if doc.index[-1][-1]:
    #    doc = add_version(doc)
    ver = len(doc.index)
    old_i = doc.index[-1][num]
    new_i = {'o_num': num, 'o_gen': old_i['o_gen'], 'o_ver': old_i['o_ver']+1, 'doc_ver': ver-1}
    new_index = doc.index.copy()
    new_index[-1] = doc.index[-1].copy()
    new_index[-1][-1] = None
    new_index[-1][num] = new_i
    new_cache = doc.cache.copy()
    new_cache[num] = new_o
    return Doc(doc.bdata, new_index, new_cache)


def add_object(doc: Doc, new_o) -> Doc:
    """Add new object at the end of current index"""
    if doc.index[-1][-1]:
        doc = add_revision(doc)
    ver = len(doc.index)
    num = len(doc.index[-1])-1
    new_i = {'o_num': num, 'o_gen': 0, 'o_ver': 0, 'doc_ver': ver-1}
    new_index = doc.index.copy()
    new_index[-1] = doc.index[-1].copy()
    new_index[-1].append(None)
    new_index[-1][-1] = None
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

