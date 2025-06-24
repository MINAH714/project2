.PHONY: build up down restart logs ps img rm rmi clean push help

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	$(MAKE) down
	$(MAKE) up

logs:
	docker-compose logs -f

ps:
	docker-compose ps

img:
	docker images | grep "minah714/project"

rm:
	docker-compose rm -f || true

rmi:
	docker rmi -f minah714/project3:latest || true

clean:
	$(MAKE) down
	docker system prune -a -f

push:
	docker push minah714/project3:latest

help:
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commands for Docker Compose (Multi-service Management):"
	@echo "  build    - Build Docker images for all services."
	@echo "  up       - Build and start all services in detached mode (-d)."
	@echo "  down     - Stop and remove all services (containers, networks, volumes)."
	@echo "  restart  - Stop, remove, and then rebuild/start all services."
	@echo "  logs     - Tail logs for all services."
	@echo "  ps       - List running containers managed by Docker Compose."
	@echo "  img      - List Docker images specific to this project."
	@echo "  rm       - Remove stopped containers for this project."
	@echo "  rmi      - Remove project-specific Docker images."
	@echo "  clean    - Full cleanup: stop, remove project resources, and global prune."
	@echo "  push     - Push project Docker images to Docker Hub."
	@echo "  help     - Show this help message."
