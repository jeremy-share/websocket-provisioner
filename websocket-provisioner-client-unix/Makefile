up-5:
	docker compose up --scale websocket-provisioner-client-unix=5

onefile-build:
	docker compose build
	docker compose run websocket-provisioner-client-unix pyinstaller websocket-provisioner-client-unix.py --onefile

onefile-run:
	docker compose -f docker-compose-onefile.yml build
	docker compose -f docker-compose-onefile.yml run --rm websocket-provisioner-client-unix-onefile
