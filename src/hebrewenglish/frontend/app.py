from nicegui import ui

from hebrewenglish.gui.page import davar_page, demo_page


class App:
    def __init__(self):
        pass

    def run(self, host: str = "0.0.0.0", port: int = 8080, show: bool = True):
        ui.page("/")(davar_page)
        ui.page("/demo")(demo_page)
        ui.run(title="Davar", host=host, port=port, show=show, reload=False)
