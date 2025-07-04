"""Module pdfsyntax.markdown: Basic html doc generation"""



def indentation_and_first_token(string: str):
    """Count indentation for spaces & blockquotes and detect first token."""
    i = 0
    indent = 0
    blockquote = False
    while i < len(string):
        c = string[i]
        if c == ' ':
            i += 1
        elif c == '>':
            blockquote = True
            i += 1
        elif c == '\t':
            i += 4
        else:
            if blockquote:
                i -= 1
            break
    return i, string[i:].split(' ')[0]


def link(string: str) -> str:
    """Turn link into HTML tag."""
    res = ''
    i = 0
    j = 0
    while i < len(string):
        f = string.find('](', i)
        if f == -1:
            break
        b1 = string.find('[', i) + 1
        b2 = f
        p1 = f + 2
        p2 = string.find(')', f) + 1
        if string[b1-2] == '!':
            j = p2
            res += string[i:b1-2]
            res += f"<img src='{string[p1:p2-1]}' alt='{string[b1:b2]}'>"
        else:
            j = p2
            res += string[i:b1-1]
            l = string[p1:p2-1]
            if l[-3:] == '.md':
                l = l[:-3] + '.html'
            res += f"<a href='{l}'>{string[b1:b2]}</a>"
        i = p2
    res += string[j:]
    return res


def style(string: str) -> str:
    """Apply HTML spans for emphasis and code."""
    res = ''
    i = 0
    current = 0
    accu = False
    search = 'TBD'
    p = ' '
    while i < len(string):
        c = string[i]
        if i > 0:
            p = string[i-1]
        if search == 'TBD':
            if c == '`':
                search = c
                res += string[current:i]
                current = i
            if c == '*' or (p in ' [>' and c == '_'):
                accu = True
                search = c
                res += string[current:i]
                current = i
        else:
            if search == '`':
                if c == '`':
                    res += f"<code>{string[current+1:i]}</code>"
                    current = i+1
                    search = 'TBD'
            elif accu:
                if c in '*_':
                    search += c
                else:
                    accu = False
            elif '*' in search or '_' in search:
                if c in '*_':
                    text = string[current+len(search):i]
                    if len(search) == 1:
                        res += f"<em>{text}</em>"
                    elif len(search) == 2:
                        res +=  f"<strong>{text}</strong>"
                    elif len(search) == 3:
                        res +=  f"<em><strong>{text}</strong></em>"
                    current = i+len(search)
                    search = 'TBD'
                    i += (len(search)-1)
            else:
                accu = False
        i += 1
        if i == len(string):
            res += string[current:i]
    return res


def parse_code_block(lines: list, start_pos = 0, mode = 'indented'):
    """Parse consecutive lines for code block."""
    res = []
    i = start_pos
    while i < len(lines):
        ln = lines[i].strip('\r')
        indent, bs = indentation_and_first_token(ln)
        ln += '\n'
        if mode == 'indented':
            if indent == 4:
                res.append(ln)
            else:
                break
        elif mode == 'fenced':
            if ln[:3] == "```":
                break
            else:
                res.append(ln)
        i += 1
    return ("PRE", i, res)


def parse_title(lines: list, start_pos = 0, mode = 'underlined'):
    """Parse header line."""
    res = []
    typ = ''
    i = start_pos
    ln = lines[i].strip('\r')
    indent, bs = indentation_and_first_token(ln)
    if mode == 'underlined':
        if lines[i+1][:2] == '==':
            typ = "H1"
        elif lines[i+1][:2] == '--':
            typ = "H2"
        res.append(ln)
        i += 1
    elif mode == 'prefixed':
        typ = f"H{len(bs)}"
        res.append(ln[len(bs)+1:])
    return (typ, i, res)


def parse_list(lines: list, start_pos = 0, mode = 'unordered'):
    """Parse consecutive lines for items list."""
    res = []
    if mode == 'unordered':
        typ = 'UL'
    elif mode == 'ordered':
        typ = 'OL'
    ref_indent, _ = indentation_and_first_token(lines[start_pos])
    i = start_pos
    while i < len(lines):
        ln = lines[i].strip('\r')
        indent, bs = indentation_and_first_token(ln)
        if mode == 'unordered':
            if bs != '*' and bs != '+' and bs != '-':
                break
        elif mode == 'ordered':
            if not bs or bs[-1] != '.':
                break
        if indent != ref_indent:
            break
        res.append(('LI' ,[ln[indent+len(bs)+1:]]))
        i += 1
    return (typ, i, res)


def parse_table(lines: list, start_pos = 0):
    """Parse consecutive lines for table."""
    res = []
    ref_indent, _ = indentation_and_first_token(lines[start_pos])
    i = start_pos
    header = True
    tbody = []
    while i < len(lines):
        ln = lines[i].strip('\r')
        indent, bs = indentation_and_first_token(ln)
        if not bs or bs[0] != '|':
            break
        if indent != ref_indent:
            break
        if header:
            header = False
            row = [('TH', [td]) for td in ln[indent:].split('|')[1:-1]]
            res.append(('THEAD', [('TR', row)]))
        else:
            row = [('TD', [td]) for td in ln[indent:].split('|')[1:-1]]
            if row[0][1][0][1:3] != '--':
                tbody.append(('TR' ,row))
        i += 1
    res.append(('TBODY', tbody))
    return ('TABLE', i, res)


def flush_p(blocks: list, b: list):
    """Flush paragraph into blocks buffer."""
    if b:
        blocks.append(('P', [''.join(b)]))
        b.clear()
    return


def parse_markdown(lines: list, start_pos = 0, start_indent = 0) -> tuple:
    """Recursively parse lines of markdown and return a tree of ('TYPE', [CONTENT]) tuples."""
    blocks = []
    b = []
    i = start_pos
    while i < len(lines):
        line = lines[i]
        ln = line.strip('\r')
        indent, bs = indentation_and_first_token(ln)
        ln_break = True if ln[-2:] == '  ' else False
        if indent + 1 < start_indent:
            flush_p(blocks, b)
            return blocks, i
        elif not bs and indent > 0 and indent + 1 > start_indent:
            flush_p(blocks, b)
            sub, i = parse_markdown(lines, i, indent + 1)
            blocks.append(('BLOCKQUOTE', sub))
        elif bs[:3] == "```":
            flush_p(blocks, b)
            typ, i, res = parse_code_block(lines, i+1, 'fenced')
            blocks.append((typ, res))
        elif bs and indent >= 4:
            flush_p(blocks, b)
            typ, i, res = parse_code_block(lines, i, 'indented')
            blocks.append((typ, res))
        elif ln and (ln == '=' * len(ln) or ln == '-' * len(ln)):
            typ, i, res = parse_title(lines, i-1, 'underlined')
            blocks.append((typ, res))
            b = []
        elif bs and bs == '#' * len(bs):
            flush_p(blocks, b)
            typ, i, res = parse_title(lines, i, 'prefixed')
            blocks.append((typ, res))
        elif bs == '*' or bs == '+' or bs == '-':
            flush_p(blocks, b)
            typ, i, res = parse_list(lines, i, 'unordered')
            blocks.append((typ, res))
        elif bs and bs[-1] == '.' and bs[0] >= '0' and bs[0] <= '9':
            flush_p(blocks, b)
            typ, i, res = parse_list(lines, i, 'ordered')
            blocks.append((typ, res))
        elif bs and bs == '|':
            flush_p(blocks, b)
            typ, i, res = parse_table(lines, i)
            blocks.append((typ, res))
        elif b and not ln:
            flush_p(blocks, b)
        else:
            b.append(line[indent:])
            if ln_break:
                b.append("<br>")
        i += 1
    return blocks, i


def tags(string: str) -> str:
    """Tranform both style & links."""
    return style(link(string))


def entities(string: str) -> str:
    """Turn special chars into HTML entities."""
    string = string.replace('<', '&lt;')
    string = string.replace('>', '&gt;')
    return string


def assemble_html(blocks: list, html = '') -> str:
    """Recusively build HTML string for parsed markdown."""
    for typ, items in blocks:
        html += f"<{typ.lower()}>"
        for x in items:
            if type(x) == tuple:
                html += assemble_html([x])
            else:
                if typ != 'PRE':
                    html += tags(x)
                else:
                    html += entities(x)
        html += f"</{typ.lower()}>\n"
    return html


def render_html(md: str):
    """Render HTML from markdown string."""
    lines = md.split('\n')
    ast, _ = parse_markdown(lines)
    html = assemble_html(ast)
    return html


def tokenize(md: str) -> list:
    """."""
    res = ['\n']
    i = 0
    last_nl = 0
    before_nl = 0
    tok = ''
    UNDER2FRONT = {'=': '#', '-': '##'}
    while i < len(md):
        c = md[i]
        if c in '\n[]()>*_`':
            if c == '\n':
                before_nl = last_nl
                last_nl = len(res) - 1
            if tok:
                if tok == '=' * len(tok) or tok == '-' * len(tok):
                    res.insert(before_nl+1, UNDER2FRONT[tok[0]])
                    tok = ''
                else:
                    res.append(tok)
                    tok = ''
            if res and res[-1][-1] in '*_' and c in '*_':
                res[-1] = res[-1] + c
            else:
                res.append(c)
        elif tok and tok[-1] in '#-' and tok[0] in '#-' and c not in '#-':
            res.append(tok)
            tok = c
        else:
            tok += c
        i += 1
    return res


def emit_html(toks: list, start = 0, context = ''):
    """."""
    res = ''
    i = start
    while i < len(toks):
        tk = toks[i]
        if tk == '\n':
            tk = '\\n'
        print(f"{i:2} {context:10} {tk}")
        if context == 'para':
            if toks[i-1] == '\n' and toks[i] == '\n':
                return i+1, res
            elif toks[i-1] == '\n' and toks[i] == len(toks[i]) * '#':
                return i, res
        elif context == 'blockquote':
            if i > 0 and toks[i-1] == '\n' and toks[i] != '>':
                return i, res
            #if toks[i] == '>':
            #    toks[i] = ''
        elif context and context == 'ul':
            if toks[i-1] == '\n' and toks[i] == '\n':
                return i, res
            elif toks[i-1] == '\n' and toks[i][0] not in '*-':
                return i, res
        elif context and context == 'li':
            if toks[i] == '\n':
                return i, res
        elif context and context[0] == 'h':
            if toks[i] == '\n':
                return i, res
        elif context and context == 'code':
            if toks[i] == '`':
                return i+1, res
        elif context and context == 'em':
            if toks[i] in '*_':
                return i+1, res
        elif context and context == 'strong':
            if toks[i].replace('_', '*') == '**':
                return i+1, res
        elif context and context == 'em&strong':
            if toks[i].replace('_', '*') == '***':
                return i+1, res
        if i == 0 and toks[0] == '\n':
            i += 1
        elif toks[i-1] == '\n' and toks[i] and toks[i] == len(toks[i]) * '#':
            hx = f'h{len(toks[i])}'
            i, r = emit_html(toks, i+1, hx)
            res += f'<{hx}>{r}</{hx}>'
        elif toks[i] == '`':
            i, r = emit_html(toks, i+1, 'code')
            res += f'<code>{r}</code>'
        elif toks[i-1] != '\n' and toks[i] in '*_':
            i, r = emit_html(toks, i+1, 'em')
            res += f'<em>{r}</em>'
        elif toks[i-1] != '\n' and toks[i].replace('_', '*') == '**':
            i, r = emit_html(toks, i+1, 'strong')
            res += f'<strong>{r}</strong>'
        elif toks[i-1] != '\n' and toks[i].replace('_', '*') == '***':
            i, r = emit_html(toks, i+1, 'em&strong')
            res += f'<em><strong>{r}</strong></em>'
        elif context == 'ul' and toks[i-1] == '\n' and toks[i] in '*-':
            i, r = emit_html(toks, i, 'li')
            res += f'<li>{r}</li>'
        elif context != 'li' and toks[i-1] == '\n' and toks[i] in '*-':
            i, r = emit_html(toks, i, 'ul')
            res += f'<ul>{r}</ul>'
        elif context != 'blockquote' and toks[i-1] == '\n' and toks[i] == '>':
            i, r = emit_html(toks, i, 'blockquote')
            res += f'<blockquote>{r}</blockquote>'
        elif context:
            res += f'{toks[i]}'
            i += 1
        else:
            if toks[i] == '\n':
                i += 1
            else:
                i, r = emit_html(toks, i, 'para')
                res += f'<p>{r}</p>'
    return i, res


