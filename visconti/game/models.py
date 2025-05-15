from django.db import models
import random
from enum import Enum
from django.db.models import F

class Phase(str, Enum):
    joining = "joining"
    choosing = "choosing"
    bidding = "bidding"
    end = "end"

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

def claim_lots(playerName: str):
    player = Player.objects.get(name=playerName)
    host = Host.objects.all().first()
    player.lots += " " + host.group_lots
    host.group_lots = ""
    player.save()
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