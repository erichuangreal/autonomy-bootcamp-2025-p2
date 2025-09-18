"""
Command worker to make decisions based on Telemetry Data.
"""

import os
import pathlib

from pymavlink import mavutil

from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from . import command
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def command_worker(
    connection: mavutil.mavfile,
    target: command.Position,
    controller: worker_controller.WorkerController,
    command_input_queue: queue_proxy_wrapper.QueueProxyWrapper,
    command_output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    height_tolerance: float,
    angle_tolerance: float,
) -> None:
    """
    Worker process for command decisions.
    """
    # Instantiate logger
    import datetime
    worker_name = pathlib.Path(__file__).stem
    process_id = os.getpid()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_id = f"{worker_name}_{process_id}_{timestamp}"
    result, local_logger = logger.Logger.create(log_id, True)
    if not result:
        print("ERROR: Worker failed to create logger")
        return
    assert local_logger is not None
    local_logger.info("Logger initialized", True)

    # Instantiate Command object
    result, command_obj = command.Command.create(
        connection, target, height_tolerance, angle_tolerance, local_logger
    )
    if not result or command_obj is None:
        local_logger.error("Failed to create Command")
        return
    local_logger.info("Command created successfully")

    # Main loop: process telemetry and send commands
    import time
    import queue
    while not controller.is_exit_requested():
        try:
            try:
                telemetry_data = command_input_queue.queue.get(timeout=1.0)
            except queue.Empty:
                time.sleep(0.1)
                continue
            except Exception as qexc:
                local_logger.error(f"Exception getting telemetry from queue: {qexc}", exc_info=True)
                time.sleep(0.1)
                continue
            local_logger.info(f"Received TelemetryData: {telemetry_data}")
            try:
                command_result = command_obj.run(telemetry_data)
            except Exception as run_exc:
                local_logger.error(f"Exception in Command.run: {run_exc}", exc_info=True)
                continue
            if command_result is not None:
                try:
                    command_output_queue.queue.put(command_result)
                    local_logger.info(f"Sent command result: {command_result}")
                except Exception as put_exc:
                    local_logger.error(f"Exception putting command result in queue: {put_exc}", exc_info=True)
            time.sleep(0.1)
        except Exception as outer_exc:
            local_logger.error(f"Unexpected exception in command worker: {outer_exc}", exc_info=True)
            time.sleep(0.1)
    local_logger.info("Command worker exiting gracefully")

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

    # Main loop: do work.


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================