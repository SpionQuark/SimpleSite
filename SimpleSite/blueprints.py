from quart import Blueprint
import os

_package_dir = os.path.dirname(os.path.abspath(__file__))

bp_scripts = Blueprint(
    "script_inject",
    __name__,
    static_folder=os.path.join(_package_dir, "templating"),
    static_url_path="/_simplesite/static",
)