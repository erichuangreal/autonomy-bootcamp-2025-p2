"""
Heartbeat worker that sends heartbeats periodically.
"""

import os
import pathlib
import time

from pymavlink import mavutil

from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from . import heartbeat_receiver
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def heartbeat_receiver_worker(
    connection: mavutil.mavfile,
    report_queue: "queue_proxy_wrapper.QueueProxyWrapper",
    worker_ctrl: "worker_controller.WorkerController",
) -> None:
    """
    Worker process.
    connection: MAVLink connection object for receiving messages
    report_queue: QueueProxyWrapper to send status reports to main process
    worker_ctrl: WorkerController for exit signaling
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

    assert local_logger is not None
    local_logger.info("Logger initialized", True)

    # =============================================================================================
    #                          ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
    # =============================================================================================
    # Instantiate class object (heartbeat_receiver.HeartbeatReceiver)
    result, heartbeat_rcv = heartbeat_receiver.HeartbeatReceiver.create(connection, local_logger)
    if not result or heartbeat_rcv is None:
        local_logger.error("Failed to create HeartbeatReceiver")
        return
    local_logger.info("HeartbeatReceiver created successfully")

    while not worker_ctrl.is_exit_requested():
        current_state = heartbeat_rcv.run()
        report_queue.queue.put(current_state)
        local_logger.info(f"Reported state: {current_state}")
        time.sleep(1.0)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
