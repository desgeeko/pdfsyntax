"""Module pdfsyntax.cli: Command Line Interface"""

import argparse
import math
from .docstruct import *
from .objects import *
from .api import *
from .display import build_html


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(prog='python3 -m pdfsyntax',
                                     description='Navigate through the structure of a PDF file')
    parser.add_argument('command',
                        type=str,
                        choices=['browse', 'disasm', 'overview', 'fonts', 'text'],
                        help='Command')
    parser.add_argument('filename', type=str, help='PDF file name')
    args = parser.parse_args()
    if args.command == 'browse':
        browse(args.filename)
    elif args.command == 'disasm':
        dump_disasm(args.filename)
    elif args.command == 'overview':
        overview(args.filename)
    elif args.command == 'fonts':
        print_fonts(args.filename)
    elif args.command == 'text':
        spatial(args.filename)


def keys_in_line(target, keys: list) -> str:
    """."""
    res = ''
    if '/Type' in keys:
        value = target.get('/Type')
        if value is not None:
            res += f"{value}  "
        keys.remove('/Type')
    for key in keys:
        value = target.get(key)
        if value is None:
            continue
        if type(value) == complex:
            value = f"{int(value.imag)},{int(value.real)}"
        res += f"{key}={value}  "
    return res


def filters_in_line(filters) -> str:
    """."""
    res = ''
    if type(filters) != list:
        filters = [filters]
    for f in filters:
        res += '_'
        if f == '/ASCIIHexDecode':
            res += 'AHex'
        elif f == '/ASCII85Decode':
            res += 'A85'
        elif f == '/LZWDecode':
            res += 'LZW'
        elif f == '/FlateDecode':
            res += 'Flate'
        elif f == '/RunLengthDecode':
            res += 'RunL'
        elif f == '/CCITTFaxDecode':
            res += 'Fax'
        elif f == '/JBIG2Decode':
            res += 'JBIG2'
        elif f == '/DCTDecode':
            res += 'DCT'
        elif f == '/JPXDecode':
            res += 'JPX'
        elif f == '/Crypt':
            res += 'Crypt'
    return res


def print_disasm_columns(lines: list, columns_mode: str = 'VARIABLE') -> list:
    """."""
    w = {}
    w['pos'] = 10
    w['size'] = 10
    w['filters_l'] = 10
    w['env_iref'] = 5
    w['seq_num'] = 5
    w['iref'] = 12
    w['addr_mode'] = 5
    w['addr'] = 10
    if columns_mode == 'VARIABLE':
        for k in w:
            w[k] = 1
        for line in lines:
            for field in w:
                f = line.get(field)
                if type(f) == int:
                    digits = 1 if f == 0 else int(math.log10(f)) + 1
                    w[field] = digits if digits > w[field] else w[field]
                elif type(f) == str:
                    w[field] = len(f) if len(f) > w[field] else w[field]
                else:
                    pass
    for line in lines:
        l = ""
        l += f"{line['macro_ind']} "
        pos = " " * (w['pos']+1) if line['pos'] is None else f"{line['pos']:0{w['pos']+1}d}"
        l += f"{pos} "
        size = " " * (w['size']+2) if line['size'] == 0 else f"[{line['size']:<{w['size']}}]"
        l += f"{size} "
        l += f"{line['ratio']:4} "
        l += f"{line['filters_l']:{w['filters_l']}} "
        l += f"{line['seq_num']:{w['seq_num']}} "
        l += f"{line['env_iref']:{w['env_iref']}} "
        l += f"{line['region_type']:9} "
        l += f"{line['iref']:{w['iref']}} "
        l += f"{line['addr_mode']:{w['addr_mode']}} "
        addr = " " * (w['addr']+1) if line['addr'] is None else f"{line['addr']:0{w['addr']+1}d}"
        l += f"{addr} "
        l += f"{line['cl']:8} "
        l += f"{line['detail']:20}"
        print(l)
    return


def dump_disasm(filename: str, columns_mode: str = 'VARIABLE') -> str:
    """Disassemble file sequence."""
    res = ""
    file_obj = open(filename, 'rb')
    fdata = bdata_provider(file_obj)
    sections = file_object_map(fdata)
    lines = []
    for start_pos, end_pos, region_type, content in sections:
        macro_ind = '+'
        pos = start_pos
        size = 0
        ratio = ''
        filters_l = ''
        env_iref = ''
        seq_num = ''
        #region_type = ''
        iref = ''
        typ = ''
        cl = ''
        addr_mode = ''
        addr = None
        detail = ''
        if start_pos is None or end_pos is None:
            size = 0
        else:
            if type(end_pos) != tuple:
                size = end_pos - start_pos
        if region_type == 'COMMENT':
            if content[:4] == b'%PDF':
                detail = content[:8].decode('ascii')
            elif content[:5] == b'%%EOF':
                detail = content[:5].decode('ascii')
            else:
                try:
                    detail = content[:10].decode('ascii')
                except:
                    detail = '<' + content[:10].hex() + '>'
            l = {'macro_ind': macro_ind, 'pos': pos, 'size': size, 'ratio': ratio, 'filters_l': filters_l,
                 'env_iref': env_iref, 'seq_num': seq_num, 'region_type': region_type.lower(), 'iref': iref,
                 'addr_mode': addr_mode, 'addr': addr, 'cl': cl, 'detail': detail
                 }
            lines.append(l)
        elif region_type == 'STARTXREF':
            startxref = int(content)
            addr = startxref
            l = {'macro_ind': macro_ind, 'pos': pos, 'size': size, 'ratio': ratio, 'filters_l': filters_l,
                 'env_iref': env_iref, 'seq_num': seq_num, 'region_type': region_type.lower(), 'iref': iref,
                 'addr_mode': addr_mode, 'addr': addr, 'cl': cl, 'detail': detail
                 }
            lines.append(l)
        elif region_type == 'XREFTABLE':
            #macro_ind = '-'
            trailer = content['trailer']
            if '/XRefStm' in trailer:
                detail = keys_in_line(trailer, ['/XRefStm', '/Prev'])
            else:
                detail = keys_in_line(trailer, ['/Root', '/Prev'])
            l = {'macro_ind': macro_ind, 'pos': pos, 'size': size, 'ratio': ratio, 'filters_l': filters_l,
                 'env_iref': env_iref, 'seq_num': seq_num, 'region_type': region_type.lower(), 'iref': iref,
                 'addr_mode': addr_mode, 'addr': addr, 'cl': cl, 'detail': detail
                 }
            lines.append(l)
            for x in content['table']:
                if len(x) == 2:
                    continue
                _, _, _, y = x
                _, index, x_num, x_gen, s = y
                iref = f"{x_num},{x_gen}"
                addr = index
                cl = 'inuse' if s == b'n' else 'free'
                macro_ind = '-'
                pos = None
                size = 0
                ratio = ''
                region_type = 'xref'
                detail = ''
                l = {'macro_ind': macro_ind, 'pos': pos, 'size': size, 'ratio': ratio, 'filters_l': filters_l,
                     'env_iref': env_iref, 'seq_num': seq_num, 'region_type': region_type.lower(), 'iref': iref,
                     'addr_mode': addr_mode, 'addr': addr, 'cl': cl, 'detail': detail
                     }
                lines.append(l)
        elif region_type == 'IND_OBJ':
            env_num = content.get('env_num')
            if env_num:
                macro_ind = '-'
                #env_pos, pos, seq_num = start_pos
                env_pos, pos, seq_num = end_pos
                env_iref = f"{env_num},"
            o_num = content['o_num']
            o_gen = content['o_gen']
            o_gen = '' if o_gen is None else o_gen
            iref = f"{o_num},{o_gen}"
            obj = content['obj']
            cl = type(obj)
            if cl == dict:
                cl = 'dict'
                detail = keys_in_line(obj, ['/Type', '/Linearized'])
            elif cl == Stream:
                cl = 'stream'
                detail = keys_in_line(obj['entries'], ['/Type', '/Root', '/Prev', '/N', '/First'])
                if len(obj['stream']):
                    ratio = f"{int(len(obj['encoded']) / len(obj['stream']) * 100)}%"
                else:
                    ratio = "!!"
                filters_l = filters_in_line(obj['entries'].get('/Filter'))
            elif cl == list:
                cl = 'array'
            elif cl == int:
                cl = 'int'
            else:
                cl = 'other'
            l = {'macro_ind': macro_ind, 'pos': pos, 'size': size, 'ratio': ratio, 'filters_l': filters_l,
                 'env_iref': env_iref, 'seq_num': seq_num, 'region_type': region_type.lower(), 'iref': iref,
                 'addr_mode': addr_mode, 'addr': addr, 'cl': cl, 'detail': detail
                 }
            lines.append(l)
        elif region_type == 'XREFSTREAM':
            trailer = content['trailer']
            for x in content['table']:
                _, _, _, y = x
                _, index, x_num, x_gen, s, env_num, raw_line = y
                iref = f"{x_num},{x_gen}"
                target = 'abs' if env_num is None else f"{env_num},"
                addr = index
                addr_mode = f"{target}"
                cl = 'inuse' if s == b'n' else 'free'
                macro_ind = '-'
                pos = None
                size = 0
                ratio = ''
                region_type = 'xref'
                detail = ''
                l = {'macro_ind': macro_ind, 'pos': pos, 'size': size, 'ratio': ratio, 'filters_l': filters_l,
                     'env_iref': env_iref, 'seq_num': seq_num, 'region_type': region_type.lower(), 'iref': iref,
                     'addr_mode': addr_mode, 'addr': addr, 'cl': cl, 'detail': detail
                     }
                lines.append(l)
        elif region_type == 'VOID':
            l = {'macro_ind': macro_ind, 'pos': pos, 'size': size, 'ratio': ratio, 'filters_l': filters_l,
                 'env_iref': env_iref, 'seq_num': seq_num, 'region_type': region_type.lower(), 'iref': iref,
                 'addr_mode': addr_mode, 'addr': addr, 'cl': cl, 'detail': detail
                 }
            lines.append(l)
    print_disasm_columns(lines, columns_mode)
    return sections


def spatial(filename: str) -> None:
    """Print text content of a file with spatial awareness."""
    doc = readfile(filename)
    for i in range(len(pages(doc))):
        print(extract_page_text(doc, i))
    return


def print_generic_table(lines: list, col_widths: list) -> None:
    """."""
    text = ''
    for line in lines:
        for i, w in enumerate(col_widths):
            text += f"{line[i][:w]:{w}} "
        text += '\n'
    print(text)
    return


def print_fonts(filename: str) -> None:
    """Print fonts used in file."""
    table = []
    doc = readfile(filename)
    fs = fonts(doc)
    table.append(['Name', 'Type', 'Encoding', 'Obj', 'Pages'])
    for iref in fs:
        f = fs[iref]
        o_num = f"{int(iref.imag)},{int(iref.real)}"
        nb_pages = f"{len(f['pages'])}"
        table.append([f['name'], f['type'], f['encoding'], o_num, nb_pages])
    print_generic_table(table, [30, 10, 16, 8, 6])
    return


def overview(filename: str) -> None:
    """Print both structure and metadata of a file."""
    doc = readfile(filename)
    s = structure(doc)
    m = metadata(doc)
    print('# Structure')
    for key in s:
        print(f"{key}: {s[key]}")
    print('\n# Metadata')
    for key in m:
        if m[key] and s['Encrypted']:
            print(f"{key}: #Encrypted#")
        else:
            print(f"{key}: {m[key]}")
    return


def file_map(fdata: Callable) -> tuple:
    """Build file sequence and sort it by absolute position."""
    new_sections = []
    chrono, nxt, nb = build_xref_sequence(fdata)
    index = build_index_from_xref_sequence(chrono, nxt, nb)
    sections = file_object_map(fdata)
    for x in sections:
        if x[2] == 'VOID':
            continue
        new_sections.append(x)
    return (new_sections, index)


def browse(filename: str) -> None:
    """Print html view of the file map."""
    file_obj = open(filename, 'rb')
    fdata = bdata_provider(file_obj)
    _, _, _, file_size = fdata(None, -1)
    sections, index = file_map(fdata)
    cross = cross_map_index(sections, index)
    doc = doc_constructor(fdata)
    s = structure(doc)
    pages = flat_page_tree(doc)
    print(build_html(sections, index, cross, filename, pages, s, file_size))




