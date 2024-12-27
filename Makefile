up: ## Stand up docker containers and start Flask server
	docker compose up

up-redis: ## Stands up redis only in Docker
	docker compose up redis --detach

up-flask-local: ## Stands up flask
	uv run flask --app prsload/app.py --debug run --port 1234

build: ## Builds dev environment
	docker compose build
	uv pip compile pyproject.toml -o requirements.txt

lock-to-requirements:  ## Write requirements.txt from pyproject.toml
	uv pip compile pyproject.toml -o requirements.txt

lint: ## Lint code
	uv run ruff format prsload settings.py
	uv run ruff check --fix prsload settings.py
	uv run mypy prsload
