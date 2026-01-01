#

all:
	@echo e.g.
	@echo "# python runserver.py"

check:
	flake8 *.py src/

test:

clean:
	find . -type d -name __pycache__ | xargs rm -rf

distclean: clean
clobber: distclean
