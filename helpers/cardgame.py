import random

suits = ["spades", "hearts", "diamonds", "clubs"]


class Card:
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value

    def __str__(self):
        return f":{self.suit}: {self.value}"

    def get_value(self):
        try:
            value = int(self.value)
            return value
        except ValueError:
            if self.value == "A":
                return 0
            else:
                return 10


class Deck:
    def __init__(self):
        self.cards = []
        self.__create_deck()

    def __create_deck(self):
        for i in range(4):
            suit = suits[i]
            for j in range(13):
                if j == 0:
                    self.cards.append(Card(suit, "A"))
                elif j == 10:
                    self.cards.append(Card(suit, "J"))
                elif j == 11:
                    self.cards.append(Card(suit, "Q"))
                elif j == 12:
                    self.cards.append(Card(suit, "K"))
                else:
                    self.cards.append(Card(suit, j + 1))

    def deal_card(self):
        card = random.choice(self.cards)
        self.cards.remove(card)
        return card

    def shuffle(self):
        random.shuffle(self.cards)


class Player:
    def __init__(self, deck: Deck, init_cards: int):
        self.__hand = []
        self.__done = False
        for i in range(init_cards):
            self.__hand.append(deck.deal_card())
        self.calc_score()

    def __len__(self):
        return len(self.__hand)

    def draw_card(self, deck: Deck):
        self.__hand.append(deck.deal_card())
        self.calc_score()

    def done(self):
        self.__done = True

    def calc_score(self):
        hand_values = []
        for card in self.__hand:
            hand_values.append(card.get_value())

        for i in range(len(hand_values)):
            if hand_values[i] == 0:
                if sum(hand_values) + 11 > 21:
                    hand_values.pop(i)
                    hand_values.insert(i, 1)
                else:
                    hand_values.pop(i)
                    hand_values.insert(i, 11)
        self.score = sum(hand_values)

    def first_score(self):
        return self.__hand[0].get_value()

    def first_card(self):
        return self.__hand[0]

    def is_done(self):
        return self.__done

    def get_cards(self):
        return self.__hand


