# Simple Makefile for some common tasks.
.PHONY: test dist upload

clean:
	find . -name "*.pyc" |xargs rm || true
	rm -r dist || true
	rm -r build || true
	rm -r *.egg-info || true
	rm -r store || true
	rm tiddlyweb.log || true

test:
	py.test -x test

test_with_coverage:
	py.test test --cov tiddlywebplugins --cov-report term-missing

pep8:
	pep8 --max-line-length=120 test tiddlywebplugins

install:
	python setup.py install

install_dev:
	pip install -e .[testing,coverage,style]

dist:
	python setup.py sdist

release: clean pypi

pypi:
	python setup.py sdist upload
