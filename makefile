
SRC_DIR = ./pdfsyntax
TST_DIR = ./tests
EGG_DIR = ./pdfsyntax.egg-info
BLD_DIR = ./dist
SPL_DIR = ./samples
DOC_DIR = ./docs
MD_DOCS = $(wildcard $(DOC_DIR)/*.md)
HT_DOCS = $(MD_DOCS:.md=.html)
MD_READ = ./README.md
HT_READ = $(DOC_DIR)/README.html

clean:
	rm -rf $(SRC_DIR)/__pycache__
	rm -rf $(TST_DIR)/__pycache__
	rm -rf $(EGG_DIR)
	rm -rf $(BLD_DIR)
	rm -f $(HT_DOCS)
	rm -f docs/README.html

test:
	python3 -m unittest discover $(TST_DIR) -v

build:
	python3 -m build

upload:
	python3 -m twine upload dist/*

inspect:
	python3 -m pdfsyntax inspect $(SPL_DIR)/simple_text_string.pdf > $(DOC_DIR)/simple_text_string.html

doc: $(HT_DOCS)

%.html: %.md
	python3 htmldoc.py $< > $@

readme: $(HT_READ)

$(HT_READ): $(MD_READ)
	python3 htmldoc.py $< > $@

.PHONY: clean test build upload

