from django.db import models
import random

# Create your models here.
class Host(models.Model):
    localIP = models.CharField(max_length=20)
    phase = models.CharField(max_length=20, default="joining", null=False)
    day = models.IntegerField(default=1, null=False, min=1, max=3)
    group_lots = models.CharField(max_length=20, default="", null=False)
    deck = models.CharField(max_length=500, default="", null=False)
    chooser = models.CharField(max_length=100)
    bidder = models.CharField(max_length=100)

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

def shuffle_deck(playerCount: int):
    deck = []
    costs = ["0", "1", "2", "3", "4", "5", "5"]
    goods = ["g", "c", "d", "s", "f"]
    deck.add("G10")
    for good in goods:
        for cost in costs:
            deck.add(good + cost)
    random.shuffle(deck)

    removed = (6 - playerCount) * 6
    deck = deck[removed:]

    return " ".join(deck)

def count_lots(lots: str):
    return len(lots.split())

def draw_lot():
    max_lots = 3
    host = Host.objects.all().first()
    currentNumLots = count_lots(host.group_lots)
    if (currentNumLots < max_lots):
        players = Player.objects.all()
        couldBid = False
        for player in players:
            emptySpaces = 5 - count_lots(player.lots)
            if (emptySpaces >= currentNumLots + 1): #found at least one person who can bid
                lotsList = host.deck.split()
                host.group_lots += " " + lotsList.pop(0)
                host.deck = " ".join(lotsList)
                host.save()
                break

def claim_lots(playerName: str):
    player = Player.objects.get(name=playerName)
    host = Host.objects.all().first()
    player.lots += " " + host.group_lots
    host.group_lots = ""
    player.save()
    host.save()