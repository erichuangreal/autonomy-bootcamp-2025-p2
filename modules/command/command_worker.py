"""
Command worker to make decisions based on Telemetry Data.
"""


import os
import pathlib
import time
import queue

from pymavlink import mavutil
from utilities.workers import worker_controller
from . import command
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================

def command_worker(
    connection: mavutil.mavfile,
    target: command.Position,
    telemetry_queue: queue.Queue,
    command_queue: queue.Queue,
    worker_ctrl: worker_controller.WorkerController,
    height_tolerance: float,
    angle_tolerance: float,
) -> None:
    """
    Worker process.

    args:
    connection: MAVLink connection object for sending commands
    target: Target position to maintain altitude and face towards
    telemetry_queue: Queue to receive TelemetryData from Telemetry worker
    command_queue: Queue to send command status to main process
    worker_ctrl: Worker controller for graceful shutdown
    height_tolerance: Tolerance for altitude deviation (meters)
    angle_tolerance: Tolerance for yaw deviation (degrees)
    """
    # =============================================================================================
    #                          ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
    # =============================================================================================

    # Instantiate logger
    worker_name = pathlib.Path(__file__).stem
    process_id = os.getpid()
    result, local_logger = logger.Logger.create(f"{worker_name}_{process_id}", True)
    if not result:
        print("ERROR: Worker failed to create logger")
        return

    # Get Pylance to stop complaining
    assert local_logger is not None

    local_logger.info("Logger initialized", True)

    # =============================================================================================
    #                          ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
    # =============================================================================================
    # Instantiate class object (command.Command)
    result, command_obj = command.Command.create(
        connection, target, height_tolerance, angle_tolerance, local_logger
    )
    if not result or command_obj is None:
        local_logger.error("Failed to create Command")
        return

    local_logger.info("Command created successfully")

    # Main loop: do work.
    while not worker_ctrl.is_exit_requested():
        try:
            # Get telemetry data from Telemetry worker
            telemetry_data = telemetry_queue.queue.get(timeout=1.0)
            local_logger.info(f"Received TelemetryData: {telemetry_data}")

            # Make decision based on telemetry data
            command_result = command_obj.run(telemetry_data)

            if command_result is not None:
                # Send command result to main process
                command_queue.queue.put(command_result)
                local_logger.info(f"Sent command result: {command_result}")

            time.sleep(0.1)

        except queue.Empty:
            # Timeout is expected, continue
            time.sleep(0.1)
        except (mavutil.mavlink.MAVError, RuntimeError) as e:
            local_logger.error(f"Error in command worker main loop: {e}")
            time.sleep(0.1)

    local_logger.info("Command worker exiting gracefully")


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
