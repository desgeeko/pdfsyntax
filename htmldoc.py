from pdfsyntax import markdown
import sys


html_header = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="stylesheet" href="pdfsyntax.css">
    <title>PDFSyntax</title>
</head>
'''

filename = sys.argv[1]

f = open(filename, 'r')
md = f.read()

print(f"{html_header}<body>\n<main>\n{markdown.render_html(md)}\n</main>\n</body>")

