.PHONY: install-dev docs

install:
	poetry install

install-dev:
	poetry install --with dev

run:
	poetry run sh ./frame_stamp/bin/open_viewer.sh


docs: install-dev
	poetry run sphinx-build -b html -c docs docs frame-stamp-docs

