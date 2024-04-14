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
            for i in range(1, len(self.index[-1])):
                if self.cache[i] is not None:
                    present += 1 
            res += f", cache loaded with {present} / {len(self.cache)-1} objects>\n"
        else:
            res += f", cache=None>\n"
        return res

EOL = b'\r\n'
SPACE = EOL + b'\x00\x09\x0c\x20'


def memoize_obj_in_cache(idx: list, fdata: Callable, key: int, cache=None, rev=-1) -> list:
    """Parse indirect object whose number is [key] and return a cache filled at index [key].

    cache argument may be:
    - a list that is updated
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
            bdata, a0, _, _ = fdata(index['abs_pos'],
                                    index['abs_next'] - index['abs_pos'])
            i, j, _ = next_token(bdata, a0)
            if bdata[i:j] == b'trailer':
                i, j, _ = next_token(bdata, j)
            else:
                i, j, _ = next_token(bdata, j)
                i, j, _ = next_token(bdata, j)
                i, j, _ = next_token(bdata, j)
            text = bdata
            i_obj = parse_obj(text, i)
            if type(i_obj) == Stream:
                i_obj = i_obj['entries']
            obj.update(i_obj)
        cache[key] = obj    
    elif 'env_num' not in idx[rev][key]:
        bdata, a0, _, _ = fdata(idx[rev][key]['abs_pos'],
                                idx[rev][key]['abs_next'] - idx[rev][key]['abs_pos'])
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
        bdata, a0, _, _ = fdata(idx[rev][container]['abs_pos'],
                                idx[rev][container]['abs_next'] - idx[rev][container]['abs_pos'])
        i, j, _ = next_token(bdata, a0)
        i, j, _ = next_token(bdata, j)
        i, j, _ = next_token(bdata, j)
        i, j, _ = next_token(bdata, j) #/ObjStm
        text = bdata
        stream_obj = parse_obj(text, i)
        if container >= len(cache):
            cache += (container-len(cache)+1) * [None]
        cache[container] = stream_obj
        _, _, _, obj_list = parse_object_stream(stream_obj, container)
        for o_num, embedded_obj, _, _, _ in obj_list:
            if o_num >= len(cache):
                cache += (o_num-len(cache)+1) * [None]
            cache[o_num] = embedded_obj
    return cache


def get_object(doc: Doc, obj):
    """Return raw object or the target of an indirect reference."""
    if isinstance(obj, complex) == True:
        ref = int(obj.imag)
        res = memoize_obj_in_cache(doc.index, doc.data[-1]['fdata'], ref, doc.cache)
        return deepcopy(res[ref])
    else: 
        return deepcopy(obj)


def flat_page_tree(doc: Doc, num=None, inherited={}, max_nb=None) -> list:
    """Recursively list the pages of a node."""
    accu = []
    if num:
        node = get_object(doc, num)
    else:
        node = get_object(doc, catalog(doc)[0]['/Pages'])
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
    """Initialize cache with trailer."""
    size = len(index[-1])
    cache = size * [None]
    memoize_obj_in_cache(index, fdata, 0, cache)
    return cache


def get_iref(doc: Doc, o_num: int, rev: int=-1) -> complex:
    """Build the relevant indirect reference for o_num in a doc revision."""
    current = doc.index[rev]
    o_gen = current[o_num]['o_gen']
    return complex(o_gen, o_num)


def in_use(doc: Doc, rev: int=-1) -> list:
    """List objects in use (not deleted)."""
    res = []
    current = doc.index[rev]
    for i in range(1, len(current)):
        iref = get_iref(doc, i, rev)
        if 'DELETED' not in current[i]:
            res.append(iref)
    return res


def changes(doc: Doc, rev: int=-1):
    """List deleted/updated/added objects."""
    res = []
    current = doc.index[rev]
    if len(doc.index) == 1:
        previous = [None] * len(current)
    else:
        previous = doc.index[rev-1]
    for i in range(1, len(current)):
        iref = get_iref(doc, i, rev)
        if i > len(previous)-1:
            res.append((iref, 'a'))
        elif i < len(previous) and previous[i] == current[i]:
            pass
        elif previous[i] != None and 'DELETED' not in previous[i] and 'DELETED' in current[i]:
            res.append((iref, 'd'))
        elif previous[i] != None and current[i] != previous[i]:
            res.append((iref, 'u'))
        else:
            res.append((iref, 'a'))
    return res


#def group_obj_into_stream(doc: Doc):
#    """Provision a ObjStm object and tag all changes to target this envelope."""
#    doc2, _ = add_object(doc, b'')
#    current = doc2.index[-1]
#    o_num = current[-2]['o_num']
#    chgs = changes(doc)
#    for c, _ in chgs:
#        i = int(c.imag)
#        if i == o_num:
#            continue
#        current[i]['env_num'] = o_num
#    d = {'/Type': '/ObjStm', '/Length': 0, '/N': 0, '/First': 0, '/FirstLine': []}
#    doc2.cache[o_num] = Stream(d, b'', b'')
#    return doc2


def envelope_objects(doc: Doc):
    """List objects streams that envelope other objects."""
    return {o.get('env_num') for o in doc.index[-1] if o.get('env_num')}


def version(doc: Doc) -> str:
    """Return PDF version."""
    fdata = doc.data[0]['fdata']
    bdata, a0, _, _ = fdata(5, 3)
    ver = bdata[a0:a0+3]
    cat, _ = catalog(doc)
    if '/Version' in cat and cat['/Version'][1:] > ver.decode('ascii'):
            return cat['/Version'][1:]
    return ver.decode('ascii')


def update_version(doc: Doc, ver: str) -> Doc:
    """Upgrade PDF version in incremental update."""
    cat, i_ref = catalog(doc)
    if '/Version' in cat:
        if cat['/Version'][1:] < ver:
            cat['/Version'] = '/' + ver
            return update_object(doc, int(i_ref.imag), cat)
        else:
            return doc
    else:
        cat['/Version'] = '/' + ver
        return update_object(doc, int(i_ref.imag), cat)


def updates(doc: Doc) -> int:
    """Return the number of updates the document received."""
    upd = len(doc.index) - 1
    return upd


def trailer(doc: Doc):
    """Return doc trailer dictionary."""
    return get_object(doc, 0j)


def encrypted(doc: Doc) -> bool:
    """Detect if doc is encrypted."""
    trail = trailer(doc)
    encrypt = trail.get('/Encrypt')
    if encrypt:
        return True
    else:
        return False


def hybrid(doc: Doc) -> bool:
    """Detect if doc is hybrid."""
    if len(doc.index) >= 2 and doc.index[1][0].get('xref_stm'):
        return True
    else:
        return False


def catalog(doc: Doc):
    """Return doc Root/Catalog dictionary."""
    root = trailer(doc)['/Root']
    return get_object(doc, root), root


def info(doc: Doc):
    """Return doc Info dictionary if present."""
    trail = trailer(doc)
    info = trail.get('/Info')
    if info:
        return get_object(doc, info)


def number_pages(doc: Doc):
    """Return doc number of pages."""
    p = get_object(doc, catalog(doc)[0]['/Pages'])
    return p['/Count']


def pages(doc: Doc, max_nb=None) -> list:
    """List page objects."""
    pl = []
    for num, in_attr in flat_page_tree(doc, max_nb=max_nb):
        temp = deepcopy(get_object(doc, num))
        for a in in_attr:
            if a not in temp:
                temp[a] = in_attr[a]
        pl.append(temp)
    return pl


def revision_index(doc: Doc, rev=-1) -> int:
    """Return bytes index of revision within the file."""
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


def merge_fdata(fdata: Callable, index: int, bdata: bytes):
    """Merge a data provider and bytes into a new composite data provider."""
    def composite_fdata(start_pos: int, length: int) -> tuple:
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
            #return (bdata, i, index, min(len(bdata) - start_pos, length)) #TODO
        else:
            return fdata(start_pos, length)
    return composite_fdata


def commit(doc: Doc) -> Doc:
    """Add new index for incremental update."""
    if len(changes(doc)) == 0:
        return doc
    nb_rev = len(doc.index)
    new_index0 = {'o_num': 0, 'o_gen': 0, 'o_ver': nb_rev, 'doc_ver': nb_rev}
    new_doc = copy_doc(doc, revision='NEXT')
    if 'eof_cut' not in new_doc.data[-1]:
        if nb_rev == 1:
            v = version(doc)
            header = f"%PDF-{v}".encode('ascii')
            idx = len(header)
            new_bdata, new_i = prepare_revision(doc, idx=idx)
            new_bdata = header + new_bdata
            new_prov = bdata_dummy(new_bdata)
        else:
            header = b''
            idx = revision_index(doc)
            new_bdata, new_i = prepare_revision(doc, idx=idx)
            new_prov = merge_fdata(new_doc.data[-1]['fdata'], idx, new_bdata)
        if new_bdata:
            new_doc.data[-1]['bdata'] = new_bdata
            new_doc.data[-1]['fdata'] = new_prov
        new_doc.index[-1] = new_i
    new_doc.data.append({'fdata': new_doc.data[-1]['fdata']})
    new_v = [new_index0] + [new_doc.index[-1][i] for i in range(1,len(new_doc.index[-1]))] 
    new_doc.index.append(new_v)
    new_trailer = doc.cache[0].copy()
    if type(new_doc.index[-2][0]) == list: #Linearized
        new_trailer['/Prev'] = new_doc.index[-2][1].get('xref_table_pos') or new_doc.index[-2][1].get('xref_stream_pos')
    else:
        new_trailer['/Prev'] = new_doc.index[-2][0].get('xref_table_pos') or new_doc.index[-2][0].get('xref_stream_pos')
    if '/XRefStm' in new_trailer:
        del new_trailer['/XRefStm']
    new_doc.cache[0] = new_trailer
    return new_doc


def prepare_revision(doc: Doc, rev:int = -1, idx:int = 0) -> tuple:
    """Build bytes representing incremental update."""
    chg = changes(doc, rev)
    if not chg:
        return b''
    for c, _ in chg:
        num = int(c.imag)
        memoize_obj_in_cache(doc.index, doc.data[rev]['fdata'], num, doc.cache, rev=-1)
    if version(doc) < '1.5':
        use_xref_stream = False
    else:
        use_xref_stream = True
    fragments, new_index = build_revision_byte_stream(chg, doc.index[rev], doc.cache, idx, use_xref_stream)
    return fragments, new_index


def rewind(doc: Doc) -> Doc:
    """Go back to previous revision."""
    if len(doc.index) == 1:
        return doc
    new_doc = copy_doc(doc, revision='PREVIOUS')
    new_doc.index.pop()
    new_doc.data.pop()
    if 'eof_cut' in new_doc.data[-1]:
        del new_doc.data[-1]['eof_cut']
    new_doc.cache.extend(build_cache(doc.data[-1]['fdata'], new_doc.index))
    return new_doc


def copy_doc(doc: Doc, revision='SAME') -> Doc:
    """Shallow copy."""
    if revision == 'SAME':
        new_doc = Doc(doc.index.copy(), doc.cache.copy(), doc.data.copy())
        new_doc.index[-1] = new_doc.index[-1].copy()
    elif revision == 'PREVIOUS':
        new_doc = Doc(doc.index.copy(), [], doc.data.copy())
        new_doc.index[-2] = new_doc.index[-2].copy()
        new_doc.data[-2] = new_doc.data[-2].copy()
    elif revision == 'NEXT':
        new_doc = Doc(doc.index.copy(), len(doc.index[-1]) * [None], doc.data.copy())
        new_doc.data[-1] = new_doc.data[-1].copy()
    else:
        return None
    return new_doc


def update_object(doc: Doc, num: int, new_o, immut=True) -> Doc:
    """Update object in the current revision."""
    ver = len(doc.index)
    old_i = doc.index[-1][num]
    new_i = {
        'o_num': num,
        'o_gen': old_i['o_gen'],
        'o_ver': old_i['o_ver']+1,
        'doc_ver': ver-1,
    }
    if new_o is None:
        new_i['DELETED'] = True
    if immut:
        new_doc = copy_doc(doc, revision='SAME')
    else:
        new_doc = doc
    new_doc.index[-1][num] = new_i
    new_doc.cache[num] = new_o
    return new_doc


def add_object(doc: Doc, new_o, immut=True) -> tuple:
    """Add new object at the end of current index."""
    ver = len(doc.index)
    num = len(doc.index[-1])
    new_i = {'o_num': num, 'o_gen': 0, 'o_ver': 0, 'doc_ver': ver-1}
    if immut:
        new_doc = copy_doc(doc, revision='SAME')
    else:
        new_doc = doc
    new_doc.index[-1].append(None)
    new_doc.index[-1][num] = new_i
    new_doc.cache.append(None)
    new_doc.cache[num] = new_o
    return new_doc, complex(0, num)


def max_num(doc: Doc, rev: int=-1) -> int:
    """Return the biggest object number in doc revision."""
    return len(doc.index[rev]) - 1


def concatenate_docs(doc1: Doc, doc2: Doc) -> Doc:
    """Add pages from doc2 at the end of doc1."""
    mapping = {}
    new_doc = copy_doc(doc1, revision='SAME')
    start_num = max_num(new_doc) + 1
    cat, cat_iref = catalog(new_doc)
    doc2 = squash(doc2)
    cat2, cat_iref2 = catalog(doc2)
    pages_iref2 = cat2['/Pages']
    pages2 = get_object(doc2, pages_iref2)
    pcount2 = get_object(doc2, pages2['/Count'])
    doc2 = update_object(doc2, int(cat_iref2.imag), None) #TODO: remove xref stream
    objs = in_use(doc2)
    ir = complex(0, start_num)
    for iref in objs:
        mapping[iref] = ir
        ir += 1j
    for iref in objs:
        obj = get_object(doc2, iref)
        new_obj = deep_ref_retarget(obj, mapping)
        new_doc, _ = add_object(new_doc, new_obj, immut=False)
    pages_iref = cat['/Pages']
    pages = get_object(new_doc, pages_iref)
    pcount = get_object(new_doc, pages['/Count'])
    kids = get_object(new_doc, pages['/Kids'])
    kids.append(mapping[pages_iref2])
    pages['/Kids'] = kids
    pages['/Count'] = pcount + pcount2
    new_doc = update_object(new_doc, int(pages_iref.imag), pages, immut=False)
    return new_doc


def dependencies(doc: Doc, obj: Any) -> set:
    """Recursively list indirect references found inside object.""" 
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
    """Delete one (an int) or more (an array of int) pages."""
    new_doc = copy_doc(doc, revision='SAME')
    if type(del_pages) != list:
        del_pages = [del_pages]
    pages = flat_page_tree(new_doc)
    del_ref = {pages[p][0] for p in del_pages}
    keep_ref = {p[0] for p in pages} - del_ref
    del_dep = set()
    keep_dep = set()
    for i in del_ref:
        del_dep = del_dep | dependencies(new_doc, i)
    for i in keep_ref:
        keep_dep = keep_dep | dependencies(new_doc, i)
    for ref in del_ref:
        parent = get_object(new_doc, ref)['/Parent']
        new_parent = get_object(new_doc, parent)
        kids = new_parent['/Kids']
        kids.remove(ref)
        new_parent['/Count'] = new_parent['/Count'] - 1
        new_doc = update_object(new_doc, int(parent.imag), new_parent, immut=False)
        while '/Parent' in new_parent:
            p = new_parent['/Parent']
            new_parent = get_object(new_doc, p)
            new_parent['/Count'] = new_parent['/Count'] - 1
            new_doc = update_object(new_doc, int(p.imag), new_parent, immut=False)
    for ref in del_dep - keep_dep:
        new_doc = update_object(new_doc, int(ref.imag), None, immut=False)
    return new_doc


#def detect_unused(doc: Doc) -> dict:
#    """ WORK IN PROGRESS """
#    current_index = doc.index[-1]
#    for i in range(1, len(current_index)):
#        ref = complex(current_index[i]['o_ver'], current_index[i]['o_num'])
#        obj = get_object(doc, ref)
#        refs = deep_ref_detect(obj, set())
#    return


def defragment_map(current_index: list, excluded={}) -> tuple:
    """Build new index without empty slots (ie deleted objects)."""
    new_index = [None]
    mapping = {}
    nb = 0
    for i, o in enumerate(current_index):
        if i == 0: #trailer
            continue
        if 'DELETED' in o or i in excluded:
            continue
        else:
            nb += 1
            old_ref = complex(o['o_gen'], o['o_num']) 
            new_index.append({'o_num': nb, 'o_gen': 0, 'o_ver': 0, 'doc_ver': 0, 'OLD_REF': old_ref})
            new_ref = complex(0, nb) 
            if old_ref != new_ref:
                mapping[old_ref] = new_ref
    return new_index, mapping


def squash(doc: Doc) -> Doc:
    """Group all revisions into a single one."""
    obj_stms = envelope_objects(doc)
    old_index = doc.index[-1]
    new_index, mapping = defragment_map(old_index, obj_stms)
    if new_index[0] is None:
        new_index[0] = {}
    new_cache = len(new_index) * [None]
    new_data = [{}]
    new_cache[0] = trailer(doc)
    for i in range(1, len(new_index)):
        old_ref = new_index[i]['OLD_REF']
        obj = get_object(doc, old_ref)
        obj = deep_ref_retarget(obj, mapping)
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
    
    new_bdata, new_i = build_revision_byte_stream(chg,
                                               new_doc.index[0],
                                               new_doc.cache,
                                               len(header),
                                               use_xref_stream)
    new_data[-1]['fdata'] = bdata_dummy(header + new_bdata)
    new_doc.index[0] = new_i
    new_doc = commit(new_doc) #TODO: keep?
    return new_doc


def prepare_w(w, default_w):
    """Decode widths for type0 / CID fonts."""
    i = 0
    width = {}
    if not w:
        def char_width_cid_default(character_num):
            return 500
        return char_width_cid_default
    while i < len(w):
        if type(w[i+1]) == list:
            current = w[i]
            for x in w[i+1]:
                width[current] = x
                current += 1
            i += 2
        else:
            first = w[i]
            last = w[i+1]
            x = w[i+2]
            for j in range(first, last+1):
                width[j] = x
            i += 3
    def char_width_cid(character_num):
        return width.get(character_num, default_w)
    return char_width_cid


def prepare_widths(widths, first_char):
    """Decode widths for simple fonts."""
    def char_width_table(character_num):
        offset = character_num-first_char
        if offset < 0 or offset >= len(widths):
            return 500
        else:
            return widths[offset]
    return char_width_table


def prepare_font(doc: Doc, iref) -> dict:
    """ """
    font_desc = {}
    o = get_object(doc, iref)
    font_desc['iref'] = iref
    font_desc['name'] = o['/BaseFont']
    font_desc['type'] = o['/Subtype']
    font_desc['descriptor'] = o.get('/FontDescriptor')
    font_desc['to_unicode'] = o.get('/ToUnicode')
    font_desc['encoding'] = o.get('/Encoding')
    first_char = o.get('/FirstChar')
    #last_char = o.get('/LastChar')
    widths = o.get('/Widths')
    descendant = o.get('/DescendantFonts')
    if widths:
        font_desc['char_width'] = prepare_widths(get_object(doc, widths), get_object(doc, first_char))
    elif descendant:
        iref = get_object(doc, descendant)[0]
        d = get_object(doc, iref)
        w = d.get('/W')
        dw = d.get('/DW', 1000)
        font_desc['char_width'] = prepare_w(get_object(doc, w), get_object(doc, dw))
    else:
        #TODO Find standard fonts widths
        default_widths = [500] * 256
        font_desc['char_width'] = prepare_widths(default_widths, 0)
    if font_desc['type'] == '/Type0':
        simple = False
    else:
        simple = True
    if font_desc['to_unicode']:
        cmap_stream = get_object(doc, font_desc['to_unicode'])
        cmap = parse_obj(b'[' + cmap_stream['stream'] + b']')
        def dec_unicode_cmap(text):
            return apply_tounicode(cmap, text, simple)
        font_desc['dec_fun'] = dec_unicode_cmap
    else:
        def dec_encoding(text):
            return apply_encoding(font_desc['encoding'], text)
        font_desc['dec_fun'] = dec_encoding
    return font_desc


def get_page_fonts(doc: Doc, page_nums: list) -> list:
    """Return a list of fonts dict of each page.

    Dict key is font name, for example /F1
    """
    ret = []
    for page_num in page_nums:
        fonts = {}
        font_res = {}
        page_ref, _ = flat_page_tree(doc)[page_num]
        resources = get_object(doc, page_ref)['/Resources']
        if resources:
            fonts = get_object(doc, resources)['/Font']
        for font in fonts:
            font_res[font] = prepare_font(doc, fonts[font])
        ret.append(font_res)
    return ret
