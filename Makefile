.PHONY: data test lint e2e clean

data:
	python scripts/build_panel.py

test:
	pytest -q

lint:
	ruff check src tests scripts

# Dashboard E2E: builds app/ and runs the Playwright check suite against it.
e2e:
	cd app && npm run test:e2e

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info src/*.egg-info
	find . -name __pycache__ -type d -exec rm -rf {} +
