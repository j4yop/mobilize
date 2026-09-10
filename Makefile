.PHONY: data test lint clean

data:
	python scripts/build_panel.py

test:
	pytest -q

lint:
	ruff check src tests scripts

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info src/*.egg-info
	find . -name __pycache__ -type d -exec rm -rf {} +
