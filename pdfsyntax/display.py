"""Module pdfsyntax.display: pretty print the PDF file structure as HTML"""

import html
from .objects import Stream

NAME_MAX_WIDTH = 20
VALUE_MAX_WIDTH = 30

HEADER = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>pdfsyntax</title>
    <style>
        body {
            font-family: monospace;
        }
        :target {
            background-color: LightYellow;
        }
        .obj-header {
            background-color: LightGray;
        }
        .obj-body {
            background-color: WhiteSmoke;
            margin: 0 0 0 0;
        }
        .obj-low {
            color: Gray;
        }
        .obj-link {
            background-color: AliceBlue;
        }
        .eof {
            background-color: AntiqueWhite;
        }
        .header-button {
            background-color: AliceBlue;
            color: Grey;
        }
        .header-link {
            color: Grey;
        }
        .important {
            background-color: AntiqueWhite;
        }
        .header {
            position: fixed;
            top: 0px;
            left: 0px;
            width: 100%;
            background-color: Black;
            color: White;
        }
        .content {
            margin-top: 5em;
        }
        pre {
            margin-top: 0.5em;
            margin-bottom: 0.5em;
        }
    </style>
</head>
<body>
'''

TRAILER = '''
</div>
</body>
'''

TRUNCATED = '<em> ...(truncated) </em>'


def build_html(articles: list, pos_index: dict, nb_ver: int, filename: str, version: bytes) -> str:
    """Compose the page layout."""
    page = HEADER
    page += build_header(filename, nb_ver, version)
    for article in articles:
        obj_attr = (article['o_num'], article['o_gen'], article['o_ver'])
        obj = article['content']
        if obj_attr[0] == -2:
            page += add_startxref(article, pos_index)
            continue
        elif obj_attr[0] == -1:
            page += add_eof(article)
            continue
        page += build_obj_header(article)
        mini_index = article['mini_index']
        if 'xref_table' in article:
            page += build_xref_table(article['xref_table'], mini_index)
            page += "\ntrailer\n"
        if 'xref_stream' in article:
            page += follow_obj(obj['entries'], mini_index, pos_index)
            page += build_xref_stream(article['xref_stream'], mini_index)
        else:
            page += follow_obj(obj, mini_index, pos_index)
        page += build_obj_trailer()
    page += TRAILER
    return page

def build_header(filename: str, nb_ver: int, version: bytes) -> str:
    """Add a banner with the file name."""
    ret = ''
    ret += f'<div class="header">\n'
    ret += f'<pre> <a class="header-button" href="#obj-2.-2.{nb_ver-1}">jump to startxref</a>'
    ret += f'     <span class="obj-low">Hypertext inspection of </span>{filename}<span class="obj-low"> generated by </span>'
    ret += f'<a class="header-link" href="https://pdfsyntax.dev">pdfsyntax</a></pre>'
    ret += f'</div>\n'
    ret += f'<div class="content">\n'
    ret += f'<pre>{version[:8].decode("ascii")}</pre>\n'
    return ret

def add_startxref(article: dict, pos_index: dict) -> str:
    """ """
    o_num, o_gen, o_ver = article['o_num'], article['o_gen'], article['o_ver']
    xref = article['content']
    ret = ''
    ret += f'<div id="obj{o_num}.{o_gen}.{o_ver}">\n<pre>\n'
    ret += f'startxref\n'
    if xref == 0:
        ret += f'0\n'
    else:
        ret += f'<a class="obj-link" href="#obj{pos_index[xref]}">{xref}</a>\n'                
    ret += f'\n</pre>\n</div>\n'
    return ret

def add_eof(article: dict) -> str:
    """ """
    o_num, o_gen, o_ver = article['o_num'], article['o_gen'], article['o_ver']
    o_num, o_gen = article['o_num'], article['o_gen']
    ret = ''
    ret += f'<div id="obj{o_num}.{o_gen}.{o_ver}">\n<pre class="eof">\n'
    ret += f'%%EOF\n'
    ret += f'</pre>\n</div>\n'
    return ret

def build_xref_table(table: list, mini_index: list) -> str:
    """Display XREF table with additional links to objects."""
    ret = ''
    for line, o_num in table:
        ret += line.decode('ascii')
        if line[:10] != b'0000000000' and o_num != None:
            o_gen, o_ver = mini_index[o_num]
            ret += '    '
            ret += f'<a href="#obj{o_num}.{o_gen}.{o_ver}">'
            ret += f'<span class="obj-link">#{o_num} {o_gen}</span>'
            ret += '</a>'
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

def follow_obj(obj, mini_index: list, pos_index: dict, depth=0) -> str:
    """Recursively construct object representation."""
    ret = ''
    content = None
    if isinstance(obj, complex):
        o_num = int(obj.imag)
        o_gen, o_ver = mini_index[o_num]
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
            value = follow_obj(obj[i], mini_index, pos_index, depth + 1)
            ret += ' ' * (NAME_MAX_WIDTH + 2) * depth
            if name == '/Type' or name == '/Subtype':
                ret += f'  {name:{NAME_MAX_WIDTH}}<span class="important">{value}</span>\n'
            elif name == '/Prev':
                ret += f'  {name:{NAME_MAX_WIDTH}}<a class="obj-link" href="#obj{pos_index[int(value)]}">{value}</a>\n'                
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
            value = follow_obj(i, mini_index, pos_index)
            ret += f'{value} '
        if len(ret) > VALUE_MAX_WIDTH and 'href' not in ret:
            ret = ret[:VALUE_MAX_WIDTH] + TRUNCATED
        ret += ']'        
    else:
        comment = False
        if type(obj) == int or type(obj) == float or type(obj) == bool or type(obj) == str:
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

def build_obj_header(article) -> str:
    """Add opening elements to object."""
    obj = article['content']
    o_num, o_gen, o_ver = article['o_num'], article['o_gen'], article['o_ver']
    ret = ''
    ret += f'<div id="obj{o_num}.{o_gen}.{o_ver}">\n<pre>\n\n\n'
    if o_num == 0:
        ret += f'<span class="obj-header"><strong>XREF table & trailer</strong></span>'
        ret += f'<em class="obj-low">  at offset {article.get("abs_pos")}</em>'
    else:
        if 'xref_stream' in article:
            ret += f'<span class="obj-header"><strong>{o_num}</strong> <span class="obj-low">{o_gen} obj</span></span>'
            ret += f'<em class="obj-low">  as XREF stream object at offset {article.get("abs_pos")}</em>'
        else:
            ret += f'<span class="obj-header"><strong>{o_num}</strong> <span class="obj-low">{o_gen} obj</span></span>'
            if 'a_' not in article:
                ret += f'<em class="obj-low">  at offset {article.get("abs_pos")}</em>'
            else:
                ret += f'<em class="obj-low">  from object stream {article.get("env_num")} above</em>'
    ret += f'<div class="obj-body">\n'
    return ret

def build_obj_trailer() -> str:
    """Add closing elements to object."""
    ret = ''
    ret += f'</div>\n'
    ret += f'</pre>\n</div>\n'
    return ret



