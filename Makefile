up-prod: ## Stand up docker containers and start Flask server
	docker compose up

up: up-flask-local  ## Run Flask locally

up-flask-local: ## Stands up flask
	uv run flask --app prsload/app.py --debug run --port 1234

build: upgrade-py lock-to-requirements ## Builds dev environment
	docker compose build

upgrade-py:
	uv lock --upgrade

lock-to-requirements:  ## Write requirements.txt from pyproject.toml (includes dev dependencies)
	uv pip compile pyproject.toml -o requirements.txt

lint: ## Lint code
	uv run ruff check --fix .
	uv run black .
	uv run mypy prsload
