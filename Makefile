.PHONY: install-dev docs

install:
	uv sync --extra svg

install-dev:
	uv sync --group dev --extra pyside svg

run:
	uv run sh ./frame_stamp/bin/open_viewer.sh


docs: install-dev
	uv run sphinx-build -b html -c docs docs frame-stamp-docs

