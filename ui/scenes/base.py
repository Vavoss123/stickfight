class Scene:
    music = "menu"     # what plays on this screen (see ui/music.py), or "keep" for no change

    def __init__(self, app):
        self.app = app

    def handle(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surf):
        pass
