ARG BASE_IMAGE=ghcr.io/srl-labs/ansible-core/2.14.10:pypy3.10

FROM ${BASE_IMAGE} as builder

COPY . /work

WORKDIR /work

RUN ansible-galaxy collection install --no-cache ..

FROM ${BASE_IMAGE}

COPY --from=builder /root/.ansible/collections /root/.ansible/collections

WORKDIR /ansible

CMD [ "ansible-playbook" ]