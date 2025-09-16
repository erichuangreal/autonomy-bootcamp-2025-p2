"""
Heartbeat receiving logic.
"""

from pymavlink import mavutil

from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
import logging
from typing import Any


class HeartbeatReceiver:
    """
    HeartbeatReceiver class to send a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> "tuple[True, HeartbeatReceiver] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        try:
            heartbeat_receiver_instance = HeartbeatReceiver(
                cls.__private_key,
                connection,
                local_logger,
            )
            local_logger.info("HeartbeatReceiver created successfully")
            return True, heartbeat_receiver_instance
        except Exception as e:
            local_logger.error(f"Failed to create HeartbeatReceiver: {e}")
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        self.connection = connection
        self.logger = local_logger
        self.state = "Disconnected"
        self.missed_heartbeats = 0
        self.MAX_MISSED_HEARTBEATS = 5
        self.logger.info("HeartbeatReceiver initialized")

    def run(
        self,
    ) -> str:
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        msg = self.connection.recv_match(type="HEARTBEAT", blocking=False, timeout=0.1)

        if msg is not None:
            #  Received heartbeat
            self.logger.info(f"Received HEARTBEAT message: {msg}")

            # Reset missed heartbeat counter
            self.missed_heartbeats = 0
            if self.state != "Connected":
                self.state = "Connected"
                self.logger.info("State changed to Connected")
        else:
            # No heartbeat received
            self.missed_heartbeats += 1
            self.logger.warning(f"Missed heartbeat #{self.missed_heartbeats}")

            # check if we should disconnect
            if self.missed_heartbeats >= self.MAX_MISSED_HEARTBEATS:
                if self.state != "Disconnected":
                    self.state = "Disconnected"
                    self.logger.warning(
                        "State changed to Disconnected - missed 5 consecutive heartbeats"
                    )

        return self.state


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
