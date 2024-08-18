""" """

from .objects import *


def prepare_pdfdoc_charset():
    """ """
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
    """Decode a PDFDocEncoded string."""
    chars = [chr(PDFDOC_CHARSET[x]) for x in string]
    return ''.join(chars)


def text_string(string: bytes) -> str:
    """Transform a fundamental string into a text string."""
    if string is None: return None
    res = ''
    string = unescape_literal_string(string)
    if string[0:1] == b'(': # Literal string
        if string[1:3] == b'\xfe\xff': 
            res = string[3:-1].decode('utf-16be')
        else:
            s = string[1:-1]
            # = s.replace(b'\x5c\x5c', b'\x5c') # x5c is backslash
            # = s.replace(b'\x5c(', b'(')
            # = s.replace(b'\x5c)', b')')
            res = decode_pdfdoc(s)
    elif string[0:1] == b'<': # Hexadecimal string
        if string[1:5] == b'FEFF':
            b = bytes.fromhex(string[5:-1].decode('ascii'))
            res = b.decode('utf-16be')
        else:
            b = bytes.fromhex(decode_pdfdoc(string[1:-1]))
            res = decode_pdfdoc(b)
    return res


def unescape_literal_string(string: bytes) -> bytes:
    """ """
    sequences = {
        b'(': b'(',
        b')': b')',
        b'n': b'\n',
        b'r': b'\r',
        b't': b'\t',
        b'b': b'\b',
        b'f': b'\f',
        b'\\': b'\\'
    }
    ret = b''
    i = 0
    while i < len(string):
        first = string[i:i+1]
        second = string[i+1:i+2]
        if first == b'\x5c': # or b'\\'
            if second in b'0123456789':
                ret += bytes([int(string[i+1:i+4], 8)])
                i += 3
            elif second in sequences :
                ret += sequences[second]
                i += 1
        else:
            ret += first
        i += 1
    return ret


def tokenize_string(string: bytes, word_l: int) -> list:
    """ """
    s_string = string[1:-1]
    if string[:1] == b'(':
        s_string = unescape_literal_string(s_string)
        return [int.from_bytes(s_string[j:j+word_l], "big") for j in range(0, len(s_string), word_l)]
    else:
        return [int(s_string[j:j+word_l*2], 16) for j in range(0, len(s_string), word_l*2)]


def apply_encoding(encoding: str, string: bytes) -> tuple:
    """ """
    s = string[1:-1]
    s = unescape_literal_string(s)
    if encoding == '/MacRomanEncoding':
        us = s.decode('mac_roman')
    else:
        us = s.decode('cp1252')
    return us, list(s)


def apply_tounicode(cmap: list, string: bytes, simple: bool = False) -> tuple:
    """ """
    i = 0
    word_l = 2 # in bytes
    section = None
    tokens = []
    while i < len(cmap):
        if cmap[i] == 'begincodespacerange':
            #word_l = (len(cmap[i+1])-2) // 2
            #tokens = tokenize_string(string, word_l)
            i += 4
            continue
        if cmap[i] == 'beginbfchar':
            section = 'CHAR'
            if not tokens:
                word_l = (len(cmap[i+1])-2) // 2
                tokens = tokenize_string(string, word_l)
                tokens_backup = tokens.copy()
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
            if not tokens:
                word_l = (len(cmap[i+1])-2) // 2
                tokens = tokenize_string(string, word_l)
                tokens_backup = tokens.copy()
            i += 1
            continue
        if section == 'RANGE' and cmap[i] != 'endbfrange':
            for k, token in enumerate(tokens):
                r_a = int(cmap[i][1:-1], 16)
                r_z = int(cmap[i+1][1:-1], 16)
                if type(token) == int and token >= r_a and token <= r_z:
                    target = cmap[i+2]
                    if type(target) == list:
                        target = cmap[i+2]
                        temp = target[token - r_a][1:-1]
                        tokens[k] = bytes.fromhex(temp.decode('ascii')).decode('utf-16be')
                    else:
                        target = cmap[i+2][1:-1]
                        x = int(target, 16) + (token - r_a)
                        if word_l == 2:
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
    for j, t in enumerate(tokens):
        if type(t) != str:
            #for DEBUG
            #tokens[j] = f"!!! {t} !!!"
            tokens[j] = ''
    return ''.join(tokens), tokens_backup


def text_element_to_unicode(fonts: dict, element: list, ts: dict) -> tuple:
    """ """
    font = ts['Tf']
    ustring = ''
    width = 0
    if element[-1] == 'Tj':
            t = element[-2]
            us, chars = fonts[font]['dec_fun'](t)
            ustring += us
            for c in chars:
                width += fonts[font]['char_width'](c) / 1000
    elif element[-1] == 'TJ':
        for t in element[-2]:
            if type(t) == bytes:
                us, chars = fonts[font]['dec_fun'](t)
                ustring += us
                for c in chars:
                    width += fonts[font]['char_width'](c) / 1000
            else:
                space_char_width = fonts[font]['char_width'](32) # char 32 is SPACE
                t -= space_char_width * 0.2
                if t <= -space_char_width:
                    nb_char = int(-t) // int(space_char_width)
                    ustring += ' ' * nb_char
                width -= t/1000
    return ustring, width
