from pydantic import BaseModel
import random
from enum import Enum, IntEnum
from typing import List

DEBUG = True


class Suit(str, Enum):
    HEARTS = "hearts"
    KROSS = "kross"
    SPADES = "spades"
    BALLS = "balls"


class GameState(str, Enum):
    BIDDING = "bidding"
    PRESSING = "pressing"
    TRUMPING = "trumping"
    DECLARING = "declaring"
    PLAYING = "playing"
    EVALUATING = "evaluating"


class Value(IntEnum):
    JACK = 2
    QUEEN = 3
    KING = 4
    TEN = 10
    ACE = 11


class Card(BaseModel):
    value: Value
    suit: Suit

    def __init__(self, value: Value, suit: Suit):
        super().__init__(value=value, suit=suit)


class Sets:
    def rundgang() -> List[Card]:
        return [
            Card(value=value, suit=suit)
            for suit in Suit
            for value in [Value.QUEEN, Value.KING]
        ]

    def family(suit: Suit) -> List[Card]:
        return [Card(value=value, suit=suit) for value in Value]

    def pair(suit: Suit) -> List[Card]:
        return [Card(value=value, suit=suit) for value in [Value.QUEEN, Value.KING]]

    def jacks() -> List[Card]:
        return [Card(value=Value.JACK, suit=suit) for suit in Suit]

    def queens() -> List[Card]:
        return [Card(value=Value.QUEEN, suit=suit) for suit in Suit]

    def kings() -> List[Card]:
        return [Card(value=Value.KING, suit=suit) for suit in Suit]

    def aces() -> List[Card]:
        return [Card(value=Value.ACE, suit=suit) for suit in Suit]

    def doubleBinokel() -> List[Card]:
        return [
            Card(value=Value.QUEEN, suit=Suit.SPADES),
            Card(value=Value.QUEEN, suit=Suit.SPADES),
            Card(value=Value.JACK, suit=Suit.BALLS),
            Card(value=Value.JACK, suit=Suit.BALLS),
        ]

    def binokel() -> List[Card]:
        return [
            Card(value=Value.QUEEN, suit=Suit.SPADES),
            Card(value=Value.JACK, suit=Suit.BALLS),
        ]


class Deck(BaseModel):
    cards: List[Card]

    def __init__(self):
        cards = []
        for _ in range(2):
            for suit in Suit:
                for value in Value:
                    cards.append(Card(value=value, suit=suit))

        super().__init__(cards=cards)

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self) -> Card:
        return self.cards.pop()


class Player(BaseModel):
    number: int
    hand: List[Card] = []
    won: List[Card] = []
    declared: List[Card] = []
    bid: int = 0
    currentPoints: int = 0


def copyCards(cards: List[Card]) -> List[Card]:
    return [Card(value=c.value, suit=c.suit) for c in cards]


def countDeclaredPoints(cards: List[Card], trump: Suit) -> int:
    points = 0

    cc = copyCards(cards)

    # check for rundgang
    if all([c in cc for c in Sets.rundgang()]):
        points += 800

    cc = copyCards(cards)

    for _ in range(2):
        for suit in Suit:
            # check for family
            if all([c in cc for c in Sets.family(suit)]):
                for c in Sets.family(suit):
                    cc.remove(c)
                if suit == trump:
                    points += 150
                else:
                    points += 100

            # check for pair
            if all([c in cc for c in Sets.pair(suit)]):
                for c in Sets.pair(suit):
                    cc.remove(c)
                if suit == trump:
                    points += 40
                else:
                    points += 20

    cc = copyCards(cards)

    for _ in range(2):
        for suit in Suit:
            # check for jacks
            if all([c in cc for c in Sets.jacks()]):
                for c in Sets.jacks():
                    cc.remove(c)
                points += 40

            # check for queens
            if all([c in cc for c in Sets.queens()]):
                for c in Sets.queens():
                    cc.remove(c)
                points += 60

            # check for kings
            if all([c in cc for c in Sets.kings()]):
                for c in Sets.kings():
                    cc.remove(c)
                points += 80

            # check for aces
            if all([c in cc for c in Sets.aces()]):
                for c in Sets.aces():
                    cc.remove(c)
                points += 100

    cc = copyCards(cards)

    # check for double binokel
    if all([c in cc for c in Sets.doubleBinokel()]):
        for c in Sets.doubleBinokel():
            cc.remove(c)
        points += 350

    # check for binokel
    if all([c in cc for c in Sets.binokel()]):
        for c in Sets.binokel():
            cc.remove(c)
        points += 40

    return points


class BinokelGame(BaseModel):
    players: List[Player]
    dapp: List[Card]
    deck: Deck
    currentPlayer: int
    dealer: int
    gameState: GameState
    folds: List[int] = []
    trump: Suit
    onTable: List[Card] = []

    def __init__(self):
        super().__init__(
            players=[],
            dapp=[],
            deck=Deck(),
            currentPlayer=-1,
            dealer=0,
            gameState=GameState.BIDDING,
            folds=[],
            trump=Suit.HEARTS,
            onTable=[],
        )

        print(self)

    def __str__(self) -> str:
        if not DEBUG:
            return ""
        return f"BinokelGame( current player {self.currentPlayer}, maxBid {self.maxBid()} {self.gameState}, {self.folds})"

    def deal(self):
        self.deck = Deck()
        self.deck.shuffle()
        self.gameState = GameState.BIDDING

        for i in range(4):
            self.players.append(Player(number=i))
            for _ in range(9):
                self.players[i].hand.append(self.deck.deal())
                self.players[i].hand.sort(key=lambda x: (x.suit, x.value))
                self.players[i].bid = 0

        for _ in range(4):
            self.dapp.append(self.deck.deal())

        self.currentPlayer = self.dealer + 1
        self.folds = []

        print(self)

    def maxBid(self) -> int:
        if len(self.players) == 0:
            return 0
        return max([player.bid for player in self.players])

    def getBidder(self) -> int:
        return max(range(4), key=lambda x: self.players[x].bid)

    def bid(self, bid: int):
        if self.gameState != GameState.BIDDING:
            return

        if DEBUG:
            print(f"Player {self.currentPlayer} bids {bid}")

        # wenn der neue bid kleiner ist als der aktuelle max bid gehen wir von fold aus
        if bid <= self.maxBid():
            self.folds.append(self.currentPlayer)

            # wenn es 3 folds gibt, ist die bidding phase vorbei
            if len(self.folds) == 3:
                self.gameState = GameState.PRESSING

            # ansonsten ist der nächste spieler dran
            else:
                # nächster spieler ist der erste nach dem aktuellen spieler, wenn er nicht gefoldet hat
                nextPlayer = (self.currentPlayer + 1) % 4
                while nextPlayer in self.folds or nextPlayer == self.currentPlayer:
                    nextPlayer = (nextPlayer + 1) % 4
                self.currentPlayer = nextPlayer

        # ansonten wird der bid gesetzt
        else:
            self.players[self.currentPlayer].bid = bid

            # nächster spieler ist der erste nach dem dealer, wenn er nicht aktueller spieler ist und nicht gefoldet hat
            nextPlayer = (self.dealer + 1) % 4
            while nextPlayer in self.folds or nextPlayer == self.currentPlayer:
                nextPlayer = (nextPlayer + 1) % 4
            self.currentPlayer = nextPlayer

        print(self)

    def press(self, cardIndex: int):
        if self.gameState != GameState.PRESSING:
            return

        # raise error wenn der index nicht im handbereich liegt
        if cardIndex < 0 or cardIndex >= len(self.players[self.currentPlayer].hand):
            raise ValueError("Invalid card index")

        self.currentPlayer = self.getBidder()

        # aktueller spieler erhält den dapp wenn er exakt 9 karten hat
        if len(self.players[self.currentPlayer].hand) == 9:
            for i in range(len(self.dapp)):
                self.players[self.currentPlayer].hand.append(
                    Card(value=self.dapp[i].value, suit=self.dapp[i].suit)
                )

        self.players[self.currentPlayer].hand.sort(key=lambda x: (x.suit, x.value))

        if DEBUG:
            print(
                f"Player {self.currentPlayer} presses {self.players[self.currentPlayer].hand[cardIndex]}"
            )
            print(len(self.players[self.currentPlayer].hand))

        self.players[self.currentPlayer].won.append(
            self.players[self.currentPlayer].hand.pop(cardIndex)
        )

        # wenn der aktuelle spieler wieder 9 karten hat, kommt die nächste phase
        if len(self.players[self.currentPlayer].hand) == 9:
            self.gameState = GameState.TRUMPING

        print(self)

    def setTrump(self, suit: Suit):
        if self.gameState != GameState.TRUMPING:
            return

        if DEBUG:
            print(f"Player {self.currentPlayer} trumps {suit}")

        self.trump = suit
        self.gameState = GameState.DECLARING

        print(self)

    def declare(self, cardIndex: int):
        if self.gameState != GameState.DECLARING:
            return

        if cardIndex < 0 or cardIndex >= len(self.players[self.currentPlayer].hand):
            if self.currentPlayer == self.getBidder():
                self.currentPlayer = (self.getBidder() + 2) % 4
            elif self.currentPlayer == (self.getBidder() + 2) % 4:
                self.currentPlayer = (self.currentPlayer - 1) % 4
            else:
                self.currentPlayer = (self.getBidder() + 3) % 4

            return

        if DEBUG:
            print(
                f"Player {self.currentPlayer} declares {self.players[self.currentPlayer].hand[cardIndex]}"
            )

        self.players[self.currentPlayer].declared.append(
            Card(
                value=self.players[self.currentPlayer].hand[cardIndex].value,
                suit=self.players[self.currentPlayer].hand[cardIndex].suit,
            )
        )

        if self.currentPlayer == (self.getBidder() + 3) % 4:
            self.gameState = GameState.PLAYING

        points = countDeclaredPoints(self.players[self.currentPlayer].declared)
        self.players[self.currentPlayer].currentPoints = points

        print(self)

    def play(self, cardIndex: int):
        if self.gameState != GameState.PLAYING:
            return

        if cardIndex < 0 or cardIndex >= len(self.players[self.currentPlayer].hand):
            raise ValueError("Invalid card index")

        if DEBUG:
            print(
                f"Player {self.currentPlayer} plays {self.players[self.currentPlayer].hand[cardIndex]}"
            )

        t = self.onTable
        h = self.players[self.currentPlayer].hand
        c = self.players[self.currentPlayer].hand[cardIndex]

        allowedMove = self.isAllowedToPlayCard(t, h, c)

        if allowedMove:
            self.onTable.append(self.players[self.currentPlayer].hand.pop(cardIndex))
        else:
            raise ValueError("Invalid move")

        if len(self.onTable) < 4:
            self.currentPlayer = (self.currentPlayer + 1) % 4
        else:
            pass

        print(self)

    def highestCardIndex(self, cards: List[Card]) -> int:
        anyTrump = any([c.suit == self.trump for c in cards])

        highestSuit = self.onTable[0].suit
        if anyTrump:
            highestSuit = self.trump

        highestCard = max(
            [c for c in cards if c.suit == highestSuit], key=lambda x: x.value
        )

        return cards.index(highestCard)

    def isAllowedToPlayCard(
        self, onTable: List[Card], hand: List[Card], card: Card
    ) -> bool:
        if len(onTable) == 0:
            return True

        currentSuit = onTable[0].suit
        highestValue = max([c.value for c in onTable if c.suit == currentSuit])
        try:
            highesValueTrump = max([c.value for c in onTable if c.suit == self.trump])
        except ValueError:
            highesValueTrump = 0

        # if the player has a card of the current follow suit, that is higher than the highest card of the current follow suit on the table, he must play it
        if any([c.suit == currentSuit and c.value > highestValue for c in hand]):
            return card.suit == currentSuit and card.value > highestValue

        # if the player has any other card in the current follow suit, he must play it
        if any([c.suit == currentSuit for c in hand]):
            return card.suit == currentSuit

        # if the player has a higher trum card than the highest trump card on the table, he must play it
        if any([c.suit == self.trump and c.value > highesValueTrump for c in hand]):
            return card.suit == self.trump and card.value > highesValueTrump

        # if the player has any trump card, he must play it
        if any([c.suit == self.trump for c in hand]):
            return card.suit == self.trump

        return True


game = BinokelGame()

game.deal()
game.bid(1)
game.bid(1)
game.bid(2)
game.bid(3)
game.bid(4)
game.bid(5)
game.bid(0)
game.bid(6)
game.bid(0)
game.bid(0)
game.bid(0)
game.bid(0)

game.press(0)
game.press(0)
game.press(0)
game.press(0)
game.press(0)
game.press(0)

game.setTrump(Suit.KROSS)

game.declare(0)
game.declare(-1)

game.declare(0)
game.declare(-1)

game.declare(0)
game.declare(-1)

game.declare(0)
game.declare(-1)


game.play(0)
game.play(0)
game.play(0)
game.play(0)
