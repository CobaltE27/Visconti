
import random
from . import aiplayer
from . import models

#initialize state
class Game():
    def __init__(self, ais):
        self.nameIndex = 0
        players = []
        for ai in ais:
            players.append(self.newPlayer(ai))
        self.state = {
            "host": self.newHost(),
            "players": players
        }

    def newPlayer(self, ai: str):
        playerProto = {
            "fields": {
                "ai": ai,
                "name": ai + str(self.nameIndex),
                "current_bid": 0,
                "lots": "",
                "money": 40,
                "money_spent": 0,
                "reward_pyramid": 0,
                "reward_pyramid_rank": 0,
                "reward_rank": 0,
                "cloth": 0,
                "dye": 0,
                "furs": 0,
                "grain": 0,
                "spice": 0,
            }
        }
        self.nameIndex += 1
        return playerProto
    
    def newHost(self):
        hostProto = {
            "fields": {
                "bidder": "",
                "chooser": "",
                "day": 1,
                "deck": "",
                "group_lots": "",
                "phase": "",
            }
        }
        return hostProto

    def run(self):
        print("running")
        hostF = self.state["host"]["fields"]
        while hostF["day"] <= 3:
            self.start_day()
            while hostF["phase"] == models.Phase.CHOOSING:
                chooser = self.playerFieldsWithName(hostF["chooser"])
                if hostF["group_lots"] == "":
                    playerDraws = True
                else:
                    playerDraws = aiplayer.aiDictionary[chooser].draw(self.state)

                if playerDraws and self.can_draw(): #draw
                    self.add_to_group(self.draw_lot())
                    self.move_to_next_chooser()
                elif hostF["group_lots"] != "": #move to bidding
                    self.end_choosing_phase()

    def start_day(self):
        '''Selects the first chooser, and sets up for choosing phase, clears players' lots, logging the current day and such.'''
        self.select_first_chooser()
        players = self.state["players"]
        self.host.deck = models.get_full_deck(len(players))
        self.host.group_lots = ""
        self.host.harbor = ""
        self.host.phase = models.Phase.CHOOSING
        for p in players:
            p = p["fields"]
            p["lots"] = ""
            p["money_spent"] = 0
            p["reward_rank"] = 0
            p["reward_pyramid"] = 0
            p["reward_pyramid_rank"] = 0
    
    def select_first_chooser(self):
        '''Sets the chooser by least money, picking randomly on first day/ties, logs this'''
        host = self.state["host"]["fields"]
        players = self.state["players"]
        if host.day == 1:
            player = random.choice(players)["fields"]
        else:
            min = None
            for p in players:
                p = p["fields"]
                if not min or p["money"] < min: player = p
        host["chooser"] = player["name"]

    def playerFieldsWithName(self, name:str):
        for p in self.state["players"]:
            p = p["fields"]
            if p["name"] == name:
                return p
        return None