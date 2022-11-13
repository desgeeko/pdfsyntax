"""Should be archived: not a part of pdfsyntax"""

#from .objects import *
#import re
#import zlib
#from collections import namedtuple

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
            res = decode_pdfdoc(string[1:-1])
    elif string[0:1] == b'<': # Hexadecimal string
        if string[1:5] == b'FEFF':
            b = bytes.fromhex(string[5:-1].decode('ascii'))
            res = b.decode('utf-16be')
        else:
            b = bytes.fromhex(decode_pdfdoc(string[1:-1]))
            res = decode_pdfdoc(b)
    return res


#def extract_text(text):
#    """ """
#    l = []
#    res = []
#    i = 0
#    while i < len(text) - 2:
#        h, i, _ = next_token(text, i)
#        obj = text[h:i]
#        l.append(obj)
#    for j, tok in enumerate(l):
#        if tok == b'Tf':
#            font = l[j-2] 
#            fsize = float(l[j-1])
#        elif tok == b'Td':
#            x = float(l[j-2]) 
#            y = float(l[j-1])
#        elif tok == b'Tj':
#            text = l[j-1]
#            res.append((x, y, font, fsize, text[1:-1]))
#    return res


#def codespacerange(toUnicode):
#    """ """
#    re_code = re.compile(rb'beginbfrange.*?<(\w*)>.*?<(\w*)>.*?<(\w*)>.*?endbfrange', re.S)
#    for match in re.finditer(re_code, toUnicode):
#        print(f"{match.group(1)} {match.group(2)} {match.group(3)}")


#def dec_empty(text):
#    """ """
#    return ''


#def dec_unicode(text):
#    """ """
#    text = text.replace(b'\\(', b'(')
#    text = text.replace(b'\\)', b')')
#    ch = [text[x:x+2].decode('utf_16_be') for x in range(0,len(text),2)]
#    res = ''.join(ch)
#    return res



