up: ## Stands up dev environment
	docker compose up

up-detach: ## Stands up dev environment
	docker compose --detach  && docker compose ps

build: ## Builds dev environment
	docker compose build

web: ## Opens web container
	docker compose exec web bash -c ". /venv/bin/activate; bash"
