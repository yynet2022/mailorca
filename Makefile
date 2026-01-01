#

all:
	@echo e.g.
	@echo "# python runserver.py"

check:
	flake8 *.py src/
	isort --diff *.py src/
	black --diff *.py src/
	mypy runserver.py

test:

clean:
	find . -type d -name __pycache__ | xargs rm -rf

distclean: clean
clobber: distclean
