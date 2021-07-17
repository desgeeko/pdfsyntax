"""Module pdfsyntax.filestruct: how objects are stored in a PDF file"""

from .objects import *


def parse_xref_table(bdata, start_pos):
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
        if len(line_a) == 2:
            o_num = int(line_a[0])
            table.append((line, None))
        elif len(line_a) == 3:
            offset = int(line_a[0])
            o_ver = int(line_a[1])
            o_start = bdata.find(b'obj', offset) + len(b'obj') + 1
            if bdata[o_start] in b'\r\n ': o_start += 1
            if o_num != 0:
                xref.append({'abs_pos': offset, 'o_num': o_num, 'o_gen': o_ver})
            table.append((line, o_num))
            o_num += 1
    xref.insert(0, {'o_num': 0, 'o_gen': 0, 'abs_pos': trailer_pos, 'xref_table':table })
    return xref

def parse_xref_stream(xref_stream, trailer_pos):
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
    cols = xref_stream['stream_def'][b'/W']
    i = 0
    obj_range = (0, 0)
    if b'/Index' in xref_stream['stream_def']:
        obj_range = xref_stream['stream_def'][b'/Index']
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
            #table.append((line, None))
        elif params[0] == 2:
            xref.append({'env_num': params[1], 'o_num': obj_num, 'o_gen': 0, 'o_pos': params[2]})
            #table.append((line, obj_num))
        obj_num += 1
    xref.insert(0, {'o_num': 0, 'o_gen': 0, 'abs_pos': trailer_pos, 'xref_stream':table})
    return xref
    
def build_chrono_from_xref(bdata):
    """ Return a merged list of all entries found in xref tables or xref streams """
    STARTXREF = b'startxref'
    XREF = b'xref'
    startxref_pos = bdata.rfind(STARTXREF)
    i, j, _ = next_token(bdata, startxref_pos + len(STARTXREF))
    xref_pos = int(bdata[i:j])
    if bdata[xref_pos:xref_pos+4] == XREF:
        chrono = parse_xref_table(bdata, xref_pos)
        i, j, _ = next_token(bdata, chrono[0]['abs_pos'])  # b'trailer'
        i, j, _ = next_token(bdata, j)                     # actual trailer dict
        trailer = parse_obj(bdata[i:j])
    else: # must be a /XRef stream
        i = beginning_next_non_empty_line(bdata, xref_pos)
        xref = parse_obj(bdata, i)
        chrono = parse_xref_stream(xref, xref_pos)
        trailer = xref['stream_def']
    while b'/Prev' in trailer:
        new_xref_pos = trailer[b'/Prev']
        xref_pos = int(new_xref_pos)
        if bdata[xref_pos:xref_pos+4] == XREF:
            tmp_index = parse_xref_table(bdata, xref_pos)
            chrono = tmp_index + chrono
            i, j, _ = next_token(bdata, chrono[0]['abs_pos'])
            trailer = parse_obj(bdata[i:j])
        else: # must be a /XRef stream
            i = beginning_next_non_empty_line(bdata, xref_pos)
            xref = parse_obj(bdata, i)
            chrono = parse_xref_stream(xref, xref_pos) + chrono
            trailer = xref['stream_def']
    return chrono

def build_index_from_chrono(chrono):
    """ Build a multi-dimensional array where each column represents a doc update"""
    nb = max(chrono, key = lambda i: i['o_num']).get('o_num') + 1
    m = nb * [None]
    abs_pos_array = nb * [0]
    index = []
    doc_ver = -1
    prev_pos = 0
    for obj in chrono:
        if obj['o_num'] == 0 and obj['abs_pos'] > prev_pos:
           m = m[:]
           m[0] = None # NEW
           index.append(m)
           doc_ver += 1
           prev_pos = obj['abs_pos']
        if m[obj['o_num']] is None:
            obj['o_ver'] = 0
        else:
            obj['o_ver'] = index[-1][obj['o_num']]['o_ver'] + 1
        obj['doc_ver'] = doc_ver
        if obj['o_num'] == 0 and m[obj['o_num']] is not None: #NEW
            m[0] = [m[0] ,obj] #NEW
        else:
            m[obj['o_num']] = obj
    for rev in index:
        abs_list = [obj for obj in rev if 'abs_pos' in obj]
        env_list = [obj for obj in rev if 'env_num' in obj]
        for obj in abs_list:
            abs_pos_array[obj['o_num']] = obj['abs_pos']
        for obj in env_list:
            obj['a_'] = abs_pos_array[obj['env_num']] + obj['o_pos'] / 1000
    return index


