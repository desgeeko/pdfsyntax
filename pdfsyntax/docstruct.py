"""Module pdfsyntax.docstruct: how objects represent a document"""

from typing import Callable
from .objects import *
from .filestruct import *
from .text import *
from collections import namedtuple
from copy import deepcopy


EOL = b'\r\n'
SPACE = EOL + b'\x00\x09\x0c\x20'

INHERITABLE_ATTRS = '/Resources /MediaBox /CropBox /Rotate'.split()


Doc = namedtuple('Doc', 'index cache data')

class Doc(Doc):

    def __repr__(self):
        """Summarize for REPL."""
        res = "<PDF Doc"
        rev = len(self.index) - 1
        mods = len(changes(self))
        res += f" in revision {rev} with {mods} modified object(s)>"
        return res

    def __getitem__(self, key):
        """Return immutable slice of pages with the square brackets syntax."""
        n = number_pages(self)
        if type(key) == int:
            page = key % n
            pages = {page}
        elif type(key) == slice:
            start, stop, step = key.indices(n)
            pages = set(range(start, stop, step))
        new_doc = keep_pages(self, pages)
        return new_doc

    def __iter__(self):
        """Return new iterator instance."""
        return DocIterator(self)

    def __add__(self, other):
        """Implement + operator for concatenation."""
        new_doc = concatenate(self, other)
        return new_doc

class DocIterator:

    def __init__(self, doc):
        """Constructor."""
        self.doc = doc
        self.current = 0
        self.end = number_pages(doc)

    def __next__(self):
        """Iterate over the doc pages."""
        if self.current < self.end:
            new_doc = keep_pages(self.doc, self.current)
            self.current += 1
            return new_doc
        else:
            raise StopIteration


def pprint_index(doc: Doc, compact: bool = False):
    """Pretty print index as tabular data."""
    if compact:
        W_NUM = 7
    else:
        W_NUM = 17
    nb_obj = len(doc.index[-1])
    ver = len(doc.index)
    matrix = [[None] * nb_obj for x in range(ver)]
    maxs = [1] * ver
    for i in range(nb_obj):
        line = f"{i:<{W_NUM}}"
        o_gen, o_ver, doc_ver = "", "", ""
        abs_pos, env_num, o_pos = "", "", ""
        for j in range(ver):
            if i > len(doc.index[j]) - 1:
                matrix[j][i] = '-'
                continue
            cell = 'idem'
            x = doc.index[j][i]
            if x:
                o_gen_new = x.get('o_gen', '')
                o_ver_new = x.get('o_ver', '')
                doc_ver_new = x.get('doc_ver', '')
                abs_pos_new = x.get('abs_pos', '-')
                env_num_new = x.get('env_num', '')
                o_pos_new = x.get('o_pos', '')
                deleted = x.get('DELETED')
                if deleted:
                    cell = "Deleted "
                elif o_gen_new != o_gen or o_ver_new != o_ver or doc_ver_new != doc_ver:
                    o_gen, o_ver, doc_ver = o_gen_new, o_ver_new, doc_ver_new
                    cell = f"{o_gen}/{o_ver}/{doc_ver}"
                if abs_pos_new != abs_pos:
                    abs_pos = abs_pos_new
                    cell += f" {abs_pos}"
                if env_num_new != env_num or o_pos_new != o_pos:
                    env_num, o_pos = env_num_new, o_pos_new
                    cell += f" {env_num}"
            matrix[j][i] = cell
            if len(cell) > maxs[j]:
                maxs[j] = len(cell)
    for i in range(1, nb_obj):
        line = f"{i:<{W_NUM}}"
        for j in range(ver):
            line += f"| {matrix[j][i]:{maxs[j]}} "
        print(line)
    print('')
    i = 0
    line = f"{'0 (trailer)':<{W_NUM}}"
    if compact:
        line += '\n' + ' ' * W_NUM
    for j in range(ver):
        line += f"| {matrix[j][i]:{maxs[j]}} "
    print(line)
    for k in 'abs_pos startxref_pos xref_table_pos xref_stream_pos xref_stream_num'.split():
        line = f"{k:<{W_NUM}}"
        if compact:
            line += '\n' + ' ' * W_NUM
        for j in range(ver):
            val = doc.index[j][0].get(k, '-')
            val = f"{val} "
            line += f"| {val:{maxs[j]}} "
        print(line)
    return


def pprint_cache(doc: Doc):
    """Pretty print cache content as a matrix."""
    idx = {}
    for iref, action in changes(doc):
        idx[int(iref.imag)] = action
    markers = '0123456789'
    header = ' ' * 6 + markers
    print(header)
    line = ''
    for i, x in enumerate(doc.cache):
        status = idx.get(i, 'x')
        if status == 'x' and doc.cache[i] is None:
            status = '-'
        line += status
        if i % 10 == 9 or i == len(doc.cache) - 1:
            prefix = f"{(i-i%10)//10}_"
            line = f"{prefix:>5} " + line
            print(line)
            line = ''
    print(line)
    return


def pprint_data_history(doc: Doc):
    """Pretty print data history across all revisions."""
    W_NUM = 10
    ver = len(doc.data)
    hist = [{} for x in range(ver)]
    maxs = [1] * ver
    for i in range(ver):
        fd = doc.data[i].get('fdata')
        bd = doc.data[i].get('bdata')
        cut = doc.data[-i].get('eof_cut')
        _, _, _, sz = fd(None, -1)
        n = fd.__name__
        hist[i]['data_f()'] = n.split('_')[0]
        hist[i]['data_sz'] = sz
        hist[i]['add_data'] = len(bd) if bd else "None"
        hist[i]['eof_cut'] = cut if cut else "None"
    for k in 'data_f() data_sz add_data eof_cut'.split():
        line = f"{k:<{W_NUM}}"
        for i in range(ver):
            line += f"| {hist[i][k]:<{W_NUM}} "
        print(line)
    return


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


def obj(doc: Doc, o_num, o_gen = None):
    """For direct access to an indirect object without reference resolution (see get_object)."""
    if o_gen is None:
        o_gen = doc.index[-1][o_num]['o_gen']
    iref = complex(o_gen, o_num)
    return get_object(doc, iref)


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
    if current[o_num]:
        o_gen = current[o_num]['o_gen']
        return complex(o_gen, o_num)
    else:
        return None


def in_use(doc: Doc, rev: int=-1) -> list:
    """List objects in use (not empty from the start and not deleted)."""
    res = []
    current = doc.index[rev]
    for i in range(1, len(current)):
        iref = get_iref(doc, i, rev)
        if iref and 'DELETED' not in current[i]:
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
        if not iref:
            continue
        if 'xref_stream_num' in current[0] and current[0]['xref_stream_num'] == i:
            continue
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


def envelopes(doc: Doc):
    """Map objects nums belonging to objects streams."""
    res = {}
    current = doc.index[-1]
    for i, x in enumerate(current):
        env_num = x.get('env_num')
        if env_num:
            if env_num not in res:
                res[env_num] = []
            res[env_num].append(i)
    return res


def group_obj_into_stream(doc: Doc , env_num: int = None, o_nums: set = None):
    """Provision a ObjStm object and tag all changes to target this envelope."""
    if not env_num:
        new_doc, iref = add_object(doc, b'')
        env_num = int(iref.imag)
    else:
        new_doc = copy_doc(doc, revision='SAME')
    current = new_doc.index[-1]
    if not o_nums:
        chgs = changes(doc)
        o_nums = set([int(iref.imag) for iref, _ in chgs])
    for o in o_nums:
        x = new_doc.obj(o)
        if type(x) == Stream:
            continue
        elif type(x) == dict and 'Length' in x:
            continue
        elif current[o]['o_gen'] != 0:
            continue
        # TODO Add another elif for encryption dict
        current[o]['env_num'] = env_num
    new_doc.cache[env_num] = Stream({'/Type': '/ObjStm'}, b'', b'')
    return new_doc


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
        if start_pos == None and length == -1:
            #_, _, _, sz = fdata(None, -1)
            sz = index
            return (None, None, None, sz + len(bdata))
        if start_pos > index:
            start_pos = start_pos - index
            #if start_pos == -1 and length == 0:
            #    return (None, None, None, len(bdata))
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
    chg = changes(doc)
    if len(chg) == 0:
        return doc
    current_index = doc.index[-1]
    nb_rev = len(doc.index)
    new_doc = copy_doc(doc, revision='NEXT')
    new_index0 = {'o_num': 0, 'o_gen': 0, 'o_ver': nb_rev, 'doc_ver': nb_rev}
    x_num = current_index[0].get('xref_stream_num')
    if x_num:
        new_index0['xref_stream_num'] = -1
        if x_num == -1:
            x_num = len(current_index)
            new_index_xs = {'o_num': x_num, 'o_gen': 0, 'o_ver': 0, 'doc_ver': nb_rev-1}
            new_doc.index[-1].append(new_index_xs)
            new_doc.index[-1][0]['xref_stream_num'] = x_num
        if new_doc.cache[0].get('/DecodeParms'):
            del new_doc.cache[0]['/DecodeParms']
    new_doc.cache[0]['/Size'] = len(new_doc.index[-1])
    if 'eof_cut' not in new_doc.data[-1]:
        if nb_rev == 1:
            v = version(doc)
            header = f"%PDF-{v}".encode('ascii')
            idx = len(header)
            new_bdata, new_i = build_revision_byte_stream(chg, new_doc.index[-1], new_doc.cache, idx, x_num)
            new_bdata = header + new_bdata
            new_prov = bdata_dummy(new_bdata)
        else:
            header = b''
            idx = revision_index(doc)
            new_bdata, new_i = build_revision_byte_stream(chg, new_doc.index[-1], new_doc.cache, idx, x_num)
            new_prov = merge_fdata(new_doc.data[-1]['fdata'], idx, new_bdata)
        if new_bdata:
            new_doc.data[-1]['bdata'] = new_bdata
            new_doc.data[-1]['fdata'] = new_prov
        new_doc.index[-1] = new_i
    new_doc.data.append({'fdata': new_doc.data[-1]['fdata']})
    new_v = [new_index0] + [new_doc.index[-1][i] for i in range(1,len(new_doc.index[-1]))] 
    new_doc.index.append(new_v)
    new_trailer = new_doc.cache[0]
    if type(new_doc.index[-2][0]) == list: #Linearized
        new_trailer['/Prev'] = new_doc.index[-2][1].get('xref_table_pos') or new_doc.index[-2][1].get('xref_stream_pos')
    else:
        new_trailer['/Prev'] = new_doc.index[-2][0].get('xref_table_pos') or new_doc.index[-2][0].get('xref_stream_pos')
    if '/XRefStm' in new_trailer:
        del new_trailer['/XRefStm']
    return new_doc


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
        new_doc = Doc(doc.index.copy(), doc.cache.copy(), doc.data.copy())
        new_doc.cache[0] = doc.cache[0].copy()
        new_doc.index[-1] = new_doc.index[-1].copy()
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


def force_xref_stream(doc: Doc, placeholder: bool = False, filt: str = '/FlateDecode') -> tuple:
    """Activate xref stream and optionally add placeholder at the end of current index."""
    if 'xref_stream_num' in doc.index[-1][0]:
        if '/Filter' in doc.cache[0] and doc.cache[0]['/Filter'] == filt:
            return doc
        else:
            new_doc = copy_doc(doc, revision='SAME')
    elif placeholder:
        new_doc, new_iref = add_object(doc, {})
        x_num = int(new_iref.imag)
        new_doc.index[-1][0] = deepcopy(new_doc.index[-1][0])
        new_doc.index[-1][0]['xref_stream_num'] = x_num
    else:
        new_doc = copy_doc(doc, revision='SAME')
        new_doc.index[-1][0] = deepcopy(new_doc.index[-1][0])
        new_doc.index[-1][0]['xref_stream_num'] = -1
    if filt:
        new_doc.cache[0]['/Filter'] = filt
    return new_doc


def max_num(doc: Doc, rev: int=-1) -> int:
    """Return the biggest object number in doc revision."""
    return len(doc.index[rev]) - 1


def concatenate(doc1: Doc, doc2: Doc) -> Doc:
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
    doc2 = update_object(doc2, int(cat_iref2.imag), None)
    x_num = doc2.index[-1][0].get('xref_stream_num')
    if x_num and x_num > 0:
        doc2 = update_object(doc2, x_num, None)
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


def keep_pages(doc: Doc, pages) -> Doc:
    """Keep one (an int) or more (an array of int) pages and remove the others."""
    n = number_pages(doc)
    if type(pages) != set:
        pages = {pages}
    del_pages = set(range(n)) - pages
    new_doc = remove_pages(doc, del_pages)
    return new_doc


def remove_pages(doc: Doc, del_pages) -> Doc:
    """Remove one (an int) or more (an array of int) pages."""
    new_doc = copy_doc(doc, revision='SAME')
    if type(del_pages) != set:
        del_pages = {del_pages}
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
    """Build new index without excluded slots (ie deleted objects)."""
    new_index = [{'o_num': 0, 'o_gen': 0, 'o_ver': 0, 'doc_ver': 0}]
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
            new_o = deepcopy(o)
            new_o['o_gen'] = 0
            new_o['o_ver'] = 0
            new_o['doc_ver'] = 0
            new_o['OLD_REF'] = old_ref
            del new_o['abs_pos']
            del new_o['abs_next']
            new_index.append(new_o)
            new_ref = complex(0, nb) 
            if old_ref != new_ref:
                mapping[old_ref] = new_ref
    return new_index, mapping


def squash(doc: Doc) -> Doc:
    """Group all revisions into a single one."""
    obj_stms = envelope_objects(doc)
    if type(doc.index[0][0]) == dict:
        xref_stream_num = doc.index[0][0].get('xref_stream_num')
    else: #TODO
        xref_stream_num = doc.index[0][0][0].get('xref_stream_num')
    old_index = doc.index[-1]
    new_index, mapping = defragment_map(old_index, set())
    if xref_stream_num:
        new_index[0]['xref_stream_num'] = xref_stream_num
    new_cache = len(new_index) * [None]
    new_data = [{}]
    new_cache[0] = {'/Root': trailer(doc)['/Root']}
    new_cache[0] = deep_ref_retarget(new_cache[0], mapping)
    for i in range(1, len(new_index)):
        old_ref = new_index[i]['OLD_REF']
        obj = get_object(doc, old_ref)
        obj = deep_ref_retarget(obj, mapping)
        new_cache[i] = obj
    new_doc = Doc([new_index], new_cache, new_data)
    chg = changes(new_doc)
    if not chg:
        return b''
    header = f"%PDF-{version(doc)}".encode('ascii')
    #new_bdata, new_i = build_revision_byte_stream(chg,
    #                                              new_doc.index[0],
    #                                              new_doc.cache,
    #                                              len(header),
    #                                              xref_stream_num)
    #new_data[-1]['fdata'] = bdata_dummy(header + new_bdata)
    new_data[-1]['fdata'] = bdata_dummy(header)
    #new_doc.index[0] = new_i
    #new_doc = commit(new_doc) #TODO: keep?
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
