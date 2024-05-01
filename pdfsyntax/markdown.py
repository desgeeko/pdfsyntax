"""Module pdfsyntax.markdown: Basic html doc generation"""



def indentation_and_first_token(string: str):
    """."""
    i = 0
    indent = 0
    while i < len(string):
        c = string[i]
        if c in ' \t':
            i += 1
        else:
            break
    return i, string[i:].split(' ')[0]


def text_style(string: str) -> list:
    """."""
    res = []
    i = 0
    current = 0
    accu = False
    search = 'TBD'
    while i < len(string):
        c = string[i]
        if search == 'TBD':
            if c == '`':
                search = c
                res.append(('TEXT', string[current:i]))
                current = i
            if c in '*_':
                accu = True
                search = c
                res.append(('TEXT', string[current:i]))
                current = i
        else:
            if search == '`':
                if c == '`':
                    res.append(('CODE', string[current+1:i]))
                    current = i+1
                    search = 'TBD'
            elif accu:
                if c in '*_':
                    search += c
                else:
                    accu = False
            elif '*' in search or '_' in search:
                if c in '*_':
                    res.append((search, string[current+len(search):i]))
                    current = i+len(search)
                    search = 'TBD'
                    i += (len(search)-1)
            else:
                accu = False
        i += 1
        if i == len(string):
            res.append(('TEXT', string[current:i]))
    return res


def parse_markdown(md: str) -> list:
    """."""
    blocks = []
    b = ''
    code = False
    lines = md.split('\n')
    for i, line in enumerate(lines):
        ln = line.strip('\r')
        indent, bs = indentation_and_first_token(ln)
        ln_break = True if ln[-2:] == '  ' else False
        if bs[:3] == "```":
            if code == False:
                code = True
            else:
                blocks.append(("PRE", indent, [('RAW', b)]))
                code = False
                b = ''
        elif code:
            line += '\n'
            b += line
        elif b and not ln:
            blocks.append(('P', indent, text_style(b)))
            b = ''
        elif ln and ln == '=' * len(ln):
            blocks.append(('H1', indent, text_style(b)))
            b = ''
        elif ln and ln == '-' * len(ln):
            blocks.append(('H2', indent, text_style(b)))
            b = ''
        elif bs and bs == '#' * len(bs):
            blocks.append((f"H{len(bs)}", indent, text_style(line[len(bs)+1:])))
            b = ''
        elif bs == '*' or bs == '+' or bs == '-':
            blocks.append(("ULI", indent, text_style(line[indent+len(bs)+1:])))
            b = ''
        elif bs and bs[-1] == '.' and bs[0] >= '0' and bs[0] <= '9':
            blocks.append(("OLI", indent, text_style(line[indent+len(bs)+1:])))
            b = ''
        elif bs and bs[0] == '>':
            blocks.append(("BLOCKQUOTE", indent, text_style(ln[2:])))
            b = ''
        elif bs and indent >= 4:
            blocks.append(("PRE", indent, [('RAW', ln)]))
            #b = ''
        else:
            if code:
                line += '\n'
            b += line
            if ln_break:
                b += "<br>"
    return blocks


def html_span(item: tuple):
    """."""
    typ, text = item
    if typ == 'TEXT':
        return text
    elif typ == 'CODE':
        return f"<code>{text}</code>"
    elif typ == 'RAW':
        return text
    elif len(typ) == 1:
        return f"<em>{text}</em>"
    elif len(typ) == 2:
        return f"<strong>{text}</strong>"
    elif len(typ) == 3:
        return f"<em><strong>{text}</strong></em>"


def assemble_html(blocks: list) -> str:
    """."""
    html = ''
    prev_typ = ''
    prev_indent = -1
    for typ, indent, items in blocks:
        s = ''
        if prev_typ[1:] != 'LI' and typ[1:] == 'LI':
            html += f"<{typ[:2].lower()}>\n"
        elif prev_typ[1:] == 'LI' and typ[1:] == 'LI':
            if prev_indent < indent:
                html += f"\n<{typ[:2].lower()}>\n"
            else:
                html += "</li>\n"
        if prev_typ[1:] == 'LI' and typ[1:] != 'LI':
            html += f"</li>\n"
            html += f"</{prev_typ[:2].lower()}>\n"
        elif prev_typ[1:] == 'LI' and typ[1:] == 'LI':
            if prev_indent > indent:
                html += f"</{typ[:2].lower()}>\n"
        for t in items:
            s += html_span(t)
        if typ == 'P':
            html += f"<p>{s}</p>\n"
        if typ == 'PRE':
            html += f"<pre><code>{s}</code></pre>\n"
        elif typ == 'BLOCKQUOTE':
            html += f"<blockquote>{s}</blockquote>\n"
        elif typ[0] == 'H':
            html += f"<{typ.lower()}>{s}</{typ.lower()}>\n"
        elif typ[1:] == 'LI':
            html += f"<{typ[1:].lower()}>{s}"
        prev_typ = typ
        prev_indent = indent
    return html


def md2html(md: str):
    """."""
    p = parse_markdown(md)
    html = assemble_html(p)
    return html


