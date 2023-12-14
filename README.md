# SR Linux Ansible Collection

Ansible Collection to manage Nokia SR Linux devices. Documentation is provided at <https://learn.srlinux.dev/ansible/collection/>

## Quick start for developers

Start with cloning the repo:

```bash
git clone git@github.com:nokia/srlinux-ansible-collection.git
cd srlinux-ansible-collection
```

Deploy the lab to support the tests:

```bash
./run.sh deploy-lab
```

Run the automated suite of tests to make sure nothing is missing. This will also prepare a dev environment (you have to make sure the venv with ansible is activated or ansible-playbook is in your path):

```bash
./run.sh test
```

To validate that the code passes Ansible's sanity check, run:

```bash
./run.sh sanity-test
```

Note, that the lab uses IXR-6 chassis, which only runs for 5 minutes without a license. This is enough to finish the test suite, but if you want to play with the lab for a longer period, remove the type or provide a license.

### Running individual tests

To run an individual test, first make sure that the local code base is used by ansible. This can be done by running:

```bash
./run.sh prepare-dev-env
```

Then either run one of the provided test playbooks (defined in [run.sh](run.sh)) or run your own:

```bash
./run.sh test-set-leaves
```
