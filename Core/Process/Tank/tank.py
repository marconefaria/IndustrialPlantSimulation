import math
import threading
import time
from colorama import Fore, Style

from Configuration.set_points import HEATING_TEMP, INITIAL_TEMP, HEATING_TIME, COOLING_TEMP, COOLING_TIME, TANK_CAPACITY
from OPCClient.opc_client import OPCClient


class Tank:
    R = 10
    C = 0.1

    def __init__(self, semaphore, client: OPCClient):
        self.semaphore = semaphore
        self.client = client

        self.fill_tank_thread = self.FillTankThread(self)
        self.empty_tank_thread = self.EmptyTankThread(self)
        self.heating_thread = self.HeatingThread(self)
        self.cooling_thread = self.CoolingThread(self)

    class FillTankThread(threading.Thread):
        def __init__(self, control):
            super().__init__()
            self.control = control

        def run(self):
            control = self.control
            current_volume = control.client.query_variable('Volume')

            while not control.client.read_open_input_valve():
                time.sleep(1)

            control.semaphore.acquire()
            time.sleep(1)
            print("Filling Tank.")

            while control.client.read_open_input_valve():
                current_volume += 10
                level = (current_volume / TANK_CAPACITY) * 100
                control.client.update_variable("Level", level)
                control.client.update_variable("Volume", current_volume)
                print(Fore.BLUE + f"Level in {level:.2f}% of capacity" + Style.RESET_ALL)

                if level == 100:
                    control.semaphore.release()
                    break

                time.sleep(1)

    class EmptyTankThread(threading.Thread):
        def __init__(self, control):
            super().__init__()
            self.control = control

        def run(self):
            control = self.control

            while not control.client.read_open_output_valve():
                time.sleep(1)

            control.semaphore.acquire()
            time.sleep(1)
            print("Emptying Tank.")
            current_volume = control.client.query_variable('Volume')

            while control.client.read_open_output_valve():
                current_volume -= 10
                level = (current_volume / TANK_CAPACITY) * 100
                control.client.update_variable("Level", level)
                control.client.update_variable("Volume", current_volume)
                print(Fore.BLUE + f"Level in {level:.2f}% of capacity" + Style.RESET_ALL)

                if level == 0:
                    control.semaphore.release()
                    break

                time.sleep(1)

    class HeatingThread(threading.Thread):
        def __init__(self, control):
            super().__init__()
            self.control = control

        def run(self):
            control = self.control

            while not control.client.read_control_temperature_on():
                time.sleep(1)

            control.semaphore.acquire()
            print(Fore.RED + "Heating Tank." + Style.RESET_ALL)
            time.sleep(1)

            while control.client.read_control_temperature_on():
                tau = control.R * control.C

                start_time = time.time()
                current_temperature = control.client.query_variable('Temperature')

                while control.client.query_variable('Temperature') <= HEATING_TEMP:
                    if control.client.read_control_temperature_off():
                        break

                    time_elapsed = time.time() - start_time
                    current_temperature += (HEATING_TEMP - INITIAL_TEMP) * (1 - math.exp(-(time_elapsed / 60) / tau))
                    control.client.update_variable("Temperature", current_temperature)

                    print(Fore.RED + f"Temperature set to {current_temperature:.2f}ºC." + Style.RESET_ALL)

                control.semaphore.release()

                time.sleep(HEATING_TIME)
                break

            while not control.client.read_control_temperature_off():
                time.sleep(1)

    class CoolingThread(threading.Thread):
        def __init__(self, control):
            super().__init__()
            self.control = control

        def run(self):
            control = self.control

            while control.client.query_variable('Temperature') < HEATING_TEMP:
                time.sleep(1)

            control.semaphore.acquire()
            print(Fore.RED + "Cooling Tank." + Style.RESET_ALL)
            time.sleep(1)

            while control.client.read_control_temperature_on():
                tau = 1 * 0.01

                start_time = time.time()
                current_temperature = control.client.query_variable('Temperature')

                while control.client.query_variable('Temperature') > COOLING_TEMP:
                    if control.client.read_control_temperature_off():
                        break

                    time_elapsed = time.time() - start_time
                    current_temperature = COOLING_TEMP + (current_temperature - COOLING_TEMP) * math.exp(
                        -time_elapsed / (60 * tau))
                    control.client.update_variable("Temperature", current_temperature)

                    print(Fore.RED + f"Temperature set to {current_temperature:.2f}ºC." + Style.RESET_ALL)

                control.semaphore.release()

                time.sleep(COOLING_TIME)
                break

            while not control.client.read_control_temperature_off():
                time.sleep(1)

    def start_threads(self):
        self.fill_tank_thread.start()
        self.empty_tank_thread.start()
        self.heating_thread.start()
        self.cooling_thread.start()

    def join_threads(self):
        self.fill_tank_thread.join()
        self.empty_tank_thread.join()
        self.heating_thread.join()
        self.cooling_thread.join()
