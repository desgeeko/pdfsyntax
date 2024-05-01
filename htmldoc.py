from pdfsyntax import markdown
import sys


filename = sys.argv[1]

f = open(filename, 'r')
md = f.read()

print(markdown.md2html(md))

