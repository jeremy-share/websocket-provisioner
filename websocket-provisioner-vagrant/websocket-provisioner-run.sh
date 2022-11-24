#!/usr/bin/env bash

set -e

ARGS=$@

echo "INFO: Running! with ${ARGS}"

REPO=${1}
echo "INFO: REPO=${REPO}"

BRANCH=${2:-"master"}
echo "INFO: BRANCH=${BRANCH}"

# Remove "git@", "https://" from front. i.e. "github.com:jeremysells/something.git"
REPO_NO_PROTOCOL=$(echo "${REPO}" | sed -e "s/^git@//" -e "s/$//" | sed -e "s/^https:\/\///" -e "s/$//")
echo "INFO: REPO_NO_PROTOCOL=${REPO_NO_PROTOCOL}"

# Removing ".git" from end. i.e. "github.com:jeremysells/something"
REPO_NO_SUFFIX=$(echo "${REPO_NO_PROTOCOL}" | sed -e 's/\(\.git\)*$//g')
echo "INFO: REPO_NO_SUFFIX=${REPO_NO_SUFFIX}"

# Changing ":" to be "/" "github.com/jeremysells/something"
REPO_URI_SEGMENT=${REPO_NO_SUFFIX/:/\/}
echo "INFO: REPO_URI_SEGMENT=${REPO_URI_SEGMENT}"

# Changing "github.com/jeremysells/something" to be "github.com"
REPO_HOST=$(echo "${REPO_URI_SEGMENT}" | cut -f1 -d"/")
echo "INFO: REPO_HOST=${REPO_HOST}"

# Trust the repo host
# TODO: Find a more secure way of doing this
ssh -o StrictHostKeyChecking=no "git@${REPO_HOST}"

# Figure out the ansible command
COMMAND="/usr/bin/ansible-pull -U ${REPO} -i 127.0.0.1, --checkout \"${BRANCH}\""

# Run the command
eval "${COMMAND}"

# Setup the cron
echo "* * * * * root ${COMMAND}" > /etc/cron.d/websocket-provisioner
