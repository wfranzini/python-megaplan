PYTHON=python

release-pypi:
	$(PYTHON) setup.py sdist upload --sign
