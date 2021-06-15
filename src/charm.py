#!/usr/bin/env python3
#   Copyright 2021 Canonical, Ltd.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# Learn more at: https://juju.is/docs/sdk
import logging
from ops.main import main
from ops.model import ActiveStatus,MaintenanceStatus

from charmlib.ConfigManagerBase import ConfigManagerBase

logger = logging.getLogger(__name__)

SERVICE_NAME = "kafka-broker"


class KafkaBrokerCharm(ConfigManagerBase):
    """Charm the service."""

    _pebble_ready = False

    def __init__(self, *args):
        """CTOR"""
        super().__init__(*args)
        self.framework.observe(self.on.kafka_broker_pebble_ready,
                               self._on_application_pebble_ready)
        self.evt_config_changed += self._on_config_rewritten

    def _on_application_pebble_ready(self, event):
        """This method is executed when the pebble_ready event fires"""
        config_file = ("#!/bin/bash\n"
        "if [ ! -f /opt/kafka/installed ]; then\n"
        "dpkg --configure -a\n"
        "apt-get update\n"
        "DEBIAN_FRONTEND=noninteractive apt-get install wget openjdk-8-jre-headless tar gzip -y\n"
        "wget -P /tmp 'https://downloads.apache.org/kafka/2.8.0/kafka_2.12-2.8.0.tgz'\n"
        "mkdir -p /opt/kafka\n"
        "pushd /opt/kafka; tar xzf /tmp/kafka_2.12-2.8.0.tgz; popd\n"
        "touch /opt/kafka/installed\n"
        "fi\n"
        "/opt/kafka/kafka_2.12-2.8.0/bin/kafka-server-start.sh /opt/kafka/config/server.properties\n")
        event.workload.push("/opt/kafka/run.sh", config_file, make_dirs=True, permissions=0o755)
        self._restart_application("App Initialized")

    def _on_config_rewritten(self, sender, eargs):
        self._restart_application("Configuration changed")

    def _kafka_layer(self) -> dict:
        """Returns Pebble configuration layer"""
        return {
            "summary": "kafka Broker layer",
            "description": "pebble config layer for kafka broker",
            "services": {
                "kafka-broker": {
                    "override": "replace",
                    "command": "/opt/kafka/run.sh",
                    "startup": "enabled"
                }
            },
        }

    def _restart_application(self, reason):
        """This method restarts the application in the workload container"""
        self.unit.status = MaintenanceStatus(
            f'Configuring the application: {reason}')
        application_container = self.unit.get_container(SERVICE_NAME)
        application_container.add_layer(
            SERVICE_NAME, self._kafka_layer(), combine=True)

        log_start = True
        if application_container.get_service(SERVICE_NAME).is_running():
            logger.info(
                "Restarting the application to apply "
                "configuration changes"
            )
            log_start = False
            application_container.stop(SERVICE_NAME)

        if not application_container.get_service(SERVICE_NAME).is_running():
            if log_start is True:
                logger.info("Starting the application")
            application_container.start(SERVICE_NAME)
            logger.debug("Application started")

        self.unit.status = ActiveStatus()


if __name__ == "__main__":
    main(KafkaBrokerCharm)