"""Module pdfsyntax.objects: Parser"""

from typing import Any
from collections import namedtuple
from dataclasses import dataclass
from .filters import *


EOL = b'\r\n'
SPACE = EOL + b'\x00\x09\x0c\x20'
DELIMITERS = b'<>[]/(){}%'


@dataclass
class Stream:
    entries: dict
    stream: bytes
    def __getitem__(self, item):
        return getattr(self, item)


def next_token(text: bytes, i=0) -> tuple:
    """Find next token in raw string starting at some index"""
    search = "TBD"
    nested = 1
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
                offset = 7 if text[i+6:i+7] == b'\n' else 8
                i += offset
            elif single in b"+-.0123456789":
                search = "VALUE"
            elif single in b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
                search = "KEYWORD"
            elif single in b"(<":
                search = "STRING"
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
        elif search == "STRING":
            if double == b'\\(' or double == b'\\)' or double == b'\\<' or double == b'\\>':
                i += 1
            else:    
                if single in b')>':
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
            if text[i:i+11] == b'\r\nendstream' or text[i:i+10] == b'\nendstream':
                return (h, i, 'STREAM')
        elif search == "ARRAY":
            if single == b'[':
                nested += 1
            elif single == b']':
                nested -= 1
            if nested == 0:
                return (h, i + 1, 'ARRAY')
        i += 1
    return (h, i, None)


def replace_ref(tokens: list) -> list:
    """Replace a sublist of X, Y, 'R' into a unique R namedtuple"""
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
    """Transform a PDF basic type into a Python basic type"""
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
    """Recursively parse bytes into PDF objects"""
    h1, j1, t1 = next_token(text, start)
    obj = text[h1:j1]
    if t1 == 'DICT':
        res = {}
        res_array = []
        h2, j2, t2 = next_token(text, j1)
        following_obj = text[h2:j2]
        if t2 == 'STREAM': 
            stream_def =  parse_obj(obj)
            stream_content = decode_stream(following_obj, stream_def)
            res = Stream(stream_def, stream_content)
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
    
    elif t1 == 'COMMENT':
        return ''

    else:
        return dedicated_type(text[h1:j1], t1)


def to_str(obj) -> bytes:
    """Transform a Python basic type into bytes"""
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
    """Recursively construct object bytes"""
    ret = b''
    content = None
    if type(obj) == dict or type(obj) == Stream:
        if type(obj) == Stream:
            content = obj['stream']
            obj = obj['entries']
            encoded_content = encode_stream(content, obj)
            obj['/Length'] = len(encoded_content) + 1
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
            ret += encoded_content
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
