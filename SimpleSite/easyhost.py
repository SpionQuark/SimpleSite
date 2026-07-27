import os, json, hmac
import sys
import quart
from quart_auth import QuartAuth, AuthUser, login_required, login_user
from SimpleSite.error_registry import ErrorRegistry, DatabaseNotAllowedError
import SimpleSite.database_helper as dh
from dotenv import load_dotenv
from os import getenv
load_dotenv()

from conf.data import TYPE_MAP

def _caller_dir(dir:str="templates") -> str:
    """
    Resolve the given folder relative to the script that's actually being
    run (e.g. test.py), not relative to this module's location inside the
    SimpleSite package.
    """
    main_module = sys.modules.get("__main__")
    main_file = getattr(main_module, "__file__", None)
    base_dir = os.path.dirname(os.path.abspath(main_file)) if main_file else os.getcwd()
    return os.path.join(base_dir, dir)


def _env_flag(name: str, default: bool = False) -> bool:
    value = getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class App:

    def __init__(self):
        self.app = quart.Quart(__name__, template_folder=_caller_dir(), static_folder=_caller_dir("static"))
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

        param route: The route of the endpoint (example.com/<route>)
        param html: Either the path to the file, raw html or a directory
        param secure: Whether the endpoint is locked behind a login
        """
        if secure and not self.auth:
            raise RuntimeError(
                "secure=True requires DEF_USER/DEF_PASS (and SECRET_KEY) to be set in .env"
            )
        path = os.getcwd()
        if not secure:
            if not route.startswith("/"):
                route = "/" + route
            route = route.replace(" ", "-")
            if os.path.isfile(os.path.join(path, "templates", html)):
                async def view(html=html, path=path):
                    return await self.quart.render_template(os.path.join(path, "templates", html))

            elif os.path.isdir(os.path.join(path, "templates", html)):
                async def view(html=html, path=path):
                    return await self.quart.send_from_directory(os.path.join(path, "templates", html), 'index.html')

            else:
                async def view(html=html):
                    return self.quart.Markup(html)
        else:
            @login_required
            async def view(html=html, path=path):
                try:
                    return await self.quart.render_template(os.path.join(path, "templates", html))
                except:
                    return self.quart.Markup(html)
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

            # Login form → submit → rerouted/logged in
            # Login form → submit → send response email → new database entry → ...

            if not luser or not lpassword:
                return self.quart.abort(400)

            if self.db_flag:
                valid = await dh.check_login(luser, lpassword)
            else:
                # Fix for issue https://github.com/SpionQuark/SimpleSite/issues/1
                # Old approach (if new one does not work or has some other issues)
                # valid = luser == getenv("DEF_USER") and lpassword == getenv("DEF_PASS")
                valid = hmac.compare_digest(luser, getenv("DEF_USER")) and hmac.compare_digest(lpassword, getenv("DEF_PASS"))

            if not valid:
                return self.quart.abort(401)

            login_user(AuthUser(luser))
            return self.quart.redirect(f"{referal if referal.startswith('/') else '/'+referal}")

        self.app.add_url_rule(route, f"{route}_login_get", login_page, methods=["GET"])
        self.app.add_url_rule(route, f"{route}_login_post", login, methods=["POST"])

    def _init_necessary_paths(self):
        @self.app.route("/favicon.ico")
        async def favicon():
            return self.quart.abort(404)

    def createForm(self, route:str, html: str = None, **kwargs):
        if not self.db_flag:
            raise DatabaseNotAllowedError("Set USE_DB=True in your .env file to use forms!")

        def parseArgsToSchema(**kwargs):
            fields = []
            for name, default in kwargs.items():
                py_type = type(default) if default is not None else str
                fields.append({
                    "name": name,
                    "type": TYPE_MAP.get(py_type, "text"),
                    "default": default,
                    "required": default is None
                })
            return {
                "endpoint": f"{route}/submit",
                "fields": fields
            }

        async def make_schema_view():
            schema = parseArgsToSchema(**kwargs)
            if not html:
                return await self.quart.render_template_string('''
                <auto-form>{{ schema | tojson }}</auto-form>
                <script src={{ auto_form }}></script>
                ''', schema=schema)
            if os.path.isfile(html):
                return await self.quart.render_template(html, schema=schema)
            else:
                return await self.quart.render_template_string(html, schema=schema)

        async def receive_answer():
            data = await self.quart.request.form
            print(data["data"])
            inputs = json.loads(data["data"])

            _data = dict()

            for input in inputs["fields"]:
                _data[input["name"]] = data[input["name"]]
            print(_data)
            return self.quart.redirect("/form")

        self.app.add_url_rule(
            route, f"{route}", make_schema_view
        )
        self.app.add_url_rule(
            rule=f"{route}/submit", endpoint=f"{route}_form_submit", methods=["POST"], view_func=receive_answer
        )

    def run(self, host='127.0.0.1', port=5000):
        """
        Runs the Quart app.
        param host: The host to run the app on. Default is '127.0.0.1'.
        param port: The port to run the app on. Default is 5000.
        param debug: Whether to run the app in debug mode. Default is True.
        """

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
        def inject_simplesite_assets() -> dict[str, str]:
            from quart import url_for
            return {
                "login": url_for(endpoint="script_inject.static", filename="js/login.js"),
                "auto_form": url_for(endpoint="script_inject.static", filename="js/auto-form.js")
            }

        from uvicorn import run
        run(self.app, host=host, port=port)
