import secrets
import asyncio
import websockets
import json
from modules.utils import Command, ConfigLoader, CommandLogger
from modules.sectorServer import EngineSector_interactor
import time
# from modules.physEngine.predictor import launch_new_TrajectoryPredictor_controller
from modules.users_controller import UsersControler

class ConnectionController:
    # токен коннекшна должен быть связан с id viewer и с id controller
    connections = {}
    connection_ips = {}
    controlled_entiies = {}
    last_activities = {}
    server = EngineSector_interactor()

    async def handler(websocket):
        pass  # print("connection started")
        token = secrets.token_urlsafe(12)
        ConnectionController.connections[token] = websocket
        ConnectionController.controlled_entiies[token] = None
        ConnectionController.connection_ips[token] = websocket.origin
        ConnectionController.last_activities[token] = time.perf_counter()
        try:
            async for message in websocket:
                ConnectionController.last_activities[token] = time.perf_counter(
                )
                message_data = json.loads(message)
                command = Command(message_data)
                CommandLogger().add(command)
                if command.contains_level("connection"):
                    ConnectionController.proceed_command(token, command)

                # if command.contains_level("predictor"):
                # launch_new_TrajectoryPredictor_controller()
                else:
                    ConnectionController.server.proceed_command(message_data)
        except Exception as e:
            pass  # print(repr(e))

        pass  # print("connection terminated")

    async def main():
        ip = ConfigLoader().get("system.ip")
        port = ConfigLoader().get("system.ws_port", int)
        async with websockets.serve(ConnectionController.handler, ip, port):
            while 1:
                await asyncio.sleep(0.04)

    def clear_connection(token):
        ConnectionController.connections.pop(token)
        ConnectionController.controlled_entiies.pop(token)
        ConnectionController.connection_ips.pop(token)
        ConnectionController.last_activities.pop(token)

    async def clear_broken_connections():
        while 1:
            timestamp_now = time.perf_counter()
            tokens = list(ConnectionController.connections.keys())
            for token in tokens:
                delta = timestamp_now - \
                    ConnectionController.last_activities[token]
                if delta > 2:
                    await ConnectionController.connections[token].close()
            await asyncio.sleep(2)

    def proceed_command(token, command: Command):
        if command.get_action() == "take_control_on_entity":
            ConnectionController.controlled_entiies[token] = command.get_params()[
                'target_id']
        if command.get_action() == "auth_login":
            password = command.get_params()["password"]
            UsersControler().auth_ws(token, password)

        if command.get_action() == "auth_logout":
            pass


    async def broadcast():
        while 1:
            try:
                tokens2delete = []
                for token in ConnectionController.connections:
                    try:
                        token_expired = UsersControler().is_token_expired(token)
                        if token_expired:
                            tokens2delete.append(token)
                            await ConnectionController.connections[token].close()
                            continue
                        global_map_data = ConnectionController.server.get_sector_map(
                            ConnectionController.controlled_entiies[token])
                        await ConnectionController.connections[token].send(json.dumps(global_map_data))
                    except websockets.ConnectionClosedOK:
                        tokens2delete.append(token)

                for token in tokens2delete:
                    del ConnectionController.connections[token]
                    del ConnectionController.connection_ips[token]
            except Exception as e:
                pass  # print(repr(e))
                del ConnectionController.connections[token]
                del ConnectionController.connection_ips[token]
            await asyncio.sleep(0.02)
