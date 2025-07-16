from abc import ABC, abstractmethod
import random
from . import models
import copy
import numpy
import scipy
import math

class AIPlayer(ABC):
    '''AI players are static and must act based only on current game state, returning an invalid move will result in a move being made for this player automatically
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
        groupCount = models.count_lots(state["host"][0]["fields"]["group_lots"])
        if groupCount == 0: return True
        elif groupCount == 1: return random.random() < 0.67
        elif groupCount == 2: return random.random() < 0.5
        return False

class Gian(AIPlayer):
    '''Indi's decent AI'''
    def bid(state: dict) -> int:
        hFields = state["host"][0]["fields"]
        groupCount = models.count_lots(hFields["group_lots"])
        myName = hFields["bidder"]
        print(myName + "'s opinion on " + str(hFields["group_lots"]))
        myFields = None
        highestCurrentBid = 0
        unfilledTotal = 0
        for i, p in enumerate(state["players"]):
            bid = int(p["fields"]["current_bid"])
            unfilledTotal += 5 - models.count_lots(p["fields"]["lots"])
            if bid > highestCurrentBid: highestCurrentBid = bid
            if p["fields"]["name"] == myName:
                myFields = p["fields"]

        print("uaq: " + str(Gian.averageQuality(Gian.unseenLots(state))) + " ug: " + str(Gian.averageGoods(Gian.unseenLots(state))))
        scoresIfTheyTake = {}
        noneAfterCanBid = True
        for i, p in enumerate(state["players"]):
            stateIfPTakes = copy.deepcopy(state)
            pFieldsIfTakes = stateIfPTakes["players"][i]["fields"]
            pRemainingSlots = 5 - models.count_lots(p["fields"]["lots"])
            if p["fields"]["money"] >= highestCurrentBid + 1 and pRemainingSlots >= groupCount:
                pFieldsIfTakes["lots"] = hFields["group_lots"] if p["fields"]["lots"] == "" else p["fields"]["lots"] + " " + hFields["group_lots"]
                if Gian.isAfterMe(state, myName, p["fields"]["name"]):
                    noneAfterCanBid = False
            else:
                stateIfPTakes["host"][0]["fields"]["harbor"] = hFields["group_lots"] if stateIfPTakes["host"][0]["fields"]["harbor"] == "" else stateIfPTakes["host"][0]["fields"]["harbor"] + " " + hFields["group_lots"]
            stateIfPTakes["host"][0]["fields"]["group_lots"] = ""
            scoresIfTheyTake[p["fields"]["name"]] = Gian.scoreWithAvgUnseenFill(stateIfPTakes)

        print(scoresIfTheyTake)
        diffIfTheyTake = {}
        maxWorthToAfter = 0
        for p in state["players"]:
            pName = p["fields"]["name"]
            scoreIfTake = 0
            avgScoreIfLeave = 0
            for name, scores in scoresIfTheyTake.items():
                if name == pName:
                    scoreIfTake = scores[pName]
                else:
                    avgScoreIfLeave += scores[pName] / (len(scoresIfTheyTake) - 1)
            diffIfTheyTake[pName] = scoreIfTake - avgScoreIfLeave
            if Gian.isAfterMe(state, myName, pName):
                maxWorthToAfter = max(maxWorthToAfter, diffIfTheyTake[pName] * (groupCount / 5))
        print(diffIfTheyTake) 
        if diffIfTheyTake[myName] < 0: #taking would, on average, decrease our score
            return 0
        
        worthToMe = math.ceil(min(max(diffIfTheyTake[myName] * (groupCount / 5), 1), int(myFields["money"]))) #proof of concept, some fraction of diff may be more optimal.
        maxBid = None
        minBid = None
        if worthToMe > maxWorthToAfter: #worth less to others, don't need to bid full worth to me
            print("more to me")
            maxBid = worthToMe
            minBid = max(math.ceil(maxWorthToAfter * 1.1), 1) #TODO, see if this should be min'ed with max bid, probably fine as is
        else: #worth more to others, worth some amount to block them
            print("more to others")
            oppWeight = 1 / (len(state["players"]) - 1)
            maxBid = math.ceil((1 - oppWeight) * worthToMe + oppWeight * maxWorthToAfter) #should really account for opponents who have already bid to know if you should outbid them
            minBid = worthToMe
        print("m: " + str(minBid) + ", M: " + str(maxBid))
        if highestCurrentBid + 1 > maxBid:
            return 0
        if hFields["chooser"] == myName or noneAfterCanBid:
            return highestCurrentBid + 1
        
        return minBid
    
    def draw(state) -> bool: #TODO reduce deck waste
        myName = state["host"][0]["fields"]["chooser"]
        hFields = state["host"][0]["fields"]
        groupCount = models.count_lots(hFields["group_lots"])
        if groupCount == 0:
            return True
        myFields = None
        for p in state["players"]:
            if p["fields"]["name"] == myName:
                myFields = p["fields"]
        slotsLeft = 5 - models.count_lots(myFields["lots"])
        if groupCount + 1 > slotsLeft:
            return False
        myName = myFields["name"]
        print(str(myName) + " choosing given " + str(hFields["group_lots"]))
        
        avgDiffForThem = Gian.rewardDiffOnTake(state)
        print("adft: " + str(avgDiffForThem))
        whoGroupIsGoodFor = []
        for p in state["players"]:
            if avgDiffForThem[p["fields"]["name"]] >= 0:
                whoGroupIsGoodFor.append(p["fields"]["name"])
        
        groupAvgQuality = Gian.averageQuality(str(hFields["group_lots"]).split(" "))
        unseenAvgQuality = Gian.averageQuality(Gian.unseenLots(state))
        potentialGroupAvgQuality = (groupCount * groupAvgQuality + unseenAvgQuality) / (groupCount + 1)
        if myName in whoGroupIsGoodFor and len(whoGroupIsGoodFor) == 1: #group is only good for me
            print("only good for me!")
            return False
        elif myName in whoGroupIsGoodFor and len(whoGroupIsGoodFor) > 1: #group is good for multiple people
            print("good for me and others")
            slotsLeftFor = {}
            for p in state["players"]:
                pName = p["fields"]["name"]
                if pName in whoGroupIsGoodFor:
                    slotsLeftFor[pName] = 5 - models.count_lots(p["fields"]["lots"])
            playersWithLessSlots = []
            for pName, pSlotsLeft in slotsLeftFor.items():
                if pSlotsLeft < slotsLeft:
                    playersWithLessSlots.append(pName)
            if len(playersWithLessSlots) == 0:
                print("can't block any")
                return False
            
            return potentialGroupAvgQuality > unseenAvgQuality * 0.9 #arbitrary threshold, maybe improve later
        elif not myName in whoGroupIsGoodFor and len(whoGroupIsGoodFor) > 0: #group is good only for others
            print("good for others only")
            numAbleToDraw = min(3, models.count_lots(hFields["deck"]))
            allCanBeBlocked = True
            for p in state["players"]:
                pName = p["fields"]["name"]
                pSlotsLeft = 5 - models.count_lots(p["fields"]["lots"])
                if pName in whoGroupIsGoodFor and pSlotsLeft >= numAbleToDraw:
                    allCanBeBlocked = False
            if allCanBeBlocked:
                print("spoiling")
                return True

            return potentialGroupAvgQuality < groupAvgQuality * 0.9
        else:
            print("group is bad for all")
            return slotsLeft >= groupCount + 1 and groupAvgQuality > unseenAvgQuality * 0.6

    def unseenLots(state) -> list[str]:
        hFields = state["host"][0]["fields"]
        full = models.get_full_deck(6, False).split(" ")
        seen = str(hFields["harbor"]).split(" ") + str(hFields["group_lots"]).split(" ")
        for p in state["players"]:
            seen = seen + str(p["fields"]["lots"]).split(" ")
        seen[:] = [x for x in seen if x != ""]#remove all empty strings
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
        for good in avgs:
            avgs[good] /= len(lotList)
        return avgs
    
    def scoreWithAvgUnseenFill(stateCopy):
        '''Returns a dictionary mapping player names to expected rewards given current state and average lot fill based on unseen lots. This is destructive to the passed state, only pass copies of current state.'''
        pQualities = dict()
        pRewards = dict()
        unfilledTotal = 0
        remainingSlotsOf = {}
        currentPIndex = 0
        pCount = len(stateCopy["players"])
        for i, p in enumerate(stateCopy["players"]):
            pRewards[p["fields"]["name"]] = 0
            lotString = p["fields"]["lots"]
            remainingSlots = 5 - models.count_lots(lotString)
            remainingSlotsOf[p["fields"]["name"]] = remainingSlots
            unfilledTotal += remainingSlots
            pQualities[p["fields"]["name"]] = models.cost_of_lots(lotString)
            p["fields"]["money"] = 0
            if p["fields"]["name"] == stateCopy["host"][0]["fields"]["chooser"]:
                currentPIndex = i
            for g in models.goodsNames:
                p["fields"][g] = min(p["fields"][g] + lotString.count(g[0]), 7)
        #TODO account for persistent value of pyramid rank and height across rounds
        
        unseenGoodsAvg = Gian.averageGoods(Gian.unseenLots(stateCopy))
        unseenAvg = Gian.averageQuality(Gian.unseenLots(stateCopy))
        AVG_LOTS_PER_GROUP = 2
        deckCount = models.count_lots(stateCopy["host"][0]["fields"]["deck"])
        while deckCount > 0 and unfilledTotal > 0:
            currentPIndex = (currentPIndex + 1) % pCount
            currentFields = stateCopy["players"][currentPIndex]["fields"]
            currentName = currentFields["name"]
            numTaken = min([AVG_LOTS_PER_GROUP, remainingSlotsOf[currentName], deckCount])
            pQualities[currentName] += numTaken * unseenAvg
            for g in models.goodsNames:
                currentFields[g] = min(currentFields[g] + numTaken * unseenGoodsAvg[g[0]], 7)

            deckCount -= numTaken
            remainingSlotsOf[currentName] -= numTaken
            unfilledTotal -= numTaken

        for p in stateCopy["players"]:
            for g in models.goodsNames:
                p["fields"][g] = round(p["fields"][g])
        # print(pQualities)
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
                        if p["fields"][g] == l:
                            levelPlayers.append(p["fields"]["name"])
                    if len(levelPlayers) > 0:
                        portion = sum(rewards[currentRewardIndex : min(currentRewardIndex + len(levelPlayers), len(rewards))]) // len(levelPlayers)
                        for winnerName in levelPlayers:
                            pRewards[winnerName] += portion
                    currentRewardIndex += len(levelPlayers)

        return pRewards

    def stateCopyIfPlayerTakes(state, playerIndex):
        '''Returns a deep copy of the given state where the player in state["players"][playerIndex] is given the lots from the current group'''
        stateCopy = copy.deepcopy(state)
        hFields = state["host"][0]["fields"]
        p = stateCopy["players"][playerIndex]
        p["fields"]["lots"] = hFields["group_lots"] if p["fields"]["lots"] == "" else p["fields"]["lots"] + " " + hFields["group_lots"]
        stateCopy["host"][0]["fields"]["group_lots"] = ""
        return stateCopy

    def rewardDiffOnTake(state):
        '''Returns a dictionary mapping player names to estimated reward difference if they take the current group. Rewards calculated with unseen fill. Players which cannot take the group are assigned -1000 reward'''
        groupSize = models.count_lots(state["host"][0]["fields"]["group_lots"])
        highestCurrentBid = 0
        rewardsIfTheyTake = {}
        for i, p in enumerate(state["players"]):
            if p["fields"]["current_bid"] > highestCurrentBid: highestCurrentBid = p["fields"]["current_bid"]
            rewardsIfTheyTake[p["fields"]["name"]] = Gian.scoreWithAvgUnseenFill(Gian.stateCopyIfPlayerTakes(state, i))
        avgDiffByTaking = {}
        numOtherPlayers = len(state["players"]) - 1
        for p in state["players"]:
            pName = p["fields"]["name"]
            if 5 - models.count_lots(p["fields"]["lots"]) < groupSize or p["fields"]["money"] < highestCurrentBid + 1: #this player cannot take the group
                avgDiffByTaking[pName] = -1000
                continue
            rewardsIfPTakes = rewardsIfTheyTake[pName]
            pRewardIfTake = rewardsIfPTakes[pName]
            avgIfLeave = 0
            for o in state["players"]:
                otherName = o["fields"]["name"]
                if otherName == pName:
                    continue
                avgIfLeave += rewardsIfTheyTake[otherName][pName]
            avgIfLeave /= numOtherPlayers
            avgDiffByTaking[pName] = pRewardIfTake - avgIfLeave
        return avgDiffByTaking

    def isAfterMe(state, myName, theirName):
        myIndex = 0
        chooserIndex = 0
        theirIndex = 0
        pCount = len(state["players"])
        for i, p in enumerate(state["players"]):
            if p["fields"]["name"] == myName: myIndex = i
            if p["fields"]["name"] == theirName: theirIndex = i
            if p["fields"]["name"] == state["host"][0]["fields"]["chooser"]: chooserIndex = i
        myIndex = (myIndex - (chooserIndex + 1)) % pCount #transalte indexes so that chooser is last
        theirIndex = (theirIndex - (chooserIndex + 1)) % pCount
        return theirIndex > myIndex

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
        max = round(min(int(myFields["money"]), 40) * groupFraction)
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

class Blackrock(AIPlayer):
    '''Donated by an anonymous benefactor'''
    NUMDAYS = 3
    #AI tunable constants
    MONOPOLYBONUS = 10#bonus if in the lead, for extra to maintain lead
    EXTRAQUALITYBONUS =1
    SQUEMISHNESS = 1.5#regarding uncertainty; 0 is certain of everything; infty is uncertain value worthless; 1 is balanced but still overconfident
    AGRESSION = 0.5#should vary from zero to one
    OPORTUNITYCOST = 3 # per card
    FOMO = 5 # per card per turn, UNUSED

    NRISKS = 5

    def bid(state) -> int:
        goods = [("cloth","c"),("dye","d"),("furs","f"),("spice","s"),("grain","g")]#G for gold is excluded
        lotIdxName = {name:i for i,(name,n) in enumerate(goods)}
        lotIdxN = {n:i for i,(name,n) in enumerate(goods)}
        goodrankpoints = [10,5]
        qualrankpoints_old = {3:[30,15],4:[30,20,10],5:[30,20,10,5],6:[30,20,15,10,5]}
        numTotalLots = {3:18,4:24,5:30,6:36}#6 per player
        permbonus=[0,0,0,0,5,10,20]
        maxgoods = 5*3+1
        maxplrs = 6
        goodrankpoints = Blackrock.pad(goodrankpoints,0,maxplrs+1)
        permbonus = Blackrock.pad(permbonus,20,maxgoods)
        qualrankpoints = {}
        for k,v in qualrankpoints_old.items():
            qualrankpoints[k] =Blackrock.pad(v,0,k+1)
        #buy buisnesss
        #fire employees
        #sell off safety equipment
        #sell company to unsuspecting buyer
        
        #ignore future lots
        host = state["host"][0]["fields"]
        thelot = host["group_lots"]
        deckSize = len(host["deck"].split())
        me = None
        mei = None
        NPlayers = len(state["players"])
        soldCards = 0
        maxCards = 0
        plridxs = {}
        currentMaxBid=0
        currentRecieverIdx = None
        for i,p in enumerate(state["players"]): 
            plridxs[p["fields"]["name"]] = i
            if(p["fields"]["name"] == host["bidder"]):
                me = p["fields"]
                mei = i
            if(p["fields"]["current_bid"]>currentMaxBid): 
                currentRecieverIdx = i
                currentMaxBid = p["fields"]["current_bid"]
        chi = plridxs[host["chooser"]]
        currentReciever = state["players"][currentRecieverIdx]["fields"] if currentRecieverIdx else None

        
        dvalueDefault = numpy.zeros(shape=(NPlayers,Blackrock.NRISKS),dtype=int)#or if no one takes
        
        dvalueMatrix = numpy.zeros(shape=(NPlayers,NPlayers,Blackrock.NRISKS),dtype=int)#me,other,risk
        for i,p in enumerate(state["players"]): 
            
            basev = Blackrock.lotValue("",p["fields"],currentReciever,state)
            newv = Blackrock.lotValue(thelot,p["fields"],p["fields"],state)
            dvalueDefault[i,:] = newv-basev
            maxCards+=5
            soldCards+=len(p["fields"]["lots"].split())
            for j,p2 in enumerate(state["players"]):
                if(i==j):continue#skip self
                #other skips are possible
                basev = Blackrock.lotValue("",p["fields"],p2["fields"],state)
                newv = Blackrock.lotValue(thelot,p["fields"],p["fields"],state)
                dvalueMatrix[i,j,:] = newv-basev
        soldCards+=len(thelot.split())#TODO account for discards and the size of the deck
        cardDeficit =maxCards - soldCards - deckSize

        certainties = numpy.zeros(shape=Blackrock.NRISKS,dtype=float)
        certainties[0]=1#certain
        saturation = float(soldCards)/float(maxCards)
        certainties[1] =1.- (Blackrock.NUMDAYS-host["day"]+1)/float(Blackrock.NUMDAYS)*(1-saturation)#for goods
        certainties[1] **= Blackrock.SQUEMISHNESS
        certainties[2] =1.- 1.*(1-saturation)#for quality
        certainties[2] **= Blackrock.SQUEMISHNESS
        certainties[3] = (1.-scipy.special.erf(cardDeficit/1.4))/2.
        certainties[4] = (1.+scipy.special.erf(cardDeficit/1.4))/2.
        dvaluemaxTake = currentMaxBid
        dvaluemaxPass = currentMaxBid
        #print("deficit=",cardDeficit)
        #print(f"saturation: {saturation}")
        #print(f"value: {dvalueDefault[mei,:]} dot {certainties}")
        i_if_take = mei
        i_if_pass = currentRecieverIdx
        
        for i,p in enumerate(state["players"]): 
            hasbid = numpy.logical_xor(numpy.logical_xor((i>chi) , (i>=mei)) , (chi >= mei))#me has not bid yet
            canbid = (p["fields"]["money"]>currentMaxBid) and (len(thelot.split())+len(p["fields"]["lots"].split()) <=5)
            if(hasbid or mei==i or not canbid):continue
            dValueTake = numpy.dot(dvalueMatrix[i,mei,:],certainties)
            dValuePass = numpy.dot(dvalueMatrix[i,currentRecieverIdx,:] if currentRecieverIdx else dvalueDefault[i,:],certainties)
            dValueTake = min(dValueTake,p["fields"]["money"])
            dValuePass = min(dValuePass,p["fields"]["money"])
            #dont bid agains someone who cant match
            #print(dValueTake.shape,dValuePass.shape)
            #dvaluemax = max(dvaluemax,numpy.dot(dvalueDefault[i,:],certainties))
            if(dvaluemaxTake<dValueTake):
                dvaluemaxTake = max(dvaluemaxTake,dValueTake)#how much worth to them for me to not have it
                i_if_take = i
            if(dvaluemaxPass<dValuePass):
                dvaluemaxPass = max(dvaluemaxPass,dValuePass)#how much worth to them for me to not have it
                i_if_pass = i
        
        dvalueme = numpy.dot(dvalueMatrix[mei,i_if_pass,:] if i_if_pass else dvalueDefault[mei,:],certainties)
        anticipateTaking = i_if_take==mei
        mybid=0
        currentMaxBid = currentMaxBid#TODO use this to bid
        #dont game theory out the value matrix; it will not stack up against bad strategies
        if(dvalueme>dvaluemaxTake): mybid= dvaluemaxTake+1#outbid future or past
        #if(dvalueme<dvaluemax): mybid= dvaluemax-1 #too agressive
        if(dvalueme<=dvaluemaxTake): mybid= int((dvalueme*(1-Blackrock.AGRESSION)+(dvaluemaxTake-1)*Blackrock.AGRESSION))#round down only
        mybid = int((mybid))#just int
        mybid = max(mybid,0)
        if(mybid==0) and (host["day"]==1) and (soldCards==len(thelot.split())):
            mybid = 1#prevent first card stalemate with self
        mybid = min(mybid,me["money"])
        return mybid

    def draw(state) -> bool:
        goods = [("cloth","c"),("dye","d"),("furs","f"),("spice","s"),("grain","g")]#G for gold is excluded
        lotIdxName = {name:i for i,(name,n) in enumerate(goods)}
        lotIdxN = {n:i for i,(name,n) in enumerate(goods)}
        goodrankpoints = [10,5]
        qualrankpoints_old = {3:[30,15],4:[30,20,10],5:[30,20,10,5],6:[30,20,15,10,5]}
        numTotalLots = {3:18,4:24,5:30,6:36}#6 per player
        permbonus=[0,0,0,0,5,10,20]
        maxgoods = 5*3+1
        maxplrs = 6
        goodrankpoints = Blackrock.pad(goodrankpoints,0,maxplrs+1)
        permbonus = Blackrock.pad(permbonus,20,maxgoods)
        qualrankpoints = {}
        for k,v in qualrankpoints_old.items():
            qualrankpoints[k] =Blackrock.pad(v,0,k+1)
        #just draw max I can bid on
        #always have a vulchers eye out for live prey
        host = state["host"][0]["fields"]
        me = None
        lotcounts = {}
        for p in state["players"]: 
            if(p["fields"]["name"] == host["chooser"]):me = p["fields"]
            plots = p["fields"]["lots"].split()
            if not (len(plots) in lotcounts.keys()) : lotcounts[len(plots)]=0
            lotcounts[len(plots)] +=1
        mylots = me["lots"].split()
        drawnlots = host["group_lots"].split()
        if(len(mylots)+len(drawnlots) < 5):
            return True
        else: 
            return False
    
    def playervec(plr):
        goods = [("cloth","c"),("dye","d"),("furs","f"),("spice","s"),("grain","g")]#G for gold is excluded
        vec = Blackrock.newvec()
        for i,(name,n) in enumerate(goods):
            vec[i]=plr[name]
        return vec
    
    def lotsvec(lotsStr):
        goods = [("cloth","c"),("dye","d"),("furs","f"),("spice","s"),("grain","g")]#G for gold is excluded
        lotIdxN = {n:i for i,(name,n) in enumerate(goods)}
        lots = lotsStr.split()
        vec = Blackrock.newvec()
        qual=0
        for lot in lots:
            if lot[:1] in lotIdxN.keys():
                vec[lotIdxN[lot[:1]]]+=1
            qual+=int(lot[1:])
        return vec,qual
    
    def lotValue(extralot,me,reciever,state):
        goodrankpoints = [10,5]
        qualrankpoints_old = {3:[30,15],4:[30,20,10],5:[30,20,10,5],6:[30,20,15,10,5]}
        numTotalLots = {3:18,4:24,5:30,6:36}#6 per player
        permbonus=[0,0,0,0,5,10,20]
        maxgoods = 5*3+1
        maxplrs = 6
        goodrankpoints = Blackrock.pad(goodrankpoints,0,maxplrs+1)
        permbonus = Blackrock.pad(permbonus,20,maxgoods)
        qualrankpoints = {}
        for k,v in qualrankpoints_old.items():
            qualrankpoints[k] =Blackrock.pad(v,0,k+1)

        host = state["host"][0]["fields"]
        #expected payout (certain, uncertaiin)
        extralotvec,extraqual = Blackrock.lotsvec(extralot)
        melotvec,melotqual = Blackrock.lotsvec(me["lots"])
        rank = Blackrock.newvec()+1
        qrank = 1
        tie = Blackrock.newvec()+1
        qtie=1
        maxvec=Blackrock.newvec()
        maxq = 0
        meRecives = 1 if (not reciever is None) and me["name"]==reciever["name"] else 0
        for i,p in enumerate(state["players"]):
            if p["fields"]["name"]==me["name"]:continue#skip self
            pRecives = 1 if (not reciever is None) and p["fields"]["name"]==reciever["name"] else 0
            plotvec,plotqual = Blackrock.lotsvec(p["fields"]["lots"])
            rank+= numpy.where(Blackrock.playervec(p["fields"]) + plotvec+extralotvec*pRecives>Blackrock.playervec(me)+ melotvec+extralotvec*meRecives,1,0)
            tie+= numpy.where(Blackrock.playervec(p["fields"]) + plotvec+extralotvec*pRecives==Blackrock.playervec(me)+ melotvec+extralotvec*meRecives,1,0)
            if (plotqual>melotqual+extraqual): qrank+=1
            if (plotqual==melotqual+extraqual): qtie+=1
            maxvec=numpy.maximum(maxvec,Blackrock.playervec(p["fields"]) + plotvec+extralotvec*pRecives)
            maxq = max(maxq,plotqual)
        daysleftEx = Blackrock.NUMDAYS-host["day"]
        valueUncertainGoods = numpy.sum([numpy.sum(goodrankpoints[rank[i]:rank[i]+tie[i]])/tie[i] for i in range(5)])\
            +numpy.sum(numpy.where(rank==1,Blackrock.playervec(me)+ melotvec+extralotvec*meRecives - maxvec,0))*Blackrock.MONOPOLYBONUS*max(daysleftEx,3)\
            +max(melotqual+extraqual - maxq,0)*Blackrock.EXTRAQUALITYBONUS
        valueUncertainQuality=numpy.sum(qualrankpoints[len(state["players"])][qrank:qrank+qtie])/qtie#quality
        valueCertain = numpy.sum([permbonus[Blackrock.playervec(me)+melotvec[i]+extralotvec[i]*meRecives] for i in range(5)])*(daysleftEx+1)\
            #TODO stop negatives and firsd draw stalemate
        valueUncertainOpportunity = -len(extralot.split())*meRecives*Blackrock.OPORTUNITYCOST
        valueUncertainFomo = len(extralot.split())*meRecives*daysleftEx*Blackrock.FOMO
        return numpy.array([valueCertain,valueUncertainGoods,valueUncertainQuality,valueUncertainOpportunity,valueUncertainFomo],dtype=int)
    
    def newvec():
        return numpy.zeros(shape=5,dtype=int)
    
    def pad(ls,num,LEN):
        ret = numpy.full(fill_value=num,shape=LEN)
        ret[:len(ls)]=ls
        return ret


aiDictionary = {
    "randy": Randy,
    "gian": Gian,
    "errata": Errata,
    "blackrock": Blackrock,
}