up: ## Stands up dev environment
	docker-compose -f docker-compose.yml up

upd: ## Stands up dev environment
	docker-compose -f docker-compose.yml up --detach

build: ## Builds dev environment
	docker-compose -f docker-compose.yml build

web: ## Opens web container
	docker-compose -f docker-compose.yml exec web bash -c ". /venv/bin/activate; bash"
