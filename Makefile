SHELL := /bin/bash

VENV := .venv
MKDOCS := $(VENV)/bin/mkdocs

.PHONY: setup serve build clean

setup:
	@if [ ! -f "$(MKDOCS)" ]; then \
		echo "Setting up Python virtual environment..."; \
		python3 -m venv $(VENV); \
		$(VENV)/bin/pip install -r requirements.txt; \
	fi

serve: setup
	$(MKDOCS) serve

build: setup
	$(MKDOCS) build

clean:
	rm -rf site/