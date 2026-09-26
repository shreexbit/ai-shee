PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
REPOSITORY_PATH ?= test_repo

.PHONY: setup run test clean

setup:
	$(PIP) install -r requirements.txt

run:
	PYTHONPATH=src $(PYTHON) src/main.py

test:
	cd $(REPOSITORY_PATH) && $(PYTHON) -m pytest

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.ai-shee-backup" -delete