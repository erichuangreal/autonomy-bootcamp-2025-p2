"""
Heartbeat sending logic.
"""

from pymavlink import mavutil


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
import logging
from typing import Any


class HeartbeatSender:
    """
    HeartbeatSender class to send a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        logger: logging.Logger,  # Put your own arguments here
    ) -> "tuple[True, HeartbeatSender] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatSender object.
        """
        try:
            instance = cls(cls.__private_key, connection, logger)
            return True, instance
        except Exception as e:
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        logger: logging.Logger,  # Put your own arguments here
    ) -> None:
        assert key is HeartbeatSender.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.logger = logger

    def send_heartbeat(self) -> None:
        """
        Send a MAVLink heartbeat message.
        """
        self.connection.mav.heartbeat_send(
            mavutil.mavlink.MAV_TYPE_GCS,  # Type: GCS
            mavutil.mavlink.MAV_AUTOPILOT_INVALID,  # Autopilot: generic
            0,  # Base mode
            0,  # Custom mode
            mavutil.mavlink.MAV_STATE_ACTIVE,  # System status
        )

    def run(
        self,
        args: object,  # Put your own arguments here
    ) -> None:
        """
        Attempt to send a heartbeat message.
        """
        self.send_heartbeat()


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
