
.PHONY: venv install run-listening run-orchestrator test

venv:
	python -m venv .venv

install: venv
	. .venv/bin/activate && pip install -r requirements.txt

run-listening:
	. .venv/bin/activate && uvicorn apps.listening_channel.app.main:app --reload --port 7001

run-orchestrator:
	. .venv/bin/activate && uvicorn apps.orchestrator.app.main:app --reload --port 7002

test:
	. .venv/bin/activate && pytest -q
