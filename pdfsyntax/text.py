"""Should be archived: not a part of pdfsyntax"""

from .objects import *
import re
import zlib
from collections import namedtuple

def extract_text(text):
    """ """
    l = []
    res = []
    i = 0
    while i < len(text) - 2:
        h, i, _ = next_token(text, i)
        obj = text[h:i]
        l.append(obj)
    for j, tok in enumerate(l):
        if tok == b'Tf':
            font = l[j-2] 
            fsize = float(l[j-1])
        elif tok == b'Td':
            x = float(l[j-2]) 
            y = float(l[j-1])
        elif tok == b'Tj':
            text = l[j-1]
            res.append((x, y, font, fsize, text[1:-1]))
    return res


def codespacerange(toUnicode):
    """ """
    re_code = re.compile(rb'beginbfrange.*?<(\w*)>.*?<(\w*)>.*?<(\w*)>.*?endbfrange', re.S)
    for match in re.finditer(re_code, toUnicode):
        print(f"{match.group(1)} {match.group(2)} {match.group(3)}")


def dec_empty(text):
    """ """
    return ''


def dec_unicode(text):
    """ """
    text = text.replace(b'\\(', b'(')
    text = text.replace(b'\\)', b')')
    ch = [text[x:x+2].decode('utf_16_be') for x in range(0,len(text),2)]
    res = ''.join(ch)
    return res



