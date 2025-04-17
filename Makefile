lint:
	pylint src

format:
	black src

check:
	make format
	make lint

# Use this in the terminal, like npm scripts, or use the tasks.json:
# make lint
# make format
# make check
