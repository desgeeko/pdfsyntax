"""Module pdfsyntax.cli: Command Line Interface"""

import argparse
import math
from .docstruct import *
from .objects import *
from .api import *
from .display import build_html


COMMANDS = {
    'browse': {
        'help': 'HTML visualization to browse the internal structure',
        'description': '',
        'epilog': '',
        'arguments': ['input_f']
        },
    'disasm': {
        'help': 'Dump of the file structure',
        'description': '',
        'epilog': '',
        'arguments': ['input_f']
        },
    'overview': {
        'help': 'General info',
        'description': '',
        'epilog': '',
        'arguments': ['input_f']
        },
    'fonts': {
        'help': 'List of fonts',
        'description': '',
        'epilog': '',
        'arguments': ['input_f']
        },
    'text': {
        'help': 'Text extraction',
        'description': '',
        'epilog': '',
        'arguments': ['input_f']
        },
    'compress': {
        'help': 'Lossless compression',
        'description': '',
        'epilog': '',
        'arguments': ['input_f', 'output']
        },
    'hexdump': {
        'help': 'Canonical hex and ascii file dump',
        'description': '',
        'epilog': '',
        'arguments': ['input_f']
        }
    }


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(prog='pdfsyntax',
                                     description='A collection of commands to inspect or transform PDF files',
                                     epilog='Use %(prog)s COMMAND -h to see arguments for COMMAND')
    subparsers = parser.add_subparsers(metavar='COMMAND',
                                       dest='command',
                                       required=True,
                                       help=f'1 of {len(COMMANDS)} values:')
    for c in COMMANDS:
        parser_sub = subparsers.add_parser(c, help=COMMANDS[c]['help'])
        for a in COMMANDS[c]['arguments']:
            if a == 'input_f':
                parser_sub.add_argument('input_f', type=str, metavar='FILE', help='input PDF file')
            elif a == 'output':
                parser_sub.add_argument('-o', '--output',
                                        dest='output_f',
                                        type=str,
                                        metavar='FILE',
                                        help='output PDF file')
    args = parser.parse_args()
    if args.command == 'browse':
        browse(args.input_f)
    elif args.command == 'disasm':
        dump_disasm(args.input_f)
    elif args.command == 'overview':
        overview(args.input_f)
    elif args.command == 'fonts':
        print_fonts(args.input_f)
    elif args.command == 'text':
        spatial(args.input_f)
    elif args.command == 'compress':
        compress_file(args.input_f, args.output_f)
    elif args.command == 'hexdump':
        hexdump_cli(args.input_f)


def keys_in_line(target, keys: list) -> str:
    """."""
    res = ''
    if '/Type' in target:
        value = target.get('/Type')
        if value is not None:
            res += f"{value}  "
    if '/JS' in target:
        res += "!/JS!  "
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


def print_disasm_columns(lines: list, columns_mode: str = 'VARIABLE'):
    """Helper function for dump_disasm."""
    cols = [
        ['macro_ind', 1],
        ['pos', 10],
        ['size', 10],
        ['ratio', 4],
        ['filters_l', 10],
        ['seq_num', 5],
        ['env_iref', 5],
        ['st', 2],
        ['region_type', 9],
        ['iref', 12],
        ['addr_mode', 5],
        ['addr', 10],
        ['cl', 8],
        ['detail', 20],
        ]
    if columns_mode == 'VARIABLE':
        for col in cols:
            col[1] = 1
        for line in lines:
            for col in cols:
                f = line.get(col[0])
                if type(f) == int:
                    digits = 1 if f == 0 else int(math.log10(f)) + 1
                    col[1] = digits if digits > col[1] else col[1]
                elif type(f) == str:
                    col[1] = len(f) if len(f) > col[1] else col[1]
                else:
                    pass
    for line in lines:
        l = ""
        for col in cols:
            k, sz = col[0], col[1]
            v = line.get(k)
            if k == 'pos':
                txt = " " * (sz+1) if v is None else f"{v:0{sz}d} "
            elif k == 'size':
                txt = " " * (sz+3) if v is None else f"[{v:<{sz}}] "
            elif k == 'addr':
                txt = " " * (sz+1) if v is None else f"{v:0{sz}d} "
            else:
                v = line.get(k, "")
                txt = f"{v:{sz}} "
            l += txt
        print(l)
    return


def dump_disasm(filename: str, columns_mode: str = 'VARIABLE') -> str:
    """Disassemble file sequence."""
    res = ""
    file_obj = open(filename, 'rb')
    fdata = bdata_provider(file_obj)
    sections = file_object_map(fdata)
    i, d, n = build_xref_sequence(fdata)
    wrong_targets = check_index_targets(sections, i)
    dir_not_indexed = {x for t, _, _, x in check_not_indexed_objects(sections, i) if t == 'DIR'}
    emb_not_indexed = {(e, n) for t, n, e, _ in check_not_indexed_objects(sections, i) if t == 'EMB'}
    lines = []
    for start_pos, end_pos, region_type, content in sections:
        pos = start_pos
        size = None
        if start_pos is None or end_pos is None:
            size = None
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
            l = {'macro_ind': '+', 'pos': pos, 'size': size,
                 'region_type': region_type.lower(), 'detail': detail
                 }
            lines.append(l)
        elif region_type == 'STARTXREF':
            startxref = int(content)
            addr = startxref
            l = {'macro_ind': '+', 'pos': pos, 'size': size,
                 'region_type': region_type.lower(), 'addr': addr
                 }
            lines.append(l)
        elif region_type == 'XREFTABLE':
            trailer = content['trailer']
            if '/XRefStm' in trailer:
                detail = keys_in_line(trailer, ['/XRefStm', '/Prev'])
            else:
                detail = keys_in_line(trailer, ['/Root', '/Prev'])
            l = {'macro_ind': '+', 'pos': pos, 'size': size,
                 'region_type': region_type.lower(), 'detail': detail
                 }
            lines.append(l)
            if pos in wrong_targets:
                wt = {x for _, _, _, x in wrong_targets[pos]}
            else:
                wt = set()
            for x in content['table']:
                st = '-@'
                if len(x) == 2:
                    continue
                _, _, _, y = x
                _, index, x_num, x_gen, s = y
                iref = f"{x_num},{x_gen}"
                addr = index
                cl = 'inuse' if s == b'n' else 'free'
                pos = None
                size = 0
                ratio = ''
                region_type = 'xref'
                detail = ''
                if addr in wt:
                    st = '-?'
                l = {'macro_ind': '-', 'region_type': region_type.lower(),
                     'iref': iref, 'addr': addr, 'cl': cl, 'st': st
                     }
                lines.append(l)
        elif region_type == 'IND_OBJ':
            macro_ind = '+'
            ratio = ''
            filters_l = ''
            env_iref = ''
            seq_num = ''
            st = '@-'
            detail = ''
            env_num = content.get('env_num')
            if env_num:
                macro_ind = '-'
                env_pos, pos, seq_num = end_pos
                env_iref = f"{env_num},"
                if (env_num, seq_num) in emb_not_indexed:
                    st = '?-'
            else:
                if pos in dir_not_indexed:
                    st = '?-'
            o_num = content['o_num']
            o_gen = content['o_gen']
            o_gen = '' if o_gen is None else o_gen
            iref = f"{o_num},{o_gen}"
            obj = content['obj']
            cl = type(obj)
            if cl == dict:
                cl = 'dict'
                detail = keys_in_line(obj, ['/Linearized'])
            elif cl == Stream:
                cl = 'stream'
                detail = keys_in_line(obj['entries'], ['/Root', '/Prev', '/N', '/First'])
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
            l = {'macro_ind': macro_ind, 'pos': pos, 'size': size, 'ratio': ratio,
                 'filters_l': filters_l, 'env_iref': env_iref, 'seq_num': seq_num,
                 'region_type': region_type.lower(), 'iref': iref, 'cl': cl,
                 'st': st, 'detail': detail
                 }
            lines.append(l)
        elif region_type == 'XREFSTREAM':
            trailer = content['trailer']
            if pos in wrong_targets:
                wt = {x for _, _, _, x in wrong_targets[pos]}
            else:
                wt = set()
            for x in content['table']:
                st = '-@'
                _, _, _, y = x
                _, index, x_num, x_gen, s, env_num, raw_line = y
                iref = f"{x_num},{x_gen}"
                target = 'abs' if env_num is None else f"{env_num},"
                addr = index
                addr_mode = f"{target}"
                cl = 'inuse' if s == b'n' else 'free'
                pos = None
                size = 0
                ratio = ''
                region_type = 'xref'
                detail = ''
                if addr in wt:
                    st = '-?'
                l = {'macro_ind': '-', 'pos': pos,
                     'region_type': region_type.lower(), 'iref': iref,
                     'addr_mode': addr_mode, 'addr': addr, 'cl': cl, 'st': st
                     }
                lines.append(l)
        elif region_type == 'VOID':
            l = {'macro_ind': '+', 'pos': pos, 'size': size,
                 'region_type': region_type.lower()
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
    return


def compress_file(filename: str, output: str) -> None:
    """Compress file."""
    doc = readfile(filename)
    new_doc = compress(doc)
    writefile(new_doc, output)
    return


def hexdump_cli(filename: str) -> None:
    """Print hex dump of file."""
    file_obj = open(filename, 'rb')
    fdata = bdata_provider(file_obj)
    print(hexdump(fdata))
    return


