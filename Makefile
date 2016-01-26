# clean out potentially stale pyc files
.PHONY: clean
clean:
	@find . -name "*.pyc" -exec rm {} \;

# check that virtualenv is enabled
.PHONY: check-venv
check-venv:
ifndef VIRTUAL_ENV
	$(error VIRTUAL_ENV is undefined, try "workon" command)
endif

# Install pip requirements.txt file
.PHONY: reqs
reqs: check-venv
	pip install --upgrade -r test_project/requirements.txt

PEP8_OPTS=--repeat --exclude=migrations,south_migrations,js,doc --show-source
.PHONY: pep8
pep8:
	pep8 $(PEP8_OPTS) .

#
# flake8
#

FLAKE8_OPTS = --max-complexity 10 --exclude='doc,migrations,south_migrations'
.PHONY: flake8
flake8: check-venv
	flake8 $(FLAKE8_OPTS) .

#
# unit tests
#

.PHONY: test
test: check-venv clean
	python -Wall ./manage.py test

#
# code coverage
#

COVERAGE_ARGS=--source=slowish
.PHONY: coverage
coverage: check-venv
	coverage erase
	-coverage run $(COVERAGE_ARGS) ./manage.py test
	coverage report
	coverage html
	@echo "See ./htmlcov/index.html for coverage report"

#
# testing within Travis
#

.PHONY: travis-tests
travis-tests: check-venv
	@echo "travis_fold:start:flake8"
	make flake8
	@echo "travis_fold:end:flake8"

	@echo "travis_fold:start:pip_freeze"
	pip freeze -l
	@echo "travis_fold:end:pip_freeze"

	@echo "travis_fold:start:test"
	make test
	@echo "travis_fold:end:test"

develop-%: check-venv
	cd ../$*; python setup.py develop -N
