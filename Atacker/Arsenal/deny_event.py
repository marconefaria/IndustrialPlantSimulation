import time

from OPCServer.opc_server import OPCServer
from Tools.mapper import get_event_name


def deny_event(server: OPCServer):
    event = get_event_name(server.query_variable('Attack_Event'))

    while not server.query_variable(event):
        time.sleep(1)

    while server.query_variable(event):
        server.update_variable(event, False)

    # "Blocks" the event by not executing it
    print(f"Event '{event}' has been denied and will not be executed.")