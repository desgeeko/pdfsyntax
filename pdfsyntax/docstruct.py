"""Module pdfsyntax.docstruct: how objects represent a document"""

from typing import Callable
from .objects import *
from .filestruct import *
from .text import *
from collections import namedtuple
from copy import deepcopy


INHERITABLE_ATTRS = '/Resources /MediaBox /CropBox /Rotate'.split()


Doc = namedtuple('Doc', 'index cache data')

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
            res += f", cache loaded with {present} / {len(self.cache)-1} objects>\n"
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
    if 'DELETED' in idx[rev][key]:
        return cache
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
            bdata, a0, _, _ = fdata(index['abs_pos'], index['abs_next'] - index['abs_pos'])
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
        bdata, a0, _, _ = fdata(idx[rev][key]['abs_pos'], idx[rev][key]['abs_next'] - idx[rev][key]['abs_pos'])
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
        bdata, a0, _, _ = fdata(idx[rev][container]['abs_pos'], idx[rev][container]['abs_next'] - idx[rev][container]['abs_pos'])
        i, j, _ = next_token(bdata, a0)
        i, j, _ = next_token(bdata, j)
        i, j, _ = next_token(bdata, j)
        i, j, _ = next_token(bdata, j)
        text = bdata
        c_obj = parse_obj(text, i)
        if container > key:
            cache += (container-key) * [None]
        cache[container] = c_obj
        offset = int(c_obj['entries']['/First'])
        nb_obj = int(c_obj['entries']['/N'])
        x_array = parse_obj(b'[' + c_obj['stream'][:offset] + b']')
        for x in range(nb_obj):
            if int(x_array[2 * x]) >= len(cache):
                cache += (int(x_array[2 * x])-len(cache)+1) * [None]
            cache[int(x_array[2 * x])] = parse_obj(c_obj['stream'], offset + int(x_array[2 * x + 1]))
        if key == 0 and type(cache[0]) == Stream:
            cache[0] = cache[0]['entries']
    return cache


def get_object(doc: Doc, obj):
    """Return raw object or the target of an indirect reference"""
    if isinstance(obj, complex) == True:
        ref = int(obj.imag)
        res = memoize_obj_in_cache(doc.index, doc.data[-1]['fdata'], ref, doc.cache)
        return deepcopy(res[ref])
    else: 
        return deepcopy(obj)


def flat_page_tree(doc: Doc, num=None, inherited={}, max_nb=None) -> list:
    """Recursively list the pages of a node"""
    accu = []
    if num:
        node = get_object(doc, num)
    else:
        node = get_object(doc, catalog(doc)['/Pages'])
    if node['/Type'] == '/Pages':
        for kid in node['/Kids']:
            e = {k: node.get(k) for k in INHERITABLE_ATTRS if node.get(k) is not None}
            inherited.update(e)
            accu = accu + flat_page_tree(doc, kid, inherited.copy(), max_nb)
            if max_nb is not None and len(accu) == max_nb:
                return accu
        return accu
    elif node['/Type'] == '/Page':
        return[(num, inherited)]


def build_cache(fdata: Callable, index: list) -> list:
    """Initialize cache with trailer"""
    size = len(index[-1])
    cache = size * [None]
    memoize_obj_in_cache(index, fdata, 0, cache)
    return cache


def changes(doc: Doc, rev: int=-1):
    """List deleted/updated/added objects"""
    res = []
    current = doc.index[rev]
    if len(doc.index) == 1:
        previous = [None] * len(current)
    else:
        previous = doc.index[rev-1]
    for i in range(1, len(current)):
        if i > len(previous)-1:
            res.append((i, 'a'))
        elif i < len(previous) and previous[i] == current[i]:
            pass
        elif previous[i] != None and 'DELETED' not in previous[i] and 'DELETED' in current[i]:
            res.append((i, 'd'))
        elif previous[i] != None and current[i] != previous[i]:
            res.append((i, 'u'))
        else:
            res.append((i, 'a'))
    return res


def group_obj_into_stream(doc: Doc):
    """Provision a ObjStm object and tag all changes to target this envelope"""
    doc2, _ = add_object(doc, b'')
    current = doc2.index[-1]
    o_num = current[-2]['o_num']
    chgs = changes(doc)
    for i, _ in chgs:
        if i == o_num:
            #print("continue")
            continue
        current[i]['env_num'] = o_num
    d = {'/Type': '/ObjStm', '/Length': 0, '/N': 0, '/First': 0, '/FirstLine': []}
    doc2.cache[o_num] = Stream(d, b'')
    return doc2


def version(doc: Doc) -> str:
    """Return PDF version"""
    fdata = doc.data[0]['fdata']
    bdata, a0, _, _ = fdata(5, 3)
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


def hybrid(doc: Doc) -> bool:
    """Detect if doc is hybrid"""
    if len(doc.index) >= 2 and doc.index[1][0].get('xref_stm'):
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


def pages(doc: Doc, max_nb=None) -> list:
    """ """
    pl = []
    for num, in_attr in flat_page_tree(doc, max_nb=max_nb):
        temp = deepcopy(get_object(doc, num))
        for a in in_attr:
            if a not in temp:
                temp[a] = in_attr[a]
        pl.append(temp)
    return pl


def revision_index(doc: Doc, rev=-1) -> int:
    index = 0
    if rev == -1:
        rev = len(doc.data)-1
    for i in range(rev):
        data = doc.data[i]
        if 'eof_cut' in data:
            index = data['eof_cut']
        else:
            index += len(data['bdata'])
    return index


def gen_fdata(fdata: Callable, index: int, bdata: bytes):
    def new_fdata(start_pos: int, length: int) -> tuple:
        if start_pos > index:
            start_pos = start_pos - index
            if start_pos == -1 and length == 0:
                return (None, None, None, len(bdata))
            if length == -1:
                length = len(bdata) - start_pos
            if start_pos == -1:
                i = len(bdata) - length
            else:
                i = start_pos
            return (bdata, i, 0, min(len(bdata) - start_pos, length))
        else:
            return fdata(start_pos, length)
    return new_fdata


def add_revision(doc: Doc) -> Doc:
    """Add new index for incremental update"""
    if len(changes(doc)) == 0:
        return doc
    ver = len(doc.index)
    current_v = doc.index[-1]
    new_cache = len(current_v) * [None]
    new_trailer = doc.cache[0].copy()
    if type(current_v[0]) == list: #Linearized
        new_trailer['/Prev'] = current_v[0][1].get('xref_table_pos') or current_v[0][1].get('xref_stream_pos')
    else:
        new_trailer['/Prev'] = current_v[0].get('xref_table_pos') or current_v[0].get('xref_stream_pos')
    new_cache[0] = new_trailer
    new_index = doc.index.copy()
    new_trailer = {'o_num': 0, 'o_gen': 0, 'o_ver': ver, 'doc_ver': ver}
    new_data = doc.data.copy()
    if 'eof_cut' not in new_data[-1]:
        idx = revision_index(doc)
        new_bdata, new_i = prepare_revision(doc, idx=idx)
        if new_bdata:
            new_data[-1]['bdata'] = new_bdata
            new_data[-1]['fdata'] = gen_fdata(new_data[-1]['fdata'], idx, new_bdata)
        new_index[-1] = new_i
    new_data.append({'fdata': new_data[-1]['fdata']})
    new_v = [new_trailer] + [new_index[-1][i] for i in range(1,len(new_index[-1]))] 
    new_index.append(new_v)
    return Doc(new_index, new_cache, new_data)


def prepare_revision(doc: Doc, rev:int = -1, idx:int = 0) -> tuple:
    """Build bytes representing incremental update"""
    chg = changes(doc, rev)
    if not chg:
        return b''
    for num, _ in chg:
        memoize_obj_in_cache(doc.index, doc.data[rev]['fdata'], num, doc.cache, rev=-1)
    if version(doc) < '1.5':
        use_xref_stream = False
    else:
        use_xref_stream = True
    fragments, new_index = build_fragment_and_xref(chg, doc.index[rev], doc.cache, idx, use_xref_stream)
    return fragments, new_index


def rewind(doc: Doc) -> Doc:
    """Go back to previous revision"""
    if len(doc.index) == 1:
        return doc
    new_index = doc.index.copy()
    new_index.pop()
    new_index[-1] = new_index[-1].copy()
    new_cache = build_cache(doc.data[-2]['fdata'], new_index)
    new_data = doc.data[0:-1]
    return Doc(new_index, new_cache, new_data)


def copy_doc(doc: Doc) -> Doc:
    """ """
    new_index = doc.index.copy()
    new_index[-1] = doc.index[-1].copy()
    new_cache = doc.cache.copy()
    return Doc(new_index, new_cache, doc.data)


def update_object(doc: Doc, num: int, new_o) -> Doc:
    """Update object in the current revision"""
    ver = len(doc.index)
    old_i = doc.index[-1][num]
    if new_o is None:
        new_i = {'o_num': num, 'o_gen': old_i['o_gen'], 'o_ver': old_i['o_ver']+1, 'doc_ver': ver-1, 'DELETED': True}
    else:
        new_i = {'o_num': num, 'o_gen': old_i['o_gen'], 'o_ver': old_i['o_ver']+1, 'doc_ver': ver-1}
    new_doc = copy_doc(doc)
    new_doc.index[-1][num] = new_i
    new_doc.cache[num] = new_o
    return new_doc


def add_object(doc: Doc, new_o) -> tuple:
    """Add new object at the end of current index"""
    if doc.index[-1][-1]:
        doc = add_revision(doc)
    ver = len(doc.index)
    num = len(doc.index[-1])
    new_i = {'o_num': num, 'o_gen': 0, 'o_ver': 0, 'doc_ver': ver-1}
    new_doc = copy_doc(doc)
    new_doc.index[-1].append(None)
    new_doc.index[-1][num] = new_i
    new_doc.cache.append(None)
    new_doc.cache[num] = new_o
    return new_doc, complex(0, num)


def dependencies(doc: Doc, obj: Any) -> set:
    """Recursively list indirect references found inside object""" 
    if type(obj) == dict:
        res = set()
        for k, v in obj.items():
            if k == '/Parent' or k == '/P':
                continue
            res = res | dependencies(doc, v)
        return res
    elif type(obj) == list:
        res = set()
        for i in obj:
            res = res | dependencies(doc, i)
        return res
    elif type(obj) == complex:
        res = {obj}
        res = res | dependencies(doc, get_object(doc, obj))
        return res
    else:   
        return set()


def delete_pages(doc: Doc, del_pages) -> Doc:
    """Delete one (an int) or more (an array of int) pages"""
    if type(del_pages) != list:
        del_pages = [del_pages]
    pages = flat_page_tree(doc)
    del_ref = {pages[p][0] for p in del_pages}
    keep_ref = {p[0] for p in pages} - del_ref
    del_dep = set()
    keep_dep = set()
    for i in del_ref:
        del_dep = del_dep | dependencies(doc, i)
    for i in keep_ref:
        keep_dep = keep_dep | dependencies(doc, i)
    for ref in del_ref:
        parent = get_object(doc, ref)['/Parent']
        new_parent = get_object(doc, parent)
        kids = new_parent['/Kids']
        kids.remove(ref)
        new_parent['/Count'] = new_parent['/Count'] - 1
        doc = update_object(doc, int(parent.imag), new_parent)
        while '/Parent' in new_parent:
            p = new_parent['/Parent']
            new_parent = get_object(doc, p)
            new_parent['/Count'] = new_parent['/Count'] - 1
            doc = update_object(doc, int(p.imag), new_parent)
    for ref in del_dep - keep_dep:
        doc = update_object(doc, int(ref.imag), None)
    return doc


def defragment_map(current_index: list) -> tuple:
    """Build new index without empty slots (ie deleted objects)"""
    new_index = [None]
    mapping = {}
    nb = 0
    for i, o in enumerate(current_index):
        if i == 0: #trailer
            continue
        if 'DELETED' in o:
            continue
        else:
            nb += 1
            old_ref = complex(o['o_gen'], o['o_num']) 
            new_index.append({'o_num': nb, 'o_gen': 0, 'doc_ver': 0, 'OLD_REF': old_ref})
            new_ref = complex(0, nb) 
            if old_ref != new_ref:
                mapping[old_ref] = new_ref
    return new_index, mapping


def flatten(doc: Doc) -> Doc:
    """ """
    new_index, mapping = defragment_map(doc.index[-1])
    new_cache = len(new_index) * [None]
    new_data = [doc.data[0]]
    new_cache[0] = trailer(doc)
    for i in range(1, len(new_index)):
        old_ref = new_index[i]['OLD_REF']
        obj = get_object(doc, old_ref)
        obj = rename_ref(obj, mapping)
        new_cache[i] = obj
    new_doc = Doc([new_index], new_cache, new_data)
    chg = changes(new_doc)
    if not chg:
        return b''
    v = version(doc)
    if v < '1.5':
        use_xref_stream = False
    else:
        use_xref_stream = True
    del new_doc.cache[0]['/Prev']
    header = f"%PDF-{v}".encode('ascii')
    new_bdata, new_i = build_fragment_and_xref(chg, new_doc.index[0], new_doc.cache, len(header), use_xref_stream)
    #new_data[-1]['bdata'] = new_bdata
    new_data[-1]['fdata'] = bdata_dummy(header + new_bdata)
    new_data[-1]['eof_cut'] = len(header + new_bdata)
    new_doc.index[0] = new_i
    return new_doc



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

