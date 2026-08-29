.PHONY: install demo clean

install:
	pip install -r requirements.txt

demo:
	# TODO: start ingest, safety worker, and dashboard together,
	# TODO: then play the sample footage from data/samples/
	@echo "not implemented yet — see the three-terminal instructions in readme.md"

clean:
	rm -rf data/chunks/* data/events.db highlights.mp4
	find . -type d -name __pycache__ -exec rm -rf {} +
