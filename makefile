help:
	@echo "targets: tests clean zip"

tests:
	cd Source-Code/User-Interface && python3 -m pytest ../../tests -q || \
		python3 ../../tests/test_race_algorithm.py

clean_user_interface:
	rm -rf Source-Code/User-Interface/__pycache__
	rm -rf Source-Code/User-Interface/pages/__pycache__
	find Source-Code/User-Interface -name '*~' -delete
	find Source-Code/User-Interface/pages -name '*~' -delete

clean_web_scraper:
	rm -rf Source-Code/Web-Scraper/__pycache__
	rm -rf Source-Code/Web-Scraper/spiders/__pycache__
	find Source-Code/Web-Scraper -name '*~' -delete

clean: clean_user_interface clean_web_scraper
	find . -name 'xcracesimulator.zip' -delete
	rm -rf __pycache__
	find . -name '*~' -delete

zip: clean
	zip -r xcracesimulator.zip Source-Code README.md makefile report.pdf requirements.txt
