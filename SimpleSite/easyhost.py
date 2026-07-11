import os
import quart
from quart_auth import QuartAuth, AuthUser, login_required, login_user
from SimpleSite.error_registry import ErrorRegistry
import SimpleSite.database_helper as dh
from dotenv import load_dotenv
from os import getenv
load_dotenv()


def _env_flag(name: str, default: bool = False) -> bool:
    value = getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class App:

    def __init__(self):
        self.app = quart.Quart(__name__)
        self.quart = quart
        self.db_flag = _env_flag("USE_DB")
        self.auth = bool(getenv("DEF_USER")) and bool(getenv("DEF_PASS"))

        if self.auth:
            secret_key = getenv("SECRET_KEY")
            if not secret_key:
                raise RuntimeError(
                    "SECRET_KEY must be set in .env when DEF_USER/DEF_PASS are configured"
                )
            self.app.secret_key = secret_key
            QuartAuth(self.app)

        self.error_registry = ErrorRegistry(self.app, self.quart)

    def hostStatic(self, route: str, html: str, secure: bool = False):
        """
        A function to host a static page. Can be secure but requires
        the setup of a login which can be created using ``createLogin()``

        The use of secure also requires html to be a file

        param route: The route of the endpoint (example.com/<route>)
        param html: Either the path to the file, raw html or a directory
        param secure: Whether the endpoint is locked behind a login
        """
        if secure and not self.auth:
            raise RuntimeError(
                "secure=True requires DEF_USER/DEF_PASS (and SECRET_KEY) to be set in .env"
            )

        if not secure:
            if not route.startswith("/"):
                route = "/" + route
            route = route.replace(" ", "-")

            if os.path.isfile(html):
                async def view(html=html):
                    return await self.quart.render_template(html)

            elif os.path.isdir(html):
                async def view(html=html):
                    return await self.quart.send_from_directory(html, 'index.html')

            else:
                async def view(html=html):
                    return self.quart.Markup(html)
        else:
            @login_required
            async def view(html=html):
                return await self.quart.render_template(html)
        self.app.add_url_rule(route, route, view)

    def createLogin(self, route: str, html: str = None, referal: str = "/"):
        """
        Registers a login endpoint. GET serves the login form, POST checks the
        submitted credentials and, on success, logs the user in via quart-auth.

        Requires DEF_USER/DEF_PASS (and therefore SECRET_KEY) to be set in .env.
        
        param route: The route where the login lives
        param html: The login template file
        param referal: Where the user should be rerouted after login succesfully
        """
        if not self.auth:
            raise RuntimeError(
                "createLogin() requires DEF_USER and DEF_PASS to be set in .env"
            )

        if not route.startswith("/"):
            route = "/" + route
        route = route.replace(" ", "-")

        async def login_page():
            if html:
                return await self.quart.render_template(html)
            return await self.quart.render_template_string(
                '<login-form></login-form>'
                '<script src="{{ login }}"></script>'
            )

        async def login():
            form = await self.quart.request.form
            luser = form.get("user")
            lpassword = form.get("password")

            if not luser or not lpassword:
                return self.quart.abort(400)

            if self.db_flag:
                valid = await dh.check_login(luser, lpassword)
            else:
                valid = luser == getenv("DEF_USER") and lpassword == getenv("DEF_PASS")

            if not valid:
                return self.quart.abort(401)

            login_user(AuthUser(luser))
            return self.quart.redirect("/")

        self.app.add_url_rule(route, f"{route}_login_get", login_page, methods=["GET"])
        self.app.add_url_rule(route, f"{route}_login_post", login, methods=["POST"])

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

        @self.app.before_serving
        async def initRequirements():
            if self.db_flag:
                await dh.start()
                if self.auth:
                    await dh.register_user(getenv("DEF_USER"), getenv("DEF_PASS"))

        from SimpleSite.blueprints import bp_scripts

        self.app.register_blueprint(bp_scripts)

        @self.app.context_processor
        def inject_simplesite_assets():
            from quart import url_for
            return {
                "login": url_for("script_inject.static", filename="js/login.js")
            }

        from uvicorn import run
        run(self.app, host=host, port=port)
