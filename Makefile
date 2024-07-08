demo-start:
	(cd websocket-provisioner-client-unix && make onefile-build)
	(cd websocket-provisioner-server && make up)
	(cd websocket-provisioner-vagrant && make setup )
	(cd websocket-provisioner-vagrant && make up )
	(cd websocket-provisioner-server && docker compose logs -f)

demo-stop:
	(cd websocket-provisioner-server && make down) || true
	(cd websocket-provisioner-vagrant && make down) || true

demo-client-details-file:
	(cd websocket-provisioner-vagrant && make box-details)

demo-client-list:
	(cd websocket-provisioner-server && make client-list)

demo-client-run:
	(cd websocket-provisioner-server && make client-run)
