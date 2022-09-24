"""Module pdfsyntax.filestruct: how objects are stored in a PDF file"""

from .objects import *

MARGIN = b'\n'


def bdata_provider(filename: str, mode: str = "SINGLE"):
    if mode == "SINGLE":
        bfile = open(filename, 'rb')
        bdata = bfile.read()
        bfile.close()
        def single_load(i: int, n: int) -> tuple:
            return (bdata, i)
        return single_load
    else:
        def continuous_load(i: int, n: int) -> tuple:
            bfile = open(filename, 'rb')
            bfile.seek(i, 0)
            bdata = bfile.read(n)
            bfile.close()
            return (bdata, 0)
        return continuous_load


def parse_xref_table(bdata: bytes, start_pos: int) -> list:
    """Return a list of dicts indexing indirect objects

       abs_pos is the absolute position of the object
       o_num is the object number
       o_gen is the object generation number
    """
    xref = []
    table = []
    trailer_pos = bdata.find(b'trailer', start_pos)
    lines = bdata[start_pos:trailer_pos].splitlines()
    for line in lines:
        line_a = line.strip(b'\n\r ').split()
        #line_a = []
        #i, n, begin_i = 0, len(line), 0
        #while i < n:
        #    if line[i] in b' ':
        #        line_a.append(line[begin_i:i])
        #        begin_i = i + 1
        #    i += 1
        #line_a.append(line[begin_i:i])
        l = len(line_a)
        if  l == 2:
            o_num = int(line_a[0])
            table.append((line, None))
        elif l == 3:
            offset = int(line_a[0])
            o_ver = int(line_a[1])
            #o_start = bdata.find(b'obj', offset) + len(b'obj') + 1
            #if bdata[o_start] in b'\r\n ': o_start += 1
            if o_num != 0:
                xref.append({'abs_pos': offset, 'o_num': o_num, 'o_gen': o_ver})
            table.append((line, o_num))
            o_num += 1
    xref.insert(0, {'o_num': 0, 'o_gen': 0, 'abs_pos': trailer_pos, 'xref_table_pos':start_pos, 'xref_table':table })
    return xref


def parse_xref_stream(xref_stream: dict, trailer_pos: int) -> list:
    """Return a list of dicts indexing indirect objects

       for regular objects:
           abs_pos is the absolute position of the object
           o_num is the object number
           o_gen is the object generation number
       for objects embedded in object streams:
           env_num is the number of the envelope object
           o_num is the object number
           o_gen is the object generation number
           o_pos is the position of the object within the stream
    """
    xref = []
    table = []
    cols = xref_stream['stream_def']['/W']
    i = 0
    obj_range = (0, 0)
    if '/Index' in xref_stream['stream_def']:
        obj_range = xref_stream['stream_def']['/Index']
    start_obj, nb_obj = int(obj_range[0]), int(obj_range[1])
    obj_num = start_obj
    while i < len(xref_stream['stream_content']):
        line = ''
        params = []
        for col in cols:
            params.append(int.from_bytes(xref_stream['stream_content'][i:i+int(col)], byteorder='big')) # struct.unpack cannot work with 3-byte words
            i += int(col)
        if params[0] == 1:
            xref.append({'abs_pos': params[1], 'o_num': obj_num, 'o_gen': params[2]})
        elif params[0] == 2:
            xref.append({'env_num': params[1], 'o_num': obj_num, 'o_gen': 0, 'o_pos': params[2]})
        obj_num += 1
    xref.insert(0, {'o_num': 0, 'o_gen': 0, 'abs_pos': trailer_pos, 'xref_stream':table})
    return xref
    

def build_chrono_from_xref(bdata: bytes) -> list:
    """Return a merged list of all entries found in xref tables or xref streams """
    EOF = b'%%EOF'
    STARTXREF = b'startxref'
    XREF = b'xref'
    eof_pos = bdata.rfind(EOF)
    startxref_pos = bdata.rfind(STARTXREF)
    i, j, _ = next_token(bdata, startxref_pos + len(STARTXREF))
    xref_pos = int(bdata[i:j])
    if bdata[xref_pos:xref_pos+4] == XREF:
        chrono = parse_xref_table(bdata, xref_pos)
        i, j, _ = next_token(bdata, chrono[0]['abs_pos'])  # b'trailer'
        i, j, _ = next_token(bdata, j)                     # actual trailer dict
        trailer = parse_obj(bdata[i:j])
    else: # must be a /XRef stream
        i, j, _ = next_token(bdata, xref_pos)
        i, j, _ = next_token(bdata, j)
        i, j, _ = next_token(bdata, j)
        i, j, _ = next_token(bdata, j)
        xref = parse_obj(bdata, i)
        chrono = parse_xref_stream(xref, xref_pos)
        trailer = xref['stream_def']
    chrono[0]['startxref_pos'] = startxref_pos
    chrono.append({'o_num': -1, 'o_gen': -1, 'abs_pos': eof_pos})
    while '/Prev' in trailer:
        new_xref_pos = trailer['/Prev']
        xref_pos = int(new_xref_pos)
        startxref_pos = bdata.find(STARTXREF, xref_pos)
        eof_pos = bdata.find(EOF, xref_pos)
        if bdata[xref_pos:xref_pos+4] == XREF:
            tmp_index = parse_xref_table(bdata, xref_pos)
            tmp_index[0]['startxref_pos'] = startxref_pos
            tmp_index.append({'o_num': -1, 'o_gen': -1, 'abs_pos': eof_pos})
            chrono = tmp_index + chrono
            i, j, _ = next_token(bdata, chrono[0]['abs_pos'])
            i, j, _ = next_token(bdata, j)                     # actual trailer dict
            trailer = parse_obj(bdata[i:j])
        else: # must be a /XRef stream
            i, j, _ = next_token(bdata, xref_pos)
            i, j, _ = next_token(bdata, j)
            i, j, _ = next_token(bdata, j)
            xref = parse_obj(bdata, i)
            tmp_index = parse_xref_stream(xref, xref_pos)
            tmp_index[0]['startxref_pos'] = startxref_pos
            tmp_index.append({'o_num': -1, 'o_gen': -1, 'abs_pos': eof_pos})
            chrono =  tmp_index + chrono
            trailer = xref['stream_def']
    seq = [i['abs_pos'] for i in chrono]
    seq.sort()
    idx = {}
    i = 0
    l = len(seq)
    while i <  l - 1:
        idx[seq[i]] = seq[i+1]
        i += 1
    idx[seq[i]] = None
    for i in chrono:
        i['abs_next'] = idx[i['abs_pos']]
    return chrono


def build_index_from_chrono(chrono: list) -> list:
    """Build a multi-dimensional array where each column represents a doc update"""
    nb = max(chrono, key = lambda i: i['o_num']).get('o_num') + 2
    m = nb * [None]
    abs_pos_array = nb * [0]
    index = []
    doc_ver = -1
    prev_pos = 0
    for obj in chrono:
        if obj['o_num'] == 0 and obj['abs_pos'] > prev_pos:
            m = m[:]
            m[0] = None
            index.append(m)
            doc_ver += 1
            prev_pos = obj['abs_pos']
        elif obj['o_num'] == -1:
            pass
        if m[obj['o_num']] is None:
            if obj['o_num'] == 0:
                obj['o_ver'] = doc_ver
            else:
                obj['o_ver'] = 0
        else:
            obj['o_ver'] = index[-1][obj['o_num']]['o_ver'] + 1
        obj['doc_ver'] = doc_ver
        if obj['o_num'] == 0 and m[obj['o_num']] is not None:
            m[0] = [m[0] ,obj]
        else:
            m[obj['o_num']] = obj
    for rev in index:
        abs_list = [obj for obj in rev if obj is not None and 'abs_pos' in obj]
        env_list = [obj for obj in rev if obj is not None and 'env_num' in obj]
        for obj in abs_list:
            abs_pos_array[obj['o_num']] = obj['abs_pos']
        for obj in env_list:
            obj['a_'] = abs_pos_array[obj['env_num']] + (obj['o_pos'] + 1) / 1000
    return index


def circular_deleted(changes: list) -> dict:
    """Build lookup dict to ref of next deleted object"""
    res = {}
    deleted = [x for x in changes if x[1] == 'd']
    for i, d in enumerate([(0, 'd')] + deleted):
        if i == len(deleted):
            res[d[0]] = 0
        else:
            res[d[0]] = deleted[i][0]
    return res


def build_xref_table(xref_table: list) -> bytes:
    """Serialize XREF table into bytes"""
    res = b'xref\n'
    for x, _ in xref_table:
        res += x
        res += b'\n'
    return res


def build_fragments(changes: list, current_index: list, cache: list, starting_pos: int) -> list:
    """List the sequence of byte blocks that make the update"""
    fragments = []
    xref_table = []
    counter = starting_pos + len(MARGIN)
    fragments.append(MARGIN)
    next_free = circular_deleted(changes)
    for num, action in ([(0, 'd')] + changes):
        if action == 'd':
            if num == 0:
                o_gen = 65535 - 1
            else:
                o_gen = current_index[num]['o_gen']
            header = str(num).encode('ascii') + b' 1'
            xref_table.append((header, None))
            ref = f'{next_free[num]:010} {(o_gen+1):05} f'.encode('ascii')
            xref_table.append((ref, num))
        else:
            o_gen = current_index[num]['o_gen']
            beginobj = f'{num} {o_gen}'.encode('ascii') + b' obj\n'
            ser = serialize(cache[num]) + b'\n'
            endobj = b'endobj\n'
            block = beginobj + ser + endobj
            fragments.append(block)
            header = str(num).encode('ascii') + b' 1'
            xref_table.append((header, None))
            ref = f'{counter:010} {o_gen:05} n'.encode('ascii')
            xref_table.append((ref, num))
            counter += len(block)
    current_index[0]['xref_table'] = xref_table
    fragments.append(build_xref_table(xref_table))
    ser0 = serialize(cache[0])
    fragments.append(b'trailer\n' + ser0 + b'\n')
    fragments.append(f'startxref\n{counter}\n'.encode('ascii'))
    fragments.append(b'%%EOF\n')
    return fragments

