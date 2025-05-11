"""Module pdfsyntax.filestruct: how objects are stored in a PDF file"""

from typing import Callable
from typing import IO
from .objects import *
import os
import math
from copy import deepcopy
from .filters import *

MARGIN = b'\n'


def bdata_provider(data_source, mode: str = "SINGLE"):
    """Build - with a higher order function - an interface to binary data.
    
    The generated function arguments are:
    - start_pos: index in the data source, can be a negative integer to count from the end
    - length: number of bytes needed
    Return a tuple containing:
    - the buffer to read,
    - the index into the buffer,
    - the offset from the beginning of the file to the buffer,
    - the number of readable bytes.
    """
    if mode == "SINGLE":
        if type(data_source) == bytes:
            bdata = data_source
        else:
            bdata = data_source.read()
        def single_load(start_pos: int, length: int) -> tuple:
            if start_pos ==  None and length == -1: #Special escape for length only
                return (None, None, None, len(bdata))
            i = (start_pos + len(bdata)) % len(bdata)
            if length == -1:
                nb_read = len(bdata) - i
            else:
                nb_read = min(len(bdata) - i, length)
            return (bdata, i, 0, nb_read)
        return single_load
    else:
        file_obj = data_source
        def continuous_load(start_pos: int, length: int) -> tuple:
            file_obj.seek(0, os.SEEK_END)
            file_size = file_obj.tell()
            if start_pos == None and length == -1:
                return (None, None, None, file_size)
            i = (start_pos + file_size) % file_size
            if length == -1:
                nb_read = file_size - i
            else:
                nb_read = min(file_size - i, length)
            file_obj.seek(i)
            bdata = file_obj.read(nb_read)
            return (bdata, i, 0, nb_read)
        return continuous_load


def bdata_dummy(bdata: bytes):
    """ """
    def dummy_load(start_pos: int, length: int) -> tuple:
        if start_pos == -1 and length == 0:
            return (None, None, None, len(bdata))
        if length == -1:
            length = len(bdata) - start_pos
        if start_pos == -1:
            i = len(bdata) - length
        else:
            i = start_pos
        return (bdata, i, 0, min(len(bdata) - start_pos, length))
    return dummy_load


def bdata_length(bdata: Callable) -> int:
    """Offer direct access to data length without reading it."""
    _, _, _, i = bdata(None, -1)
    return i


def bdata_all(bdata: Callable) -> bytes:
    """Return full bdata content as bytes."""
    bdata, _, _, _ = bdata(0, -1)
    return bdata


def hexdump(bdata: Callable, start: int = None, stop: int = None) -> str:
    """Build a string similar to hexdump -C for binary data exploration"""
    LN = 10
    ret = ''
    _, _, _, sz = bdata(None, -1)
    if start is None:
        start = 0
    if stop is None or stop > sz:
        stop = sz
    length = stop - start
    idx = (start // LN) * LN
    buf, d0, i0, sz0 = bdata(idx, length+(start-idx))
    i = d0 + i0
    while i < d0 + i0 + sz0:
        l = buf[i:i+LN]
        hexl = bytes.hex(l, ' ')
        hext = bytes([ascii_hexdump_printable(c) for c in l]).decode('ascii')
        ret += f"{i:0{LN}d}  {hexl:{LN*3-1}}  |{hext}|\n"
        i += LN
    return ret


def file_object_map(fdata: Callable) -> list:
    """Parse whole file in sequential order without using xref."""
    sections = []
    bdata, _, _, length = fdata(0, -1) #Read all
    i = 0
    while i < length:
        mo = parse_region(bdata, i)
        if mo is None:
            break
        bo, eo, t, content = mo
        sections.append(mo)
        if t == 'XREFTABLE':
            table = content['table']
            subsection = -1
            for i, a in enumerate(table):
                if len(a) == 2:
                    subsection += 1
                    ln = 0
                    continue
                index, i_num, i_gen, s = a
                r_pos = subsection, ln
                s = (r_pos, None, 'XREF', ('XREF_T', index, i_num, i_gen, s))
                table[i] = s
                ln += 1
        elif t == 'IND_OBJ' and type(content['obj']) == Stream:
            if content['obj']['entries'].get('/Type') == '/XRef':
                xrefstream = parse_xref_stream_raw(content['obj'], bo)
                _, _, typ, obj = xrefstream
                table = obj['table']
                current_sub = -1
                sections.append(xrefstream)
                for i, a in enumerate(table):
                    index, env_num, i_num, i_gen, s, raw_line, subsection = a
                    if subsection != current_sub:
                        ln = -1
                        current_sub = subsection
                    ln += 1
                    r_pos = subsection, ln
                    s = (r_pos, None, 'XREF', ('XREF_S', index, i_num, i_gen, s, env_num, raw_line))
                    table[i] = s
            elif content['obj']['entries'].get('/Type') == '/ObjStm':
                _, _, typ, obj = parse_object_stream(content['obj'], content['o_num'])
                j = 0
                for embedded in obj:
                    i_num, obj, env_num, theorical_pos, actual_pos = embedded
                    abs_pos = bo + (j + 1) / 10000
                    r_pos = bo, actual_pos, j
                    j += 1
                    s = (abs_pos, r_pos, 'IND_OBJ', {'o_num':i_num, 'o_gen':None, 'obj':obj, 'env_num':env_num})
                    sections.append(s)
        i = eo
    return sections


def parse_xref_table(bdata: bytes, start_pos: int, general_offset: int) -> list:
    """Return a list of dicts indexing indirect objects.

    - abs_pos is the absolute position of the object
    - o_num is the object number
    - o_gen is the object generation number
    """
    xref = []
    table = []
    _, _, _, xref_table = parse_xref_table_raw(bdata, start_pos)
    lines = xref_table['table']
    trailer_pos = bdata.find(b'trailer', start_pos)
    for line in lines:
        if len(line) == 2:
            table.append((f"{line[0]} {line[1]}".encode('ascii'), None))
        elif len(line) == 4:
            offset, o_num, o_gen, keyword = line
            if keyword != b'f' and o_num != 0:
                xref.append({'abs_pos': offset, 'o_num': o_num, 'o_gen': o_gen})
            table.append((f"{offset:010d} {o_gen:05d} {keyword.decode('ascii')} ".encode('ascii'), o_num))
            o_num += 1
    trailer = {
        'o_num': 0,
        'o_gen': 0,
        'abs_pos': general_offset + trailer_pos,
        'xref_table_pos':general_offset + start_pos,
        #'xref_table':table,   #Simplify
    }
    xref.insert(0, trailer)
    return xref


def parse_xref_stream(xref_stream: dict, trailer_pos: int, o_num: int) -> list:
    """Return a list of dicts indexing indirect objects.

    for regular objects:
    - abs_pos is the absolute position of the object
    - o_num is the object number
    - o_gen is the object generation number
    for objects embedded in object streams:
    - env_num is the number of the envelope object
    - o_num is the object number
    - o_gen is the object generation number
    - o_pos is the position of the object within the stream
    """
    xref_stream_num = o_num
    xref = []
    table = []
    _, _, _, xref_table = parse_xref_stream_raw(xref_stream)
    lines = xref_table['table']
    #envs = xref_table['envs']
    for line in lines:
        offset, env_iref, o_num, o_gen, keyword, raw_line, _ = line
        if o_num == 0:
            table.append((raw_line, o_num))
            continue
        if keyword == b'f':
            continue
        if env_iref:
            #float_pos = envs[env_iref] + (offset + 1) / 10000
            float_pos = (env_iref, offset)
            xref.append({'o_pos': offset, 'env_num':env_iref, 'o_num': o_num, 'o_gen': o_gen, 'abs_pos': float_pos})
        else:
            xref.append({'abs_pos': offset, 'o_num': o_num, 'o_gen': o_gen})
        table.append((raw_line, o_num))
        o_num += 1
    trailer = {
        'o_num': 0,
        'o_gen': 0,
        'abs_pos': trailer_pos,
        'xref_stream_pos': trailer_pos,
        'xref_stream_num': xref_stream_num,
        #'xref_stream': table,              #Simplify
    }
    xref.insert(0, trailer)
    return xref


def build_xref_sequence(fdata: Callable) -> tuple:
    """Build a list of all xref sequentially found in file.

    Return:
    - the list of xref
    - a dict that gives the following abs_pos
    - the max obj number
    """
    EOF = b'%%EOF'
    STARTXREF = b'startxref'
    XREF = b'xref'
    start = True
    prev = False
    xrefstm = False
    prev_eof = None
    chrono = []
    seq = []
    while start or prev or xrefstm:
        a0 = 0
        o0 = 0
        if start:
            start = False
            bdata, a0, o0, _ = fdata(-100, -1)
            eof_pos = o0 + bdata.rfind(EOF, a0)
            startxref_pos = o0 + bdata.rfind(STARTXREF, a0)
            i, j, _ = next_token(bdata, startxref_pos + len(STARTXREF) - o0)
            xref_pos = int(bdata[i:j])
            last = startxref_pos
        elif xrefstm:
            xref_pos = xrefstm
            startxref_pos = o0 + bdata.find(STARTXREF, xref_pos)
            eof_pos = o0 + bdata.find(EOF, xref_pos)
            last = eof_pos
            xrefstm = False
        elif prev:
            xref_pos = prev
            startxref_pos = o0 + bdata.find(STARTXREF, xref_pos)
            eof_pos = o0 + bdata.find(EOF, xref_pos)
            last = eof_pos
            prev = False
        bdata, a0, o0, _ = fdata(xref_pos, last - xref_pos)
        if bdata[a0:a0+4] == XREF:
            xref_index = parse_xref_table(bdata, a0, o0)
            i, j, _ = next_token(bdata, xref_index[0]['abs_pos'] - o0) #b'trailer'
            i, j, _ = next_token(bdata, j)                            #dict
            trailer = parse_obj(bdata[i:j])
        else: # must be a /XRef stream
            bdata, a0, o0, _ = fdata(xref_pos, startxref_pos - xref_pos)
            i, j, _ = next_token(bdata, a0 - o0) #o_num
            o_num = parse_obj(bdata, i)
            i, j, _ = next_token(bdata, j)       #o_ver
            i, j, _ = next_token(bdata, j)       #b'obj'
            i, j, _ = next_token(bdata, j)       #dict
            xref = parse_obj(bdata, i)
            xref_index = parse_xref_stream(xref, xref_pos, o_num)
            trailer = xref['entries']
        xref_index[0]['startxref_pos'] = startxref_pos
        xref_index.append({'o_num': -1, 'o_gen': -1, 'abs_pos': eof_pos})
        chrono.append(xref_index)
        seq += [(i.get('abs_pos'), i.get('o_num')) for i in xref_index if 'abs_pos' in i and 'env_num' not in i]
        if xrefstm == False and prev == False:
            if '/XRefStm' in trailer:
                xref_index[0]['xref_stm'] = True
                xrefstm = int(trailer['/XRefStm'])
            if '/Prev' in trailer:
                prev = int(trailer['/Prev'])
    idx = sorted([i[0] for i in seq])
    _, _, _, file_sz = fdata(None, -1)
    idx.append(file_sz)
    #idx.append(None)
    nxt = {idx[i]: idx[i+1] for i in range(len(idx)-1) if idx[i] < idx[i+1]}
    #nxt = {idx[i]: idx[i+1] for i in range(len(idx)-1)}
    nb = max(seq, key = lambda i: i[1])[1]
    return chrono, nxt, nb


def build_index_from_xref_sequence(xref_seq: list, nxt: dict, nb: int) -> list:
    """Build a multi-dimensional array where each column represents a doc update."""
    nb = nb + 2
    m = nb * [None]
    abs_pos_array = nb * [0]
    index = []
    doc_ver = -1
    prev_pos = 0
    xref_seq = xref_seq[:]
    xref_seq.reverse()
    for x in xref_seq:
        trailer = x[0]
        if trailer['abs_pos'] > prev_pos or trailer.get('xref_stm'):
            m = m[:]
            index.append(m)
            doc_ver += 1
            m[0] = trailer
            prev_pos = trailer['abs_pos']
        else:
            m[0] = [m[0], trailer]
        trailer['o_ver'] = doc_ver
        trailer['doc_ver'] = doc_ver
        for obj in x[1:]:
            if m[obj['o_num']] is None:
                obj['o_ver'] = 0
                obj['doc_ver'] = doc_ver
            else:
                old_obj = index[-1][obj['o_num']]
                if 'abs_pos' in old_obj and 'abs_pos' in obj and old_obj['abs_pos'] == obj['abs_pos']:
                    #Special case for hybrid docs where an obj appears both in xref table and stream
                    obj = old_obj
                else:
                    obj['o_ver'] = old_obj['o_ver'] + 1
                    obj['doc_ver'] = doc_ver
            m[obj['o_num']] = obj
    for current in index:
        for x in current:
            if x is None:
                continue
            elif type(x) == dict:
                x = [x]
            for y in x:
                if y.get('abs_next'):
                    continue
                abs_pos = y.get('abs_pos')
                env_num = y.get('env_num')
                if type(abs_pos) == tuple:
                    e, offset = abs_pos
                    loc = current[e]['abs_pos']
                    y['abs_pos'] = loc + (offset + 1) / 10000
                    abs_pos = loc
                y['abs_next'] = nxt[abs_pos]
    return index


def eof_cut(eof_index: int, fdata: Callable) -> int:
    """Calculate where to cut the byte stream of a revision: after %%EOF and possibly EOLs"""
    bdata, start, _, n = fdata(eof_index, bdata_length(fdata) - eof_index)
    i = start + len('%%EOF')
    while i < start + n:
        if bdata[i] not in EOL:
            break
        i += 1
    return i


def circular_deleted(changes: list) -> dict:
    """Build lookup dict to ref of next deleted object."""
    res = {}
    deleted = [x for x in changes if x[1] == 'd']
    for i, d in enumerate([(0j, 'd')] + deleted):
        e = int(d[0].imag)
        if i == len(deleted):
            res[e] = 0
        else:
            t = deleted[i][0]
            res[e] = int(t.imag)
    return res


def format_xref_table(elems: list, trailer: dict, next_free: dict) -> bytes:
    """Build XREF table."""
    xref_table = []
    for use, num, o_gen, counter, _ in elems:
        if use == 'f':
            ref = f'{next_free[num]:010} {(o_gen+1):05} f'.encode('ascii')
            xref_table.append((ref, num))
        else:
            ref = f'{counter:010} {o_gen:05} n'.encode('ascii')
            xref_table.append((ref, num))
    # add_xref_table_subsections
    i = len(xref_table) - 1
    num = xref_table[i][1]
    nb = 1
    while i >= 1:
        i -= 1
        if xref_table[i][1] + 1 == num: #contiguous
            nb += 1
        else:
            header = str(num).encode('ascii') + b' ' + str(nb).encode('ascii')
            xref_table.insert(i+1, (header, None))
            nb = 1
        num = xref_table[i][1]
    header = str(num).encode('ascii') + b' ' + str(nb).encode('ascii')
    xref_table.insert(0, (header, None))
    build_xref_table = b'xref\n'
    for x, _ in xref_table:
        build_xref_table += x
        build_xref_table += b'\n'
    ser0 = serialize(trailer)
    build_xref_table += b'trailer\n'
    build_xref_table += ser0 
    build_xref_table += b'\n'
    return build_xref_table


def format_xref_stream(elems: list, trailer: dict, next_free: dict, o_num: int) -> bytes:
    """Build XREF stream object."""
    xref_stream = []
    index = []
    trailer['/Type'] = '/XRef'
    trailer['/Length'] = -1
    max_counter = max([e[3] for e in elems if e[3] is not None])
    b = (int(math.log2(max_counter+1)) // 8) + 1
    trailer['/W'] = [1, b, b]
    for use, num, o_gen, counter, env_num in elems:
        if use == 'f':
            ref = b'\x00' + (next_free[num]).to_bytes(b, "big") + (o_gen+1).to_bytes(b, "big")
            xref_stream.append((ref, num))
        else:
            if env_num:
                ref = b'\x02' + (env_num).to_bytes(b, "big") + (counter).to_bytes(b, "big")
                xref_stream.append((ref, num))
            else:
                ref = b'\x01' + (counter).to_bytes(b, "big") + (o_gen).to_bytes(b, "big")
                xref_stream.append((ref, num))
    # Index 
    i = len(xref_stream) - 1
    num = xref_stream[i][1]
    nb = 1
    while i >= 1:
        i -= 1
        if xref_stream[i][1] + 1 == num: #contiguous
            nb += 1
        else:
            index = [num, nb] + index
            nb = 1
        num = xref_stream[i][1]
    index = [num, nb] + index
    trailer['/Index'] = index
    st = b''
    for x, _ in xref_stream:
        st += x
    s, _ = forge_stream(trailer, st)
    ser0 = serialize(s)
    build_xref_stream = b''
    build_xref_stream += f'{o_num}'.encode('ascii')
    build_xref_stream += b' 0 obj\n'
    build_xref_stream += ser0 
    build_xref_stream += b'\n'
    build_xref_stream += b'endobj\n'
    return build_xref_stream


def serialize_fragment(num, o_gen, obj):
    """Build ascii block representing indirect object in file."""
    beginobj = f'{num} {o_gen}'.encode('ascii') + b' obj\n'
    ser = serialize(obj) + b'\n'
    endobj = b'endobj\n'
    block = beginobj + ser + endobj
    return block


def append_to_stream_fragment(num, obj, envelope):
    """Concatenate object at the end of stream."""
    ser = serialize(obj) + b'\n'
    entries = envelope['entries'].copy()
    if '/FirstLine' not in entries:
        entries['/FirstLine'] = []
    entries['/FirstLine'].append(num)
    entries['/FirstLine'].append(len(envelope['stream']))
    new_ser = envelope['stream'] + ser
    #Do not encode/forge this temporary Stream yet
    envelope = Stream(entries, new_ser, None)
    return envelope


def get_pos_in_stream(envelope):
    """Calculate current object position in the stream."""
    entries = envelope['entries']
    pos = (len(entries['/FirstLine']) // 2) - 1
    return pos


def finalize_stream(envelope):
    """Add index at the beginning of stream and count objects."""
    header = b''
    entries = envelope['entries'].copy()
    if '/First' not in entries and '/N' not in entries:
        tokens = entries['/FirstLine']
        for i in tokens:
            header += f'{i} '.encode('ascii')
        header += b'\n'
        entries['/First'] = len(header)
        entries['/N'] = len(tokens) // 2
        del entries['/FirstLine']
    entries['/Length'] = -1
    new_ser = header + envelope['stream']
    envelope, _ = forge_stream(entries, new_ser)
    return envelope


def build_revision_byte_stream(
        changes: list, current_index: list, cache: list,
        starting_pos: int, xref_stream_num: int) -> tuple:
    """List the sequence of byte blocks that make the update."""
    fragments = []
    xref_table = []
    res = b''
    new_index = deepcopy(current_index)
    counter = starting_pos + len(MARGIN)
    fragments.append(MARGIN)
    next_free = circular_deleted(changes)
    l = [(0j, 'd')] + changes
    for c, action in l:
        num = int(c.imag)
        o_gen = current_index[num]['o_gen']
        env_num = current_index[num].get('env_num')
        if action != 'd' and env_num:
            new_env = append_to_stream_fragment(num, cache[num], cache[env_num])
            cache[env_num] = new_env
            xref_table.append(('n', num, o_gen, get_pos_in_stream(new_env), env_num))
    for c, action in l:
        num = int(c.imag)
        if action == 'd':
            if num == 0:
                o_gen = 65535 - 1
            else:
                o_gen = current_index[num]['o_gen']
            xref_table.append(('f', num, o_gen, None, None))
        else:
            o_gen = current_index[num]['o_gen']
            env_num = current_index[num].get('env_num')
            if not env_num:
                obj = cache[num]
                if type(obj) == Stream and obj['entries'].get('/Type') == '/ObjStm':
                    obj = finalize_stream(obj)
                block = serialize_fragment(num, o_gen, obj)
                fragments.append(block)
                xref_table.append(('n', num, o_gen, counter, env_num))
                new_index[num]['abs_pos'] = counter
                new_index[num]['abs_next'] = counter + len(block)
                counter += len(block)
    xref_table.sort(key=lambda xr: xr[1])
    if not xref_stream_num:
        #cache[0]['/Size'] = len(current_index)
        built_xref = format_xref_table(xref_table, cache[0], next_free)
        new_index[0]['xref_table_pos'] = counter
        new_index[0]['abs_pos'] = counter + built_xref.rfind(b'trailer')
        new_index[0]['abs_next'] = counter + len(built_xref)
    else:
        xref_table.append(('n', xref_stream_num, 0, counter, None))
        built_xref = format_xref_stream(xref_table, cache[0], next_free, xref_stream_num)
        new_index[xref_stream_num]['abs_pos'] = counter
        new_index[xref_stream_num]['abs_next'] = counter + len(block)
        new_index[0]['xref_stream_pos'] = counter
        new_index[0]['abs_pos'] = counter
        new_index[0]['abs_next'] = counter + len(built_xref)
    fragments.append(built_xref)
    fragments.append(f'startxref\n{counter}\n'.encode('ascii'))
    fragments.append(b'%%EOF\n')
    for i in fragments:
        res += i
    return res, new_index


def linearized(fdata: Callable) -> dict:
    """ """
    HEADER = b'%PDF-X.Y'
    bdata, a0, o0, _ = fdata(len(HEADER), 1024 - len(HEADER))
    i, j, _ = next_token(bdata, a0) #comment
    i, j, _ = next_token(bdata, j)  #o_num
    i, j, _ = next_token(bdata, j)  #gen_num
    i, j, _ = next_token(bdata, j)  #obj keyword
    i, j, t = next_token(bdata, j)  #dict ?
    if t == 'DICT':
        o = bdata[i:j]
        first_obj = parse_obj(o)
        if type(first_obj) == dict and '/Linearized' in first_obj:
            return first_obj
    return None


def check_index_targets(object_map: list, xref_seq: list):
    """List, for every xref structure, the entries that do not lead to anything."""
    ret = {}
    ind_objs = [x for x in object_map if x[2] == 'IND_OBJ']
    dir_objs = {('DIR', x[3]['o_num'], x[3]['o_gen'], x[0]) for x in ind_objs if type(x[0]) == int}
    emb_objs = {('EMB', x[3]['o_num'], x[3]['env_num'], x[1][2]) for x in ind_objs if type(x[0]) == float}
    objs = dir_objs | emb_objs
    for xref in xref_seq:
        errors = []
        for o in xref:
            if o['o_num'] == 0:
                pos = o.get('xref_table_pos')
                if pos is None:
                    pos = o.get('xref_stream_pos')
                continue
            elif o['o_num'] < 0:
                continue
            if 'env_num' in o:
                k = ('EMB', o['o_num'], o['env_num'], o['o_pos'])
            else:
                k = ('DIR', o['o_num'], o['o_gen'], o['abs_pos'])
            if k in objs:
                continue
            errors.append(k)
        ret[pos] = errors
    return ret


def check_not_indexed_objects(object_map: list, xref_seq: list):
    """List objects that are not indexed by any xref structure."""
    ret = []
    indexed = set()
    for xref in xref_seq:
        errors = []
        for o in xref:
            if o['o_num'] <= 0:
                continue
            if 'env_num' in o:
                k = ('EMB', o['o_num'], o['env_num'], o['o_pos'])
            else:
                k = ('DIR', o['o_num'], o['o_gen'], o['abs_pos'])
            indexed.add(k)
    ind_objs = [x for x in object_map if x[2] == 'IND_OBJ']
    for x in ind_objs:
        if type(x[0]) == int:
            o = ('DIR', x[3]['o_num'], x[3]['o_gen'], x[0])
        elif type(x[0]) == float:
            o = ('EMB', x[3]['o_num'], x[3]['env_num'], x[1][2])
        else:
            continue
        if o not in indexed:
            ret.append(o)
    return ret

