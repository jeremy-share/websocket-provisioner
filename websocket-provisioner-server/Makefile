docker-build:
	docker compose build --pull

up:
	docker compose up -d

down:
	docker compose down

client-list:
	./bin/development/clients-txt.sh

client-run:
	./bin/development/client-run.sh

client-ping:
	curl --request GET --header 'Content-Type: application/json' http://127.0.0.1/clients/ping

client-refresh:
	curl --request GET --header 'Content-Type: application/json' http://127.0.0.1/clients/refresh
