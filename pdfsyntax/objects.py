"""Module pdfsyntax.objects: Parser"""

from typing import Any
from collections import namedtuple
from dataclasses import dataclass
from .filters import *
#from .filestruct import expand_xref_index

EOL = b'\r\n'
SPACE = EOL + b'\x00\x09\x0c\x20'
DELIMITERS = b'<>[]/(){}%'


@dataclass
class Stream:
    entries: dict
    stream: bytes
    encoded: bytes

    def __getitem__(self, item):
        return getattr(self, item)

    def __repr__(self):
        res = "<PDF Stream," + f" entries: {self.entries},"
        if len(self.stream) > 40:
            res += f" decoded stream: {self.stream[:10]+b' (...truncated...)'}>\n"
        else:
            res += f" decoded stream: {self.stream}>\n"
        return res


def update_internal_stream_length(stream: Stream):
    """Calculate and apply /Length."""
    entries = stream['entries']
    encoded = stream['encoded']
    length = len(encoded) + 1
    if '/Length' in entries and type(entries['/Length']) == int:
        entries['/Length'] = length
    return length


def forge_stream(entries: dict, content: bytes) -> tuple:
    """Encode stream and calculate its length."""
    encoded = encode_stream(content, entries)
    envelope = Stream(entries, content, encoded)
    length = update_internal_stream_length(envelope)
    return envelope, length


def next_line(bdata: bytes, start_pos: int=0) -> tuple:
    """Advance to the next non EOL char and detect following EOL."""
    cursor = start_pos
    i = cursor
    start_found = False
    while cursor < len(bdata):
        if not start_found and bdata[cursor] not in EOL:
            start_found = True
            i = cursor
        if start_found and bdata[cursor] in EOL:
            j = cursor
            return i, j
        cursor += 1
    return None, None


def next_token(text: bytes, i=0) -> tuple:
    """Find next token in raw string starting at some index."""
    search = "TBD"
    nested = 1
    text_in_array = 0
    h = i
    while i < len(text):
        single = text[i:i+1]
        double = text[i:i+2]
        if search == "TBD":
            if single == b']':
                return (h, i, None)
            elif double == b'>>':
                return (h, i+1, None)
            elif double == b'<<':
                search = "DICT"
            elif single == b'[':
                search = "ARRAY"
            elif single == b"/":
                search = "NAME"
            elif text[i:i+6] == b"stream":
                search = "STREAM"
                #if text[i+6:i+8] == b'\r\n':
                #    offset = 8
                #else:
                #    offset = 7
                offset = 0
                i += offset
            elif single in b"+-.0123456789":
                search = "VALUE"
            elif single in b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
                search = "KEYWORD"
            elif single in b"(":
                search = "LSTRING"
            elif single in b"<":
                search = "HSTRING"
            elif single == b'%':
                search = "COMMENT"
            h = i
        elif search == "DICT":
            if double == b'<<':
                nested += 1
                i += 1
            elif double == b'>>':
                nested -= 1
                i += 1
            if nested == 0:
                return (h, i + 1, 'DICT')
            else:
                pass
        elif search == "NAME":
            if single in (SPACE + DELIMITERS):
                return (h, i, 'NAME')
        elif search == "COMMENT":
            if single in EOL:
                return (h, i, 'COMMENT')
        elif search == "LSTRING":
            if double == b'\\(' or double == b'\\)':
                i += 1
            elif single == b'(':
                nested += 1
            elif single == b')':
                nested -= 1
            if nested == 0:
                return (h, i + 1, 'STRING')
        elif search == "HSTRING":
            if double == b'\\<' or double == b'\\>':
                i += 1
            else:
                if single in b'>':
                    return (h, i + 1, 'STRING')
        elif search == "KEYWORD":
            if single in (SPACE + DELIMITERS): #or i == len(text) - 1:
                if b'true' == text[h:i]:
                    return (h, i, 'TRUE')
                elif b'false' == text[h:i]:
                    return (h, i, 'FALSE')
                else:
                    return (h, i, 'KEYWORD')
        elif search == "VALUE":
            if single in (SPACE + DELIMITERS): #or i == len(text) - 1:
                if b'.' in text[h:i]:
                    return (h, i, 'REAL')
                else:
                    return (h, i, 'INTEGER')
        elif search == "STREAM":
            if text[i:i+11] == b'\r\nendstream':
                return (h, i+11, 'STREAM')
            elif  text[i:i+10] == b'\nendstream':
                return (h, i+10, 'STREAM')
            elif  text[i:i+10] == b'\rendstream':
                return (h, i+10, 'STREAM')
            elif  text[i:i+9] == b'endstream':
                return (h, i+9, 'STREAM')
        elif search == "ARRAY":
            if single == b'(':
                text_in_array = 1
            elif single == b')':
                text_in_array = 0
            elif text_in_array == 0 and single == b'[':
                nested += 1
            elif text_in_array == 0 and single == b']':
                nested -= 1
            if nested == 0:
                return (h, i + 1, 'ARRAY')
        i += 1
    return (h, i, None)


def replace_ref(tokens: list) -> list:
    """Replace a sublist of X, Y, 'R' into a unique R namedtuple."""
    size = len(tokens)
    new_list = []
    i = 0
    while i < size:
        if i < size - 2 and tokens[i + 2]  == 'R':
            new_list.append(complex(0, tokens[i]))
            i += 3
        else:
            new_list.append(tokens[i])
            i += 1
    return new_list


def dedicated_type(text: bytes, type: str) -> Any:
    """Transform a PDF basic type into a Python basic type."""
    if type == 'INTEGER':
        return int(text)
    elif type == 'REAL':
        return float(text)
    elif type == 'TRUE':
        return True
    elif type == 'FALSE':
        return False
    elif type == 'KEYWORD' or type == 'NAME':
        return text.decode('ascii')
    else:
        return text


def parse_obj(text: bytes, start=0) -> Any:
    """Recursively parse bytes into PDF objects."""
    h1, j1, t1 = next_token(text, start)
    obj = text[h1:j1]
    if t1 == 'DICT':
        res = {}
        res_array = []
        h2, j2, t2 = next_token(text, j1)
        following_obj = text[h2:j2]
        if t2 == 'STREAM': 
            stream_def =  parse_obj(obj)
            stream_encoded =  parse_obj(following_obj)
            stream_content = decode_stream(stream_encoded, stream_def)
            res = Stream(stream_def, stream_content, stream_encoded)
            return res

        i = start + 2
        while i < j1 - 1:
            h, i, t = next_token(text, i)
            if t and t != 'COMMENT':
                if i < j1 and t:
                    if t == 'DICT' or t == 'ARRAY':
                        obj = parse_obj(text[h:i])
                    else:
                        obj = dedicated_type(text[h:i], t)
                    res_array.append(obj)
        toggle = True
        res_array = replace_ref(res_array)
        j = len(res_array) - 1
        while j >= 0:
            if toggle:
                val = res_array[j]
                toggle = False
            else:
                key = res_array[j]
                res[key] = val
                toggle = True
            j -= 1
        return res
    elif t1 == 'ARRAY':
        res = []
        i = start + 1
        while i < j1 - 1:
            h, i, t = next_token(text, i)
            if t and t != 'COMMENT':
                if t == 'DICT' or t == 'ARRAY':
                    obj = parse_obj(text[h:i])
                else:
                    obj = dedicated_type(text[h:i], t)
                res.append(obj)
        res = replace_ref(res)
        return res
    elif t1 == 'STREAM':
        b1 = b'stream' + b'\r\n'
        b2 = b'stream' + b'\n'
        e1 = b'\r\n' + b'endstream'
        e2 = b'\n' + b'endstream'
        e3 = b'\r' + b'endstream'
        e4 = b'endstream'
        if obj[:len(b1)] == b1:
            b = len(b1)
        elif obj[:len(b2)] == b2:
            b = len(b2)
        else:
            return None
        if obj[-len(e1):] == e1:
            e = len(e1)
        elif obj[-len(e2):] == e2:
            e = len(e2)
        elif obj[-len(e3):] == e3:
            e = len(e3)
        elif obj[-len(e4):] == e4:
            e = len(e4)
        else:
            return None
        s = obj[b:-e]
        return s
    elif t1 == 'COMMENT':
        return ''
    else:
        return dedicated_type(text[h1:j1], t1)


def parse_indirect_obj(text: bytes, start=0) -> tuple:
    """Recursively parse indirect object starting at X Y R."""
    bl, el = next_line(text, start)
    bo = bl
    i1, j1, _ = next_token(text, start) #o_num
    i2, j2, _ = next_token(text, j1) #o_gen
    o_num = int(text[i1:j1])
    o_gen = int(text[i2:j2])
    i, j, _ = next_token(text, j2) #obj
    i, j, _ = next_token(text, j) #object1
    o = parse_obj(text, i)
    i, j, t = next_token(text, j)
    if t == 'STREAM':
        _, j, _ = next_token(text, j) #endobj
    return (bo, j, 'IND_OBJ', {'o_num':o_num, 'o_gen':o_gen, 'obj':o})


def parse_object_stream(obj_stream: Stream, env_num) -> tuple:
    """List objects embedded within an object stream (/ObjStm)."""
    res = []
    data = obj_stream['stream']
    offset = int(obj_stream['entries']['/First'])
    theorical_nb_obj = int(obj_stream['entries']['/N'])
    i = 0
    tokens = []
    while i < len(data):
        bo, eo, typ = next_token(data, i)
        tokens.append(bo)
        i = eo
    actual_nb_obj = len(tokens) // 3
    actual_offset = tokens[2 * actual_nb_obj]
    y_array = parse_obj(b'[' + data[:offset] + b']')
    y_pos = [y+offset for j, y in enumerate(y_array) if j % 2]
    for x in range(actual_nb_obj):
        actual_pos = tokens[2 * actual_nb_obj + x]
        o_num = parse_obj(data, tokens[2 * x])
        obj = parse_obj(data, actual_pos)
        theorical_pos = actual_pos if actual_pos in y_pos else None
        res.append((o_num, obj, env_num, theorical_pos, actual_pos))
    return (None, None, 'OBJSTREAM', res)


def parse_xref_table_raw(bdata: bytes, start_pos: int=0) -> tuple:
    """."""
    res = []
    XREF = b'xref'
    if bdata[start_pos:start_pos+len(XREF)] != XREF:
        return None
    bl, el = next_line(bdata, start_pos+len(XREF))
    bo = bl
    while b'0' <= bdata[bl:bl+1] <= b'9':
        items = bdata[bl:el].strip(b' ').split()
        if len(items) == 2: #subsection
            o_num, nb = int(items[0]), int(items[1])
            res.append((o_num, nb))
        if len(items) == 3:
            offset = int(items[0])
            o_ver = int(items[1])
            keyword = items[2]
            res.append((offset, o_num, o_ver, keyword))
            o_num += 1
        bl, el = next_line(bdata, el)
    bl, bf, _l = next_token(bdata, el)
    trailer = parse_obj(bdata, bl)
    return (start_pos, bf, 'XREFTABLE', {'table':res, 'trailer':trailer})


def expand_xref_index(xref_index: list) -> list:
    """Transform index section pairs into a flat list of (object_number, subsection) tuples."""
    res = []
    subsection = 0
    i = 0
    while i < len(xref_index):
        o_num = xref_index[i]
        i += 1
        res.append((o_num, subsection))
        for j in range(xref_index[i]-1):
            res.append((o_num+j+1, subsection))
        i += 1
        subsection += 1
    return res


def parse_xref_stream_raw(xref_stream: Stream, start_pos=None) -> tuple:
    """."""
    res = []
    cols = xref_stream['entries']['/W']
    i = 0
    if '/Index' in xref_stream['entries']:
        obj_range = xref_stream['entries']['/Index']
    else:
        obj_range = [0, xref_stream['entries']['/Size']]
    obj_nums = expand_xref_index(obj_range)
    while i < len(xref_stream['stream']):
        params = []
        ppr = b''
        obj_num, subsection = obj_nums.pop(0)
        for col in cols:
            x = xref_stream['stream'][i:i+int(col)]
            #struct.unpack cannot work with 3-byte words
            params.append(int.from_bytes(x, byteorder='big'))
            i += int(col)
            ppr += asciihex(x) + b' '
        if params[0] == 0:
            offset = params[1]
            o_gen = params[2]
            res.append((offset, None, obj_num, o_gen, b'f', ppr, subsection))
        elif params[0] == 1:
            offset = params[1]
            o_gen = params[2]
            res.append((offset, None, obj_num, o_gen, b'n', ppr, subsection))
        elif params[0] == 2:
            env_num = params[1]
            o_pos = params[2]
            res.append((o_pos, env_num, obj_num, 0, b'n', ppr, subsection))
    return (start_pos, None, 'XREFSTREAM', {'table': res, 'trailer': xref_stream['entries']})


def parse_region(text: bytes, start=0) -> tuple:
    """Recursively parse bytes into macro PDF objects (indirect/xref/xref table/startxref)."""
    PERCENT = b'%'
    STARTXREF = b'startxref'
    OBJ = b'obj'
    XREF = b'xref'
    #bl, el = next_line(text, start)
    bl, el, typ = next_token(text, start)
    if bl is None:
        return None
    if bl != start:
        return (start, bl, 'VOID', text[start:bl])
    elif typ is None:
        return (start, el, 'VOID', text[start:el])
    elif text[bl:bl+len(PERCENT)] == PERCENT:
        return (bl, el, 'COMMENT', text[bl:el])
    elif text[bl:bl+len(STARTXREF)] == STARTXREF:
        i1, j1, _ = next_token(text, bl)
        i2, j2, _ = next_token(text, j1)
        return (bl, j2, 'STARTXREF', text[i2:j2])
    elif typ == 'INTEGER':
        i1, j1, _ = next_token(text, bl)
        i2, j2, _ = next_token(text, j1)
        i3, j3, t = next_token(text, j2)
        if t == 'KEYWORD' and text[i3:j3] == OBJ:
            ind_o = parse_indirect_obj(text, bl)
            return ind_o
        else:
            return None
    elif text[el-len(XREF):el] == XREF:
        return parse_xref_table_raw(text, bl)
    return None


def to_str(obj) -> bytes:
    """Transform a Python basic type into bytes."""
    if type(obj) == bool:
        if obj == True:
            return b'true'
        else:
            return b'false'    
    elif type(obj) == int:
        return str(obj).encode('ascii')
    elif type(obj) == float:
        return str(obj).encode('ascii')
    elif type(obj) == str:
        return obj.encode('ascii')
    elif type(obj) == complex:
        s = f'{int(obj.imag)} {int(obj.real)} R'
        return s.encode('ascii')
    elif type(obj) == bytes:
        return obj
    else:
        return obj.encode('ascii')


def serialize(obj, depth=0) -> bytes:
    """Recursively construct object bytes."""
    ret = b''
    content = None
    if type(obj) == dict or type(obj) == Stream:
        if type(obj) == Stream:
            content = obj['encoded']
            obj = obj['entries']
        ret += b'<< '
        keys = list(obj.keys())
        for i in keys:
            name = i
            value = serialize(obj[i], depth + 1)
            ret += b' '  * depth
            ret += to_str(name)
            ret += b' '
            ret += value
            ret += b' '
        ret += b' ' * depth
        ret += b'>>'
        if content:
            ret += b'\nstream\n'
            #ret += b'\n'
            ret += content
            ret += b'\nendstream'
    elif type(obj) == list:
        ret += b'[ '
        for i in obj:
            value = serialize(i)
            ret += value
            ret += b' '
        ret += b']'        
    else:
        ret += to_str(obj)
    return ret


def deep_ref_retarget(obj: Any, mapping: dict) -> Any:
    """Recursively replace an indirect reference in object tree.""" 
    if type(obj) == complex:
        if obj in mapping:
            return mapping[obj]
    elif type(obj) == dict:
        for k in obj:
            obj[k] = deep_ref_retarget(obj[k], mapping)
    elif type(obj) == list:
        for k in range(len(obj)):
            obj[k] = deep_ref_retarget(obj[k], mapping)
    return obj


def deep_ref_detect(obj: Any, l = None) -> set:
    """Recursively detect all references in object tree."""
    if l is None:
        l = set()
    if type(obj) == complex:
        return l.add(obj)
    elif type(obj) == Stream:
            deep_ref_detect(obj['entries'], l)
    elif type(obj) == dict:
        for k in obj:
            deep_ref_detect(obj[k], l)
    elif type(obj) == list:
        for k in range(len(obj)):
            deep_ref_detect(obj[k], l)
    return l
