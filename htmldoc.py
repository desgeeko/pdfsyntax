from pdfsyntax import markdown
import sys


HEAD = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="stylesheet" href="pdfsyntax.css">
    <title>PDFSyntax</title>
</head>
'''
HEADER = '''<header>
<a href="https://pdfsyntax.dev"><img src="logo.svg" width="50"/></a>
</header>
'''
FOOTER = '''<footer>
&copy; 2025 <a href="mailto:desgeeko@gmail.com">Martin D.</a> &lt;desgeeko@gmail.com&gt;
</footer>
'''

filename = sys.argv[1]
f = open(filename, 'r')
md = f.read()
main = f"<main>\n{markdown.render_html(md)}\n</main>\n"
print(f"{HEAD}<body>\n{HEADER}{main}{FOOTER}</body>\n</html>")

