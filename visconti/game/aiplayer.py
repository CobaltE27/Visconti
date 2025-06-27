from abc import ABC, abstractmethod
import random
from . import models

class AIPlayer(ABC):
    '''AI players are static and must act based only on current game state, rteurning an invalid move will result in a move being made for this player automatically
    state refers to a nested dictionary representing the game state, this is identical in format to the JSON object printed to the browser console each update.
    Methods are time-limited to 5 seconds to prevent infinite looping, if an AI times out a default choice will be made for them.'''

    @abstractmethod
    def bid(state) -> int:
        '''Returns the integer amount this player will bid given the game state, a bid of 0 is counted as a pass'''
        pass

    @abstractmethod
    def draw(state) -> bool:
        '''Returns whether this player will draw another lot given the game state'''
        pass

class Randy(AIPlayer):
    '''Makes all game decisions randomly. 50% chance to draw each lot, 50% chance to pass or bid 1 higher.'''
    def bid(state) -> int:
        if bool(random.choice([True, False])):
            return 0
        
        highest = 0
        for p in state["players"]:
            bid = p["fields"]["current_bid"]
            if bid > highest: highest = bid
        if highest + 1 <= p["fields"]["money"]:
            return highest + 1
        return 0
    
    def draw(state) -> bool:
        return bool(random.choice([True, False]))
    
class Gian(AIPlayer):
    '''Indi's AI'''
    def bid(state) -> int:
        minBid = 0
        minBid += 1
        if minBid > myFields["money"]:
            return 0
        hFields = state["host"][0]["fields"]
        myName = hFields["bidder"]
        myFields = None
        for p in state["players"]:
            bid = p["fields"]["current_bid"]
            if bid > minBid: minBid = bid
            if p["fields"]["name"] == myName:
                myFields = p["fields"]
        groupAvg = Gian.averageQuality(hFields["group_lots"].split(" "))
        unseenAvg = Gian.averageQuality(Gian.unseenLots(state))
        oppAvgs = dict()
        for i, p in enumerate(state["players"]):
            if p["fields"]["name"] != myName:
                oppAvgs[i] = Gian.averageQuality(p["fields"]["lots"].split(" "))
        
        
        return 0
    
    def draw(state) -> bool:
        me = state["host"][0]["fields"]["chooser"]
        return True
    
    def unseenLots(state) -> list[str]:
        hFields = state["host"][0]["fields"]
        full = models.get_full_deck(6, False).split(" ")
        seen = hFields["harbor"].split(" ") + hFields["group_lots"].split(" ")
        for p in state["players"]:
            seen += p["fields"]["lots"].split(" ")
        for s in seen:
            full.remove(s)
        return full
    
    def averageQuality(lotList: list[str]):
        return models.cost_of_lots(" ".join(lotList)) / len(lotList)

class Errata(AIPlayer):
    '''Deliberately terrible AI that plays erratically and bids wildly'''
    def bid(state) -> int:
        if random.random() < 0.3:
            return 0
        
        hFields = state["host"][0]["fields"]
        myName = hFields["bidder"]
        myFields = None
        for p in state["players"]:
            if p["fields"]["name"] == myName:
                myFields = p["fields"]
        groupFraction = models.count_lots(hFields["group_lots"]) / 5
        max = min(int(myFields["money"]), 40) * groupFraction
        if models.highest_bid() < max:
            if myName == hFields["chooser"]:
                return models.highest_bid() + 1
            else:
                return max
        else:
            return 0

    def draw(state) -> bool:
        hFields = state["host"][0]["fields"]
        # myName = hFields["chooser"]
        # myLots = None
        # for p in state["players"]:
        #     if p["fields"]["name"] == myName:
        #         myLots = p["fields"]["lots"]
        # spacesLeft = 5 - models.count_lots(myLots)
        return models.count_lots(hFields["group_lots"]) < 1

aiDictionary = {
    "randy": Randy,
    "gian": Gian,
    "errata": Errata,
}