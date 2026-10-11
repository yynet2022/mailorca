#

all:
	@echo e.g.
	@echo "# python runserver.py"

check:
	-ruff check *.py src/ tests/
	-ruff format --check *.py src/ tests/
	-mypy *.py src/ tests/
	-python -m compileall *.py src/ tests/

test:
	pytest -q

clean:
	find . -type d -name __pycache__ | xargs rm -rf

distclean: clean
clobber: distclean
	rm -rf .mypy_cache .pytest_cache .ruff_cache
