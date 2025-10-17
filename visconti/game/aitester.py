from . import views

class Game():
    def __init__(self, ais):
        self.ais = ais
    
    def run(self):
        views.testMatch(self.ais)

players = ["randy", "randy", "randy"]
game = Game(players)
game.run()