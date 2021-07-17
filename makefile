
SRC_DIR = ./pdfsyntax
TST_DIR = ./tests/

clean:
	rm -rf $(SRC_DIR)/__pycache__
	rm -rf $(TST_DIR)/__pycache__

test:
	python3 -m unittest discover $(TST_DIR)

build:
	python3 -m build

upload:
	python3 -m twine upload dist/*

.PHONY: clean test build upload

