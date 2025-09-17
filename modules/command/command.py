"""
Decision-making logic.
"""

import math

from pymavlink import mavutil

from ..common.modules.logger import logger
from ..telemetry import telemetry


class Position:
    """
    3D vector struct.
    """

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class Command:  # pylint: disable=too-many-instance-attributes
    """
    Command class to make a decision based on recieved telemetry,
    and send out commands based upon the data.
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        target: Position,
        height_tolerance: float,
        angle_tolerance: float,
        local_logger: logger.Logger,
    ) -> "tuple[bool, Command | None]":
        """
        Falliable create (instantiation) method to create a Command object.
        """
        try:
            command_instance = cls(
                cls.__private_key,
                connection,
                target,
                height_tolerance,
                angle_tolerance,
                local_logger,
            )
            local_logger.info("Command created successfully")
            return True, command_instance
        except (ValueError, AttributeError, RuntimeError) as e:
            local_logger.error(f"Failed to create Command: {e}")
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        height_tolerance: float,
        angle_tolerance: float,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.target = target
        self.height_tolerance = height_tolerance
        self.angle_tolerance = angle_tolerance
        self.logger = local_logger

        self.velocity_history = []
        self.logger.info("Command initialized")


    def run(
        self,
        telemetry_data: telemetry.TelemetryData,
    ) -> str | None:
        """
        Make a decision based on received telemetry data.
        """

        if (
            telemetry_data.x_velocity is not None
            and telemetry_data.y_velocity is not None
            and telemetry_data.z_velocity is not None
        ):
            current_velocity = (
                telemetry_data.x_velocity,
                telemetry_data.y_velocity,
                telemetry_data.z_velocity,
            )
            self.velocity_history.append(current_velocity)

            # Calculate average velocity
            avg_x = sum(v[0] for v in self.velocity_history) / len(self.velocity_history)
            avg_y = sum(v[1] for v in self.velocity_history) / len(self.velocity_history)
            avg_z = sum(v[2] for v in self.velocity_history) / len(self.velocity_history)

            self.logger.info(
                f"Average velocity so far: x={avg_x:.2f}, y={avg_y:.2f}, z={avg_z:.2f} m/s"
            )

        # Check altitude adjustment needed
        if telemetry_data.z is not None:
            altitude_error = self.target.z - telemetry_data.z
            if abs(altitude_error) > self.height_tolerance:
                # Send altitude change command
                self.connection.mav.command_long_send(
                    target_system=1,
                    target_component=0,
                    command=mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                    confirmation=0,
                    param1=self.target.z,  # Target altitude
                    param2=0,
                    param3=0,
                    param4=0,
                    param5=0,
                    param6=0,
                    param7=0,
                )
                self.logger.info(
                    f"Sent altitude change command: target={self.target.z}, current={telemetry_data.z}, delta={altitude_error}"
                )
                return f"CHANGE ALTITUDE: {altitude_error:.2f}"

        # Check yaw adjustment needed
        if (
            telemetry_data.x is not None
            and telemetry_data.y is not None
            and telemetry_data.yaw is not None
        ):

            # Calculate desired yaw towards target
            target_yaw = math.atan2(
                self.target.y - telemetry_data.y, self.target.x - telemetry_data.x
            )

            # Calculate yaw error (shortest rotation)
            yaw_error = target_yaw - telemetry_data.yaw

            # Normalize to [-π, π]
            while yaw_error > math.pi:
                yaw_error -= 2 * math.pi
            while yaw_error < -math.pi:
                yaw_error += 2 * math.pi

            # Check if adjustment needed
            yaw_error_degrees = math.degrees(yaw_error)
            if abs(yaw_error_degrees) > self.angle_tolerance:
                # Send yaw change command (relative)
                self.connection.mav.command_long_send(
                    target_system=1,
                    target_component=0,
                    command=mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                    confirmation=0,
                    param1=yaw_error_degrees,  # Relative angle in degrees
                    param2=0,  # Angular speed (doesn't matter per requirements)
                    param3=1,  # Direction: 1=relative, 0=absolute
                    param4=1,  # Relative offset: 1=relative to current yaw
                    param5=0,
                    param6=0,
                    param7=0,
                )
                self.logger.info(
                    f"Sent yaw change command: current={math.degrees(telemetry_data.yaw):.1f}°, target={math.degrees(target_yaw):.1f}°, delta={yaw_error_degrees:.1f}°"
                )
                return f"CHANGE YAW: {yaw_error_degrees:.1f}"

        return None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
