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

ps:
	vagrant status --machine-readable | awk -F, '$3 == "state" {print $2 ": " $4}'

ssh:
	make box-ssh

box-ssh:
	vagrant ssh machine1

box-service-logs:
	vagrant ssh machine1 --command "sudo journalctl -u app-client -n 50 --no-pager"

box-service-logs-follow:
	vagrant ssh machine1 --command "sudo journalctl -u app-client -n 50 -f"

box-service-file:
	vagrant ssh machine1 --command "cat /etc/systemd/system/app-client.service"

box-details:
	vagrant ssh machine1 --command 'while [ ! -f /details.txt ]; do sleep 0.1; done; watch -n 0.1 cat /details.txt'

