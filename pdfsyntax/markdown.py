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


def render_htmlV2(md: str):
    """Render HTML from markdown string."""
    t = tokenize(md)
    _, html = emit_html(t)
    return html


def tokenize(md: str) -> list:
    """Split input string and transform some tokens to facilitate further processing."""
    res = ['\n', '\n']
    i = 2
    last_nl = 0
    before_nl = 0
    tok = ''
    UNDER2FRONT = {'=': '#', '-': '##'}
    while i < len(md):
        c = md[i]
        #y, z = res[-2], res[-1]
        if c in '\n[]()>*_`-+.':
            if c == '\n':
                before_nl = last_nl
                last_nl = len(res) - 1
            if tok and (tok == '=' * len(tok) or tok == '-' * len(tok)):
                # Turn setext into atx style heading
                res.insert(before_nl+1, UNDER2FRONT[tok[0]])
                tok = ''
            elif len(res) > 1 and res[-2] == '\n' and res[-1] in '>>>>>' and c == '>':
                # Concatenate gt signs for nested blockquotes
                res[-1] = res[-1] + c
            elif len(res) > 1 and res[-2] == '\n' and res[-1] in '``' and c == '`':
                # Concatenate backquotes signs for fenced code
                res[-1] = res[-1] + c
            elif res[-1][-1] in '*_' and tok == '' and c in '*_':
                # Concatenate signs for em & strong styles
                res[-1] = res[-1] + c
            elif len(res) > 1 and res[-2] == '\n' and res[-1] in '-*+':
                # Normalize sign for ul and add empty space when no indent
                del res[-1]
                res += ['', '-*+', tok.lstrip(), c]
                tok = ''
            elif len(res) > 2 and res[-3] == '\n' and res[-2] == len(res[-2]) * ' ' and res[-1] in '-*+':
                # Normalize sign for ul
                del res[-1]
                res += ['-*+', tok.lstrip(), c]
                tok = ''
            elif len(res) > 2 and res[-1] == '\n' and len(tok) != len(tok.lstrip(' ')) and tok.lstrip(' '):
                # Isolate spaces
                t = tok.lstrip(' ')
                nb_sp = len(tok) - len(t)
                res += [nb_sp * ' ', t, c]
                tok = ''
            elif len(res) > 2 and res[-3] == '\n' and res[-2].lstrip(' ').isdigit() and res[-1] == '.':
                # Isolate spaces before ol
                dgts = res[-2].lstrip(' ')
                nb_sp = len(res[-2]) - len(dgts)
                del res[-2:]
                res += [nb_sp * ' ', f"{dgts}.", tok.lstrip(), c]
                tok = ''
            else:
                if tok:
                    res.append(tok)
                    tok = ''
                res.append(c)
        elif tok and tok[-1] in '#' and tok[0] in '#' and c not in '#':
            # Concatenate atx style heading
            res.append(tok)
            tok = ''
        else:
            tok += c
        i += 1
    return res


def emit_html(toks: list, start = 2, stack = ['']):
    """."""
    res = ''
    i = start
    while i < len(toks):
        context = stack[-1]
        x, y, z = toks[i-2], toks[i-1], toks[i]
        tk = f'\\n' if toks[i] == '\n' else toks[i]
        print(f"{i:2} | {'/'.join(stack):20} | {tk}")
        if not context:
            pass
        elif context == 'p':
            if y == '\n' and z == '\n':
                return i+1, res
            elif y == '\n' and z == len(toks[i]) * '#':
                return i, res
            elif y == '\n' and z in '>>>>>>' and len(stack) > 1 and stack[-2] in '>>>>>>':
                return i, res
        elif context in '>>>>>>':
            if i > 0 and y == '\n' and (z == context[:-1] or z[0] != '>'):
               return i+1, res
        elif context == 'indented':
            if i > 0 and y == '\n' and z != '    ':
                return i, res
        elif context == 'fenced':
            if i > 0 and y == '\n' and (z == '```' or z == '~~~'):
                return i+1, res
        elif context[:2] == 'ul':
            if x == '\n' and y == len(y) * ' ' and z == '-*+' and len(y) < int(context[2:]):
                return i, res
            elif x == '\n' and y == '\n' and z and z[0] != ' ':
                return i, res
        elif context[:2] == 'ol':
            if x == '\n' and y == len(y) * ' ' and z[-1] == '.' and len(y) < int(context[2:]):
                return i, res
            elif x == '\n' and y == '\n' and z and z[0] != ' ':
                return i, res
        elif context == 'li':
            if x == '\n' and y == len(y) * ' ' and z == '-*+' and len(y) <= int(stack[-2][2:]):
                return i, res
            elif x == '\n' and y == len(y) * ' ' and z[-1] == '.' and len(y) <= int(stack[-2][2:]):
                return i, res
            elif x == '\n' and y == '\n' and z and z[0] != ' ':
                return i, res
        elif context[0] == 'h':
            if z == '\n':
                return i, res
        elif context == 'code':
            if z == '`':
                return i+1, res
        elif context == 'link_text':
            if z == ']':
                return i+1, res
        elif context == 'link_url':
            if z == ')':
                return i+1, res
        elif context == 'em':
            if z in '*_':
                return i+1, res
        elif context == 'strong':
            if z.replace('_', '*') == '**':
                return i+1, res
        elif context == 'em&strong':
            if z.replace('_', '*') == '***':
                return i+1, res

        if i == 0 and toks[0] == '\n':
            i += 1
        elif y == '\n' and z and z == len(z) * '#':
            hx = f'h{len(z)}'
            i, r = emit_html(toks, i+1, stack + [hx])
            res += f'\n<{hx}>{r}</{hx}>'
        elif y == '\n' and (z == '```' or z == '~~~'):
            if i < len(toks) -1 and toks[i+1] != '\n':
                i, r = emit_html(toks, i+2, stack + ['fenced'])
            else:
                i, r = emit_html(toks, i+1, stack + ['fenced'])
            res += f'\n<pre><code>{r}</code></pre>'
        elif z == '[':
            i, r1 = emit_html(toks, i+1, stack + ['link_text'])
            i, r2 = emit_html(toks, i+1, stack + ['link_url'])
            res += f'<a href="{r2}">{r1}</a>'
        elif z == '`':
            i, r = emit_html(toks, i+1, stack + ['code'])
            res += f'<code>{r}</code>'
        elif y != '\n' and z and z in '*_':
            i, r = emit_html(toks, i+1, stack + ['em'])
            res += f'<em>{r}</em>'
        elif y != '\n' and z.replace('_', '*') == '**':
            i, r = emit_html(toks, i+1, stack + ['strong'])
            res += f'<strong>{r}</strong>'
        elif y != '\n' and z.replace('_', '*') == '***':
            i, r = emit_html(toks, i+1, stack + ['em&strong'])
            res += f'<em><strong>{r}</strong></em>'
        elif context[:2] == 'ul' and x == '\n' and y == len(y) * ' ' and z == '-*+':
            i, r = emit_html(toks, i+1, stack + ['li'])
            res += f'\n<li>{r.rstrip("\n")}</li>'
        elif context[:2] == 'ol' and x == '\n' and y == len(y) * ' ' and z[-1] == '.':
            i, r = emit_html(toks, i+1, stack + ['li'])
            res += f'\n<li>{r.rstrip("\n")}</li>'
        elif x == '\n' and y == len(y) * ' ' and z == '-*+':
            i, r = emit_html(toks, i, stack + [f'ul{len(toks[i-1])}'])
            res += f'\n<ul>{r}\n</ul>'
        elif x == '\n' and y == len(y) * ' '  and z[-1] == '.':
            i, r = emit_html(toks, i, stack + [f'ol{len(y)}'])
            res += f'\n<ol>{r}\n</ol>'
        elif context != '>' and y == '\n' and z == '>':
            if i < len(toks) - 1:
                toks[i+1] = toks[i+1].lstrip()
            i, r = emit_html(toks, i+1, stack + ['>'])
            res += f'\n<blockquote>{r}\n</blockquote>'
        elif context in '>>>>>' and y == '\n' and z == context + '>':
            if i < len(toks) - 1:
                toks[i+1] = toks[i+1].lstrip()
            i, r = emit_html(toks, i, stack + [toks[i]])
            res += f'\n<blockquote>{r}\n</blockquote>'
        elif context in '>>>>>' and toks[i-1] == '\n' and toks[i] == '    ':
            i, r = emit_html(toks, i+1, stack + ['indented'])
            res += f'\n<pre><code>{r}</code></pre>'
        elif context == 'pre&code' and y == '\n' and z == '    ':
            i += 1
        elif context and context[:2] in ['ul', 'ol'] and z == len(z) * ' ':
            i += 1
        elif context and context[:2] not in ['ul', 'ol'] and context not in '>>>>>':
            res += z
            i += 1
        else:
            if z == '' or z == '\n':
                i += 1
            else:
                i, r = emit_html(toks, i, stack + ['p'])
                res += f'\n<p>{r.rstrip("\n")}</p>'
    return i, res


