#!/usr/bin/env bash

set -e

SID="${1}"

if [[ -z "${SID}" ]] ; then
  read -r -p "SID=" SID
fi

curl \
  --request PUT \
  --header 'Content-Type: application/json' \
  --data '["git@gitlab.com:jeremy-share/ansible-pull.git", "master"]' \
  "http://127.0.0.1/client/${SID}/run"
