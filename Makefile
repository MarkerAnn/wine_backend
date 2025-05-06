lint:
	pylint app

format:
	black src

check:
	make format
	make lint

run-local:
	uvicorn app.main:app --reload --port 8001

# Use this in the terminal, like npm scripts, or use the tasks.json:
# make lint
# make format
# make check
