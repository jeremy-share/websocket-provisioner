setup:
	cp ../websocket-provisioner-client-unix/dist/ . -rp

up:
	vagrant up --parallel

re-provision:
	vagrant up --provision

down:
	vagrant destroy --force

cleanup:
	make down || true

up-clean:
	make cleanup
	make up

ssh:
	make box-ssh

box-ssh:
	vagrant ssh machine1

box-service-logs:
	vagrant ssh machine1 --command "sudo journalctl -u websocket-provisioner-client -n 50 --no-pager"

box-service-logs-follow:
	vagrant ssh machine1 --command "sudo journalctl -u websocket-provisioner-client -n 50 -f"
