"""
Heartbeat receiving logic.
"""

from pymavlink import mavutil

from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
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
    ) -> tuple[bool, "HeartbeatReceiver"]:
        instance = cls(cls.__private_key, connection, local_logger)
        local_logger.info("HeartbeatReceiver created successfully")
        return True, instance

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
        self.max_missed_heartbeats = 5
        self.logger.info(
            f"HeartbeatReceiver initialized with max_missed_heartbeats={self.max_missed_heartbeats}"
        )

    def run(self) -> str:
        msg = self.connection.recv_match(type="HEARTBEAT", blocking=False, timeout=0.5)
        if msg is not None:
            self.logger.info(f"Received HEARTBEAT message: {msg}")
            self.missed_heartbeats = 0
            if self.state != "Connected":
                self.state = "Connected"
                self.logger.info("State changed to Connected")
        else:
            self.missed_heartbeats += 1
            self.logger.warning(f"Missed heartbeat #{self.missed_heartbeats}")
            if self.missed_heartbeats >= self.max_missed_heartbeats:
                if self.state != "Disconnected":
                    self.state = "Disconnected"
                    self.logger.warning(
                        "State changed to Disconnected - missed 5 consecutive heartbeats"
                    )
        return self.state


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
