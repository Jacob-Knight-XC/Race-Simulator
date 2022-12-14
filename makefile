help:
	echo target: tests clean_race_predictor clean_test clean zip

clean_race_predictor:
	rm -rf race_predictor/__pycache__
	rm -rf race_predictor/.vscode
	rm -rf race_predictor/race_predictor/.vscode
	rm -rf race_predictor/race_predictor/__pycache__
	rm -rf race_predictor/race_predictor/spiders/__pycache__
	find race_predictor -name '*~' -delete
	find race_predictor/race_predictor -name '*~' -delete
	find race_predictor/race_predictor/spiders -name '*~' -delete

clean_user_interface:
	rm -rf race_predictor/user_interface/__pycache__
	rm -rf race_predictor/user_interface/pages/__pycache__
	find race_predictor/user_interface -name '*~' -delete
	find race_predictor/user_interface/pages -name '*~' -delete

clean: clean_race_predictor clean_user_interface
	find . -name racepredictor.zip -delete 
	rm -rf __pycache__
	rm -rf .gitattributes
	rm -rf .vscode
	rm -rf Race-Predictor.code-workspace
	find . -name '*~' -delete

zip: clean
	zip -r xcracesimulator.zip race_predictor Makefile