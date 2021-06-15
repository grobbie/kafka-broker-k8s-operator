# Kafka Broker for k8s juju demo charm using opi toolkit for Juju configuration autowiring

## What is this?
This is a kafka broker charm that uses the configuration autowiring functionality of the `OpI` Juju charm library. The library automatically wires changes to [juju relations](https://juju.is/docs/sdk/relations) into your charmed application's configuration files.

## Run me
To run this charm and see it working, follow the steps below:

```sh
# install the stuff
snap install juju --classic
snap install charmcraft
snap install microk8s --classic
sudo usermod -aG microk8s $(whoami)
su - $(whoami)
microk8s status --wait-ready
microk8s enable dns storage
juju bootstrap microk8s micro
juju add-model kafka
```

```sh
# get this code
git clone https://github.com/grobbie/kafka-broker-k8s-operator.git
pushd kafka-broker-k8s-operator
charmcraft build
juju deploy ./kafka-broker.charm --resource application-image=ubuntu:20.04 -n 3
popd
```

```sh
juju deploy zookeeper-k8s -n 3
```

```sh
juju add-relation zookeeper-k8s kafka-broker
```
## Roadmap
- Currently this charm doesn't support `juju actions`. When it does, it'll be much more powerful.
- Not all server.properties have been configured yet
- Still to expose a client interface