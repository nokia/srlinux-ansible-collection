# SR Linux Ansible Collection

Ansible Collection to manage Nokia SR Linux devices. Documentation is provided at <https://learn.srlinux.dev/ansible/collection/>

## Dev setup

Start with cloning the repo:

```bash
git clone git@github.com:nokia/srlinux-ansible-collection.git
cd srlinux-ansible-collection
```

Deploy the lab to support the tests:

```bash
./run.sh deploy-lab
```

Run the automated suite of tests to make sure nothing is missing. This will also prepare a dev environment

```bash
./run.sh test
```

To validate that the code passes Ansible's sanity check, run:

```bash
./run.sh sanity-test
```
