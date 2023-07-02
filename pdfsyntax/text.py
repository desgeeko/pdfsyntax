""" """

from .objects import *

def prepare_pdfdoc_charset():
    charset = []
    charset += list(range(0, 0x18))
    charset += [0x02d8, 0x02c7, 0x02c6, 0x02d9, 0x02dd, 0x02db, 0x02da, 0x02dc]
    charset += list(range(0x20, 0x80))
    charset += [0x2022, 0x2020, 0x2021, 0x2026, 0x2014, 0x2013, 0x0192, 0x2044]
    charset += [0x2039, 0x203a, 0x2212, 0x2030, 0x201e, 0x201c, 0x201d, 0x2018]
    charset += [0x2019, 0x201a, 0x2122, 0xfb01, 0xfb02, 0x0141, 0x0152, 0x0160]
    charset += [0x0178, 0x017d, 0x0131, 0x0142, 0x0153, 0x0161, 0x017e, 0x009f, 0x20ac]
    charset += list(range(0xa1, 256))
    return charset

PDFDOC_CHARSET = prepare_pdfdoc_charset()

def decode_pdfdoc(string: bytes) -> str:
    """Decode a PDFDocEncoded string"""
    chars = [chr(PDFDOC_CHARSET[x]) for x in string]
    return ''.join(chars)


def text_string(string: bytes) -> str:
    """Transform a fundamental string into a text string"""
    if string is None: return None
    res = ''
    if string[0:1] == b'(': # Literal string
        if string[1:3] == b'\xfe\xff': 
            res = string[3:-1].decode('utf-16be')
        else:
            s = string[1:-1]
            s = s.replace(b'\x5c\x5c', b'\x5c') # x5c is backslash
            s = s.replace(b'\x5c(', b'(')
            s = s.replace(b'\x5c)', b')')
            res = decode_pdfdoc(s)
    elif string[0:1] == b'<': # Hexadecimal string
        if string[1:5] == b'FEFF':
            b = bytes.fromhex(string[5:-1].decode('ascii'))
            res = b.decode('utf-16be')
        else:
            b = bytes.fromhex(decode_pdfdoc(string[1:-1]))
            res = decode_pdfdoc(b)
    return res


def unespace_literal_string(string: bytes) -> bytes:
    """ """
    ret = b''
    i = 0
    while i < len(string) :
        if string[i:i+1] == b'\x5c':
            if string[i+1:i+2] > b'0' and string[i+1:i+2] < b'9':
                ret += bytes([int(string[i+1:i+4], 8)])
                i += 3
            elif string[i+1:i+2] == b'(':
                ret += b'('
                i += 1
            elif string[i+1:i+2] == b')':
                ret += b')'
                i += 1
        else:
            ret += string[i:i+1]
        i += 1
    return ret


def apply_encoding(encoding: str, string: bytes) -> str:
    """ """
    s = string[1:-1]
    s = unespace_literal_string(s)
    return s.decode('cp1252')


def apply_tounicode(cmap: list, string: bytes, simple: bool = False) -> str:
    """ """
    i = 0
    word_l = 4
    section = None
    tokens = []
    string = string[1:-1]
    while i < len(cmap):
        if cmap[i] == 'begincodespacerange':
            if simple:
                string = unespace_literal_string(string)
                tokens = [string[j] for j in range(0, len(string))]
                i += 4
            else:
                word_l = len(cmap[i+1])-2
                tokens = [int(string[j:j+word_l], 16) for j in range(0, len(string), word_l)]
                i += 4
            continue
        if cmap[i] == 'beginbfchar':
            section = 'CHAR'
            i += 1
            continue
        if section == 'CHAR' and cmap[i] != 'endbfchar':
            for k, token in enumerate(tokens):
                if token == int(cmap[i][1:-1], 16):
                    tokens[k] = bytes.fromhex(cmap[i+1][1:-1].decode('ascii')).decode('utf-16be')
            i += 2
            continue
        if section == 'CHAR' and cmap[i] == 'endbfchar':
            section = None
            i += 1
            continue
        if cmap[i] == 'beginbfrange':
            section = 'RANGE'
            i += 1
            continue
        if section == 'RANGE' and cmap[i] != 'endbfrange':
            for k, token in enumerate(tokens):
                r_a = int(cmap[i][1:-1], 16)
                r_z = int(cmap[i+1][1:-1], 16)
                if type(token) == int and token >= r_a and token <= r_z:
                    target = cmap[i+2][1:-1]
                    if type(target) == list:
                        tokens[k] = bytes.fromhex(target[token - r_a][1:-1].decode('ascii')).decode('utf-16be')
                    else:
                        x = int(target, 16) + (token - r_a)
                        if word_l == 4:
                            tokens[k] = bytes.fromhex(f'{x:04X}').decode('utf-16be')
                        else:
                            tokens[k] = bytes.fromhex(f'{x:02X}').decode('utf-16be')
            i += 3
            continue
        if section == 'RANGE' and cmap[i] == 'endbfrange':
            section = None
            i += 1
            continue
        i += 1
    return ''.join(tokens)


def parse_text_content(content_stream: bytes):
    """ """
    ret = []
    tokens = parse_obj(b'[' + content_stream + b']')
    i = len(tokens) - 1
    section = None
    current = []
    while i >= 0:
        if tokens[i] == 'ET':
            section = 'TEXT'
            current = [tokens[i]] + current
            i -= 1
            continue
        if tokens[i] == 'BT':
            current = [tokens[i]] + current
            ret.insert(0, current)
            current = []
            section = None
            i -= 1
            continue
        if section == 'TEXT':
            current = [tokens[i]] + current
            i -= 1
            continue
        i -= 1
    return ret


def text_element_to_unicode(fonts: dict, element: list):
    """ """
    font = ''
    ret = ''
    for i, o in enumerate(element):
        if o == 'Tf':
            if font != element[i-2]:
                font = element[i-2]
                ret += f'[{font}] ' #for debug purpose
        elif o == 'Tj':
                t = element[i-1]
                ret += fonts[font]['dec_fun'](t)
        elif o == 'TJ':
            for t in element[i-1]:
                if type(t) == bytes:
                    ret += fonts[font]['dec_fun'](t)
    return ret
