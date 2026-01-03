#

all:
	@echo e.g.
	@echo "# python runserver.py"

check:
	-flake8 *.py src/ tests/
	-isort --check *.py src/ tests/
	-black --check *.py src/ tests/ | cat
	-mypy *.py src/ tests/

test:
	pytest

clean:
	find . -type d -name __pycache__ | xargs rm -rf

distclean: clean
clobber: distclean
	rm -rf .mypy_cache .pytest_cache
