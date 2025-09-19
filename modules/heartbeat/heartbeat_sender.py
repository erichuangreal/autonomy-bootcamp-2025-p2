"""
Heartbeat sending logic.
"""

from pymavlink import mavutil


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================


class HeartbeatSender:
    """
    HeartbeatSender class to send a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        logger: object | None = None,
    ) -> tuple[bool, "HeartbeatSender"]:
        """
        Create a new HeartbeatSender instance with the given connection and logger.
        Returns a tuple (success, HeartbeatSender instance).
        """
        instance = cls(cls.__private_key, connection, logger)
        return True, instance

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        logger: object | None = None,
    ) -> None:
        """
        Initialize the HeartbeatSender instance.
        """
        assert key is HeartbeatSender.__private_key, "Use create() method"
        self.connection = connection
        self.logger = logger

    def run(self) -> None:
        """
        Run the heartbeat sender loop.
        """
        if self.logger:
            self.logger.info("Sending heartbeat", True)
        self.connection.mav.heartbeat_send(
            mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0
        )
        if self.logger:
            self.logger.info("Heartbeat sent", True)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
