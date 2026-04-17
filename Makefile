.PHONY: install-backend install-frontend run-backend run-frontend test build-frontend docker-up docker-down

install-backend:
	pip install -r backend/requirements.txt

install-frontend:
	cd frontend && npm install

run-backend:
	python backend/main.py

run-frontend:
	cd frontend && npm run dev

test:
	pytest

build-frontend:
	cd frontend && npm run build

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down
