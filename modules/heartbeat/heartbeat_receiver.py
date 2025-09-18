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
    HeartbeatReceiver class to receive a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ):
        try:
            heartbeat_receiver_instance = HeartbeatReceiver(
                cls.__private_key,
                connection,
                local_logger,
            )
            local_logger.info("HeartbeatReceiver created successfully")
            return True, heartbeat_receiver_instance
        except Exception as err:
            local_logger.error(f"Failed to create HeartbeatReceiver: {err}")
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
        self.max_missed_heartbeats = 5
        self.logger.info("HeartbeatReceiver initialized")

    def run(self) -> str:
        try:
            msg = self.connection.recv_match(type="HEARTBEAT", blocking=False, timeout=0.1)
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
                        self.logger.warning("State changed to Disconnected - missed 5 consecutive heartbeats")
        except Exception as e:
            self.logger.error(f"Error in HeartbeatReceiver run: {e}")
        return self.state

# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
