import time

from OPCServer.opc_server import OPCServer
from Tools.mapper import get_event_name


def intercept_event(server: OPCServer):
    event = get_event_name(server.query_variable('Attack_Event'))

    if event in server.query_processed_events():
        print(f"Event '{event}' already processed, interception not possible.")
        return
    else:
        server.update_variable(event, True)
        server.add_to_processed_events(event)

    time.sleep(0.01)
    print(f"Event '{event}' was intercepted and executed.")