"""Should be archived: not a part of pdfsyntax"""

#from .objects import *
#import re
#import zlib
#from collections import namedtuple


def text_string(string: bytes) -> str:
    """Transform a fundamental string into a text string"""
    if string is None: return None
    res = ''
    if string[0:1] == b'(': # Literal string
        if string[1:3] == b'\xfe\xff': 
            res = string[3:-1].decode('utf-16be')
        else:
            res = string[1:-1].decode('ascii') # TODO PDFDocEncoding
    elif string[0:1] == b'<': # Hexadecimal string
        if string[1:5] == b'FEFF':
            b = bytes.fromhex(string[5:-1].decode('ascii'))
            res = b.decode('utf-16be')
        else:
            b = bytes.fromhex(string[1:-1].decode('ascii'))
            res = b.decode('ascii')
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



