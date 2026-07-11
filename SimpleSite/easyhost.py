import os
import quart
from SimpleSite.error_registry import ErrorRegistry

class App:


    def __init__(self):
        self.app = quart.Quart(__name__)
        self.quart = quart
        self.error_registry = ErrorRegistry(self.app, self.quart)

    def hostStatic(self, route: str, html: str, secure: bool = False):
        """
        A function to host a static page. Can be secure but requires 
        the setup of a login which can be created using ``createLogin()``
        param route: The route of the endpoint (example.com/<route>)
        param html: Either the path to the file or raw html
        param secure: Whether the endpoint is locked behind a login
        """
        if not route.startswith("/"):
            route = "/" + route
        route = route.replace(" ", "-")

        if os.path.isfile(html):
            async def view(html=html):
                return await self.quart.render_template(html)
            self.app.add_url_rule(route, route, view)

        elif os.path.isdir(html):
            async def view(html=html):
                return await self.quart.send_from_directory(html, 'index.html')
            self.app.add_url_rule(route, route, view)

        else:
            async def view(html=html):
                return await self.quart.render_template_string(html)
            self.app.add_url_rule(route, route, view)

    def createLogin(def_user: str = None, def_pass: str = None, use_dotenv: bool = False):
        if use_dotenv:
            from dotenv import load_dotenv
            from os import getenv
            load_dotenv()
            def_user = load_dotenv("def_user")
            def_pass = load_dotenv("def_pass")
        


    def _init_necessary_paths(self):
        @self.app.route("/favicon.ico")
        async def favicon():
            return self.quart.abort(404)
        


    def run(self, host='127.0.0.1', port=5000):
        """
        Runs the Quart app.
        param host: The host to run the app on. Default is '127.0.0.1'.
        param port: The port to run the app on. Default is 5000.
        param debug: Whether to run the app in debug mode. Default is True.
        """
        import os
        print(os.getcwd())
        self._init_necessary_paths()
        from uvicorn import run
        run(self.app, host=host, port=port)

