.PHONY: venv install-dependencies setup

VENV_DIR ?= venv
PYTHON    ?= python3

venv:
	$(PYTHON) -m venv $(VENV_DIR)

install-dependencies: venv
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install .

setup: venv install-dependencies
	@echo "Environment setup complete. Activate with 'source $(VENV_DIR)/bin/activate'"