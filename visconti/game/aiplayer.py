from abc import ABC, abstractmethod
import random

class AIPlayer(ABC):
    '''AI players are static and must act based only on current game state.
    state refers to a nested dictionary representing the game state, this is identical in format to the JSON object printed to the browser console each update.'''

    @abstractmethod
    def bid(self, state):
        '''Returns the integer amount this player will bid given the game state, a bid of 0 is counted as a pass'''
        pass

    @abstractmethod
    def draw(self, state):
        '''Returns whether this player will draw another lot given the game state'''
        pass

class Randy(AIPlayer):
    def bid(self, state):
        if bool(random.choice([True, False])):
            return 0
        
        highest = 0
        for p in state["players"]:
            bid = p["fields"]["current_bid"]
            if bid > highest: highest = bid
        return highest + 1
    
    def draw(self, state):
        return bool(random.choice([True, False]))