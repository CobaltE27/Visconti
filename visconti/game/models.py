from django.db import models
import random
from enum import Enum
from django.db.models import F
import re

class Phase(str, Enum):
    JOINING = "joining"
    CHOOSING = "choosing"
    BIDDING = "bidding"
    END = "end"

class Good(str, Enum):
    GRAIN = "grain"
    CLOTH = "cloth"
    DYE = "dye"
    SPICE = "spice"
    FURS = "furs"

# for what to do if migrations fail after no such column or no such table https://stackoverflow.com/questions/34548768/no-such-table-exception
# Create your models here.
class Host(models.Model):
    localIP = models.CharField(max_length=20)
    phase = models.CharField(max_length=20, default=Phase.JOINING, null=False) #joining, choosing, bidding, end
    day = models.IntegerField(default=1, null=False)
    group_lots = models.CharField(max_length=20, default="", null=False)
    deck = models.CharField(max_length=500, default="", null=False)
    chooser = models.CharField(max_length=100, default="")
    bidder = models.CharField(max_length=100, default="")
    steps = models.IntegerField(default=0)
    log = models.TextField(default="Match opened.\n")

class Player(models.Model):
    name = models.CharField(max_length=100, unique=True)
    money = models.IntegerField(default=40)
    lots = models.CharField(max_length=20, default="", null=False)
    current_bid = models.IntegerField()
    grain = models.IntegerField(default=0, null=False)
    cloth = models.IntegerField(default=0, null=False)
    dye = models.IntegerField(default=0, null=False)
    spice = models.IntegerField(default=0, null=False)
    furs = models.IntegerField(default=0, null=False)

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

#returns drawn lot
def draw_lot() -> str:
    host = get_host()
    if can_draw():
        lotsList = host.deck.split()
        draw = lotsList.pop(0)
        host.deck = " ".join(lotsList)
        host.save()
        return draw

#adds lot to group and saves the group
def add_to_group(lot: str):
    host = get_host()
    if host.group_lots == "":
        host.group_lots += lot
    else:
        host.group_lots += " " + lot
    host.save()

def add_to_player_lots(playerName: str, lotOrLots: str):
    player = get_players().get(name=playerName)
    if player.lots == "":
        player.lots += lotOrLots
    else:
        player.lots += " " + lotOrLots
    player.save()

def can_draw():
    currentNumLots = count_lots(get_host().group_lots)
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
        player.money -= player.current_bid
        player.save()
        add_to_player_lots(player.name, host.group_lots)
    host.group_lots = ""
    host.save()

#sets host.chooser
def select_first_chooser():
    host = Host.objects.all().first()
    players = Player.objects.all().order_by("money")
    if host.day == 1:
        player = random.choice(players)
    else:
        player = players.first()
    host.chooser = player.name
    host.save()

def start_day():
    select_first_chooser()
    host = get_host()
    players = get_players()
    host.deck = get_shuffled_deck(len(players))
    host.group_lots = ""
    host.phase = Phase.CHOOSING
    host.save()
    for p in get_players():
        p.lots = ""
        p.save()

def move_to_next_bidder():
    host = get_host()
    while True:
        host.bidder = get_next_indexed_player(get_players().get(name=host.bidder)).name
        bidderLotCount = count_lots(get_players().get(name=host.bidder).lots)
        if bidderLotCount < 5 and count_lots(host.group_lots) <= 5 - bidderLotCount:
            break
    host.save()

def is_remaining_bidder() -> bool:
    host = get_host()
    hypothBidder = get_players().get(name=host.bidder)
    while True:
        hypothBidder = get_next_indexed_player(hypothBidder)
        bidderLotCount = count_lots(hypothBidder.lots)
        if bidderLotCount < 5 and count_lots(host.group_lots) <= 5 - bidderLotCount:
            return True
        if hypothBidder.name == host.chooser:
            break
    return False

def move_to_next_chooser():
    host = get_host()
    while True:
        host.chooser = get_next_indexed_player(get_players().get(name=host.chooser)).name
        if count_lots(get_players().get(name=host.chooser).lots) < 5: 
            break
    host.save()

#tallies scores for players, empties all players' lots
def score_day():
    #calculate costs
    players = get_players()
    playerCosts = dict()
    for p in players:
        playerCosts[p.name] = cost_of_lots(p.lots)
    playerCosts = {k: v for k, v in sorted(playerCosts.items(), key=lambda item: item[1], reverse=True)} #sort dictionary by descending cost
    rewards = []
    if len(players) == 3: rewards = [30, 15]
    elif len(players) == 4: rewards = [30, 20, 10]
    elif len(players) == 5: rewards = [30, 20, 10, 5]
    elif len(players) == 6: rewards = [30, 20, 15, 10, 5]
    currentRewardIndex = 0
    while (currentRewardIndex < len(rewards)):
        highestPlayers = [list(playerCosts.keys())[0]]
        highestCost = list(playerCosts.values())[0]
        for key in list(playerCosts.keys())[1:]:
            if playerCosts[key] == highestCost:
                highestPlayers.append(key)
            else:
                break
        portion = sum(rewards[currentRewardIndex : min(currentRewardIndex + len(highestPlayers), len(rewards))]) // len(highestPlayers)
        for pName in highestPlayers:
            add_money(pName, portion)
            # print("r:" + pName + str(portion))
        currentRewardIndex += len(highestPlayers)
        for highest in highestPlayers:
            del playerCosts[highest]
    #update pyramids
    goodsNames = {Good.GRAIN, Good.CLOTH, Good.DYE, Good.SPICE, Good.FURS}
    players = get_players()
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
            # print("pc:" + p.name + str(cumulative_pyramid_score(getattr(p, good))))
        p.save()
    #relative pyramid points
    levelRewards = [10, 5]
    for good in goodsNames:
        currentRewardIndex = 0
        for l in range(7,-1,-1):
            if currentRewardIndex < len(levelRewards):
                levelPlayers = []
                for p in players:
                    if getattr(p, good) == l:
                        levelPlayers.append(p.name)
                if len(levelPlayers) > 0:
                    portion = sum(levelRewards[currentRewardIndex : min(currentRewardIndex + len(levelPlayers), len(levelRewards))]) // len(levelPlayers)
                    for winner in levelPlayers:
                        add_money(winner, portion)
                        # print("pr:" + winner + str(portion))
                currentRewardIndex += len(levelPlayers)

def end_bidding_phase():
    players = get_players()
    highestBid = 0
    highestPlayerName = None
    for p in players:
        if p.current_bid > highestBid:
            highestBid = p.current_bid
            highestPlayerName = p.name
    claim_lots(highestPlayerName)

    players = get_players()
    maxedCount = 0
    leftoverPlayer = None
    for p in players:
        if count_lots(p.lots) == 5: 
            maxedCount += 1
        else: 
            leftoverPlayer = p.name
    
    if (maxedCount >= len(players) - 1 or count_lots(get_host().deck) == 0): #all players but one maxed or deck empty, fill leftover and end bidding
        while count_lots(get_players().get(name=leftoverPlayer).lots) < 5 and count_lots(get_host().deck) > 0:
            add_to_player_lots(leftoverPlayer, draw_lot())

        score_day()

        host = get_host()
        host.bidder = ""
        if (host.day == 3):
            host.phase = Phase.END
            host.save()
        else:
            host.day += 1
            host.save()
            start_day()
    else: #more space to fill, go to next chooser for the day
        host = get_host()
        host.phase = Phase.CHOOSING
        host.save()
        move_to_next_chooser()

def end_choosing_phase():
    host = get_host()
    host.phase = Phase.BIDDING
    #bidding setup
    host.bidder = get_players().get(name=host.chooser).name
    host.save()
    move_to_next_bidder() #find first viable bidder after chooser
    for p in get_players():
        p.current_bid = 0
        p.save()

def add_money(name: str, amount: int):
    p = Player.objects.get(name=name)
    p.money += amount
    p.save()

def advance_step():
    host = get_host()
    host.steps += 1
    host.save()

def cumulative_pyramid_score(level: int) -> int:
    if level == 7: return 20
    elif level == 6: return 10
    elif level == 5: return 5
    return 0

def highest_bid() -> int:
    return Player.objects.all().order_by("-current_bid").first().current_bid

def cost_of_lots(lots: str) -> int:
    lotList = lots.split()
    sum = 0
    for lot in lotList:
        sum += int(re.sub(r"\D", "", lot))
    return sum

def get_players() -> models.Manager[Player]:
    return Player.objects.all().order_by("id")

def get_next_indexed_player(player: Player) -> Player:
    players = get_players()
    next = False
    for p in players:
        if next:
            return p
        if p.id == player.id:
            next = True
    return players.first() #if the loop is over and no player was returned, the current player is last by id so we wrap around

def get_host() -> Host:
    return Host.objects.all().first()