from SimpleSite.easyhost import App

app = App()

app.hostStatic("/", "<h1>Index</h1>")

app.run()