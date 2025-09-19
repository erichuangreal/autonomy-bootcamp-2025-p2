"""
Telemetry gathering logic.
"""

import time

from pymavlink import mavutil

from ..common.modules.logger import logger


class TelemetryData:  # pylint: disable=too-many-instance-attributes
    """
    Python struct to represent Telemtry Data. Contains the most recent attitude and position reading.
    """

    def __init__(
        self,
        time_since_boot: int | None = None,  # ms
        x: float | None = None,  # m
        y: float | None = None,  # m
        z: float | None = None,  # m
        x_velocity: float | None = None,  # m/s
        y_velocity: float | None = None,  # m/s
        z_velocity: float | None = None,  # m/s
        roll: float | None = None,  # rad
        pitch: float | None = None,  # rad
        yaw: float | None = None,  # rad
        roll_speed: float | None = None,  # rad/s
        pitch_speed: float | None = None,  # rad/s
        yaw_speed: float | None = None,  # rad/s
    ) -> None:
        self.time_since_boot = time_since_boot
        self.x = x
        self.y = y
        self.z = z
        self.x_velocity = x_velocity
        self.y_velocity = y_velocity
        self.z_velocity = z_velocity
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        self.roll_speed = roll_speed
        self.pitch_speed = pitch_speed
        self.yaw_speed = yaw_speed

    def __str__(self) -> str:
        return f"""{{
            time_since_boot: {self.time_since_boot},
            x: {self.x},
            y: {self.y},
            z: {self.z},
            x_velocity: {self.x_velocity},
            y_velocity: {self.y_velocity},
            z_velocity: {self.z_velocity},
            roll: {self.roll},
            pitch: {self.pitch},
            yaw: {self.yaw},
            roll_speed: {self.roll_speed},
            pitch_speed: {self.pitch_speed},
            yaw_speed: {self.yaw_speed}
        }}"""


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class Telemetry:
    """
    Telemetry class to read position and attitude (orientation).
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> tuple[bool, "Telemetry"]:
        telemetry_instance = cls(
            cls.__private_key,
            connection,
            local_logger,
        )
        local_logger.info("Telemetry created successfully")
        return True, telemetry_instance

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"
        self.connection = connection
        self.logger = local_logger
        self.timeout = 1.0

    def run(self) -> TelemetryData | None:
        start_time = time.time()
        attitude_msg = None
        position_msg = None
        most_recent_time = 0
        while time.time() - start_time < self.timeout:
            if attitude_msg is None:
                msg = self.connection.recv_match(type="ATTITUDE", blocking=False, timeout=0.1)
                if msg is not None:
                    attitude_msg = msg
                    most_recent_time = max(most_recent_time, msg.time_boot_ms)
                    self.logger.info(f"Received ATTITUDE message: {msg}")
            if position_msg is None:
                msg = self.connection.recv_match(
                    type="LOCAL_POSITION_NED", blocking=False, timeout=0.1
                )
                if msg is not None:
                    position_msg = msg
                    most_recent_time = max(most_recent_time, msg.time_boot_ms)
                    self.logger.info(f"Received LOCAL_POSITION_NED message: {msg}")
            if attitude_msg is not None and position_msg is not None:
                telemetry_data = TelemetryData(
                    time_since_boot=most_recent_time,
                    x=position_msg.x,
                    y=position_msg.y,
                    z=position_msg.z,
                    x_velocity=position_msg.vx,
                    y_velocity=position_msg.vy,
                    z_velocity=position_msg.vz,
                    roll=attitude_msg.roll,
                    pitch=attitude_msg.pitch,
                    yaw=attitude_msg.yaw,
                    roll_speed=attitude_msg.rollspeed,
                    pitch_speed=attitude_msg.pitchspeed,
                    yaw_speed=attitude_msg.yawspeed,
                )
                self.logger.info(f"Created TelemetryData: {telemetry_data}")
                return telemetry_data
            time.sleep(0.01)
        # Timeout occurred
        if attitude_msg is None and position_msg is None:
            self.logger.error(
                "Timeout: No ATTITUDE or LOCAL_POSITION_NED messages received within 1 second"
            )
        elif attitude_msg is None:
            self.logger.error("Timeout: Missing ATTITUDE message within 1 second")
        elif position_msg is None:
            self.logger.error("Timeout: Missing LOCAL_POSITION_NED message within 1 second")
        return None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
