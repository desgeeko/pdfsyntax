"""Module pdfsyntax.display: pretty print the PDF file structure as HTML"""

import html

NAME_MAX_WIDTH = 20
VALUE_MAX_WIDTH = 40

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


def build_html(articles, pos_index, filename, version):
    """Compose the page layout"""
    page = HEADER
    last_o = max(list(pos_index.keys()))
    startxref = pos_index[last_o]
    page += build_header(filename, startxref, version)
    for article in articles:
        obj_attr = (article['o_num'], article['o_gen'], article['o_ver'])
        obj = article['content']
        mini_index = article['mini_index']
        if obj_attr[0] == -1:
            page += add_startxref(article, pos_index)
            continue
        elif obj_attr[0] == -2:
            page += add_eof(article)
            continue
        page += build_obj_header(article)
        if 'xref_table' in article:
            page += build_xref_table(article['xref_table'], mini_index)
        page += follow_obj(obj, mini_index, pos_index)
        page += build_obj_trailer()
    page += TRAILER
    return page

def build_header(filename, startxref, version):
    """Add a banner with the file name"""
    ret = ''
    ret += f'<div class="header">\n'
    ret += f'<pre> <a class="header-button" href="#obj{startxref}">jump to startxref</a>'
    ret += f'     <span class="obj-low">Hypertext inspection of </span>{filename}<span class="obj-low"> generated by </span>'
    ret += f'<a class="header-link" href="https://github.com/desgeeko/pdfsyntax">pdfsyntax</a></pre>'
    ret += f'</div>\n'
    ret += f'<div class="content">\n'
    ret += f'<pre>{version.decode("ascii")}</pre>\n'
    return ret

def add_startxref(article, pos_index):
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

def add_eof(article):
    """ """
    o_num, o_gen, o_ver = article['o_num'], article['o_gen'], article['o_ver']
    ret = ''
    ret += f'<div id="obj{o_num}.{o_gen}.{o_ver}">\n<pre class="eof">\n'
    ret += f'%%EOF\n'
    ret += f'</pre>\n</div>\n'
    return ret

def build_xref_table(table, mini_index):
    """Display XREF table with additional links to objects """
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

def move_list_item(mod_list, item, new_pos):
    """Reposition an item in a list"""
    if item in mod_list:
        old_pos = mod_list.index(item)
        mod_list.pop(old_pos)
        mod_list.insert(new_pos, item)
    return mod_list

def follow_obj(obj, mini_index, pos_index, depth=0):
    """Recursively construct object representation"""
    ret = ''
    content = None
    if type(obj) == dict: 
        if 'stream_content' in obj:
            content = obj['stream_content']
        if 'stream_def' in obj:
            obj = obj['stream_def']
        if '_REF' in obj:
            o_num = int(obj['_REF'])
            o_gen, o_ver = mini_index[o_num]
            ret += f'<a href="#obj{o_num}.{o_gen}.{o_ver}">'
            ret += f'<span class="obj-link">{o_num} {o_gen} R</span>'
            ret += '</a>'
            return ret
        ret += '<<\n'
        keys = list(obj.keys())
        keys = move_list_item(keys, b'/Type', 0)
        keys = move_list_item(keys, b'/Subtype', 1)
        for i in keys:
            name = i.decode('ascii')
            value = follow_obj(obj[i], mini_index, pos_index, depth + 1)
            ret += ' ' * (NAME_MAX_WIDTH + 2) * depth
            if name == '/Type' or name == '/Subtype':
                ret += f'  {name:{NAME_MAX_WIDTH}}<span class="important">{value}</span>\n'
            elif name == '/Prev':
                ret += f'  {name:{NAME_MAX_WIDTH}}<a class="obj-link" href="#obj{pos_index[int(value)]}">{value}</a>\n'                
            else:
                ret += f'  {name:{NAME_MAX_WIDTH}}{value}\n'
        if content:
            content = f'{content}'[2:-1]
            content = content[:VALUE_MAX_WIDTH * 2] + TRUNCATED
            ret += f'  {"stream":{NAME_MAX_WIDTH}}{content}\n'                
        ret += ' ' * (NAME_MAX_WIDTH + 2) * depth
        ret += '>>'
    elif type(obj) == list:
        ret += '[ '
        nb_char = 0
        for i in obj:
            value = follow_obj(i, mini_index, pos_index)
            ret += f'{value} '
        if len(ret) > VALUE_MAX_WIDTH and 'href' not in ret:
            ret = ret[:VALUE_MAX_WIDTH] + TRUNCATED
        ret += ']'        
    else:
        comment = False
        if obj[0:1] == b'(':
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

def build_obj_header(article):
    """Add opening elements to object"""
    obj = article['content']
    o_num, o_gen, o_ver = article['o_num'], article['o_gen'], article['o_ver']
    ret = ''
    ret += f'<div id="obj{o_num}.{o_gen}.{o_ver}">\n<pre>\n\n\n'
    if o_num == 0:
        ret += f'<span class="obj-header"><strong>XREF table & trailer</strong></span>'
        ret += f'<em class="obj-low">  at offset {article.get("abs_pos")}</em>'
    else:
        ret += f'<span class="obj-header"><strong>{o_num}</strong> <span class="obj-low">{o_gen} obj</span></span>'
        if 'a_' not in article:
            ret += f'<em class="obj-low">  at offset {article.get("abs_pos")}</em>'
        else:
            ret += f'<em class="obj-low">  from object stream {article.get("env_num")} above</em>'
    ret += f'<div class="obj-body">\n'
    return ret

def build_obj_trailer():
    """Add closing elements to object"""
    ret = ''
    ret += f'</div>\n'
    ret += f'</pre>\n</div>\n'
    return ret



