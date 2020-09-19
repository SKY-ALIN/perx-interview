from datetime import datetime
import asyncio
from aiohttp import web

class Server:
    """Web server class with 2 endpoints and 1 worker.

    Endpoints:
        '/' POST method (Server.add_task): add a arithmetic
        progression to the queue.
        '/' GET method (Server.get_tasks): view the list of arithmetic
        progressions.
    """

    active_item = None

    def __init__(self, host, port):
        """Constructor.

        Args:
            host (str): ip addr of server.
            port (int): server port.
        """

        self.host = host
        self.port = port
        self.loop = asyncio.get_event_loop()
        self.queue = asyncio.Queue(loop=self.loop)


    async def worker(self):
        """Worker to calculate arithmetic progression."""

        while True:
            item = await self.queue.get()
            item['start'] = datetime.utcnow().strftime("%Y/%m/%d")
            item['status'] = "process"
            self.active_item = item
            print(item)

            for i in range(item['n']):
                item['value'] += item['d']
                print(f"value={item['value']}")
                await asyncio.sleep(item['interval'])

            self.active_item = None


    async def start_worker(self, app):
        """Func start our worker.

        This function is called when the application starts.

        Args:
            app (aiohttp.web_app.Application): Our app.
        """

        app['dispatch'] = app.loop.create_task(self.worker())


    async def cleanup_worker(self, app):
        app['dispatch'].cancel()
        await app['dispatch']


    async def add_task(self, request):
        """View (POST method) for adding new arithmetic
        progressions.
        """

        data = await request.json()
        n = data.get('n')
        d = data.get('d')
        n1 = data.get('n1')
        interval = data.get('interval')

        if n is None or d is None or n1 is None or interval is None:
            return web.Response(status=400)

        try:
            n = int(n)
            d = float(d)
            n1 = int(n1)
            interval = float(interval)
        except ValueError:
            return web.Response(status=400)

        self.queue.put_nowait({
            "n": n,
            "d": d,
            "n1": n1,
            "interval": interval,
            "value": n1,
            "status": "queue"
        })

        return web.Response(status=200)


    async def get_tasks(self, request):
        """View (GET method) for viewing the list of arithmetic
        progressions.
        """

        items = list(self.queue._queue)

        if self.active_item:
            items.insert(0, self.active_item)

        res = [{**item, 'position': i} for i, item in enumerate(items)]

        return web.json_response(res)


    async def create_app(self):
        """Func creates and returns our app.

        Returns:
            aiohttp.web_app.Application: our app.
        """

        app = web.Application()
        app.add_routes([
            web.post('/', self.add_task),
            web.get('/', self.get_tasks)
        ])
        return app


    def run_app(self):
        """Func starts web server."""

        loop = self.loop
        app = loop.run_until_complete(self.create_app())
        app.on_startup.append(self.start_worker)
        app.on_cleanup.append(self.cleanup_worker)
        web.run_app(app, host=self.host, port=self.port)
