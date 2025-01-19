"""Module pdfsyntax.display: pretty print the PDF file structure as HTML"""

import os
import html
from .objects import Stream


NAME_MAX_WIDTH = 15
VALUE_MAX_WIDTH = 30

HEADER = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDFSyntax</title>
    <style>
        content {
            font-family: monospace;
        }
        pre {
            margin-top: 0.5em;
            margin-bottom: 0.5em;
        }
        ul {
           padding-left: 1em;
           list-style: none;
           line-height: 0.9em;
        }
        nav {
            position: fixed;
            right: 1em;
            width: 20em;
            border: 2px dotted grey;
        }
        #nav-pages {
            top: 4em;
            height: 6em;
            overflow-x: scroll;
        }
        #nav-objects {
            top: 12em;
            height: 75%;
            overflow-y: scroll;
        }
        #nav-end {
            bottom: 2em;
            height: 2.5em;
         }
        .block {
            padding-top: 1em;
        }
        .obj-body {
            margin: 0 0 0 0;
        }
        .header {
            position: fixed;
            top: 0;
            right: 1em;
            height: 2em;
            padding: 0 1em 0.2em 1em;
            border: 2px dotted Grey;
        }
        .title {
            position: sticky;
            top: 0;
            left: 0;
            height: 1.8em;
            padding: 0.3em 1em 0.1em 1em;
        }
        .nav-idx {
            display: inline-block;
            width: 4em;
            height: 1.2em;
            padding-left: 0.5em;
        }
        .b0 {
            background-color: white;
        }
        .b1 {
            background-color: whitesmoke;
        }
        .b2 {
            background-color: lightgrey;
        }
        .b3 {
            background-color: silver;
        }
        .c0 {
            color: black;
        }
        .c1 {
            color: grey;
        }
        :target {
            background-color: lightyellow;
        }
        .important {
            background-color: antiquewhite;
        }
        a {
            color: blue;
        }
        :visited {
            color: blue;
        }

@media (prefers-color-scheme: dark) {
       body {
            background-color: black;
            color: white;
        }
        .b0 {
            background-color: black;
        }
        .b1 {
            background-color: #111;
        }
        .b2 {
            background-color: #222;
        }
        .b3 {
            background-color: #444;
        }
        .c0 {
            color: white;
        }
        .c1 {
            color: grey;
        }
        :target {
            background-color: #220;
        }
        .important {
            background-color: olive;
        }
        a {
            color: deepskyblue;
        }
        :visited {
            color: deepskyblue;
        }
}

    </style>
</head>
<body>
<div class="content">
'''

TRAILER = '''
<div id="end"><code><em>(end of file)</em></code></div>
</div>
</body>
'''

TRUNCATED = '<em> ...(truncated) </em>'


def pos2ref_from_index(index: list, abs_pos: int) -> dict:
    """."""
    for _, current in enumerate(index):
        for x in current:
            if x is None:
                continue
            if abs_pos == x.get('abs_pos') and x.get('o_num') != 0:
                o_num = x['o_num']
                o_gen = x['o_gen']
                o_ver = x['o_ver']
                return (o_num, o_gen, o_ver)
    return None


def recent_ref_from_index(index: list, iref: complex) -> dict:
    """."""
    res = None
    o_num = int(iref.imag)
    for _, current in enumerate(index):
        x = current[o_num]
        if x is None:
            continue
        else:
            res =  (o_num, x['o_gen'], x['o_ver'])
    return res


def build_html(articles: list, index: list, filename: str, pages: list) -> str:
    """Compose the page layout."""
    nb_ver = len(index)
    page = HEADER
    for article in articles:
        pos, _, typ, content = article
        if typ == 'STARTXREF':
            page += add_startxref(article, index)
        elif typ == 'COMMENT':
            if content == b'%%EOF':
                page += add_eof(article)
            else:
                page += add_comment(article)
        elif typ == 'IND_OBJ':
            page += build_obj_header(article, index)
            page += follow_obj(content['obj'], index)
            page += build_obj_trailer()
        elif typ == 'XREFTABLE':
            page += build_obj_header(article, index)
            page += build_xref_table(content['table'], index)
            page += "\ntrailer\n"
            page += follow_obj(content['trailer'], index)
            page += build_obj_trailer()
        elif typ == 'XREF' and content[0] == 'XREF_S':
            page += build_xref_item_header()
            page += build_xref_stream_item(content, index)
            page += build_obj_trailer()
    page += build_header(filename)
    page += build_page_nav(pages, index)
    page += build_nav_menu(articles)
    page += build_nav_end()
    page += TRAILER
    return page


def build_page_nav(pages, index) -> str:
    """."""
    ret = '\n'
    ret += '<nav class="b0" id="nav-pages">\n'
    ret += f'<div class="title b3">\n'
    ret += f'<code>Pages</code>\n'
    ret += f'</div>\n'
    ret += f'<pre>\n'
    for i, page in enumerate(pages):
        iref, _ = page
        o_num = int(iref.imag)
        o_gen = int(iref.real)
        o_ver = index[-1][o_num]['o_ver']
        ret += f' <a class="nav-idx b2" href="#obj{o_num}.{o_gen}.{o_ver}">{i}</a>'
    ret += f'</pre>\n'
    ret += f'</nav>\n'
    ret += '\n'
    return ret


def build_nav_menu(articles) -> str:
    """."""
    ret = '\n'
    ret += '<nav class="b0" id="nav-objects">\n'
    ret += f'<div class="title b3">\n'
    ret += f'<code>Minimap</code>\n'
    ret += f'</div>\n'
    ret += f'<pre>\n'
    ret += '<ul>\n'
    for article in articles:
        pos, _, typ, obj = article
        t = ''
        if typ != 'IND_OBJ':
            if typ == 'XREFTABLE':
                ret += '<li>'
                ret += f'<a class="nav-idx b2" href="#idx{pos}">xref</a> XREF table & trailer'
                ret += '</li>\n'
            continue
        q = obj['o_num']
        c = obj['obj']
        if type(c) == dict or type(c) == Stream: 
            if type(c) == Stream:
                content = c['stream']
                c = c['entries']
            t = c.get("/Type", "")
        ret += '<li>'
        if type(pos) == tuple:
            ret += f'<a class="nav-idx b2" href="#obj{q}.0.0">{q}</a> {t}'
        else:
            ret += f'<a class="nav-idx b2" href="#idx{pos}">{q}</a> {t}'
        ret += '</li>\n'
    ret += f'</ul>\n'
    ret += f'</pre>\n'
    ret += f'</nav>\n'
    ret += '\n'
    return ret


def build_nav_end() -> str:
    """."""
    ret = '\n'
    ret += '<nav class="b0" id="nav-end">\n'
    ret += f'<pre>\n'
    ret += f'&gt;&gt;&gt; <a class="header-button" href="#end">Scroll to end of file</a>'
    ret += f'</pre>\n'
    ret += f'</nav>\n'
    ret += '\n'
    return ret


def build_header(filename: str) -> str:
    """."""
    ret = ''
    ret += f'<div class="header b3">\n'
    ret += f'<pre>\n'
    ret += f'{os.path.basename(filename)} - '
    ret += f'internal view generated by '
    ret += f'<a href="https://pdfsyntax.dev">PDFSyntax</a>\n'
    ret += f'</pre>\n'
    ret += f'</div>\n'
    return ret


def add_startxref(article: dict, index: list) -> str:
    """ """
    pos, _, _, xref = article
    ref = pos2ref_from_index(index, int(xref))
    if ref is None:
        href = f'idx{int(xref)}'
    else:
        o_num, o_gen, o_ver = ref
        href = f'obj{o_num}.{o_gen}.{o_ver}'
    ret = ''
    ret += f'<div class="block" id="idx{pos}">\n'
    ret += f'<div>\n'
    ret += f'<pre>\n'
    ret += f'startxref\n'
    if xref == 0:
        ret += f'0\n'
    else:
        ret += f'<a class="obj-link" href="#{href}">{int(xref)}</a>\n'
    ret += f'\n</pre>\n</div>\n</div>\n'
    return ret


def add_comment(article: dict) -> str:
    """ """
    pos, _, _, comment = article
    try:
        detail = comment[:10].decode('ascii')
    except:
        detail = '<' + comment.hex() + '>'
    ret = ''
    ret += f'<div class="block" id="idx{pos}">\n'
    ret += f'<div>\n'
    ret += f'<pre class="comment">\n'
    ret += f'{detail}\n'
    ret += f'</pre>\n'
    ret += f'</div>\n'
    ret += f'</div>\n'
    return ret


def add_eof(article: dict) -> str:
    """ """
    pos, _, _, _ = article
    ret = ''
    ret += f'\n'
    ret += f'<div class="block" id="idx{pos}">\n'
    ret += f'<div>\n'
    ret += f'<pre class="eof b1">\n'
    ret += f'%%EOF\n'
    ret += f'</pre>\n'
    ret += f'</div>\n'
    ret += f'</div>\n'
    return ret


def build_xref_table(table: list, index: list) -> str:
    """Display XREF table with additional links to objects."""
    ret = ''
    for x in table:
        if len(x) == 2:
            start, size = x
            ret += f'{start}  {size}'
        elif len(x) == 4:
            pos, o_num, o_gen, st = x
            ret += f'{pos:010} {o_gen:05} {st.decode("ascii")}'
            if st != b'f':
                _, _, o_ver = recent_ref_from_index(index, complex(o_gen, o_num))
                ret += '    '
                ret += f'<a href="#idx{pos}">'
                #ret += f'<a href="#obj{o_num}.{o_gen}.{o_ver}">'
                ret += f'<span class="obj-link">#{o_num} {o_gen}</span>'
                ret += '</a>'
        ret += '\n'
    return ret


def build_xref_stream_item(item: tuple, index: list) -> str:
    """Display XREF stream item."""
    ret = ' '
    _, pos, o_num, o_gen, st, env_num, raw_line = item
    _, _, o_ver = recent_ref_from_index(index, complex(o_gen, o_num))
    if o_num != 0:
        ret += f'<a href="#obj{o_num}.{o_gen}.{o_ver}">'
        ret += f'<span class="obj-link">#{o_num} {o_gen}</span>'
        ret += '</a>'
        ret += '    '
        if env_num:
            ret += f'In object stream {env_num} at {pos:010} {st.decode("ascii")}'
        else:
            ret += f'At absolute position {pos:010} {st.decode("ascii")}'
    ret += '\n'
    return ret


def build_xref_stream(table: list, mini_index: list) -> str:
    """Display XREF stream with additional links to objects."""
    ret = '\nstream\n'
    for line, o_num in table:
        ret += line.decode('ascii')
        if o_num != None:
            o_gen, o_ver = mini_index[o_num]
            ret += '    '
            ret += f'<a href="#obj{o_num}.{o_gen}.{o_ver}">'
            ret += f'<span class="obj-link">#{o_num} {o_gen}</span>'
            ret += '</a>'
        ret += '\n'
    return ret


def move_list_item(mod_list: list, item: int, new_pos: int) -> str:
    """Reposition an item in a list."""
    if item in mod_list:
        old_pos = mod_list.index(item)
        mod_list.pop(old_pos)
        mod_list.insert(new_pos, item)
    return mod_list


def follow_obj(obj, index: list, depth=0) -> str:
    """Recursively construct object representation."""
    ret = ''
    content = None
    if isinstance(obj, complex):
        o_num, o_gen, o_ver = recent_ref_from_index(index, obj)
        ret += f'<a href="#obj{o_num}.{o_gen}.{o_ver}">'
        ret += f'<span class="obj-link">{o_num} {o_gen} R</span>'
        ret += '</a>'
        return ret
    if type(obj) == dict or type(obj) == Stream: 
        if type(obj) == Stream:
            content = obj['stream']
            obj = obj['entries']
        ret += '<<\n'
        keys = list(obj.keys())
        keys = move_list_item(keys, '/Type', 0)
        keys = move_list_item(keys, '/Subtype', 1)
        for i in keys:
            name = i #name = i.decode('ascii')
            value = follow_obj(obj[i], index, depth + 1)
            ret += ' ' * (NAME_MAX_WIDTH + 2) * depth
            if name == '/Type' or name == '/Subtype':
                ret += f'  {name:{NAME_MAX_WIDTH}}<span class="important">{value}</span>\n'
            elif name == '/Prev':
                ret += f'  {name:{NAME_MAX_WIDTH}}<a class="obj-link" href="#idx{value}">{value}</a>\n'
            else:
                ret += f'  {name:{NAME_MAX_WIDTH}}{value}\n'
        ret += ' ' * (NAME_MAX_WIDTH + 2) * depth
        ret += '>>'
        if content:
            content = f'{content}'[2:-1]
            content = content[:VALUE_MAX_WIDTH * 2] + TRUNCATED
            ret += f'  \n{"stream":{NAME_MAX_WIDTH}}\n{content}\n'
    elif type(obj) == list:
        ret += '[ '
        for i in obj:
            value = follow_obj(i, index)
            ret += f'{value} '
        if len(ret) > VALUE_MAX_WIDTH and 'href' not in ret:
            ret = ret[:VALUE_MAX_WIDTH] + TRUNCATED
        ret += ']'        
    else:
        comment = False
        if type(obj) == int or type(obj) == float or type(obj) == bool or type(obj) == str or obj is None:
            ret += str(obj)
        elif isinstance(obj, complex) == True:
            ret += str(obj.num)
        elif obj[0:1] == b'(':
            if len(obj) > VALUE_MAX_WIDTH:
                obj = obj[:VALUE_MAX_WIDTH]
                comment = True
            obj = f'{obj}'
            ret += f'{obj[2:-1]}'
        else:
            ret += obj.decode('ascii')
        ret = html.escape(ret)
        if comment == True:
            ret += TRUNCATED
    return ret


def build_xref_item_header() -> str:
    """."""
    ret = ''
    ret += f'<div><div><pre><div>'
    #ret += f'<div class="obj-body">\n'
    return ret


def build_obj_header(article, index) -> str:
    """Add opening elements to object."""
    pos, _, typ, obj = article
    ref = pos2ref_from_index(index, pos)
    ret = ''
    if ref:
        o_num, o_gen, o_ver = ref
        ret += f'\n'
        ret += f'<div class="block" id="idx{pos}">\n'
        ret += f'<div id="obj{o_num}.{o_gen}.{o_ver}">\n<pre>\n'
        ret += f'<span class="obj-header b1"><strong>{o_num}</strong> <span class="c1">{o_gen} obj</span></span>'
        ret += f'<em class="obj-low">  at offset {pos}</em>'
    elif type(pos) == tuple:
        o_num, o_gen, o_ver = obj['o_num'], 0, 0
        ret += f'\n'
        ret += f'<div id="obj{o_num}.{o_gen}.{o_ver}">\n'
        ret += f'<div>\n<pre>\n'
        ret += f'<span class="obj-header b1"><strong>{o_num}</strong> <span class="c1">{o_gen} obj</span></span>'
        ret += f'<em class="obj-low">  from object stream {obj["env_num"]} above</em>'
    else:
        ret += f'\n'
        ret += f'<div class="block" id="idx{pos}">\n'
        ret += f'<div>\n'
        ret += f'<pre>\n'
        ret += f'<span class="obj-header b1"><strong>XREF table & trailer</strong></span>'
        ret += f'<em class="c1">  at offset {pos}</em>\n'
    ret += f'<div class="obj-body b1">\n'
    return ret


def build_obj_trailer() -> str:
    """Add closing elements to object."""
    ret = ''
    ret += f'</div>\n'
    ret += f'</pre>\n</div>\n'
    ret += f'</div>\n'
    return ret



