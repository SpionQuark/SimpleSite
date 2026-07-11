# SimpleSite

Host a website in three lines of Python. SimpleSite is a thin, ergonomic layer over [Quart](https://quart.palletsprojects.com/)
that removes the boilerplate of serving static pages, without hiding Quart underneath if you ever need it.

```python
from SimpleSite.easyhost import App

app = App()
app.hostStatic("/", "index.html")
app.hostStatic("/about", "<h1>About us</h1>")
app.run(port=8000)
```

## Why?

Serving a simple static page or two with Quart/Flask normally means writing a route, a view function and wiring up templates by hand. **Every time**. SimpleSite collapses that down to one call per page, while still giving you:

- **File or inline HTML**: point `hostStatic` at a file, a folder or just pass raw HTML directly

- **Automatic error pages**: Drop a `404.html` / `500.html` / etc. into your `templates/` folder and SimpleSite serves it automatically on the matching error. No file? You get a built-in fallback instead of a stack trace.

- Still just Quart: The underlying app is a real `quart.Quart` instance. Nothing is hidden. More on how to still use `quart.Quart` later. You can reach in and use Quart/Jinja features directly whenever you need to.

## Install

*Not yet published! For now clone the repo and import it locally*

Requires Python>=3.10

After cloning run 
```shell
pip install -r requirements.txt
```

## Quick start

```python

from SimpleSite.easyhost import App

app = App()

# Serve a file
app.hostStatic("/", "index.html")

# Serve a whole folder (looks for index.html inside it)
app.hostStatic("/docs", "docs/")

# Serve raw HTML directly, no file needed
app.hostStatic("/hello", "<h1>Hello, world!</h1>")

# Finally host the page
app.run(host="127.0.0.1", port=8000)

```

## Custom error pages

SimpleSite scans your `templates/` folder at startup for files named after HTTP status codes:

```
templates/
├── 404.html
├── 500.html
└── 403.html
```

If a matching file exists, it's served automatically when that error occurs. If not, SimpleSite falls back to a built-in error page. Your site never shows a raw traceback to visitors thanks to the fallbacks.

Supported codes out of the box: `400, 401, 403, 404, 405, 500, 502, 503`

## API reference

### `App`

Creates a new SimpleSite application, wrapping a Quart app internally.

### `app.hostStatic(route: str, source: str, secure: bool = False)`

Registers a route

| ``source`` is... | Behaviour |
| ---------------- | --------- |
| a file path      | Serves that file at ``route``|
| a directory path | Serves ``index.html`` from that directory |
| a raw HTML string| Serves the string directly as the page content |

To distinguish those three types, SimpleSite checks if the source is a file. If that check misses, it checks if the path is a directory. If that misses too, it currently assumes that it is a raw HTML string.

---

``route`` should be named ``/<route>`` as a naming convention, but can also be ``<route>``.

``super duper route to my site``<br> will be parsed  as<br>``/super-duper-route-to-my-site``.

---
Hosts with the ``secure=True`` attribute will require being logged in. For that one has to create a ``.env``-file within the project directory.



### ``app.run(host="127.0.0.1", port=5000)``

Starts the server (via [`uvicorn`](https://uvicorn.dev/) under the hood)

### How to still use Quart if needed?

```python
from SimpleSite.easyhost import App

app = App()

# Use the Quart component to create a specific endpoint
@app.app.route("/")
async def index():
    return await app.quart.render_template("index.html")
```

| Name | What it is | What it can be used for |
| ---   | ---------------- | ------------------------------------- |
| app   | The Quart-Object | Used to add more routes or websockets |
| quart | The thing | Call any function requires the application context, but not the object (e.g. ``render_template()``) |


## Structure

### SimpleSite

```
SimpleSite/
├── conf/
│   ├── paths.toml
│   └── customs.toml
├── requirements.txt
├── ReadMe.md
├── .gitignore
├── templates/
├── .env
├── easyhost.py
└── error_registry.py
```

Content for ``.env``:

```.env
DEF_USER='Admin-Username'
DEF_PASS='super-secure-admin-pass'
USE_DB=True
```

| Fieldname | What it is used for | IsRequired | What happens without? |
| --------- | ------------------- | ---------- | --------------------- |
| DEF_USER  | The username you need for any login added using SimpleSite | False | The secure-flag for the endpoints is not added, resulting in insecure endpoints |
| DEF_PASS  | The password you need for any login added using SimpleSite | False | The secure-flag for the endpoints is not added, resulting in insecure endpoints |
| USE_DB | Determine if the DB should be used | False | The database won't be used. However, if ``DEF_PASS`` and ``DEF_USER`` are given it uses plain-text comparison. With DB a Argon2 hash will be used.


### Project built with SimpleSite

```
SimpleSite/
Project/
├── main.py
├── templates (folder with all html-files)
├── static (folder with all scripts/stylesheets etc)
└── others
```

Import for ``main.py``

```python
from SimpleSite.easyhost import App
```



## Roadmap

- [ ]  hostFolder(): auto-map an entire directory to routes, file-based-routing style
- [ ] Dev mode with live reload
- [ ] Config file support for error template overrides
- [ ] Login-Templating



# License

**MIT**