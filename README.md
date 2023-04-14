# SR Linux Ansible Collection

## Dev setup

Start with cloning the repo:

```bash
git clone git@github.com:srl-labs/srl-ansible-collection.git
cd srl-ansible-collection
```

Deploy the lab to support the tests:

```bash
./run.sh deploy-lab
```

Run the automated suite of tests to make sure nothing is missing. This will also prepare a dev environment

```bash
./run.sh test
```

To validate that the code passes ansible's sanity check, run:

```bash
./run.sh sanity-test
```
