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
                        choices=['browse', 'disasm', 'overview', 'text'],
                        help='Command')
    parser.add_argument('filename', type=str, help='PDF file name')
    args = parser.parse_args()
    if args.command == 'browse':
        browse(args.filename)
    elif args.command == 'disasm':
        dump_disasm(args.filename)
    elif args.command == 'overview':
        overview(args.filename)
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
        elif region_type == 'STARTXREF':
            startxref = int(content)
            addr = startxref
        elif region_type == 'XREFTABLE':
            macro_ind = '-'
            trailer = content['trailer']
            detail = keys_in_line(trailer, ['/Root', '/Prev'])
        elif region_type == 'IND_OBJ':
            env_num = content.get('env_num')
            if env_num:
                macro_ind = '-'
                seq_num, pos = start_pos
                env_iref = f"{env_num},"
            o_num = content['o_num']
            o_gen = content['o_gen']
            o_gen = '' if o_gen is None else o_gen
            iref = f"{o_num},{o_gen}"
            obj = content['obj']
            cl = type(obj)
            if cl == dict:
                cl = 'dict'
                detail = keys_in_line(obj, ['/Type'])
            elif cl == Stream:
                cl = 'stream'
                detail = keys_in_line(obj['entries'], ['/Type', '/Root', '/Prev', '/N', '/First'])
                ratio = f"{int(len(obj['encoded']) / len(obj['stream']) * 100)}%"
                filters_l = filters_in_line(obj['entries'].get('/Filter'))
            elif cl == list:
                cl = 'array'
            elif cl == int:
                cl = 'int'
            else:
                cl = 'other'
        elif region_type == 'XREF':
            macro_ind = '-'
            pos = None
            if content[0] == 'XREF_T':
                _, index, x_num, x_gen, s = content
                iref = f"{x_num},{x_gen}"
                addr = index
            else:
                _, index, x_num, x_gen, s, env_num, raw_line = content
                iref = f"{x_num},{x_gen}"
                target = 'abs' if env_num is None else f"{env_num},"
                addr = index
                addr_mode = f"{target}"
            cl = 'inuse' if s == b'n' else 'free'
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


def browse(filename: str) -> None:
    """Print html view of the file map."""
    file_obj = open(filename, 'rb')
    fdata = bdata_provider(file_obj)
    file_seq, pos_index, nb_ver = file_map(fdata)
    print(build_html(file_seq, pos_index, nb_ver, filename, fdata(0, 8)[0]))

    
def file_map(fdata: Callable) -> tuple:
    """Build file sequence and sort it by absolute position."""
    file_seq = build_chrono_from_xref(fdata)
    file_index = build_index_from_chrono(file_seq)    
    pos_index = {}
    mini_indexes = []
    temp_2 = []
    nb_ver = len(file_index)
    for ver_index in file_index:
        l = []
        for x in ver_index:
            if x is not None and type(x) == dict:
                l.append((x['o_gen'], x['o_ver']))
            elif x is not None and type(x) == list:
                l.append((x[1]['o_gen'], x[1]['o_ver']))
        mini_indexes.append(l)
    for obj in file_seq:
        if obj['o_num'] >= 0:
            if obj['o_num'] == 0:
                content = 1
                o_ver = obj['o_ver']
                i0 = file_index[obj['doc_ver']][0]
                if type(i0) == list:
                    i1 = i0.pop(0)
                    if len(i0) == 1:
                        content = 0
                        o_ver = 1
                    else:
                        o_ver = 0
                else:
                    i1 = i0
                bdata, a0, _, _ = fdata(i1['abs_pos'], i1['abs_next'] - i1['abs_pos'])
                i, j, _ = next_token(bdata, a0)
                i, j, _ = next_token(bdata, j)
                if 'xref_stream' in i1:
                    i, j, _ = next_token(bdata, j)
                    i, j, _ = next_token(bdata, j)
                i_obj = parse_obj(bdata, i)
                if type(i_obj) == Stream:
                    i_obj = i_obj['entries']
                obj['content'] = i_obj
                if content:
                    content = obj.get('xref_table_pos') or obj.get('xref_stream_pos')
                x = {
                    'o_num': -2,
                    'o_gen': -2,
                    'o_ver': o_ver,
                    'content': content,
                    'abs_pos': obj['startxref_pos'],
                }
                temp_2.append(x)
                pos_index[obj['startxref_pos']] = f"-2.-2.{o_ver}"
            else:
                obj['content'] = memoize_obj_in_cache(file_index,
                                                      fdata,
                                                      obj['o_num'],
                                                      rev=obj['doc_ver'])[obj['o_num']]
        elif obj['o_num'] == -1:
            obj['content'] = None
        obj['mini_index'] = mini_indexes[obj['doc_ver']]
        if 'abs_pos' in obj:
            if 'xref_table_pos' in obj:
                obj['abs_pos'] = obj['xref_table_pos']
            pos_index[obj['abs_pos']] = f"{obj['o_num']}.{obj['o_gen']}.{obj['o_ver']}"
        if 'abs_pos' not in obj:
            obj['abs_pos'] = obj['a_']
    file_seq.extend(temp_2)
    file_seq.sort(key=lambda x: x.get('abs_pos') or x.get('a_'))

    for i, x in enumerate(file_seq):
        if i > 0 and file_seq[i-1]['abs_pos'] == file_seq[i]['abs_pos']:
            if file_seq[i-1].get('xref_stream_num') == file_seq[i]['o_num']:
                file_seq[i]['xref_stream'] = file_seq[i-1]['xref_stream']
                del file_seq[i-1]
            elif file_seq[i].get('xref_stream_num') == file_seq[i-1]['o_num']:
                file_seq[i-1]['xref_stream'] = file_seq[i]['xref_stream']
                del file_seq[i]
    return (file_seq, pos_index, nb_ver)
