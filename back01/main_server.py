
if __name__ == '__main__':
    import asyncio
    import multiprocessing as mp
    from multiprocessing import Process, Manager, freeze_support
    from threading import Thread
    import time
    import asyncio
    import websockets
    import json
    import time
    import secrets

    mp.set_start_method('spawn')
    freeze_support()

    from modules.sectorServer import EngineSector_interactor
    from modules.flaskApp import ServerInteractorFlaskApp
    from modules.network.WebsocketController import ConnectionController

    ctx_manager = Manager()
    server = EngineSector_interactor()
    server.init_server(ctx_manager)
    server.start()
    # ConnectionController.server = server
    loop = asyncio.new_event_loop()

    thread_async = Thread(target=loop.run_forever)
    asyncio.set_event_loop(loop)

    loop.create_task(ConnectionController.main())
    loop.create_task(ConnectionController.broadcast())
    # loop.create_task(ConnectionController.clear_broken_connections())
    thread_async = Thread(target=loop.run_forever)
    thread_async.start()

    flask_app = ServerInteractorFlaskApp()
    flask_app.run_forever()

    pass
