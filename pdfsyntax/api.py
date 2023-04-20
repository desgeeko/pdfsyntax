"""Module pdfsyntax.api: Application Programming Interface"""

from copy import deepcopy
from .docstruct import *
from .filestruct import *
from .objects import *
from .text import *

METADATA_ATTRS = '/Title /Author /Subject /Keywords /Creator /Producer'.split()

def in2pt(inches: float) -> int:
    """Convert inches into points"""
    return int(inches*72)

def mm2pt(millimeters: int) -> int:
    """Convert millimeters into points"""
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


def init_doc(fdata: Callable) -> tuple:
    """Initialize doc object representing PDF file"""
    chrono = build_chrono_from_xref(fdata)
    index = build_index_from_chrono(chrono)
    data = build_data_from_cache(index, fdata)
    for i in index:
        del i[-1]
    cache = build_cache(fdata, index)
    doc = Doc(index, cache, data)
    return doc, chrono


#def load(fp) -> Doc:
#    """ """
#    bdata = fp.read()
#    doc, _ = init_doc(bdata)
#    doc = add_version(doc)
#    return doc


#def loads(bdata) -> Doc:
#    """ """
#    doc, _ = init_doc(bdata)
#    doc = add_version(doc)
#    return doc


def read(filename: str, mode: str = "SINGLE") -> Doc:
    """Read file and initialize doc"""
    #bfile = open(filename, 'rb')
    #bdata = bfile.read()
    #bfile.close()
    fdata = bdata_provider(filename, mode)
    doc, _ = init_doc(fdata)
    doc = add_revision(doc)
    return doc


def write(doc: Doc, filename: str) -> Doc:
    """Write doc into file"""
    bdata = b''
    idx = 0
    doc = add_revision(doc)
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
    else:
        FILE_HEADER = b'%PDF-' + version(doc).encode('ascii') + b'\n'
        bdata += FILE_HEADER
        idx += len(FILE_HEADER)
    for i in range(eof_rev+1, nb_rev-1):
        fragment = doc.data[i]['bdata']
        bdata += fragment
        idx += len(fragment)
    bfile = open(filename, 'wb')
    bfile.write(bdata)
    bfile.close()
    return doc


def structure(doc: Doc) -> dict:
    """Return various doc attributes (other than metadata)"""
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


def metadata(doc: Doc) -> dict:
    """Return doc metadata"""
    ret = {}
    i = info(doc) or {}
    for entry in METADATA_ATTRS:
        ret[entry[1:]] = text_string(get_object(doc, i.get(entry))) or None
    ret['CreationDate'] = text_string(get_object(doc, i.get('/CreationDate'))) or None
    ret['ModDate'] = text_string(get_object(doc, i.get('/ModDate'))) or None
    return ret 


def paper(mediabox: list) -> str:
    """Detect paper size"""
    x, y = mediabox[2] - mediabox[0], mediabox[3] - mediabox[1]
    ptype = PAPER_SIZES.get((x, y)) or PAPER_SIZES.get((y, x)) or "unknown"
    pdim = f'{int(x*25.4/72)}x{int(y*25.4/72)}mm or {round(x/72, 2)}x{round(y/72, 2)}in'
    return pdim + f' ({ptype})'


def page_layouts(doc: Doc, max_nb=None) -> list:
    """List page layouts"""
    pl = pages(doc, max_nb)
    med = [(p['/MediaBox'], p.get('/Rotate')) for p in pl]
    return med


def rotate(doc: Doc, degrees: int = 90, pages: list = []) -> Doc:
    """Rotate 1 or several pages"""
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


def single_text_annotation(doc: Doc, page_num: int, text: str) -> Doc:
    """Add simple text annotation"""
    annot = {
        '/Type': '/Annot',
        '/Subtype': '/Text',
        '/Rect': [50, 50, 150, 150],
        '/Contents': f"({text})",
        '/Open': False,
    }
    doc, a_iref = add_object(doc, annot)
    annot_array = [a_iref]
    doc, aa_iref = add_object(doc, annot_array)
    page_ref, _ = flat_page_tree(doc)[page_num]
    new_page = deepcopy(get_object(doc, page_ref))
    new_page['/Annots'] = aa_iref
    doc = update_object(doc, int(page_ref.imag), new_page)
    return doc


Doc.trailer = trailer
Doc.catalog = catalog
Doc.metadata = metadata
Doc.structure = structure
Doc.get_object = get_object
Doc.rewind = rewind
Doc.rotate = rotate
Doc.page_layouts = page_layouts
Doc.flat_page_tree = flat_page_tree
Doc.pages = pages

