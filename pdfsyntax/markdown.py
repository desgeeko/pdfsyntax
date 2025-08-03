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
    _, _, html = emit_html(t)
    return html


def tokenize(md: str) -> list:
    """Split input string and transform some tokens to facilitate further processing."""
    res = [[''], ['']]
    i = 0
    tok = ''
    line = []
    html = False
    while i < len(md):
        c = md[i]
        #print(f"#{tok}# @{c}@")
        if c == '<' or html:
            #
            html = True
            tok += c
            if c == '>' and html:
                html = False
        elif c != '#' and not line and tok and tok == len(tok) * '#':
            # Isolate header level
            line.append(tok)
            tok = '' if c == ' ' else c
        elif c != ' ' and not line and tok and tok == len(tok) * ' ':
            # Isolate consecutive spaces at bol
            if len(tok) >= 4:
                line.append(tok)
            tok = c
        elif c in '-' and line and line[-1][0] in '-' and line[-1] == len(line[-1]) * '-':
            # Concatenate setext underline
            line[-1] = line[-1] + c
        elif c == '`' and line and not tok and line[-1] in '``':
            # Concatenate backquotes signs for fenced code
            line[-1] = line[-1] + c
        elif c in '*_' and line and line[-1][-1] in '*_' and tok == '':
            # Concatenate signs for em & strong styles
            line[-1] = line[-1] + c
        elif c in '![' and checkLinkOrImage(md, i):
            if c == '[':
                t = 'lnk['
            else:
                t = 'img['
                i += 1
            if tok:
                line.append(tok)
                tok = ''
            line.append(t)
            line.append('[')
        elif c in '\n[]()-+.>*_`':
            if tok:
                line.append(tok)
                tok = ''
            line.append(c)
        else:
            tok += c

        if line and line[-1] == '\n':
            del line[-1]
            if line and line[-1] == len(line[-1]) * '=':
                res[-1].insert(0, '#')
            elif line and line[-1] == len(line[-1]) * '-':
                res[-1].insert(0, '##')
            else:
                if not line:
                    line = ['']
                res.append(line)
            line = []
        i += 1
    res.append([''])
    return res


def putLineInContext(stack: list, line: list, list_indent: int):
    """."""
    j = 0
    k = 0
    list_indent = 4 if not list_indent else list_indent
    while j < len(line) and k < len(stack):
        if stack[k][0] == 'u':
            if not line[j]:
                break
            else:
                j -= 1
        elif stack[k] == 'li':
            if not line[j] or line[j] in '-*+':
                if j>0 and len(line[j-1]) < len(stack) / 2 * 4 :
                    break
                else:
                    j -= 1
        elif stack[k] == 'blockquote':
            if line[j] != '>':
                break
        elif stack[k][0] == 'h':
                break
        elif stack[k] == 'fenced':
            if line[j] == '```' or line[j] == '~~~':
                j -= 1
                break
        elif stack[k] == 'indented':
            if line[j] != '    ':
                j -= 1
                break
        #elif stack[k] == 'a':
        #    if line[j-1] == ')':
        #        break
        elif stack[k][0] == 'p':
            if line[j] in ['', '#', '##']:
                break
        else:
            break
        j += 1
        k += 1
    if j > len(line) -1:
        bol = 0
    else:
        bol = j
    keepers = -1 if k >= len(stack) else k
    return (bol, keepers)


def detectNewBlock(tok, prev_tok, stack: list, list_indent: int):
    """."""
    if tok and tok == len(tok) * '#':
        return f'h{len(tok)}', 1
    elif tok and tok == '```' or tok == '~~~':
        return 'fenced', 1
    elif tok and tok == '    ':
        return 'indented', 1
    elif tok and tok in '>':
        return 'blockquote', 1
    elif tok and tok == 'lnk[' and stack[-1] != 'a':
        return 'a', 0
    elif tok and tok == 'img[' and stack[-1] != 'img':
        return 'img', 0
    elif stack and stack[-1][:2] == 'ul' and tok in '-*+':
        return 'li', 1
    elif (not stack or stack[-1][:2] != 'ul') and tok and tok in '*+-':
        return 'ul', 0
    elif not stack and tok:
        return 'p', 0
    else:
        return None, 0


def checkLinkOrImage(md: str, start: int):
    """."""
    obj = False
    url = False
    i = start
    if md[start] == '!' and i+1 < len(md) and md[i+1] == '[':
        i += 1
    while i < len(md):
        if md[i] == '\n':
            return False
        elif md[i-1:i+1] == '](':
            obj = True
        elif md[i] == ')':
            url = True
        if obj and url:
            return True
        i += 1
    return False


def detectNewOrClosingSpan(tok: str, stack: list):
    """."""
    h = [
        ('`',  'code',   '`',  ['p']),
        ('_',  'em',     '_',  ['em', 'p', 'obj']), # or *
        ('__', 'strong', '__', ['p']),# or **
        ('[',  'obj',   ']',   ['a']),
        ('(',  'url',    ')',  ['a']),
    ]
    for opening, element, closing, auths in h:
        if opening == closing and tok == opening:# and element in auths:
            if element not in stack:
                return 'opening', element
            else:
                return 'closing', element
        elif tok == opening:# and element in auths:
            return 'opening', element
        elif tok == closing:# and element in auths:
            return 'closing', element
    return None, None


def html_text(element: str, content):
    """."""
    isBlock = '\n' if element[0] in ['p', 'h', 'b'] else ''
    if element in ['fenced', 'indented']:
        res = f'\n<pre><code>{content}</code></pre>'
    elif element in ['a', 'img']:
        title = f' title="{content["title"]}"' if 'title' in content else ''
        res = f'<{element} href="{content["url"]}"{title}>{content["obj"]}</a>'
    else:
        res = f'{isBlock}<{element}>{content}</{element}>'
    return res


def emit_html(toks: list, lstart = 2, tstart = 0):
    """."""
    accu = ['']
    stack = []
    isLineCtx = True
    i = lstart
    j = tstart
    list_indent = 0
    while i < len(toks) and j <= len(toks[i]):
        print(f'{i:2} {j:2} | {isLineCtx:1} | {".".join(stack):20} | {str(accu[-1])[:40].replace('\n','.')} ')
        line = toks[i]
        if not isLineCtx:
            j, k = putLineInContext(stack, line, list_indent)
            if 0 <= k <= len(stack) - 1:
                if j < 0:
                    i += 1
                else:
                    j = 0
                elt = stack.pop()
                last = accu.pop()
                accu[-1] += html_text(elt, last)
                continue

        tok = line[j] if j < len(line) else ''
        prev_tok = line[j-1] if j > 0 else ''
        tst = None
        node, offset = detectNewBlock(tok, prev_tok, stack, list_indent)
        list_indent = len(prev_tok) if node == 'li' and not list_indent else list_indent
        if not node:
            tst = detectNewOrClosingSpan(tok, stack)

        if node:
            isLineCtx = True
            j += offset
            stack += [node]
            if node in ['a', 'img']:
                accu += [{'url':''}]
            else:
                accu += ['']
        elif tst and tst[0] == 'opening':
            #isLineCtx = True
            j += 1
            stack += [tst[1]]
            accu += ['']
            continue
        elif tst and tst[0] == 'closing':
            j += 1
            elt = stack.pop()
            last = accu.pop()
            if elt == 'obj':
                accu[-1][elt] = last
            elif elt == 'url':
                tmp = last.split('"')
                url = tmp[0]
                if len(tmp) > 1:
                    accu[-1]['title'] = tmp[1]
                    url = url[:-1]
                accu[-1]['url'] += url
            else:
                accu[-1] += html_text(elt, last)
            if elt in ['a', 'img']:
                j -= 1
            continue
        elif stack:
            if stack[-1] not in ['a', 'img']:
                accu[-1] += tok
            j += 1
        else:
            j += 1

        if j >= len(line):
            i += 1
            j = 0
            isLineCtx = False

    return i, j, accu[0]


