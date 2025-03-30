"""Module pdfsyntax.display: pretty print the PDF file structure as HTML"""

import os
import html
from .objects import Stream
from .graphics import printable_stream_content
from .api import bool2yesno


NAME_MAX_WIDTH = 20
VALUE_MAX_WIDTH = 30
INFO_MAX_WIDTH = 15

HEADER = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDFSyntax</title>
    <style>
        .content {
            font-family: monospace;
            background: linear-gradient(to right, #cccccc 10ch, transparent 5ch);
        }
	.s {
	    position: relative;
	    left: 11ch;
	    background-color: green;
	}
        pre {
            margin-top: 0;
            margin-bottom: 0;
        }
        ul {
           padding-left: 1em;
           list-style: none;
           line-height: 0.9em;
        }
        nav {
            position: fixed;
            right: 1em;
            width: 22em;
            top: 4em;
            max-height: 80%;
            overflow-x: scroll;
            border: 2px dotted grey;
        }
        p {
            line-height: 2em;
            padding-top: 1em;
            padding-bottom: 1em;
            padding-left: 1em;
        }
        .nav-x {
            overflow-x: scroll;
        }
        .nav-y {
            overflow-y: scroll;
        }
        .block {
            margin-top: 0.5em;
            margin-bottom: 0.5em;
            padding-top: 1em;
            padding-bottom: 1em;
        }
        .xref-item {
	    position: relative;
	    left: 11ch;
            margin: 0 0 0 0;
        }
        .obj-body {
	    position: relative;
	    left: 12ch;
            margin: 0 0 0 0;
        }
        .obj-header {
	    position: relative;
	    left: 2ch;
            margin: 0 0 0 0;
        }
        .header {
            position: fixed;
            top: 0;
            right: 1em;
            height: 2em;
            padding: 0.2em 1em 0 1em;
            border: 2px dotted Grey;
        }
        .title {
            position: sticky;
            top: 0;
            left: 0;
            height: 1.8em;
            padding: 0.3em 1em 0.1em 1em;
            margin-bottom: 0.5em;
        }
        .nav-idx {
            display: inline-block;
            width: 4em;
            padding-left: 0.5em;
        }
        .b0 {
            background-color: white;
        }
        .b1 {
            background-color: #dddddd;
        }
        .b2 {
            background-color: #cccccc;
        }
        .b3 {
            background-color: #bbbbbb;
        }
        .c0 {
            color: black;
        }
        .c1 {
            color: #555555;
        }
        :target {
            background-color: lightyellow;
        }
        .important {
            background-color: antiquewhite;
        }
        .warning {
            background-color: crimson;
        }
        a {
            color: blue;
        }
        .stream-content {
            color: blue;
            text-decoration: underline;
            font-style: italic;
        }
        :visited {
            color: blue;
        }

@media (prefers-color-scheme: dark) {
       body {
            background-color: black;
            color: white;
        }
        .content {
            font-family: monospace;
            background: linear-gradient(to right, #333333 10ch, transparent 5ch);
        }
        .b0 {
            background-color: black;
        }
        .b1 {
            background-color: #222222;
        }
        .b2 {
            background-color: #333333;
        }
        .b3 {
            background-color: #444444;
        }
        .c0 {
            color: #dddddd;
        }
        .c1 {
            color: grey;
        }
        :target {
            background-color: #222200;
        }
        .important {
            background-color: olive;
        }
        .warning {
            background-color: firebrick;
        }
        a {
            color: deepskyblue;
        }
        .stream-content {
            color: deepskyblue;
            text-decoration: underline;
            font-style: italic;
        }
        :visited {
            color: deepskyblue;
        }
}

    </style>
</head>
<body class="b1 c0">
<div class="content">
'''

TRAILER = '''
<div id="end"><code><em>endoffile</em></code></div>
</div>
</body>
'''

TRUNCATED = '<em> ...(truncated) </em>'



def build_html(articles: list, index: list, cross: dict, filename: str, pages: list, structure: dict, file_size: int) -> str:
    """Compose the page layout."""
    page = HEADER
    for article in articles:
        abs_pos, _, typ, content = article
        if typ == 'STARTXREF':
            page += add_startxref(article, index, cross)
        elif typ == 'COMMENT':
            if content == b'%%EOF':
                page += add_eof(article)
            else:
                page += add_comment(article)
        elif typ == 'IND_OBJ':
            page += build_obj_header(article, index, cross)
            _, relevance, _, _ = cross[abs_pos]
            _, ver = relevance
            o = content['obj']
            if type(o) == Stream and '/Type' in o['entries'] and o['entries']['/Type'] == '/XRef':
                page += follow_obj(o, index[ver], display_stream=False)
            else:
                page += follow_obj(o, index[ver], display_stream=True)
                page += '\n\nendobj'
                page += build_obj_trailer()
        elif typ == 'XREFTABLE':
            page += build_obj_header(article, index, cross)
            page += build_xref_table(content['table'], index)
            page += "\ntrailer\n"
            page += follow_obj(content['trailer'], index[ver])
            page += build_obj_trailer()
        elif typ == 'XREFSTREAM':
            page += build_xref_stream(content['table'], index)
            page += '\n\nendobj'
            page += build_obj_trailer()
    page += build_header(filename)
    page += build_nav_begin()
    page += build_nav_info(structure, file_size)
    page += build_nav_pages(pages, index)
    page += build_nav_objects(articles)
    page += build_nav_quick()
    page += build_nav_end()
    page += TRAILER
    return page


def build_nav_pages(pages, index) -> str:
    """."""
    ret = '\n'
    ret += f'<details class="b3">\n'
    ret += f'<summary class="title b3"><code> Pages</code></summary>\n'
    ret += f'<p class="nav-y b2">\n'
    for i, page in enumerate(pages):
        iref, _ = page
        o_num = int(iref.imag)
        o_gen = int(iref.real)
        o_ver = index[-1][o_num]['o_ver']
        ret += f' <a class="nav-idx" href="#obj{o_num}.{o_gen}.{o_ver}">{i+1}</a>'
    ret += f'</p>\n'
    ret += f'</details>\n'
    ret += '\n'
    return ret


def build_nav_objects(articles) -> str:
    """."""
    ret = '\n'
    ret += '<details class="b3">\n'
    ret += '<summary class="title b3"><code> Minimap</code></summary>\n'
    ret += '<pre class="nav-y b2">\n'
    ret += '<ul>\n'
    for article in articles:
        pos, _, typ, obj = article
        t = ''
        if typ != 'IND_OBJ':
            if typ == 'XREFTABLE':
                ret += '<li>'
                ret += f'<a class="nav-idx" href="#idx{pos}">xref</a> XREF table & trailer'
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
        ret += f'<a class="nav-idx" href="#idx{pos}">{q}</a> {t}'
        ret += '</li>\n'
    ret += '</ul>\n'
    ret += '</pre>\n'
    ret += '</details>\n'
    ret += '\n'
    return ret


def build_nav_quick() -> str:
    """."""
    ret = '\n'
    ret += '<details class="b3">\n'
    ret += '<summary class="title b3"><code> Quick access</code></summary>\n'
    ret += '<pre class="b2">\n'
    ret += '<ul>\n'
    ret += '<li>&UpArrowBar; <a class="header-button" href="#idx0">Beginning</a></li>\n'
    ret += '<li>&DownArrowBar; <a class="header-button" href="#end">End of file</a></li>\n'
    ret += '</ul>'
    ret += '</pre>\n'
    ret += '</details>\n'
    ret += '\n'
    return ret


def build_nav_info(structure, file_size) -> str:
    """."""
    ret = '\n'
    ret += '<details class="b3">\n'
    ret += '<summary class="title b3"><code> Info</code></summary>\n'
    ret += '<pre class="b2">\n'
    ret += '<ul>'
    attrs = []
    attrs.append(f'{"Version: ":{INFO_MAX_WIDTH}}{structure["Version"]}')
    attrs.append(f'{"Page(s): ":{INFO_MAX_WIDTH}}{structure["Pages"]}')
    attrs.append(f'{"Revision(s): ":{INFO_MAX_WIDTH}}{structure["Revisions"]}')
    attrs.append(f'{"Hybrid: ":{INFO_MAX_WIDTH}}{bool2yesno(structure["Hybrid"])}')
    attrs.append(f'{"Linearized: ":{INFO_MAX_WIDTH}}{bool2yesno(structure["Linearized"])}')
    attrs.append(f'{"File size: ":{INFO_MAX_WIDTH}}{file_size} bytes')
    for x in attrs:
        ret += f' <li class="">{x}</li>'
    ret += '</ul>\n'
    ret += '</pre>\n'
    ret += '</details>\n'
    ret += '\n'
    return ret


def build_nav_begin() -> str:
    """."""
    ret = '\n'
    ret += '<nav class="b2">\n'
    ret += '\n'
    return ret


def build_nav_end() -> str:
    """."""
    ret = '\n'
    ret += '</nav>\n'
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


def add_startxref(article: dict, index: list, cross) -> str:
    """ """
    pos, _, _, xref = article
    href = f'idx{int(xref)}'
    ret = ''
    ret += f'<div class="block" id="idx{pos}">\n'
    ret += f'<div>\n'
    ret += f'<pre>\n'
    ret += f'<span class="c1">{pos:010d}</span><span class="obj-header b0">startxref</span>\n'
    ret += f'<div class="obj-body b0">\n'
    if xref == 0:
        ret += f'0\n'
    else:
        ret += f'<a class="obj-link" href="#{href}">{int(xref)}</a>\n'
    ret += f'</div>\n'
    ret += f'\n</pre>\n</div>\n</div>\n'
    return ret


def add_comment(article: dict) -> str:
    """ """
    pos, _, _, comment = article
    try:
        detail = comment[:10].decode('ascii')
    except:
        detail = '&lt;' + comment.hex() + '&gt;'
    ret = ''
    ret += f'<div class="block" id="idx{pos}">\n'
    ret += f'<div>\n'
    ret += f'<pre class="comment">\n'
    ret += f'<span class="c1">{pos:010d}</span><span class="obj-header b0">{detail}</span>\n'
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
    ret += f'<pre class="eof">\n'
    ret += f'<span class="c1">{pos:010d}</span><span class="obj-header b0">%%EOF</span>\n'
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
        else:
            _, _, _, y = x
            _, pos, o_num, o_gen, st = y
            ret += f'{pos:010} {o_gen:05} {st.decode("ascii")}'
            if st != b'f':
                ret += '    '
                ret += f'<a href="#idx{pos}">'
                ret += f'<span class="obj-link">#{o_num} {o_gen}</span>'
                ret += '</a>'
        ret += '\n'
    return ret


def build_xref_stream(table: list, index: list) -> str:
    """Display XREF table with additional links to objects."""
    ret = ''
    ret += '\nstream\n\n'
    for x in table:
        _, _, _, y = x
        _, pos, o_num, o_gen, st, env_num, raw_line = y
        if o_num != 0:
            if env_num:
                #abs_pos = envs[env_num] + (pos + 1) / 10000
                #ret += f'<a href="#idx{abs_pos}">'
                ret += f'<a href="#obj{o_num}.{o_gen}.0">'
            else:
                ret += f'<a href="#idx{pos}">'
            ret += f'<span class="obj-link">#{o_num} {o_gen}</span>'
            ret += '</a>'
            ret += '    '
            if env_num:
                ret += f'In object stream {env_num} at {pos:010} {st.decode("ascii")}\n'
            else:
                ret += f'At absolute position {pos:010} {st.decode("ascii")}\n'
    ret += '\nendstream\n'
    return ret


def move_list_item(mod_list: list, item: int, new_pos: int) -> str:
    """Reposition an item in a list."""
    if item in mod_list:
        old_pos = mod_list.index(item)
        mod_list.pop(old_pos)
        mod_list.insert(new_pos, item)
    return mod_list


def follow_obj(obj, index: list, depth=0, display_stream=True) -> str:
    """Recursively construct object representation."""
    ret = ''
    content = None
    if isinstance(obj, complex):
        o_num = int(obj.imag)
        o_gen = int(obj.real)
        abs_pos = index[o_num].get('abs_pos')
        ret += f'<a href="#idx{abs_pos}">'
        ret += f'<span class="obj-link">{o_num} {o_gen} R</span>'
        ret += '</a>'
        return ret
    if type(obj) == dict or type(obj) == Stream: 
        if type(obj) == Stream:
            content = obj['stream']
            obj = obj['entries']
        ret += '&lt;&lt;\n'
        keys = list(obj.keys())
        keys = move_list_item(keys, '/Type', 0)
        keys = move_list_item(keys, '/Subtype', 1)
        for i in keys:
            name = i #name = i.decode('ascii')
            value = follow_obj(obj[i], index, depth + 1)
            ret += ' ' * (NAME_MAX_WIDTH + 2) * depth
            if name == '/Type' or name == '/Subtype':
                ret += f'  {name:{NAME_MAX_WIDTH}}<span class="important">{value}</span>\n'
            elif name == '/JS':
                ret += f'  <span class="warning">{name:{NAME_MAX_WIDTH}}</span>{value}\n'
            elif value == '/JavaScript':
                ret += f'  {name:{NAME_MAX_WIDTH}}<span class="warning">{value}</span>\n'
            elif name == '/Prev':
                ret += f'  {name:{NAME_MAX_WIDTH}}<a class="obj-link" href="#idx{value}">{value}</a>\n'
            else:
                ret += f'  {name:{NAME_MAX_WIDTH}}{value}\n'
        ret += ' ' * (NAME_MAX_WIDTH + 2) * depth
        ret += '&gt;&gt;'
        if content and display_stream:
            p = printable_stream_content(content)
            ret += f'  \nstream\n'
            if p:
                ret += f'<details>\n<summary class="stream-content">see content</summary>\n'
                ret += f'<pre class="detail">{p}</pre>\n</details>\n'
            else:
                detail = '&lt;' + content.hex() + '&gt;'
                content = detail[:VALUE_MAX_WIDTH * 2] + TRUNCATED
                ret += f'{content}\n'
            ret += f'endstream\n'
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
    ret += f'<div><div><pre><div class="xref-item">'
    return ret


def build_obj_header(article, index, cross) -> str:
    """Add opening elements to object."""
    pos, addon, typ, obj = article
    ret = ''
    if typ == 'XREFTABLE':
        ret += f'\n'
        ret += f'<div class="block" id="idx{pos}">\n'
        ret += f'<div>\n'
        ret += f'<pre>\n'
        ret += f'<span class="c1">{pos:010d}</span>'
        ret += f'<span class="obj-header b0"><strong>XREF table & trailer</strong></span>'
    elif typ == 'XREFSTREAM':
        ret += f'\n'
        ret += f'<div class="block" id="idx{pos}">\n'
        ret += f'<div>\n'
        ret += f'<pre>\n'
    elif type(pos) == int:
        _, relevance, _, used_by = cross[pos]
        o_num, ver = relevance
        o_gen = index[ver][o_num]['o_gen']
        o_ver = index[ver][o_num]['o_ver']
        ret += f'\n'
        ret += f'<div class="block" id="idx{pos}">\n'
        ret += f'<div id="obj{o_num}.{o_gen}.{o_ver}">\n'
        ret += f'<pre>\n'
        ret += f'<span class="c1">{pos:010d}</span>'
        ret += f'<span class="obj-header b0"><strong>{o_num}</strong> '
        ret += f'{o_gen} obj</span>'
        if used_by:
            ret += f'<em><span class="c1">                 used in '
            for n, p in used_by:
                if n == 0:
                    ret += f'<a href="#idx{p}">trailer</a> '
                else:
                    ret += f'<a href="#idx{p}">{n}</a> '
            ret += f'</span></em>'
    elif type(addon) == tuple:
        env_pos, pos_in_env, seq = addon
        o_num, o_gen, o_ver = obj['o_num'], 0, 0
        _, _, _, used_by = cross[pos]
        ret += f'\n'
        ret += f'<div class="block" id="idx{pos}">\n'
        ret += f'<div id="obj{o_num}.{o_gen}.{o_ver}">\n'
        ret += f'<pre>\n'
        embedded = f'{obj["env_num"]} #{seq}'
        ret += f'<span class="c1">{embedded:10}</span>'
        ret += f'<span class="obj-header b0"><strong>{o_num}</strong> '
        ret += f'{o_gen} obj</span>'
        if used_by:
            ret += f'<em><span class="c1">                 used in '
            for n, p in used_by:
                if n == 0:
                    ret += f'<a href="#idx{p}">trailer</a> '
                else:
                    ret += f'<a href="#idx{p}">{n}</a> '
            ret += f'</span></em>'
    ret += f'<div class="obj-body b0">\n'
    return ret


def build_obj_trailer() -> str:
    """Add closing elements to object."""
    ret = '\n'
    ret += f'</div>'
    ret += f'</pre>\n</div>\n'
    ret += f'</div>\n'
    return ret



