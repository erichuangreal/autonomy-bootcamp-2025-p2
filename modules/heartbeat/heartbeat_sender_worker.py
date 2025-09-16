"""
Heartbeat worker that sends heartbeats periodically.
"""

import os
import pathlib
import time

from pymavlink import mavutil

from utilities.workers import worker_controller
from . import heartbeat_sender
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
from threading import Event
from typing import Optional


def heartbeat_sender_worker(
    connection: mavutil.mavfile, heartbeat_period: float = 1.0, stop_event: Optional[Event] = None
) -> None:
    """
    Worker process.

    args:
        connection: MAVLink connection to send heartbeats through
        heartbeat_period: Time between heartbeats in seconds (1 sec)
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
    # Instantiate class object (heartbeat_sender.HeartbeatSender)

    result, heartbeat_sender_instance = heartbeat_sender.HeartbeatSender.create(
        connection, local_logger
    )

    # Main loop: do work.
    while not (stop_event and stop_event.is_set()):
        try:
            heartbeat_sender_instance.send_heartbeat()

            time.sleep(heartbeat_period)  # should be 1 second

        except Exception as e:
            local_logger.error(f"Error in heartbeat sender worker: {e}", True)
            break


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
