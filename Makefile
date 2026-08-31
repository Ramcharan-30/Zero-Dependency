.PHONY: run test build clean

run:
	python3 zero_shrink.py

test:
	python3 -m unittest tests/test_zero_shrink.py

build:
	python3 build.py

clean:
	find . -name "*.zshrink" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
