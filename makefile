
SRC_DIR = ./pdfsyntax
TST_DIR = ./tests
EGG_DIR = ./pdfsyntax.egg-info
BLD_DIR = ./dist

clean:
	rm -rf $(SRC_DIR)/__pycache__
	rm -rf $(TST_DIR)/__pycache__
	rm -rf $(EGG_DIR)
	rm -rf $(BLD_DIR)

test:
	python3 -m unittest discover $(TST_DIR) -v

build:
	python3 -m build

upload:
	python3 -m twine upload dist/*

inspect:
	python3 -m pdfsyntax inspect samples/simple_text_string.pdf > docs/simple_text_string.html

.PHONY: clean test build upload

