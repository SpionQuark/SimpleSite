from SimpleSite.easyhost import App

app = App()

app.createLogin("/login", "login.html", referal="/s")

app.hostStatic("/", "<h1>Index</h1>")

app.hostStatic("/s", "<h1>Secure Part</h1>", True)

app.run()