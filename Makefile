.ONESHELL:
.PHONY: docs
.DEFAULT_GOAL: all

DEV ?= 1

all: install lint test cover

debug:
	pip install . --force --no-deps

update:
	wget https://gitlab.com/tzip/tzip/-/raw/master/proposals/tzip-16/metadata-schema.json -O pytezos/contract/metadata-schema.json
	wget https://gitlab.com/tzip/tzip/-/raw/master/proposals/tzip-16/examples/example-000.json -O tests/metadata/example-000.json
	wget https://gitlab.com/tzip/tzip/-/raw/master/proposals/tzip-16/examples/example-001.json -O tests/metadata/example-001.json
	wget https://gitlab.com/tzip/tzip/-/raw/master/proposals/tzip-16/examples/example-002.json -O tests/metadata/example-002.json
	wget https://gitlab.com/tzip/tzip/-/raw/master/proposals/tzip-16/examples/example-003.json -O tests/metadata/example-003.json
	wget https://gitlab.com/tzip/tzip/-/raw/master/proposals/tzip-16/examples/example-004.json -O tests/metadata/example-004.json
	wget https://gitlab.com/tzip/tzip/-/raw/master/proposals/tzip-16/examples/example-005.json -O tests/metadata/example-005.json

install:
	git submodule update --init
	poetry install `if [ "${DEV}" = "0" ]; then echo "--no-dev"; fi`

notebook:
	poetry run jupyter notebook

isort:
	poetry run isort src

pylint:
	poetry run pylint src || poetry run pylint-exit $$?

mypy:
	poetry run mypy src

lint: isort pylint mypy

test_contract:
	poetry run pytest --cov-report=term-missing --cov=pytezos --cov-report=xml -v tests/contract_tests

test_dapps:
	poetry run pytest --cov-report=term-missing --cov=pytezos_dapps --cov-report=xml -v tests/dapps_tests

test_integration:
	poetry run pytest --cov-report=term-missing --cov=pytezos --cov=pytezos_dapps --cov-report=xml -v tests/integration_tests

test_sandbox:
	poetry run pytest --cov-report=term-missing --cov=pytezos --cov-report=xml -v tests/sandbox_tests

test_unit:
	poetry run pytest --cov-report=term-missing --cov=pytezos --cov=pytezos_dapps --cov-report=xml -v tests/unit_tests

test:
	poetry run pytest --cov-report=term-missing --cov=pytezos --cov=pytezos_dapps --cov-report=xml -v tests

cover:
	poetry run diff-cover coverage.xml

build:
	poetry build

docs:
	cd docs && rm -rf ./build && $(MAKE) html

rpc-docs:
	python -m scripts.fetch_docs

release-patch:
	bumpversion patch
	git push --tags
	git push

release-minor:
	bumpversion minor
	git push --tags
	git push

release-major:
	bumpversion major
	git push --tags
	git push