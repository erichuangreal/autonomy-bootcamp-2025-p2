"""
Bootcamp F2025

Main process to setup and manage all the other working processes
"""

import multiprocessing as mp
import queue
import time

from pymavlink import mavutil

from modules.common.modules.logger import logger
from modules.common.modules.logger import logger_main_setup
from modules.common.modules.read_yaml import read_yaml
from modules.command import command
from modules.command import command_worker
from modules.heartbeat import heartbeat_receiver_worker
from modules.heartbeat import heartbeat_sender_worker
from modules.telemetry import telemetry_worker
from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from utilities.workers import worker_manager


# MAVLink connection
CONNECTION_STRING = "tcp:localhost:12345"

# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
# Set queue max sizes (<= 0 for infinity)
HEARTBEAT_QUEUE_SIZE = 10
TELEMETRY_QUEUE_SIZE = 50
COMMAND_QUEUE_SIZE = 10

# Set worker counts
HEARTBEAT_SENDER_WORKERS = 1
HEARTBEAT_RECEIVER_WORKERS = 1
TELEMETRY_WORKERS = 1
COMMAND_WORKERS = 1

# Any other constants
MAIN_LOOP_DURATION = 100
MAIN_LOOP_SLEEP = 0.1
HEARTBEAT_PERIOD = 1.0
HEIGHT_TOLERANCE = 5.0
ANGLE_TOLERANCE = 10.0
# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================


def main() -> int:
    """
    Main function.
    """
    # Configuration settings
    result, config = read_yaml.open_config(logger.CONFIG_FILE_PATH)
    if not result:
        print("ERROR: Failed to load configuration file")
        return -1

    # Get Pylance to stop complaining
    assert config is not None

    # Setup main logger
    result, main_logger, _ = logger_main_setup.setup_main_logger(config)
    if not result:
        print("ERROR: Failed to create main logger")
        return -1

    # Get Pylance to stop complaining
    assert main_logger is not None

    # Create a connection to the drone. Assume that this is safe to pass around to all processes
    # In reality, this will not work, but to simplify the bootamp, preetend it is allowed
    # To test, you will run each of your workers individually to see if they work
    # (test "drones" are provided for you test your workers)
    # NOTE: If you want to have type annotations for the connection, it is of type mavutil.mavfile
    connection = mavutil.mavlink_connection(CONNECTION_STRING)
    connection.wait_heartbeat(timeout=30)  # Wait for the "drone" to connect

    # =============================================================================================
    #                          ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
    # =============================================================================================
    # Create a worker controller
    controller = worker_controller.WorkerController()

    # Create a multiprocess manager for synchronized queues
    manager = mp.Manager()

    # Create queues using QueueProxyWrapper
    heartbeat_report_queue = queue_proxy_wrapper.QueueProxyWrapper(manager, HEARTBEAT_QUEUE_SIZE)
    telemetry_report_queue = queue_proxy_wrapper.QueueProxyWrapper(manager, TELEMETRY_QUEUE_SIZE)
    command_request_queue = queue_proxy_wrapper.QueueProxyWrapper(manager, COMMAND_QUEUE_SIZE)

    # Create worker properties for each worker type (what inputs it takes, how many workers)
    result, heartbeat_sender_properties = worker_manager.WorkerProperties.create(
        count=HEARTBEAT_SENDER_WORKERS,
        target=heartbeat_sender_worker.heartbeat_sender_worker,
        work_arguments=(connection, HEARTBEAT_PERIOD),  # connection, heartbeat_period
        input_queues=[],
        output_queues=[],
        controller=controller,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create Heartbeat Sender worker properties")
        return -1

    # Heartbeat receiver - takes (connection, report_queue)
    result, heartbeat_receiver_properties = worker_manager.WorkerProperties.create(
        count=HEARTBEAT_RECEIVER_WORKERS,
        target=heartbeat_receiver_worker.heartbeat_receiver_worker,
        work_arguments=(connection,),  # connection only, queue handled by framework
        input_queues=[],
        output_queues=[heartbeat_report_queue],
        controller=controller,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create Heartbeat Receiver worker properties")
        return -1

    # Telemetry - takes (connection, telemetry_queue, worker_ctrl)
    result, telemetry_properties = worker_manager.WorkerProperties.create(
        count=TELEMETRY_WORKERS,
        target=telemetry_worker.telemetry_worker,
        work_arguments=(connection,),  # connection only, queue and controller handled by framework
        input_queues=[],
        output_queues=[telemetry_report_queue],
        controller=controller,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create Telemetry worker properties")
        return -1

    # Command - takes (connection, target, telemetry_queue, command_queue, worker_ctrl, height_tolerance, angle_tolerance)
    target_position = command.Position(x=0.0, y=0.0, z=100.0)  # Example target position
    result, command_properties = worker_manager.WorkerProperties.create(
        count=COMMAND_WORKERS,
        target=command_worker.command_worker,
        work_arguments=(
            connection,
            target_position,
            HEIGHT_TOLERANCE,
            ANGLE_TOLERANCE,
        ),  # connection, target, height_tolerance, angle_tolerance
        input_queues=[telemetry_report_queue],
        output_queues=[command_request_queue],
        controller=controller,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create Command worker properties")
        return -1

    # Create the workers (processes) and obtain their managers
    worker_managers: list[worker_manager.WorkerManager] = []

    result, heartbeat_sender_manager = worker_manager.WorkerManager.create(
        worker_properties=heartbeat_sender_properties,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create manager for Heartbeat Sender")
        return -1
    assert heartbeat_sender_manager is not None
    worker_managers.append(heartbeat_sender_manager)

    result, heartbeat_receiver_manager = worker_manager.WorkerManager.create(
        worker_properties=heartbeat_receiver_properties,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create manager for Heartbeat Receiver")
        return -1
    assert heartbeat_receiver_manager is not None
    worker_managers.append(heartbeat_receiver_manager)

    result, telemetry_manager = worker_manager.WorkerManager.create(
        worker_properties=telemetry_properties,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create manager for Telemetry")
        return -1
    assert telemetry_manager is not None
    worker_managers.append(telemetry_manager)

    result, command_manager = worker_manager.WorkerManager.create(
        worker_properties=command_properties,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create manager for Command")
        return -1
    assert command_manager is not None
    worker_managers.append(command_manager)

    # Start worker processes
    for manager in worker_managers:
        manager.start_workers()

    main_logger.info("Started")

    # Main's work: read from all queues that output to main, and log any commands that we make
    start_time = time.time()

    try:
        while time.time() - start_time < MAIN_LOOP_DURATION:
            # Check if connection is still alive
            if not connection.target_system:
                main_logger.warning("Drone disconnected")
                break

            # Process heartbeat reports
            try:
                while True:
                    heartbeat_data = heartbeat_report_queue.get_nowait()
                    main_logger.info(f"Received heartbeat: {heartbeat_data}")
            except queue.Empty:
                pass

            # Process telemetry reports
            try:
                while True:
                    telemetry_data = telemetry_report_queue.get_nowait()
                    main_logger.info(f"Received telemetry: {telemetry_data}")
            except queue.Empty:
                pass

            if int(time.time() - start_time) % 10 == 0:  # Every 10 seconds
                try:
                    test_command = {"type": "test", "data": f"command at {time.time()}"}
                    command_request_queue.put_nowait(test_command)
                    main_logger.info(f"Sent command: {test_command}")
                except queue.Full:
                    main_logger.warning("Command queue is full")

            time.sleep(MAIN_LOOP_SLEEP)

    except KeyboardInterrupt:
        main_logger.info("Keyboard interrupt received")

    # Stop the processes
    controller.request_exit()

    main_logger.info("Requested exit")

    # Fill and drain queues
    command_request_queue.fill_and_drain_queue()
    telemetry_report_queue.fill_and_drain_queue()
    heartbeat_report_queue.fill_and_drain_queue()

    main_logger.info("Queues cleared")

    # Clean up workers
    for manager in worker_managers:
        manager.join_workers()

    main_logger.info("Stopped")

    controller.clear_exit()

    # =============================================================================================
    #                          ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
    # =============================================================================================

    return 0


if __name__ == "__main__":
    result_main = main()
    if result_main < 0:
        print(f"Failed with return code {result_main}")
    else:
        print("Success!")
