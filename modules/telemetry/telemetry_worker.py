"""
Telemtry worker that gathers GPS data.
"""

import os
import pathlib
import time
import queue

from pymavlink import mavutil
from utilities.workers import worker_controller
from . import telemetry
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================


def telemetry_worker(
    connection: mavutil.mavfile,
    telemetry_queue: queue.Queue,
    worker_ctrl: worker_controller.WorkerController,
    # Add other necessary worker arguments here
) -> None:
    """
    Worker process.

    args...
    connection: MAVLink connection object for receiving messages
    telemetry_queue: Queue to send TelemetryData objects to Command worker
     worker_ctrl: Worker controller for graceful shutdown
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
    # Instantiate class object (telemetry.Telemetry)
    result, telemetry_obj = telemetry.Telemetry.create(connection, local_logger)
    if not result or telemetry_obj is None:
        local_logger.error("Failed to create Telemetry")
        return
    local_logger.info("Telemetry created successfully")
    # Main loop: do work.
    while not worker_ctrl.is_exit_requested():
        try:
            telemetry_data = telemetry_obj.run()
            if telemetry_data is not None:
                telemetry_queue.queue.put(telemetry_data)
                local_logger.info(f"Sent TelemetryData to Command worker: {telemetry_data}")
            else:
                local_logger.warning("Telemetry timeout - restarting collection")
            time.sleep(0.1)
        except Exception as e:
            local_logger.error(f"Error in telemetry worker main loop: {e}")
            time.sleep(0.1)

    local_logger.info("Telemetry worker exiting gracefully")


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
