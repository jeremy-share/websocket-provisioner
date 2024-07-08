#!/usr/bin/env bash

set -e

SID="${1}"
BRANCH="${2}"

if [[ -z "${SID}" ]] ; then
  read -r -p "SID=" SID
fi

if [[ -z "${BRANCH}" ]] ; then
  read -r -p "BRANCH=" BRANCH
fi

curl \
  --request PUT \
  --header 'Content-Type: application/json' \
  --data "[\"https://gitlab.com/jeremy-share/websocket-provisioner-ansible-pull\", \"${BRANCH}\"]" \
  "http://127.0.0.1/client/${SID}/run"
