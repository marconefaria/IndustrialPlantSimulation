import threading
import time

from Core.Control.controller import Controller
from Core.Process.Tank.tank import Tank
from Core.SubSystems.InputValve.input_valve import InputValve
from Core.SubSystems.LevelTransmitter.level_transmitter import LevelTransmitter
from Core.SubSystems.Mixer.mixer import Mixer
from Core.SubSystems.OutputValve.output_valve import OutputValve
from Core.Process.process import Process
from Core.SubSystems.Pump.pump import Pump
from Core.SubSystems.TemperatureControl.temperature_control import TemperatureControl
from OPCClient.opc_client import OPCClient
from OPCServer.opc_server import OPCServer

if __name__ == "__main__":
    class TerminateProgramException(Exception):
        pass

    system_initialized = False
    semaphore = threading.Semaphore(1)

    # Initialize server
    server = OPCServer()
    server.start()

    # Connect process plant client
    process_client = OPCClient()
    process_client.connect()
    process = Process(semaphore, process_client)

    # Connect tank plant client
    tank_client = OPCClient()
    tank_client.connect()
    tank = Tank(semaphore, process_client)

    # Connect input valve client
    client_input = OPCClient()
    client_input.connect()
    input_valve = InputValve(client_input)

    # Connect output valve client
    client_output = OPCClient()
    client_output.connect()
    output_valve = OutputValve(client_output)

    # Connect level transmitter client
    client_level_transmitter = OPCClient()
    client_level_transmitter.connect()
    level_transmitter = LevelTransmitter(semaphore, client_level_transmitter)

    # Connect mixer client
    client_mixer = OPCClient()
    client_mixer.connect()
    mixer = Mixer(semaphore, client_mixer)

    # Connect pump client
    client_pump = OPCClient()
    client_pump.connect()
    pump = Pump(semaphore, client_pump)

    # Connect temperature control client
    client_temperature_control = OPCClient()
    client_temperature_control.connect()
    temperature_control = TemperatureControl(semaphore, client_temperature_control)

    # Initialize controller
    controller = Controller(semaphore, server)

    def initialize_system():
        process.start()
        tank.start_threads()
        input_valve.start()
        output_valve.start()
        mixer.start()
        pump.start()
        temperature_control.start()
        level_transmitter.start()
        controller.start()

        print("System initialized.")
        controller.server.update_finish_process(False)

    # Keep the execution of program until a keyboard interruption
    while not controller.server.finish_process():
        try:
            if controller.server.start_process():
                initialize_system()
                time.sleep(1000)
        except TerminateProgramException as e:
            print("Stopping all threads and server...")
            controller.join()
            process.join()
            tank.join_threads()
            input_valve.join()
            output_valve.join()
            mixer.join()
            pump.join()
            temperature_control.join()
            level_transmitter.join()
            client_input.disconnect()
            client_output.disconnect()
            server.stop()
            break

    exit()
