help:
	@echo "targets: tests clean zip"

tests:
	python3 tests/test_race_algorithm.py -v

clean:
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -name '*~' -delete
	find . -name 'xcracesimulator.zip' -delete

zip: clean
	zip -r xcracesimulator.zip app scraper data tests README.md Makefile requirements.txt report.pdf \
		-x 'data/archives/*' '*/__pycache__/*'
