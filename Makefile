PYTHON ?= python
AS_OF ?= 2026-06-15
GENERATED_AT ?= 2026-06-15T12:00:00Z
DEMO_DIR := examples/synthetic_city
OUTPUT_DIR := $(DEMO_DIR)/output

.PHONY: install test validate demo verify privacy clean all

install:
	$(PYTHON) -m pip install -e .

test:
	$(PYTHON) -m unittest discover -s tests -v

validate:
	housing-decision validate \
		--listings $(DEMO_DIR)/listings.csv \
		--preferences $(DEMO_DIR)/preferences.json \
		--as-of $(AS_OF)

demo:
	housing-decision evaluate \
		--listings $(DEMO_DIR)/listings.csv \
		--preferences $(DEMO_DIR)/preferences.json \
		--as-of $(AS_OF) \
		--generated-at $(GENERATED_AT) \
		--output-dir $(OUTPUT_DIR)

verify:
	$(PYTHON) scripts/verify_demo.py

privacy:
	$(PYTHON) scripts/privacy_scan.py

clean:
	rm -rf build dist src/*.egg-info src/housing_decision_kit/__pycache__ tests/__pycache__

all: test privacy demo verify
