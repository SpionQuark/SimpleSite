class ErrorRegistry:
    def __init__(self, quart_app, quart):
        self.quart_app = quart_app
        self.quart = quart
        self.error_codes = [
            {"code": 400, "text": "Bad Request"}, {"code": 401, "text": "Unauthorized"},
            {"code": 403, "text": "Forbidden"}, {"code": 404, "text": "Not Found"},
            {"code": 405, "text": "Method Not Allowed"}, {"code": 500, "text": "Internal Server Error"},
            {"code": 502, "text": "Bad Gateway"}, {"code": 503, "text": "Service Unavailable"},
        ]
        self.error_templates = self._load_default_error_templates()
        self._register_error_handlers()

    def _load_default_error_templates(self):
        return {
            entry["code"]: (
                f"<h1>{entry['code']} - {entry['text']}</h1>"
                f"<p>Contact the site owner if the error persists or try again later</p>"
                f"<a href='/'>← Back</a>"
            )
            for entry in self.error_codes
        }

    def _has_custom_template(self, code):
        import os
        template_dir = self.quart_app.template_folder or "templates"
        template_path = os.path.join(self.quart_app.root_path, template_dir)
        os.makedirs(template_path, exist_ok=True)
        return f"{code}.html" in os.listdir(template_path)

    def _register_error_handlers(self):
        for entry in self.error_codes:
            code = entry["code"]
            use_custom = self._has_custom_template(code)

            @self.quart_app.errorhandler(code)
            async def handler(e, code=code, use_custom=use_custom):
                if use_custom:
                    return await self.quart.render_template(f"{code}.html"), code
                return self.error_templates[code], code
            


class DatabaseNotAllowedError (Exception):
    def __init__(self, message):
        super().__init__(message)
        self.error = "Usage of database not permitted in .env"
