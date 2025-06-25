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
    def bid(state) -> int:
        return 0
    def draw(state) -> bool:
        return True

aiDictionary = {
    "randy": Randy,
    "gian": Gian,
}