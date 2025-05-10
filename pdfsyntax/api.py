"""Module pdfsyntax.api: Application Programming Interface"""

import sys
from copy import deepcopy
from .docstruct import *
from .filestruct import *
from .objects import *
from .text import *
from .graphics import *
from .layout import *
from .markdown import *


METADATA_ATTRS = '/Title /Author /Subject /Keywords /Creator /Producer'.split()

def in2pt(inches: float) -> int:
    """Convert inches into points."""
    return int(inches*72)

def mm2pt(millimeters: int) -> int:
    """Convert millimeters into points."""
    return round(millimeters/25.4*72)


PAPER_SIZES = {
    (in2pt(11.0), in2pt(17.0)): "US Tabloid",
    (in2pt( 8.5), in2pt(14.0)): "US Legal",
    (in2pt( 8.5), in2pt(11.0)): "US Letter",
    (mm2pt( 841), mm2pt(1189)): "A0",
    (mm2pt( 594), mm2pt( 841)): "A1",
    (mm2pt( 420), mm2pt( 594)): "A2",
    (mm2pt( 297), mm2pt( 420)): "A3",
    (mm2pt( 210), mm2pt( 297)): "A4",
    (mm2pt( 148), mm2pt( 210)): "A5",
    (mm2pt( 105), mm2pt( 148)): "A6",
    (mm2pt(  74), mm2pt( 105)): "A7",
    (mm2pt(  52), mm2pt(  74)): "A8",
    (mm2pt(  37), mm2pt(  52)): "A9",
    (mm2pt(  26), mm2pt(  37)): "A10",
}


def doc_constructor(fdata: Callable) -> Doc:
    """Initialize doc and close first revision."""
    chrono, nxt, nb = build_xref_sequence(fdata)
    index = build_index_from_xref_sequence(chrono, nxt, nb)
    data = [{'eof_cut': eof_cut(i[-1]['abs_pos'], fdata), 'fdata': fdata} for i in index if i[-1]]
    for i in index:
        del i[-1]
    cache = build_cache(fdata, index)
    doc_initial = Doc(index, cache, data)
    doc_new_rev = commit(doc_initial)
    return doc_new_rev


def load(file_obj, mode: str = "SINGLE") -> Doc:
    """Load from file."""
    fdata = bdata_provider(file_obj, mode)
    return doc_constructor(fdata)


def loads(bdata) -> Doc:
    """Load from bytes sequence."""
    fdata = bdata_provider(bdata, "SINGLE")
    return doc_constructor(fdata)


def readfile(filename: str) -> Doc:
    """Read file and initialize doc."""
    with open(filename, 'rb') as file_obj:
        doc = load(file_obj, "SINGLE")
    return doc


def writefile(doc: Doc, filename: str = None) -> Doc:
    """Write doc into file"""
    bdata = b''
    idx = 0
    doc = commit(doc)
    nb_rev = len(doc.index)
    eof_rev = -1
    for i in range(nb_rev):
        if 'eof_cut' in doc.data[i]:
            eof_rev = i
        else:
            break
    if eof_rev >= 0:
        eof_cut = doc.data[eof_rev]['eof_cut']
        prov = doc.data[0]['fdata'](0, eof_cut)
        bdata += prov[0][prov[1]:eof_cut]
        idx += len(bdata)
    #else:
        #FILE_HEADER = b'%PDF-' + version(doc).encode('ascii') + b'\n'
        #bdata += FILE_HEADER
        #idx += len(FILE_HEADER)
    for i in range(eof_rev+1, nb_rev-1):
        fragment = doc.data[i]['bdata']
        bdata += fragment
        idx += len(fragment)
    if filename:
        bfile = open(filename, 'wb')
        bfile.write(bdata)
        bfile.close()
    else:
        sys.stdout.buffer.write(bdata)
        sys.stdout.buffer.flush()
    return doc


def structure(doc: Doc) -> dict:
    """Return various doc attributes (other than metadata)."""
    ret = {}
    ret['Version'] = version(doc)
    ret['Pages'] = number_pages(doc)
    ret['Revisions'] = updates(doc)
    ret['Encrypted'] = encrypted(doc)
    ret['Hybrid'] = hybrid(doc)
    if linearized(doc.data[0]['fdata']):
        ret['Linearized'] = True
    else:
        ret['Linearized'] = False
    ret['Paper of 1st page'] = paper(page_layouts(doc, 1)[0][0])
    return ret


def bool2yesno(b: bool) -> str:
    """."""
    if b == True:
        return "yes"
    else:
        return "no"


def metadata(doc: Doc) -> dict:
    """Return doc metadata."""
    ret = {}
    i = info(doc) or {}
    for entry in METADATA_ATTRS:
        ret[entry[1:]] = text_string(get_object(doc, i.get(entry))) or None
    ret['CreationDate'] = text_string(get_object(doc, i.get('/CreationDate'))) or None
    ret['ModDate'] = text_string(get_object(doc, i.get('/ModDate'))) or None
    return ret 


def paper(mediabox: list) -> str:
    """Detect paper size."""
    x, y = mediabox[2] - mediabox[0], mediabox[3] - mediabox[1]
    ptype = PAPER_SIZES.get((x, y)) or PAPER_SIZES.get((y, x)) or "unknown"
    pdim = f'{int(x*25.4/72)}x{int(y*25.4/72)}mm or {round(x/72, 2)}x{round(y/72, 2)}in'
    return pdim + f' ({ptype})'


def page_layouts(doc: Doc, max_nb=None) -> list:
    """List page layouts."""
    pl = pages(doc, max_nb)
    med = [(p['/MediaBox'], p.get('/Rotate')) for p in pl]
    return med


def rotate(doc: Doc, degrees: int = 90, pages: list = []) -> Doc:
    """Rotate 1 or several pages."""
    pl = page_layouts(doc)
    if pages:
        work_pages = pages
    else:
        work_pages = list(range(len(pl)))
    a = [(i ,x[1]) for i, x in enumerate(pl) if i in work_pages]
    c = flat_page_tree(doc)
    for nb, old_degrees in a:
        old_degrees = old_degrees or 0
        iref = c[nb][0]
        obj = deepcopy(get_object(doc, iref))
        obj['/Rotate'] = (old_degrees + degrees) % 360
        doc = update_object(doc, int(iref.imag), obj)
    return doc


def list_streams(doc: Doc) -> list:
    """List all in use Streams of doc."""
    ret = []
    for iref in in_use(doc):
        o = get_object(doc, iref)
        if type(o) == Stream:
            ret.append(int(iref.imag))
    return ret


def apply_filter(doc: Doc, streams: list, flt: str = '/FlateDecode') -> Doc:
    """Force new filter state, for example /FlateDecode."""
    for o_num in streams:
        o = doc.obj(o_num)
        entries = o['entries']
        if '/Filter' in entries:
            if entries['/Filter'] == flt:
                continue
            else:
                for e in entries['/Filter'].split():
                    if e not in DECODED_FILTERS:
                        continue
        entries = deepcopy(entries)
        if '/Filter' in entries and flt == '':
            del entries['/Filter']
        else:
            entries['/Filter'] = flt
        s, length = forge_stream(entries, o['stream'])
        doc = update_object(doc, o_num, s)
    return doc


def add_text_annotation(doc: Doc, page_num: int, text: str, rect: list, opened: bool = False) -> Doc:
    """Add simple text annotation."""
    annot = {
        '/Type': '/Annot',
        '/Subtype': '/Text',
        '/Rect': rect,
        '/Contents': f"({text})",
        '/Open': opened,
    }
    doc, a_iref = add_object(doc, annot)
    page_ref, _ = flat_page_tree(doc)[page_num]
    new_page = deepcopy(get_object(doc, page_ref))
    if '/Annots' in new_page:
        annot_obj = new_page['/Annots']
        new_array = deepcopy(get_object(doc, new_page['/Annots']))
        new_array.append(a_iref)
        doc = update_object(doc, int(annot_obj.imag), new_array)
    else:
        annot_array = [a_iref]
        doc, aa_iref = add_object(doc, annot_array)
        new_page['/Annots'] = aa_iref
        doc = update_object(doc, int(page_ref.imag), new_page)
    return doc


def fonts(doc: Doc) -> dict:
    """Return each font with its attributes and the pages where it appears."""
    ret = {}
    nb = number_pages(doc)
    font_index = get_page_fonts(doc, list(range(nb)))
    for i, page_fonts in enumerate(font_index):
        for font in page_fonts:
            o = page_fonts[font]['iref']
            n = page_fonts[font]['name'][1:]
            t = page_fonts[font]['type'][1:]
            e = page_fonts[font]['encoding']
            if t == 'Type1':
                if e is None:
                    e = 'built-in'
                else:
                    if type(e) != str:
                        e = 'other'
                    else:
                        e = e[1:]
            else:
                if type(e) != str:
                    e = 'other'
                else:
                    e = e[1:]
            if page_fonts[font]['to_unicode']:
                u = True
            else:
                u = False
            if o not in ret:
                ret[o] = {'name': n,
                          'type': t,
                          'encoding': e,
                          'pages': [],
                          'to_unicode': u,
                          }
            ret[o]['pages'].append(i)
    return ret


def compress(doc: Doc) -> Doc:
    """Compress file."""
    doc = squash(doc)
    v = version(doc)
    if v < '1.5':
        doc = update_version(doc, '1.5')
    #for debug:
    #doc = force_xref_stream(doc, False, '/ASCIIHexDecode')
    ##
    doc = force_xref_stream(doc)
    envs = envelopes(doc)
    l = list(envs.keys())
    if l:
        env1 = l[0]
    else:
        env1 = None
    doc = group_obj_into_stream(doc, env_num = env1)
    s = list_streams(doc)
    doc = apply_filter(doc, s)
    doc = commit(doc)
    return doc


def get_page_contents(doc: Doc, page_num: int) -> list:
    """List all content streams of a page."""
    ret = []
    pages = flat_page_tree(doc)
    i_c = get_object(doc, pages[page_num][0])['/Contents']
    if type(i_c) == complex:
        i_c = [i_c]
    for content in i_c:
        c2 = get_object(doc, content)
        if type(c2) != list:
            c2 = [c2]
        for content2 in c2:
            c3 = get_object(doc, content2)
            ret.append(c3)
    return ret


def build_text_fragments(page_contents: list, f: list):
    """List all text fragmemts that are part of a page, with their coordinates.
    
    Each list item is another list made of:
    - the intial transformation matrix
    - the text
    - the final tranformation matrix
    """
    tfs = []
    gs = []
    ts = {}
    c_all = b''
    for c in page_contents:
        c_all += c['stream']
    t =parse_stream_content(c_all)
    for te in t:
        if te[-1] not in 'lmchnfgGref*':
             #print(te)
             pass
        apply_command(te, gs, ts)
        #print(ts['tm'])
        if te[-1] == 'TJ' or te[-1] == 'Tj':
            old_trm = trm(ts, gs)
            #print(f"TRM ====> {old_trm}")
            uc, displacement = text_element_to_unicode(f[0], te, ts)
            tx = (displacement * ts['Tfs'] + ts['Tc'] + ts['Tw']) * ts['Th'] / 100
            ty = 0 #TODO
            ts['tm'] = multiply_matrices([1, 0, 0, 1, tx, ty], ts['tm'])
            new_trm = trm(ts, gs)
            tfs.append([old_trm, uc, new_trm])
    return tfs


def extract_page_text(doc: Doc, page_num: int):
    """Return all page text as a single string."""
    f = get_page_fonts(doc, [page_num])
    pcs = get_page_contents(doc, page_num)
    tfs = build_text_fragments(pcs, f)
    #print(tfs)
    simplify_horizontal_text_elements(tfs)
    #print_debug(tfs)
    fs = typical_font_size(tfs)
    #print(typical_line_spacing(tfs, fs))
    #print(typical_char_width(tfs, fs))
    return basic_spatial_layout(tfs)


def pprint_page_contents(doc: Doc, page_num: int) -> str:
    """."""
    ret = ''
    contents = get_page_contents(doc, page_num)
    for content in contents:
        f = format_stream_content(content)
        ret += '$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n'
        ret += f
    print(ret)
    return ret


def find_xref_table_pos_in_index(xref_table_pos, index):
    """."""
    found = None
    obj = index[0][0]
    if type(obj) == dict:
        obj_list = [obj]
    else:
        obj_list = obj
    for o in obj_list:
        if o.get('xref_table_pos') == xref_table_pos:
            found = (0, 0)
    for ver in range(1, len(index)):
        obj = index[ver][0]
        if obj is None:
            continue
        if obj.get('xref_table_pos') == xref_table_pos:
            found = (0, ver)
    return found


def find_abs_pos_in_index(abs_pos, index):
    """."""
    found = None
    max_num = len(index[-1]) - 1
    for num in range(1, max_num+1):
        for ver in range(len(index)):
            if num > len(index[ver]) - 1:
                continue
            obj = index[ver][num]
            if obj is None:
                continue
            if obj.get('abs_pos') == abs_pos:
                found = (num, ver)
        if found:
            return found
    return found


def cross_map_index(sections, index):
    """."""
    ret = {}
    for section in sections:
        abs_pos, addon, typ, payload = section
        if typ == 'XREFTABLE':
            trailer = payload['trailer']
            relevance = find_xref_table_pos_in_index(abs_pos, index)
            targets = deep_ref_detect(trailer)
            ret[abs_pos] = 0, relevance, targets, []
        elif typ == 'IND_OBJ':
            o_num = payload['o_num']
            o_gen = payload['o_gen']
            obj = payload['obj']
            relevance = find_abs_pos_in_index(abs_pos, index)
            targets = deep_ref_detect(obj)
            ret[abs_pos] = o_num, relevance, targets, []
    for abs_pos in ret:
        o_num, relevance, targets, _ = ret[abs_pos]
        _, ver = relevance
        if ver < len(index) - 1:
            continue
        for target in targets:
            target_num = int(target.imag)
            target_pos = index[-1][target_num]['abs_pos']
            _, _, _, target_used_by = ret[target_pos]
            target_used_by.append((o_num, abs_pos))
    return ret


Doc.trailer = trailer
Doc.catalog = catalog
Doc.metadata = metadata
Doc.structure = structure
Doc.get_object = get_object
Doc.obj = obj
Doc.rewind = rewind
Doc.rotate = rotate
Doc.page_layouts = page_layouts
Doc.flat_page_tree = flat_page_tree
Doc.pages = pages

