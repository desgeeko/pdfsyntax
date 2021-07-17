"""Module pdfsyntax.cli: Command Line Interface"""

import argparse
from .docstruct import *
from .objects import *
from .display import build_html

def main():
    parser = argparse.ArgumentParser(prog='python3 -m pdfsyntax', description='Navigate through the structure of a PDF file')
    parser.add_argument('command', type=str, choices=['inspect'], help='Command')
    parser.add_argument('filename', type=str, help='PDF file name')
    args = parser.parse_args()
    if args.command == 'inspect':
        inspect(args.filename)

def inspect(filename):
    """Reconstruct file sequence of objects from index, sorted by absolute position"""
    bfile = open(filename, 'rb')
    bdata = bfile.read()
    bfile.close()
    doc = loads(bdata)
    file_seq = []
    second = None
    for ver, snapshot in enumerate(doc.index):
        nb_obj = len(snapshot)
        cache = nb_obj * [None]
        mini_index = nb_obj * [None]
        for i in range(1, len(snapshot)):
            mini_index[i] = (snapshot[i]['o_gen'], snapshot[i]['o_ver'])
        if type(snapshot[0]) == list:
            second = snapshot[0].pop()
            snapshot[0] = snapshot[0][0]
            memoize_obj_in_cache([snapshot], doc.bdata, i, cache)
            snapshot[0]['content'] = cache[0]
            snapshot[0]['mini_index'] = mini_index
            if 'xref_stream' not in snapshot[0]:
                file_seq.append(snapshot[0])
            snapshot[0] = second
        for i in range(len(snapshot)):
            if snapshot[i]['o_num'] == 0 and 'xref_stream' in snapshot[i]:
                snapshot[i]['ignore'] = True
                continue
            memoize_obj_in_cache([snapshot], doc.bdata, i, cache)
            snapshot[i]['content'] = cache[i]
            snapshot[i]['mini_index'] = mini_index
            if i == 0: print(snapshot[i])
        file_seq.extend(snapshot)
    file_seq = [x for x in file_seq if x is not None and 'ignore' not in x]
    pos_index = {}

    STARTXREF = b'startxref'
    startxref_pos = 0
    while True:
        startxref_pos = bdata.find(STARTXREF, startxref_pos)
        if startxref_pos == -1:
            break
        i, j, _ = next_token(bdata, startxref_pos + len(STARTXREF))
        xref_pos = int(bdata[i:j])
        file_seq.append({'abs_pos':startxref_pos, 'o_num':-1, 'o_gen':-1, 'o_ver':startxref_pos,
                         'mini_index':None, 'content':xref_pos})
        startxref_pos += len(STARTXREF)

    EOF = b'%%EOF'
    eof_pos = 0
    while True:
        eof_pos = bdata.find(EOF, eof_pos)
        if eof_pos == -1:
            break
        file_seq.append({'abs_pos':eof_pos, 'o_num':-2, 'o_gen':-2, 'o_ver':eof_pos,
                         'mini_index':None, 'content':None})
        eof_pos += len(EOF)
    
    for obj in file_seq:
        if 'abs_pos' in obj and obj['o_num'] != -2:
            pos_index[obj['abs_pos']] = f"{obj['o_num']}.{obj['o_gen']}.{obj['o_ver']}"
    file_seq.sort(key=lambda x: x.get('abs_pos') or x.get('a_'))  
    print(build_html(file_seq, pos_index, filename))


