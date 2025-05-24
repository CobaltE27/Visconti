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
    WAITING = "waiting"

class Good(str, Enum):
    GRAIN = "grain"
    CLOTH = "cloth"
    DYE = "dye"
    SPICE = "spice"
    FURS = "furs"

class RewardSources(str, Enum):
    RANK = "rank"
    PYRAMID_TOP = "pyramid"
    PYRAMID_RANK = "pyramid_rank"

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
    log = models.TextField(default="<span><strong>Match opened.</strong></span>")

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
    ready = models.BooleanField(default=False)
    money_spent = models.IntegerField(default=0)
    reward_rank = models.IntegerField(default=0)
    reward_pyramid = models.IntegerField(default=0)
    reward_pyramid_rank = models.IntegerField(default=0)

def get_shuffled_deck(playerCount: int) -> str:
    '''Returns a space-seperated string containing and amount of lots appropriate for the given number of players'''
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

def draw_lot() -> str:
    '''Removes a lot from the deck and returns it.'''
    host = get_host()
    if can_draw():
        lotsList = host.deck.split()
        draw = lotsList.pop(0)
        host.deck = " ".join(lotsList)
        host.save()
        return draw

def add_to_group(lot: str):
    '''Adds the given lot to the current group lots, displays a message indicating which lot was drawn'''
    host = get_host()
    if host.group_lots == "":
        host.group_lots += lot
    else:
        host.group_lots += " " + lot
    host.save()
    add_line_to_log(format_lots(lot) + " was drawn.")

def add_to_player_lots(playerName: str, lotOrLots: str):
    '''Adds the given lot string to the given player's lots.'''
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

def claim_lots(playerName: str):
    '''Moves lots from the current group to the given player, or delete them if None is given, subtracting bid money and logging this action.'''
    host = Host.objects.all().first()
    if playerName:
        player = Player.objects.get(name=playerName)
        player.money -= player.current_bid
        player.money_spent += player.current_bid
        player.save()
        add_to_player_lots(player.name, host.group_lots)
        logLine = format_player_name(playerName) + " claimed " + format_lots(host.group_lots) + " for " + format_money(player.current_bid) + "."
    else:
        logLine = "Lacking any bids, the group " + format_lots(host.group_lots) + " was tossed into the harbor."
    host.group_lots = ""
    host.save()
    add_line_to_log(logLine)

def select_first_chooser():
    '''Sets the chooser by least money, picking randomly on first day/ties, logs this'''
    host = Host.objects.all().first()
    players = Player.objects.all().order_by("money")
    if host.day == 1:
        player = random.choice(players)
    else:
        player = players.first()
    host.chooser = player.name
    host.save()
    add_line_to_log("The first chooser is " + format_player_name(get_host().chooser) + ".")

def start_day():
    '''Selects the first chooser, and sets up for choosing phase, clears players' lots, logging the current day and such.'''
    add_line_to_log("Start choosing for day " + str(get_host().day) + ".", True)
    select_first_chooser()
    host = get_host()
    players = get_players()
    host.deck = get_shuffled_deck(len(players))
    host.group_lots = ""
    host.phase = Phase.CHOOSING
    host.save()
    for p in get_players():
        p.lots = ""
        p.ready = False
        p.money_spent = 0
        p.reward_rank = 0
        p.reward_pyramid = 0
        p.reward_pyramid_rank = 0
        p.save()

def move_to_next_bidder():
    '''Changes the bidder to the next viable option, logging all skipped players and the next viable bidder.'''
    host = get_host()
    linesToLog = []
    while True:
        host.bidder = get_next_indexed_player(get_players().get(name=host.bidder)).name
        bidderLotCount = count_lots(get_players().get(name=host.bidder).lots)
        if bidderLotCount < 5 and count_lots(host.group_lots) <= 5 - bidderLotCount:
            break
        linesToLog.append(format_player_name(host.bidder) + " cannot bid.")
    host.save()
    for l in linesToLog:
        add_line_to_log(l)
    add_line_to_log(format_player_name(get_host().bidder) + " is now bidding.")

def is_remaining_bidder() -> bool:
    '''returns if anyone is left who can bid'''
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
    '''Sets the chooser to the nex viable option in turn order, logging viable chooser and skipped choosers'''
    host = get_host()
    linesToLog = []
    while True:
        host.chooser = get_next_indexed_player(get_players().get(name=host.chooser)).name
        if count_lots(get_players().get(name=host.chooser).lots) < 5: 
            break
        linesToLog.append(format_player_name(host.chooser) + " has too many lots to choose.")
    host.save()
    for l in linesToLog:
        add_line_to_log(l)
    add_line_to_log(format_player_name(get_host().chooser) + " is now choosing.")

def score_day():
    '''Distributes rewards, updates pyramids, logging such'''
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
            add_money(pName, portion, RewardSources.RANK)
            add_line_to_log(format_player_name(pName) + " is awarded " + format_money(portion) + " (" + format_rank_index(currentRewardIndex) + ").")
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
        #absolute pyramid points
        for good in goodsNames:
            reward = cumulative_pyramid_score(getattr(p, good))
            p.money += reward
            p.reward_pyramid += reward
            if (reward > 0):
                add_line_to_log(format_player_name(p.name) + " is awarded " + format_money(reward) + " for their investment in " + good + ".")
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
                    for winnerName in levelPlayers:
                        add_money(winnerName, portion, RewardSources.PYRAMID_RANK)
                        add_line_to_log(format_player_name(winnerName) + " is awarded " + format_money(portion) + " (" + format_rank_index(currentRewardIndex) + " in " + good + ").")
                        # print("pr:" + winner + str(portion))
                currentRewardIndex += len(levelPlayers)
    
    playerMoneyTotals = ""
    for p in get_players():
        playerMoneyTotals += format_player_name(p.name) + ": " + format_money(p.money) + ", "
    add_line_to_log("After scoring: " + playerMoneyTotals[:len(playerMoneyTotals) - 2] + ".")

def end_bidding_phase():
    '''Claims lots for highest bidder, gives lots to last non-full player if applicable, scores players, determines which phase comes next.
    If the day is over, increments day and starts new one.
    If the day continues, selects next chooser.
    Logs all this.'''
    players = get_players()
    highestBid = 0
    highestPlayerName = None
    for p in players:
        if p.current_bid > highestBid:
            highestBid = p.current_bid
            highestPlayerName = p.name
    claim_lots(highestPlayerName)

    add_line_to_log("Bidding is over.", True)

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
            drawnLot = draw_lot()
            add_to_player_lots(leftoverPlayer, drawnLot)
            add_line_to_log(format_player_name(leftoverPlayer) + " gets " + format_lots(drawnLot) + "for free.")
        add_line_to_log("Auctioning is over for the day.", True)

        score_day()

        host = get_host()
        host.bidder = ""
        if (host.day == 3):
            host.phase = Phase.END
            host.save()
            add_line_to_log("The game is over.", True)
        else:
            host.phase = Phase.WAITING
            host.save()
    else: #more space to fill, go to next chooser for the day
        host = get_host()
        host.phase = Phase.CHOOSING
        host.save()
        add_line_to_log("Begin choosing lots to auction.", True)
        move_to_next_chooser()

def end_choosing_phase():
    '''Changes phase and sets up for bidding, logs the phase change.'''
    add_line_to_log("Start bidding.", True)
    host = get_host()
    host.phase = Phase.BIDDING
    #bidding setup
    host.bidder = get_players().get(name=host.chooser).name
    host.save()
    move_to_next_bidder() #find first viable bidder after chooser
    for p in get_players():
        p.current_bid = 0
        p.save()

def end_waiting_phase():
    host = get_host()
    host.day += 1
    host.save()
    start_day()

def add_money(name: str, amount: int, source: RewardSources=None):
    '''Increases the given player's money by the given amount.'''
    p = Player.objects.get(name=name)
    p.money += amount
    if source != None:
        if source == RewardSources.RANK:
            p.reward_rank += amount
        elif source == RewardSources.PYRAMID_RANK:
            p.reward_pyramid_rank += amount
        elif source == RewardSources.PYRAMID_TOP:
            p.reward_pyramid += amount
    p.save()

def advance_step():
    '''Increments game's step counter.'''
    host = get_host()
    host.steps += 1
    host.save()

def add_line_to_log(line: str, bold:bool=False):
    '''Add the given string to game logs'''
    host = get_host()
    if bold:
        host.log = "<span>" + format_bold(line) + "</span>" + host.log
    else:
        host.log = "<span>" + line + "</span>" + host.log
    host.save()

def format_lots(lots: str) -> str:
    '''formats lots into a loggable group'''
    lotsList = lots.split()
    goodClass = ""
    for (i, lot) in enumerate(lotsList):
        if "G" in lot:
            goodClass = "gold"
        elif "g" in lot:
            goodClass = Good.GRAIN
        elif "c" in lot:
            goodClass = Good.CLOTH
        elif "d" in lot:
            goodClass = Good.DYE
        elif "s" in lot:
            goodClass = Good.SPICE
        elif "f" in lot:
            goodClass = Good.FURS
        lotsList[i] = '<abbr class="' + goodClass + '">[' + lot + ']</abbr>'
    return "".join(lotsList)

FLORIN = "ƒ"
def format_money(money: int) -> str:
    '''formats money for logging'''
    sign = "-" if money < 0 else ""
    return sign + FLORIN + str(abs(money))

SUFFIXES = {1: 'st', 2: 'nd', 3: 'rd'}
def format_rank_index(index: int) -> str:
    '''Returns ordinal number string for given index under 10, 0 -> 1st and so on.'''
    # Adapted from https://gist.github.com/FlantasticDan/3eb192fac85ab5efa2002fb7165e4f35
    return str(index + 1) + SUFFIXES.get(index + 1, "th")

def format_bold(input: str) -> str:
    '''Formats a string as bold for logging'''
    return "<strong>" + input + "</strong>"

def format_player_name(name: str) -> str:
    '''Formats player's name for logging'''
    return format_bold(name)

def cumulative_pyramid_score(level: int) -> int:
    '''Returns money rewarded for being on the given pyramid tier independent of ranking.'''
    if level == 7: return 20
    elif level == 6: return 10
    elif level == 5: return 5
    return 0

def highest_bid() -> int:
    '''Finds highest current bid among players.'''
    return Player.objects.all().order_by("-current_bid").first().current_bid

def cost_of_lots(lots: str) -> int:
    '''Determines numeric value of lots string'''
    lotList = lots.split()
    sum = 0
    for lot in lotList:
        sum += int(re.sub(r"\D", "", lot))
    return sum

def get_players() -> models.Manager[Player]:
    return Player.objects.all().order_by("id")

def get_next_indexed_player(player: Player) -> Player:
    '''Returns the player next in turn order (next highest id)'''
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