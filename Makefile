export APP_NAME=slowish

# clean out potentially stale pyc files
.PHONY: clean
clean:
	@find . -name "*.pyc" -exec rm {} \;

distclean: clean
	rm -f test_project/db.sqlite3

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
# reset database (and apply migrations)
#
.PHONY: reset
reset: check-venv createdb
	./manage.py migrate

#
# unit tests
#

.PHONY: test
test: check-venv clean
	python -Wall ./manage.py test --keepdb

#
# Drop and recreate databases
#

DATABASE_HOST ?= ''
DATABASE_PORT ?= 5432
DATABASE_NAME ?= ${APP_NAME}
DATABASE_USER ?= ${USER}
DATABASE_PASSWORD ?= ''

.PHONY: reset
createdb: check-venv
	# Testing DB
	-@ PGHOST=${DATABASE_HOST} PGPORT=${DATABASE_PORT} \
	  PGUSER=${DATABASE_USER} PGPASSWORD=${DATABASE_PASSWORD} \
	  psql -c 'drop database ${DATABASE_NAME}_test;'
	@ PGHOST=${DATABASE_HOST} PGPORT=${DATABASE_PORT} \
	  PGNAME=${DATABASE_NAME} PGUSER=${DATABASE_USER} \
	  PGPASSWORD=${DATABASE_PASSWORD} \
	  psql -c 'create database ${DATABASE_NAME}_test;'
	  # Runserver DB
	-@ PGHOST=${DATABASE_HOST} PGPORT=${DATABASE_PORT} \
	  PGUSER=${DATABASE_USER} PGPASSWORD=${DATABASE_PASSWORD} \
	  psql -c 'drop database ${DATABASE_NAME};'
	@ PGHOST=${DATABASE_HOST} PGPORT=${DATABASE_PORT} \
	  PGNAME=${DATABASE_NAME} PGUSER=${DATABASE_USER} \
	  PGPASSWORD=${DATABASE_PASSWORD} \
	  psql -c 'create database ${DATABASE_NAME};'

#
# code coverage
#

COVERAGE_ARGS=--source=slowish
.PHONY: coverage
coverage: check-venv
	coverage erase
	-coverage run $(COVERAGE_ARGS) ./manage.py test --keepdb
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

	coverage erase
	@echo "travis_fold:start:test"
	coverage run $(COVERAGE_ARGS) ./manage.py test --keepdb
	@echo "travis_fold:end:test"

	@echo "travis_fold:start:coverage"
	coverage report
	coverage html
	@echo "travis_fold:end:coverage"

develop-%: check-venv
	cd ../$*; python setup.py develop -N
