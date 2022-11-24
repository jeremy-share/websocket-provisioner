demo-start:
	(cd websocket-provisioner-client-unix && make onefile-build)
	(cd websocket-provisioner-server && make up)
	(cd websocket-provisioner-vagrant && make up )
	(cd websocket-provisioner-server && docker-compose logs -f)

demo-stop:
	(cd websocket-provisioner-server && make down) || true
	(cd websocket-provisioner-vagrant && make down) || true
