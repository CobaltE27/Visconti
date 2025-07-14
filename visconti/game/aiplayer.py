from abc import ABC, abstractmethod
import random
from . import models
import copy
import numpy
import scipy

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
        groupCount = models.count_lots(state["host"][0]["fields"]["group_lots"])
        if groupCount == 0: return True
        elif groupCount == 1: return random.random() < 0.67
        elif groupCount == 2: return random.random() < 0.5
        return False
    
class Gian(AIPlayer):
    '''Indi's basic AI'''
    def bid(state: dict) -> int:
        hFields = state["host"][0]["fields"]
        groupCount = models.count_lots(hFields["group_lots"])
        print(str(hFields["group_lots"]))
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
        stateIfTake = copy.deepcopy(state)
        leaveScores = []
        noneCanBid = True
        for p in stateIfTake["players"]:
            if p["fields"]["name"] == myName:
                p["fields"]["lots"] = hFields["group_lots"] if p["fields"]["lots"] == "" else p["fields"]["lots"] + " " + hFields["group_lots"]
                stateIfTake["host"][0]["fields"]["group_lots"] = ""
            else:
                # print(str(p["fields"]["name"]) + " takes?")
                stateIfThisOppTakes = copy.deepcopy(state)
                stateIfThisOppTakes["host"][0]["fields"]["group_lots"] = ""
                for opp in stateIfThisOppTakes["players"]:
                    if opp["fields"]["name"] == p["fields"]["name"]:
                        oppRemainingSlots = 5 - models.count_lots(opp["fields"]["lots"])
                        if opp["fields"]["money"] >= highestCurrentBid + 1 and oppRemainingSlots >= groupCount: #this opp can bid for the group
                            opp["fields"]["lots"] = hFields["group_lots"] if opp["fields"]["lots"] == "" else opp["fields"]["lots"] + " " + hFields["group_lots"]
                            noneCanBid = False
                        leaveScores.append(Gian.scoreWithAvgUnseenFill(stateIfThisOppTakes))
        # print("If I take?")
        takeScore = Gian.scoreWithAvgUnseenFill(stateIfTake)
        avgLeaveScore = dict()
        for leaveScore in leaveScores:
            for pName in leaveScore.keys():
                avgLeaveScore[pName] = avgLeaveScore.get(pName, 0) + leaveScore[pName] / len(leaveScores)
        
        print(str(takeScore) + " " + str(leaveScores))
        diffByTake = takeScore[myName] - avgLeaveScore[myName]
        print(diffByTake)
        if diffByTake < 0: #taking would, on average, decrease our score
            return 0
        #taking if worth it, but how much? TODO calculate worth to others and add value of blocking, TODO bias based on slots left and num lots left

        maxBid = min(max(diffByTake * (groupCount / 5), 1), int(myFields["money"])) #proof of concept, some fraction of diffByTake may be more optimal.
        if highestCurrentBid > maxBid:
            return 0

        if hFields["chooser"] == myName or noneCanBid:
            return highestCurrentBid + 1
        
        return maxBid
    
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
                return False
            
            return potentialGroupAvgQuality > unseenAvgQuality #arbitrary threshold, maybe improve later
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
        deckCount = models.count_lots(stateCopy["host"][0]["fields"]["deck"])
        unseenAvg = Gian.averageQuality(Gian.unseenLots(stateCopy))
        unseenGoodsAvg = Gian.averageGoods(Gian.unseenLots(stateCopy))
        unfilledTotal = 0
        for p in stateCopy["players"]:
            unfilledTotal += 5 - models.count_lots(p["fields"]["lots"])
            p["fields"]["money"] = 0
        dilutedUnseenAvg = unseenAvg * (deckCount / unfilledTotal)
        # print("ua:" + str(dilutedUnseenAvg))
        for p in stateCopy["players"]:
            pRewards[p["fields"]["name"]] = 0
            lotString = p["fields"]["lots"]
            remainingSlots = 5 - models.count_lots(lotString)
            pQualities[p["fields"]["name"]] = models.cost_of_lots(lotString) + remainingSlots * dilutedUnseenAvg
            for g in models.goodsNames:
                p["fields"][g] = min(p["fields"][g] + lotString.count(g[0]) + int(round(remainingSlots * unseenGoodsAvg[g[0]])), 7)
                pRewards[p["fields"]["name"]] += models.cumulative_pyramid_score(p["fields"][g])
        pQualities = {k: v for k, v in sorted(pQualities.items(), key=lambda item: item[1], reverse=True)} #sort dictionary by descending quality
        # print("p: " + str(pRewards))
        # print("q: " + str(pQualities))
        
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
        # print("qr: " + str(pRewards))

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
        # print("pr: " + str(pRewards))

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
        '''Returns a dictionary mapping player names to estimated reward difference if they take the current group. Rewards culculated with unseen fill. Players which cannot take the group are assigned -1000 reward'''
        groupSize = models.count_lots(state["host"][0]["fields"]["group_lots"])
        rewardsIfTheyTake = {}
        for i, p in enumerate(state["players"]):
            rewardsIfTheyTake[p["fields"]["name"]] = Gian.scoreWithAvgUnseenFill(Gian.stateCopyIfPlayerTakes(state, i))
        avgDiffByTaking = {}
        numOtherPlayers = len(state["players"]) - 1
        for p in state["players"]:
            pName = p["fields"]["name"]
            if 5 - models.count_lots(p["fields"]["lots"]) < groupSize: #this player cannot take the group
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
    ''''''
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