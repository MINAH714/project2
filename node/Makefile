.PHONY: build run stop start restart logs ps img rm rmi clean

APP_NAME = my-nodejs-web
PORT = 3000

build:
	docker build -t $(APP_NAME) .

run: 
	build
	docker run -it -d -p $(PORT):$(PORT) --name $(APP_NAME) $(APP_NAME)

exec:
	docker exec -it $(APP_NAME) /bin/bash

start:
	docker start $(APP_NAME)

stop:
	docker stop $(APP_NAME)

restart: 
	stop run

logs:
	docker logs -f $(APP_NAME)

ps:
	docker ps -a

img:
	docker images

rm:
	docker rm -f $(docker ps -aq) || true

rmi:
	docker rmi -f $(docker images -q) || true

clean: 
	rm rmi

help:
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commands:"
	@echo "  build    - Build the Docker image."
	@echo "  run      - Build and run the Docker container."
	@echo "  exec     - Exec into the running container."
	@echo "  start    - Start the stopped container."
	@echo "  stop     - Stop the running container."
	@echo "  restart  - Restart the container."
	@echo "  logs     - Tail logs for the container."
	@echo "  ps       - List all Docker containers."
	@echo "  img      - List all Docker images."
	@echo "  rm       - Remove all stopped containers."
	@echo "  rmi      - Remove all Docker images."
	@echo "  clean    - Remove all containers and images."
	@echo "  help     - Show this help message."