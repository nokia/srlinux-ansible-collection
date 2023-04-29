#!/usr/bin/env bash
# Copyright 2023 Nokia
# Licensed under the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause


set -o errexit
set -o pipefail

# lab node name
NODE_NAME="clab-ansible-srl"

# Directory where the scripts are located.
SCRIPTS_DIR="scripts"

# Directory where the tests are located.
TESTS_DIR="$(pwd)/tests"

# -----------------------------------------------------------------------------
# Helper functions start with _ and aren't listed in this script's help menu.
# -----------------------------------------------------------------------------

# Change to the tests directory only if we're not already there.
function _cdTests() {
  if [ "$(pwd)" != "${TESTS_DIR}" ]; then
    cd "${TESTS_DIR}"
  fi
}

# -----------------------------------------------------------------------------
# Install functions.
# -----------------------------------------------------------------------------

# Install containerlab.
# To install a specific version, pass a version (without v prefix).
function install-containerlab {
  if [ -z "$1" ]; then
    echo "Installing latest containerlab version"
    bash -c "$(curl -sL https://get.containerlab.dev)"
  else
    echo "Installing containerlab version $1"
    bash -c "$(curl -sL https://get.containerlab.dev)" -- -v "$1"
  fi
}

# Install a local collection.
function install-local-collection {
  ansible-galaxy collection install --force ..
}

function remove-local-collection {
  rm -rf ~/.ansible/collections/ansible_collections/nokia
}

# Install a netcommon dependency in case ansible-core is installed.
function install-netcommon {
  ansible-galaxy collection install --force ansible.netcommon:==4.1.0
}

# Deploy test lab.
function deploy-lab {
  cd ${SCRIPTS_DIR}
  sudo -E containerlab deploy -c
  # generate a checkpoint named "initial" that we can revert to to guarantee a clean state
  docker exec ${NODE_NAME} sr_cli /tools system configuration generate-checkpoint name initial
}

# Prepare local dev environment by setting the symlink to the collection.
function prepare-dev-env {
  # setup the symlink for ansible to resolve collection paths
  rm -f /tmp/srl_ansible_dev/ansible_collections/nokia/srlinux
  mkdir -p /tmp/srl_ansible_dev/ansible_collections/nokia
  ln -s "$(pwd)" /tmp/srl_ansible_dev/ansible_collections/nokia/srlinux

  # setup .env file for python to resolve imports
  echo "PYTHONPATH=$(realpath ~)/.ansible/collections:/tmp/srl_ansible_dev" > .env
}

# revert to initial checkpoint to guarantee the node initial state
function revert-to-checkpoint {
  # revert to the checkpoint named "initial" to guarantee a clean state
  docker exec ${NODE_NAME} sr_cli /tools system configuration checkpoint initial revert
}

# copy sanity ignore files from ignore-2.10.txt to all other supported ansible versions
function copy-sanity-ignore {
  _cdTests
  cd sanity
  for version in 2.11 2.12 2.13 2.14; do
    cp ignore-2.10.txt ignore-${version}.txt
  done
}

# -----------------------------------------------------------------------------
# Test functions.
# -----------------------------------------------------------------------------

function test-auth-fail {
  _cdTests
  ansible-playbook playbooks/auth-fail.yml "$@"
}

function test-config-backup {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/backup-cfg.yml "$@"
}

function test-tls-fail {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/tls-missed-check-fail.yml "$@"
}

function test-tls-skip {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/tls-skipped-check.yml "$@"
}

function test-get-container {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/get-container.yml "$@"
}

function test-get-multiple-paths {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/get-multiple-paths.yml "$@"
}

function test-get-oc-container {
  _cdTests
  ansible-playbook playbooks/get-oc-container.yml "$@"
}

function test-get-wrong-path {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/get-wrong-path.yml "$@"
}

function test-backup-cfg {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/backup-cfg.yml "$@"
}

function test-cli-show-version {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/cli-show-version.yml "$@"
}

function test-cli-wrong-cmd {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/cli-wrong-cmd.yml "$@"
}

function test-set-check-mode {
  _cdTests
  revert-to-checkpoint

  # file to store the output of the playbook so we can grep it and test diff mode
  OUT_LOG=/tmp/srl-ansible-set-check-mode.log
  rm -f ${OUT_LOG}

  ansible-playbook playbooks/set-check.yml "$@" | tee ${OUT_LOG}

  # ensure that diff was printed
  grep -q "+             contact \"Some contact\"" ${OUT_LOG}
}

function test-set-leaves {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/set-leaves.yml "$@"
}

function test-set-wrong-value {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/set-wrong-value.yml "$@"
}

function test-set-multiple-paths {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/set-multiple-paths.yml "$@"
}

function test-set-oc-leaf {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/set-oc-leaf.yml "$@"
}

function test-set-tools {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/set-tools.yml "$@"
}

function test-delete-leaves {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/delete-leaves.yml "$@"
}

function test-set-idempotent {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/set-idempotent.yml "$@"
}

function test-replace-full-congig {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/replace-full-cfg.yml "$@"
}

function test-validate {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/validate.yml "$@"
}

function test-oc-validate {
  _cdTests
  revert-to-checkpoint
  ansible-playbook playbooks/oc-validate.yml "$@"
}

# Shouldn't be called directly, use test or ci-test instead.
# Meant to define the collection of tests to run.
function _run-tests {
  test-auth-fail "$@"
  test-get-container "$@"
  test-config-backup "$@"
  test-get-wrong-path "$@"
  test-cli-show-version "$@"
  test-cli-wrong-cmd "$@"
  test-tls-fail "$@"
  test-tls-skip "$@"
  test-set-check-mode "$@"
  test-set-leaves "$@"
  test-set-wrong-value "$@"
  test-set-multiple-paths "$@"
  test-set-tools "$@"
  test-delete-leaves "$@"
  test-set-idempotent "$@"
  test-replace-full-congig "$@"
  test-get-multiple-paths "$@"

  # OC-related tests
  test-get-oc-container "$@"
  test-set-oc-leaf "$@"
  test-oc-validate "$@"
}

# prepare local dev environment and run tests
# to enable debug, pass -vvvv as an argument
function test {
  prepare-dev-env
  revert-to-checkpoint

  _run-tests "$@"
}

# ci-test is a wrapper for testing in CI which first setups the environment.
function ci-test {
  install-containerlab 0.38.0
  install-local-collection
  deploy-lab

  # at this point we are already in ./tests dir
  # since we changed into it in deploy-lab
  # we use ci-ansible.cfg to make sure default collections paths is used
  ANSIBLE_CONFIG=ci-ansible.cfg _run-tests "$@"
}

# sanity-test runs ansible-test tool with sanity checks.
function sanity-test {
  install-local-collection

  cd ~/.ansible/collections/ansible_collections/nokia/srlinux
  ansible-test sanity --docker default -v "$@"

  remove-local-collection
}

# -----------------------------------------------------------------------------
# Publish functions.
# -----------------------------------------------------------------------------

function build-collection {
  # cleanup
  rm -f nokia-srlinux-*.tar.gz
  # build the collection
  ansible-galaxy collection build --force
}

function publish-collection {
  # build the collection
  build-collection
  ansible-galaxy collection publish -v --token $(cat apikey) $(ls -1 nokia-srlinux-*.tar.gz)
}

# -----------------------------------------------------------------------------
# Bash runner functions.
# -----------------------------------------------------------------------------
function help {
  printf "%s <task> [args]\n\nTasks:\n" "${0}"

  compgen -A function | grep -v "^_" | cat -n

  printf "\nExtended help:\n  Each task has comments for general usage\n"
}

# This idea is heavily inspired by: https://github.com/adriancooney/Taskfile
TIMEFORMAT=$'\nTask completed in %3lR'
time "${@:-help}"