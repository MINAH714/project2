# 본인 Docker Hub 아이디로 변경하세요
DOCKERHUB_ID = minah714
IMAGE_NAME = streamlit_project
TAG = latest

build:
	docker build -t $(IMAGE_NAME):$(TAG) .

run:
	docker run -it -d -p 8503:8501 -v C:/Users/kibwa22/project2/docker:/app --name streamlit_project $(IMAGE_NAME):$(TAG)

exec:
	docker exec -it streamlit-app /bin/bash

start:
	docker start streamlit-app

stop:
	docker stop streamlit-app

logs:
	docker logs streamlit-app

ps:
	docker ps -a

img:
	docker images

rm:
	docker rm -f $$(docker ps -aq)

rmi:
	docker rmi -f $$(docker images -q)

login:
	docker login

tag:
	docker tag $(IMAGE_NAME):$(TAG) $(DOCKERHUB_ID)/$(IMAGE_NAME):$(TAG)

push:
	docker push $(DOCKERHUB_ID)/$(IMAGE_NAME):$(TAG)

all: build tag push
