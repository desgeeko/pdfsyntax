"""Module pdfsyntax.cli: Command Line Interface"""

import argparse
from .docstruct import *
from .objects import *
from .api import *
from .display import build_html

def main():
    """ """
    parser = argparse.ArgumentParser(prog='python3 -m pdfsyntax', description='Navigate through the structure of a PDF file')
    parser.add_argument('command', type=str, choices=['inspect', 'overview'], help='Command')
    parser.add_argument('filename', type=str, help='PDF file name')
    args = parser.parse_args()
    if args.command == 'inspect':
        inspect(args.filename)
    elif args.command == 'overview':
        overview(args.filename)

def overview(filename: str) -> None:
    """Print both structure and metadata of a file"""
    fdata = bdata_provider(filename)
    doc, _ = init_doc(fdata)
    doc = add_revision(doc)
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

def inspect(filename: str) -> None:
    """Print html view of the file map"""
    fdata = bdata_provider(filename)
    file_seq, pos_index, nb_ver = file_map(fdata)
    print(build_html(file_seq, pos_index, nb_ver, filename, fdata(0, 8)[0]))

def file_map(fdata: Callable) -> tuple:
    """Build file sequence and sort it by absolute position"""
    file_seq = build_chrono_from_xref(fdata)
    file_index = build_index_from_chrono(file_seq)    
    pos_index = {}
    mini_indexes = []
    temp_2 = []

    nb_ver = len(file_index)
    for ver_index in file_index:
        mini_indexes.append([(x['o_gen'], x['o_ver']) for x in ver_index if x is not None])
 
    for obj in file_seq:
        if obj['o_num'] >= 0:
            obj['content'] = memoize_obj_in_cache(file_index, fdata, obj['o_num'], rev=obj['doc_ver'])[-1]
            if obj['o_num'] == 0:
                temp_2.append({'o_num': -2, 'o_gen': -2, 'o_ver': obj['o_ver'], 'content': obj.get('xref_table_pos') or obj.get('xref_stream_pos'), 'abs_pos': obj['startxref_pos']})
                pos_index[obj['startxref_pos']] = f"-2.-2.{obj['o_ver']}"
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
    #file_seq = [x for i, x in enumerate(file_seq) if i == 0 or file_seq[i-1]['abs_pos'] != x['abs_pos']]
    for i, x in enumerate(file_seq):
        if i > 0 and file_seq[i-1]['abs_pos'] == file_seq[i]['abs_pos']:
            if file_seq[i-1].get('xref_stream_num') == file_seq[i]['o_num']:
                file_seq[i]['xref_stream'] = file_seq[i-1]['xref_stream']
                del file_seq[i-1]
            elif file_seq[i].get('xref_stream_num') == file_seq[i-1]['o_num']:
                file_seq[i-1]['xref_stream'] = file_seq[i]['xref_stream']
                del file_seq[i]
    return (file_seq, pos_index, nb_ver)
