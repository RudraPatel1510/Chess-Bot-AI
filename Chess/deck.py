import random

class Deck:
    def __init__(self):
        self.suits = ['♠', '♥', '♦', '♣']
        self.values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.cards = []
        self.initialize_deck()

    def initialize_deck(self):
        self.cards = [(value, suit) for suit in self.suits for value in self.values]
        random.shuffle(self.cards)

    def draw_card(self):
        if len(self.cards) == 0:
            print("Deck is empty. Reinitializing...")
            self.initialize_deck()
        return self.cards.pop()


