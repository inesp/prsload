up: ## Stands up dev environment
	docker compose up

build: ## Builds dev environment
	docker compose build

web: ## Opens web container
	docker compose exec web bash -c ". /venv/bin/activate; bash"
