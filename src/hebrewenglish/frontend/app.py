from nicegui import ui

from hebrewenglish.gui.page import davar_page


class App:
    def __init__(self):
        pass

    def run(self):
        ui.page("/")(davar_page)
        ui.run(title="Davar", reload=False)
