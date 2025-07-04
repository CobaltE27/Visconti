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
    '''Indi's basic AI'''
    def bid(state: dict) -> int:
        hFields = state["host"][0]["fields"]
        myName = hFields["bidder"]
        myFields = None
        highestCurrentBid = 0
        for p in state["players"]:
            bid = int(p["fields"]["current_bid"])
            if bid > highestCurrentBid: highestCurrentBid = bid
            if p["fields"]["name"] == myName:
                myFields = p["fields"]
        
        unfilledTotal = 0
        for p in state["players"]:
            unfilledTotal += 5 - models.count_lots(p["fields"]["lots"])
        stateIfTake = state.copy()
        leaveScores = []
        for p in stateIfTake["players"]:
            if p["fields"]["name"] == myName:
                p["fields"]["lots"] = hFields["group_lots"] if p["fields"]["lots"] == "" else p["fields"]["lots"] + " " + hFields["group_lots"]
            else:
                stateIfThisOppTakes = state.copy()
                for opp in stateIfThisOppTakes["players"]:
                    if opp["fields"]["name"] == p["fields"]["name"]:
                        opp["fields"]["lots"] = hFields["group_lots"] if opp["fields"]["lots"] == "" else opp["fields"]["lots"] + " " + hFields["group_lots"]
                        leaveScores.append(Gian.scoreWithAvgUnseenFill(stateIfThisOppTakes))
        takeScore = Gian.scoreWithAvgUnseenFill(stateIfTake)
        avgLeaveScore = dict()
        for leaveScore in leaveScores:
            for pName in leaveScore.keys():
                avgLeaveScore[pName] = avgLeaveScore.get(pName, 0) + leaveScore[pName] / len(leaveScores)
        
        print(str(takeScore) + " " + str(leaveScores))
        diffByTake = takeScore[myName] - avgLeaveScore[myName]
        if diffByTake < 0: #taking would, on average, decrease our score
            return 0
        #taking if worth it, but how much?

        maxBid = min(diffByTake, int(myFields["money"])) #proof of concept, some fraction of diffByTake may be more optimal
        if highestCurrentBid > maxBid:
            return 0
        
        if hFields["chooser"] == myName:
            return highestCurrentBid + 1
        
        return maxBid
    
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
    
    def averageGoods(lotList: list[str]):
        avgs = { 
            "g": 0, 
            "c": 0,
            "d": 0,
            "s": 0,
            "f": 0,
        }
        for lot in lotList:
            if "G" != lot[0]:
                avgs[lot[0]] += 1
        for avg in avgs:
            avg /= len(lotList)
        return avgs
    
    def scoreWithAvgUnseenFill(stateCopy):
        pQualities = dict()
        pRewards = dict()
        deckCount = models.count_lots(stateCopy["host"][0]["fields"]["deck"])
        unseenAvg = Gian.averageQuality(Gian.unseenLots(stateCopy))
        unseenGoodsAvg = Gian.averageGoods(Gian.unseenLots(stateCopy))
        unfilledTotal = 0
        for p in stateCopy["players"]:
            unfilledTotal += 5 - models.count_lots(p["fields"]["lots"])
        dilutedUnseenAvg = unseenAvg * (deckCount / unfilledTotal)
        for p in stateCopy["players"]:
            pRewards[p["fields"]["name"]] = 0
            lotString = p["fields"]["lots"]
            remainingSlots = 5 - models.count_lots(lotString)
            pQualities[p["fields"]["name"]] = models.cost_of_lots(lotString) + remainingSlots * dilutedUnseenAvg
            for g in models.goodsNames:
                p["fields"][g] = min(p["fields"][g] + lotString.count(g[0]) + int(round(remainingSlots * unseenGoodsAvg[g[0]])), 7)
                pRewards[p["fields"]["name"]] += models.cumulative_pyramid_score(p["fields"][g])
        pQualities = {k: v for k, v in sorted(pQualities.items(), key=lambda item: item[1], reverse=True)} #sort dictionary by descending quality
        
        rewards = models.rankRewards[len(stateCopy["players"])]
        currentRewardIndex = 0
        while (currentRewardIndex < len(rewards)):
            highestPNames = [list(pQualities.keys())[0]]
            highestQuality = list(pQualities.values())[0]
            for key in list(pQualities.keys())[1:]:
                if pQualities[key] == highestQuality:
                    highestPNames.append(key)
                else:
                    break
            portion = sum(rewards[currentRewardIndex : min(currentRewardIndex + len(highestPNames), len(rewards))]) // len(highestPNames)
            for pName in highestPNames:
                pRewards[pName] += portion
            currentRewardIndex += len(highestPNames)
            for highest in highestPNames:
                del pQualities[highest]
        
        for g in models.goodsNames:
            rewards = [10, 5]
            currentRewardIndex = 0
            for l in range(7,-1,-1):
                if currentRewardIndex < len(rewards):
                    levelPlayers = []
                    for p in stateCopy["players"]:
                        if p[g] == l:
                            levelPlayers.append(p["fields"]["name"])
                    if len(levelPlayers) > 0:
                        portion = sum(rewards[currentRewardIndex : min(currentRewardIndex + len(levelPlayers), len(rewards))]) // len(levelPlayers)
                        for winnerName in levelPlayers:
                            pRewards[winnerName] += portion
                    currentRewardIndex += len(levelPlayers)
        
        return pRewards



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
        groupFraction = models.count_lots(hFields["group_lots"]) // 5
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