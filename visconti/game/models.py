from django.db import models
import random
from enum import Enum
from django.db.models import F
import re

class Phase(str, Enum):
    joining = "joining"
    choosing = "choosing"
    bidding = "bidding"
    end = "end"

class Good(str, Enum):
    grain = "grain"
    cloth = "cloth"
    dye = "dye"
    spice = "spice"
    furs = "furs"

# Create your models here.
class Host(models.Model):
    localIP = models.CharField(max_length=20)
    phase = models.CharField(max_length=20, default=Phase.joining, null=False) #joining, choosing, bidding, end
    day = models.IntegerField(default=1, null=False, min=1, max=3)
    group_lots = models.CharField(max_length=20, default="", null=False)
    deck = models.CharField(max_length=500, default="", null=False)
    chooser = models.CharField(max_length=100, default="")
    bidder = models.CharField(max_length=100, default="")

class Player(models.Model):
    name = models.CharField(max_length=100, unique=True)
    money = models.IntegerField(default=40, min=0)
    lots = models.CharField(max_length=20, default="", null=False)
    current_bid = models.IntegerField()
    grain = models.IntegerField(default=0, null=False, max=7, min=0)
    cloth = models.IntegerField(default=0, null=False, max=7, min=0)
    dye = models.IntegerField(default=0, null=False, max=7, min=0)
    spice = models.IntegerField(default=0, null=False, max=7, min=0)
    furs = models.IntegerField(default=0, null=False, max=7, min=0)

def get_shuffled_deck(playerCount: int):
    deck = []
    costs = ["0", "1", "2", "3", "4", "5", "5"]
    goods = ["g", "c", "d", "s", "f"]
    deck.append("G10")
    for good in goods:
        for cost in costs:
            deck.append(good + cost)
    random.shuffle(deck)

    removed = (6 - playerCount) * 6
    deck = deck[removed:]

    return " ".join(deck)

def count_lots(lots: str):
    return len(lots.split())

def draw_lot():
    host = Host.objects.all().first()
    currentNumLots = count_lots(host.group_lots)
    if can_draw(currentNumLots):
        lotsList = host.deck.split()
        host.group_lots += " " + lotsList.pop(0)
        host.deck = " ".join(lotsList)
        host.save()

def can_draw(currentNumLots: int):
    if currentNumLots >= 3:
        return False
    players = Player.objects.all()
    for player in players:
        emptySpaces = 5 - count_lots(player.lots)
        if (emptySpaces >= currentNumLots + 1): #found at least one person who can bid
            return True
    return False

#move group lots to selected player, is playerName is None: lot group is discarded
def claim_lots(playerName: str):
    host = Host.objects.all().first()
    if playerName:
        player = Player.objects.get(name=playerName)
        player.lots += " " + host.group_lots
        player.save()
    host.group_lots = ""
    host.save()

def select_first_chooser():
    host = Host.objects.all().first()
    players = Player.objects.all().order_by("money")
    if host.day == 1:
        player = random.choice(players)
    else:
        player = players.first()
    return player.name

def start_day():
    host = get_host()
    players = get_players()
    host.chooser = select_first_chooser()
    host.deck = get_shuffled_deck(len(players))
    host.group_lots = ""
    host.phase = Phase.choosing
    host.bidder = get_next_indexed_player(get_players().get(name=host.chooser)).name
    host.save()

def move_to_next_bidder():
    host = get_host()
    host.bidder = get_next_indexed_player(get_players.get(name=host.bidder)).name
    host.save()

def move_to_next_chooser():
    host = get_host()
    host.chooser = get_next_indexed_player(get_players.get(name=host.chooser)).name
    host.save()

def score_day():
    print("scoring")
    players = get_players()
    #calculate costs
    playerCosts = dict()
    for p in players:
        playerCosts[p.name] = cost_of_lots(p.lots)
    playerCosts = {k: v for k, v in sorted(playerCosts.items(), key=lambda item: item[1], reverse=True)} #sort dictionary by descending cost
    rewards = [30, 20, 10]
    currentRewardIndex = 0
    while (currentRewardIndex < len(rewards)):
        highestPlayers = [playerCosts.keys[0]]
        highestCost = [playerCosts.items[0]]
        for key in playerCosts.keys[1:]:
            if playerCosts[key] == highestCost:
                highestPlayers.append(playerCosts[key])
            else:
                break
        portion = sum(rewards[currentRewardIndex : min(currentRewardIndex + len(highestPlayers), len(rewards))]) // len(highestPlayers)
        for pName in highestPlayers:
            Player.objects.get(name=pName).money += portion
        currentRewardIndex += len(highestPlayers)
    #update pyramids
    goodsNames = {Good.grain, Good.cloth, Good.dye, Good.spice, Good.furs}
    for p in players:
        p.grain = min(p.grain + p.lots.count("g"), 7)
        p.cloth = min(p.cloth + p.lots.count("c"), 7)
        p.dye = min(p.dye + p.lots.count("d"), 7)
        p.spice = min(p.spice + p.lots.count("s"), 7)
        p.furs = min(p.furs + p.lots.count("f"), 7)
        #clear lots
        p.lots = ""
        #absolute pyramid points
        for good in goodsNames:
            p.money += cumulative_pyramid_score(getattr(p, good))
    #relative pyramid points
    levelRewards = [10, 5]
    currentRewardIndex = 0
    for good in goodsNames:
        for l in range(7,-1,-1):
            levelPlayers = []
            for p in players:
                if getattr(p, good) == l:
                    levelPlayers.append(p.name)
            portion = sum(levelRewards[currentRewardIndex : min(currentRewardIndex + len(levelPlayers), len(levelRewards))]) // len(levelPlayers)
            for winner in levelPlayers:
                Player.objects.get(name=winner).money += portion
            currentRewardIndex += len(levelPlayers)
            if currentRewardIndex >= len(levelRewards):
                break

def cumulative_pyramid_score(level: int) -> int:
    if level == 7: return 20
    if level == 6: return 10
    if level == 5: return 5
    return 0

def cost_of_lots(lots: str) -> int:
    lotList = lots.split()
    sum = 0
    for lot in lotList:
        sum += int(filter(str.isdigit, lot))
    return sum

def get_players() -> models.BaseManager[Player]:
    return Player.objects.all().order_by(id)

def get_next_indexed_player(player: Player) -> Player:
    players = get_players()
    next = False
    for p in players:
        if next:
            return p
        if p.id == player.id:
            next = True
    return players.first() #if the loop is over and no player was returned, the current player is last by id so we srap around

def get_host() -> Host:
    return Host.objects.all().first()