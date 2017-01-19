full-test: test

test:
	pytest --cov-report term-missing --cov=silver_payu tests/

run:
	echo "TBA"

build:
	echo "No need to build someting"

lint:
	echo "TBA"

.PHONY: test full-test build lint run
