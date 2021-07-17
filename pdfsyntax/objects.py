"""Module pdfsyntax.objects: Parser"""

import re
import zlib
from collections import namedtuple

EOL = b'\r\n'
SPACE = EOL + b'\x00\x09\x0c\x20'

def skip_chars(chars, text, i):
    """ syntax
    """
    while i < len(text):
        if text[i] not in chars: return i
        i += 1
    return None        


def next_token(text, i):
    """ syntax Find next token in raw string starting at some index
    """
    search = "TBD"
    nested = 1
    h = i
    while i < len(text):
        single = text[i:i+1]
        double = text[i:i+2]
        if search == "TBD":
            if double == b'<<':
                search = "DICT"
            elif single == b'[':
                search = "ARRAY"
            elif single == b"/":
                search = "NAME"
            elif text[i:i+6] == b"stream":
                search = "STREAM"
                offset = 7 if text[i+6:i+7] == b'\n' else 8 # else is b'\r\n'
                i += offset
            elif single in b"+-.0123456789":
                search = "VALUE"
            elif single in b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
                search = "KEYWORD"
            elif single in b"(<":
                search = "TEXT"
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
            if single in b' \n\r[]/<>(':
                return (h, i, 'NAME')
        elif search == "TEXT":
            if double == b'\\(' or double == b'\\)' or double == b'\\<' or double == b'\\>':
                i += 1
            else:    
                if single in b')>':
                    return (h, i + 1, 'TEXT')
        elif search == "KEYWORD":
            if single in b' \n\r>/]' or i == len(text) - 1:
                return (h, i, 'KEYWORD')
        elif search == "VALUE":
            if single in b' \n\r>/]' or i == len(text) - 1:
                return (h, i, 'VALUE')
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
    return (h, i + 1, '')


def replace_ref(tokens):
    """ syntax
    """
    size = len(tokens)
    new_list = []
    i = 0
    while i < size:
        if i < size - 2 and tokens[i + 2]  == b'R':
            new_list.append({'_REF': tokens[i]})
            i += 3
        else:
            new_list.append(tokens[i])
            i += 1
    return new_list

def decode_predictor(bdata, predictor, columns):
    size = len(bdata)
    res = b''
    columns += 1
    prev_row = [0] * columns
    i = 0
    while i < size:
        row = list(bdata[i:i+columns])
        decoded_row = [(val + prev_row[index]) & 0xff for (index, val) in enumerate(row)]
        prev_row = decoded_row
        res += bytes(decoded_row[1:])
        i += columns
    return res


def decode_stream(stream, stream_def):
    res = stream
    if b'/Filter' in stream_def and stream_def[b'/Filter'] == b'/FlateDecode':
        res = zlib.decompress(stream) #+ b'\r')
    if b'/DecodeParms' in stream_def and b'/Predictor' in stream_def[b'/DecodeParms']:
        predictor = int(stream_def[b'/DecodeParms'][b'/Predictor'])
        columns = int(stream_def[b'/DecodeParms'][b'/Columns'])
        res = decode_predictor(res, predictor, columns)
    return res


def parse_obj(text, start=0):
    """ syntax
    """
    ref_list = []
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
            res = { 'stream_def': stream_def, 'stream_content': stream_content }
            return res

        i = start + 2
        while i < j1:
            h, i, ttt = next_token(text, i)
            if i < j1 and ttt:                             # TODO ?
                if ttt == 'DICT' or ttt == 'ARRAY':
                    obj = parse_obj(text[h:i])
                else:
                    obj = text[h:i]
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
        while i < j1:
            h, i, ttt = next_token(text, i)
            if ttt:
                obj = text[h:i]
                res.append(obj)
        res = replace_ref(res)
        return res
    else:
        return None


def beginning_next_non_empty_line(bdata, i):
    """ doc
    """
    while bdata[i] not in EOL:
        i += 1
    while bdata[i] in EOL:
        i += 1
    return i



