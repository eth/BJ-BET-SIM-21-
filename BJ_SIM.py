import sys, os
import csv
import datetime
from random import shuffle
import numpy as np

# >>> import modules for creating plot maps <<<
#import scipy.stats as stats
#import pylab as pl
#import matplotlib.pyplot as plt

from importer.StrategyImporter import StrategyImporter

DEBUG_PRINT =0 # Debug Print to Console 
CSV_OUTPUT = 0 # Export details to CSV

GAME_OPTIONS = {
    'usecount' : True, # Modify Bet based on Card Counting Strat
}

SIMULATIONS = 1 #Simulation ends when # Shoes is reached OR Player_Bank <=0 OR Player_Bank >= WALK_AWAY
SHOES = 10000 #No. of shoes to simulate  
SHOE_SIZE = 4 # No. of Decks per shoe
SHOE_PENETRATION = 0.3 # Remaining % of cards before shuffle 

BET_MINIMUM = 1 # Minimum Bet 
BET_INCREMENT = 50 # set to 0 to disable Progressive betting
BANK_START = 20000 # Player Bank
WIN_STREAK = 999999999999 # consecutive hands to win before returning to Bet_Min
BET_AFT_SURR = False # False = BetMin | True = Bet greater of 50% or Min
WALK_AWAY = 999999999999 #BET_MINIMUM * 26.7 # amount to win before Ending Game

HOUSE_RULES = {
    'triple7': False,  # Count 3x7 as a blackjack
    'hitsoft17': False, # Does dealer hit soft 17
    'allowsurr': False, # Surrender Allowed (Assumes Late Surr)
    #TODO'maxsplithands': 4 # player max hands to split | aces only split once hard coded 
}

DECK_SIZE = 52.0
CARDS = {"Ace": 11, "Two": 2, "Three": 3, "Four": 4, "Five": 5, "Six": 6, "Seven": 7, "Eight": 8, "Nine": 9, "Ten": 10, "Jack": 10, "Queen": 10, "King": 10}

#//////////  COUNTING CARDS OPTIONS  \\\\\\\\\\\\
CC_OMEGA_II = {"Ace": 0, "Two": 1, "Three": 1, "Four": 2, "Five": 2, "Six": 2, "Seven": 1, "Eight": 0, "Nine": -1, "Ten": -2, "Jack": -2, "Queen": -2, "King": -2} # ADVANCED Hi-Opt 2
CC_OMEGA_I = {"Ace": 0, "Two": 0, "Three": 1, "Four": 1, "Five": 1, "Six": 1, "Seven": 0, "Eight": 0, "Nine": 0, "Ten": -1, "Jack": -1, "Queen": -1, "King": -1} # MID LEVEL Einstein - Hi-Opt 1
CC_HIGHLOW = {"Ace": -1, "Two": 1, "Three": 1, "Four": 1, "Five": 1, "Six": 1, "Seven": 0, "Eight": 0, "Nine": 0, "Ten": -1, "Jack": -1, "Queen": -1, "King": -1} # Basic Counting 
CC_RAPC = {"Ace": -4, "Two": 2, "Three": 3, "Four": 3, "Five": 4, "Six": 3, "Seven": 2, "Eight": 0, "Nine": -1, "Ten": -3, "Jack": -3, "Queen": -3, "King": -3}

COUNT_STRATEGY = CC_RAPC
BET_SPREAD = 10.0 #BET Multiplierr if truecount is favorable
COUNT_TIER = [5,10,15] # TrueCount Values for setting bet level - Higher truecount = bet more


#//////////  STRATEGY & FILE IMPORT OPTIONS  \\\\\\\\\\\\
if len(sys.argv) >1:
    STRATEGY_FILE = sys.argv[1] #user passed custom strategy file 
else:
    if HOUSE_RULES['hitsoft17']:
        STRATEGY_FILE = "BS_1.csv" #hitsoft17 
    else:
        STRATEGY_FILE = "BS_2.csv" #standall17's

HARD_STRATEGY = {}
SOFT_STRATEGY = {}
PAIR_STRATEGY = {}
#CARD3_STRATEGY = {}


#////////// Global Settings and Information accross ALL Games \\\\\\\\\\\\\
Player_Bank = BANK_START
Player_Bank_Max = [BANK_START,1] #Max, Hand #
Player_Bank_Min =  [BANK_START,1] #Min, Hand #
Bet_Curr = BET_MINIMUM
Bet_Streak = 0

#///////// <<< END HEADER / OPTIONS >>> \\\\\\\\\\\\\
#////////////////////////\\\\\\\\\\\\\\\\\\\\\\\\\\\\


def blockPrint():
    # Disable Printing to console
    sys.stdout = open(os.devnull, 'w')
    
def enablePrint():
    # Restore Printing to console
    sys.stdout = sys.__stdout__

def csv_create():
    try:
        with open('BJSIMDATA.csv','r') as file:
            reader = csv.reader(file)
            csv_file = csv.DictReader(file)
#            rows = list(csv_file)
#            x = rows[len(rows)-1]
            
        with open('BJSIMDATA.csv','a', newline='') as file:
            writer =csv.writer(file)
            writer.writerow(["NG","<<<<",datetime.datetime.now(),"<<<<"])
            
    except FileNotFoundError:
        with open('BJSIMDATA.csv', 'w', newline = '') as file:
            writer = csv.writer(file)
            writer.writerow(["SIM#","Shoe#","Hand", "Sub_Hand", "Status", "Bet", "$AMT$","P_Total","P_Hand","D_Total","D_Hand","Busted","BJ","Split","Surr","Double","Soft","Bank"])

def csv_write(c_objHand,c_nbhand,c_subhand,c_status,c_amt,c_DH,c_bank,c_bet,d_cards,p_cards,n_sim,s_num):
    with open('BJSIMDATA.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([n_sim,s_num,c_nbhand,c_subhand,c_status,c_bet,c_amt,c_objHand.value,p_cards,c_DH,d_cards,c_objHand.busted(),c_objHand.blackjack(),c_objHand.splithand,c_objHand.surrender,c_objHand.doubled,c_objHand.soft(),c_bank])


#>>> CARD <<<
class Card(object):
    """
    Represents a playing card with name and value.
    """
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return "%s" % self.name

#>>> SHOE <<<
class Shoe(object):
    """
    Represents the shoe, which consists of a number of card decks.
    """
    reshuffle = False

    def __init__(self, decks):
        self.count = 0
        self.count_history = []
        self.ideal_count = {}
        self.decks = decks
        self.cards = self.init_cards()
        self.init_count()

    def __str__(self):
        s = ""
        for c in self.cards:
            s += "%s\n" % c
        return s

    def init_cards(self):
        """
        Initialize the shoe with shuffled playing cards and set count to zero.
        """
        self.count = 0
        self.count_history.append(self.count)

        cards = []
        for d in range(self.decks):
            for c in CARDS:
                for i in range(0, 4):
                    cards.append(Card(c, CARDS[c]))
        shuffle(cards)
        return cards

    def init_count(self):
        """
        Keep track of the number of occurrences for each card in the shoe in the course over the game. ideal_count
        is a dictionary containing (card name - number of occurrences in shoe) pairs
        """
        for card in CARDS:
            self.ideal_count[card] = 4 * SHOE_SIZE

    def deal(self):
        """
        Returns:    The next card off the shoe. If the shoe penetration is reached,
                    the shoe gets reshuffled.
        """
        if self.shoe_penetration() < SHOE_PENETRATION:
            self.reshuffle = True
        
        card = self.cards.pop()
        
        assert self.ideal_count[card.name] > 0, "cc"
        self.ideal_count[card.name] -= 1

        self.do_count(card)
        return card

    def do_count(self, card):
        """
        Add the dealt card to current count.
        """
        self.count += COUNT_STRATEGY[card.name]
        self.count_history.append(self.truecount())

    def truecount(self):
        """
        Returns: The current true count.
        """
        return self.count / (self.decks * self.shoe_penetration())

    def shoe_penetration(self):
        """
        Returns: Ratio of cards that are still in the shoe to all initial cards.
        """
        return len(self.cards) / (DECK_SIZE * self.decks)

#>>> HAND <<<
class Hand(object):
    """
    Represents a hand, either from the dealer or from the player
    """
    _value = 0
    _aces = []
    _aces_soft = 0
    splithand = False
    surrender = False
    doubled = False

    def __init__(self, cards):
        self.cards = cards

    def __str__(self):
        h = ""
        for c in self.cards:
            h += "%s " % c
        return h

    @property
    def value(self):
        """
        Returns: The current value of the hand (aces are either counted as 1 or 11).
        """
        self._value = 0
        for c in self.cards:
            self._value += c.value

        if self._value > 21 and self.aces_soft > 0:
            for ace in self.aces:
                if ace.value == 11:
                    self._value -= 10
                    ace.value = 1
                    if self._value <= 21:
                        break

        return self._value

    @property
    def aces(self):
        """
        Returns all aces in the current hand.
        """
        self._aces = []
        for c in self.cards:
            if c.name == "Ace":
                self._aces.append(c)
        return self._aces

    @property
    def aces_soft(self):
        """
        Returns: The number of aces valued as 11
        """
        self._aces_soft = 0
        for ace in self.aces:
            if ace.value == 11:
                self._aces_soft += 1
        return self._aces_soft

    def soft(self):
        """
        Determines whether the current hand is soft (soft means that it consists of aces valued at 11).
        """
        if self.aces_soft > 0 and not self.blackjack():
            return True
        else:
            return False

    def splitable(self):
        """
        Determines if the current hand can be split.
        """
        if self.length() == 2 and self.cards[0].name == self.cards[1].name:
            return True
        else:
            return False

    def blackjack(self):
        """
        Check a hand for a blackjack
        """
        
        if self.value == 21:
            if all(c.value == 7 for c in self.cards) and HOUSE_RULES['triple7']:
                return False
            elif self.length() == 2: # 2 card 21 = blackjack and splithand = false
                return True
            else:
                return False
        else:
            return False

    def busted(self):
        """
        Checks if the hand is busted.
        """
        if self.value > 21:
            return True
        else:
            return False

    def add_card(self, card):
        """
        Add a card to the current hand.
        """
        self.cards.append(card)

    def split(self):
        """
        Split the current hand.
        Returns: The new hand created from the split.
        """
        self.splithand = True
        c = self.cards.pop()
        new_hand = Hand([c])
        new_hand.splithand = True
        return new_hand

    def length(self):
        """
        Returns: The number of cards in the current hand.
        """
        return len(self.cards)


#>>> PLAYER <<<
class Player(object):
    """
    Represent a player
    """
    def __init__(self, hand=None, dealer_hand=None):
        self.hands = [hand]
        self.dealer_hand = dealer_hand

    def set_hands(self, new_hand, new_dealer_hand):
        self.hands = [new_hand]
        self.dealer_hand = new_dealer_hand

    def play(self, shoe):
        for hand in self.hands:
            # print "Playing Hand: %s" % hand
            self.play_hand(hand, shoe)

    def play_hand(self, hand, shoe):
        split_aces = False
        if hand.length() < 2: #SPLIT HANDS
            if hand.cards[0].name == "Ace":
                hand.cards[0].value = 11
                split_aces = True # split aces once and only take 1 card
            self.hit(hand, shoe) #adding 2nd card to split hand
            
        while not hand.busted() and not hand.blackjack() and not split_aces:
            if hand.soft():
                flag = SOFT_STRATEGY[hand.value][self.dealer_hand.cards[0].name]
            elif hand.splitable():
                flag = PAIR_STRATEGY[hand.value][self.dealer_hand.cards[0].name]
            else:
                flag = HARD_STRATEGY[hand.value][self.dealer_hand.cards[0].name]

            if flag == 'D':
                if hand.length() == 2:
                    # print "Double Down"
                    hand.doubled = True
                    self.hit(hand, shoe) #take 1 card
                    break
                else:
                    
                    #TODO - BUG - if > 2 cards AND soft AND val>17 - flag = S
                    #example: soft 13 vs 4 = hit, draw 4 now have 3 card soft 18 = S
                    flag = 'H'
                    
            if flag in ('Sr','RS'):
                if HOUSE_RULES['allowsurr']:
                    if hand.length() == 2:
                        # print "Surrender"
                        hand.surrender = True
                        break
                    elif flag == 'RS':
                        flag = 'S' # Break on check for S flag
                    else:
                        flag = 'H'
                else: #Surrender Not Permitted
                    if flag == 'RS':
                        flag = 'S'
                    else:
                        flag = 'H'

            if flag == 'H':
                self.hit(hand, shoe)

            if flag == 'P':
                self.split(hand, shoe)

            if flag == 'S':
                break

    def hit(self, hand, shoe):
        c = shoe.deal()
        hand.add_card(c)
        print ("Player hit: %s" % (c))

    def split(self, hand, shoe):
        self.hands.append(hand.split())
        print ("SPLIT %s" % hand)
        self.play_hand(hand, shoe)

#>>> DEALER <<<
class Dealer(object):
    """
    Represent the dealer
    """
    def __init__(self, hand=None):
        self.hand = hand

    def set_hand(self, new_hand):
        self.hand = new_hand

    def play(self, shoe):

        if HOUSE_RULES['hitsoft17']:
            while self.hand.value < 17 or (self.hand.value == 17 and self.hand.soft()):
                if self.hand.value == 17 and self.hand.soft():
                    print("SOFT 17 | %d" % (nb_hands[0]))
                self.hit(shoe)
        else:
            while self.hand.value < 17:
                self.hit(shoe)

    def hit(self, shoe):
        c = shoe.deal()
        self.hand.add_card(c)
        print ("Dealer hit: %s" % (c))

#>>> GAME <<<
class Game(object):
    """
    A sequence of Blackjack Rounds that keeps track of total money won or lost
    """
    def __init__(self):
        self.shoe = Shoe(SHOE_SIZE)
        self.money = 0 # Bankroll gain/loss per shoe
        self.bet = 0 # Cumulative bets per shoe
        self.wager = 0
        self.player = Player()
        self.dealer = Dealer()
        #DL Additions
        self.wins = 0
        self.loss = 0
        self.hands = 0
        Bet_Curr = BET_MINIMUM
        Bet_Streak =0
        
        

    def play_round(self,n_sim,n_shoe):
        global Player_Bank

        if GAME_OPTIONS['usecount']:
            tc = self.shoe.truecount() 
            if tc > 6:
                self.wager = (tc - 1) * BET_INCREMENT
                if self.wager > 250:
                    self.wager = 250
            else:
                self.wager = BET_MINIMUM
        else:
            self.wager = Bet_Curr

        player_hand = Hand([self.shoe.deal(), self.shoe.deal()])
        dealer_hand = Hand([self.shoe.deal()])
                
        self.player.set_hands(player_hand, dealer_hand)
        self.dealer.set_hand(dealer_hand)
        
        dealer_upcard = self.dealer.hand.cards[0].value
        
        print ("--- %d ---" % (nb_hands[0]))
        print ("Player Hand: %s" % self.player.hands[0])
        print ("Dealer UPCARD: %s" % dealer_upcard)
        
        self.dealer.hit(self.shoe) #popping dealer hole card
        print ("Dealer Hand: %s" % self.dealer.hand)
        
        #player only plays if the dealer does not have blackjack
        if self.dealer.hand.blackjack() and dealer_upcard >= 10:
            print ("Dealer BlackJack - player does not draw")
        else:
            self.player.play(self.shoe)
            
        
        All_Bust = True
        for b_hand in self.player.hands:
            if b_hand.busted() != True:
                All_Bust = False
        
        #dealer only plays if players have not busted all hands AND do not have black jack
        if not All_Bust and not self.player.hands[0].blackjack(): 
            #self.dealer.play(self.shoe,All_Bust)
            self.dealer.play(self.shoe)
        else:
            print("Player BUSTED all hands - dealer does not draw")
            
        win_net = 0
        subhand = 0
        for hand in self.player.hands:
            win, bet, status = self.get_hand_winnings(hand) # Determine if Win or Lose then adjust bet/banks accordingly def set_bets()
            
            win_net += win # appends the cumulative wins/losses for hands that include splits/ sub-hands
            Player_Bank += win
            
            self.money += win # Bank for each shoe
            self.bet += bet # Cumulative bet - used to deterimine avg bet size
            self.hands += 1 # No hands per shoe
    
            print ("RESULT: %d.%d " % (nb_hands[0],subhand + 1))
            print ("Player:%s $%d (%d) %s| Busted:%r, BlackJack:%r, Splithand:%r, Soft:%r, Surrender:%r, Doubled:%r" % (status,win, hand.value, self.player.hands[subhand], hand.busted(), hand.blackjack(), hand.splithand, hand.soft(), hand.surrender, hand.doubled))
    
            print ("Dealer:    (%d) %s" % (self.dealer.hand.value,self.dealer.hand))
            print ("")
            if CSV_OUTPUT == 1:
                csv_write(hand,nb_hands[0],subhand + 1,status,win,self.dealer.hand.value,Player_Bank,self.wager,self.dealer.hand,self.player.hands[subhand],n_sim+1,n_shoe+1)
            
            subhand +=1
            
        self.set_bets(win_net,status)
    
    
    def get_hand_winnings(self, hand):
        win = 0.0 # win/loss multiplier of the bet
        bet = self.wager
        if not hand.surrender:
            if hand.busted():
                status = "LOST"
                nb_hands[4] += 1
            else:
                if hand.blackjack():
                    nb_hands[5] +=1
                    if self.dealer.hand.blackjack():
                        status = "PUSH"
                    else:
                        status = "WON 3:2"
                elif self.dealer.hand.busted():
                    status = "WON"
                elif self.dealer.hand.value < hand.value:
                    status = "WON"
                elif self.dealer.hand.value > hand.value:
                    status = "LOST"
                elif self.dealer.hand.value == hand.value:
                    if self.dealer.hand.blackjack():
                        status = "LOST"  # player's 21 vs dealers blackjack
                    else:
                        status = "PUSH"
        else:
            status = "SURRENDER"
            nb_hands[6] += 1

        if status == "LOST":
            self.loss += 1
            nb_hands[2] += 1
            win += -1
        elif status == "WON":
            self.wins += 1
            nb_hands[1] += 1
            win += 1
            
        elif status == "WON 3:2":
            self.wins += 1
            nb_hands[1] += 1
            win += 1.5
        elif status == "SURRENDER":
            self.loss += 1
            #nb_hands[2] += 1
            win += -0.5
        elif status == "PUSH":
            nb_hands[3] += 1
        
        if hand.doubled:
            win *= 2
            bet *= 2

        win *= self.wager
        return win, bet, status

    def set_bets(self,n_win,s_status):
        global Player_Bank_Max #Max, Hand #
        global Player_Bank_Min #
        #Bet_Prev = Bet_Minimum
        global Bet_Curr
        global Bet_Streak
        
        
        if Player_Bank > Player_Bank_Max[0]:
            Player_Bank_Max[0] = Player_Bank
            Player_Bank_Max[1] = nb_hands[0]
        elif Player_Bank < Player_Bank_Min[0]:
            Player_Bank_Min[0] = Player_Bank
            Player_Bank_Min[1] = nb_hands[0]
            
        if n_win > 0: # winner - raise bet
            Bet_Streak +=1
        
            if Bet_Streak < WIN_STREAK:
                Bet_Curr += BET_INCREMENT
            elif Bet_Streak >= WIN_STREAK:
                Bet_Curr = BET_MINIMUM
                Bet_Streak = 0
                
        elif n_win < 0: #loser - reset bets
            if s_status == "SURRENDER" and BET_AFT_SURR:
                Bet_Curr *= 0.5
                if Bet_Curr < BET_MINIMUM:
                    Bet_Curr = BET_MINIMUM
            else:
                Bet_Curr = BET_MINIMUM
            Bet_Streak = 0
            # else PUSH - do nothing
        

    def get_hands(self):
        return self.hands

    def get_wins(self):
        return self.wins

    def get_loss(self):
        return self.loss

    def get_money(self):
        return self.money

    def get_bet(self):
        return self.bet



if __name__ == "__main__":
    importer = StrategyImporter(STRATEGY_FILE)
    HARD_STRATEGY, SOFT_STRATEGY, PAIR_STRATEGY = importer.import_player_strategy()

    if CSV_OUTPUT == 1:
        csv_create() # create default output CSV file 


    for s_num in range(SIMULATIONS):
        #//// RESET all data for each simulation \\\\
        moneys = []
        bets = []
        countings = []
        total_win = 0.0 # Total Win/Loss $ over all games
        total_bet = 0.0 # Total cumlative bet of all hands
        nb_hands = [0,0,0,0,0,0,0] # 0hands, 1win, 2loss, 3push, 4bust, 5bj, 6surr
        w_away = False

        Player_Bank = BANK_START
        Player_Bank_Max = [BANK_START,1] #Max, Hand #
        Player_Bank_Min =  [BANK_START,1] #Min, Hand #
        Bet_Curr = BET_MINIMUM
        Bet_Streak = 0
        print ('\n%s SIMULATION no. %d %s' % (8 * '#', s_num + 1, 8 * '#'))
        
        for g_num in range(SHOES):
            game = Game()
            while not game.shoe.reshuffle:
                
                if DEBUG_PRINT == 1: 
                    enablePrint()
                else:
                    blockPrint()
                            
                nb_hands[0] += 1
                game.play_round(s_num,g_num)
                
                if (Player_Bank - BANK_START) > WALK_AWAY:
                    w_away = True
                    break
                elif Player_Bank <= 0:
                    w_away = True
                    break
                
            moneys.append(game.get_money())
            total_win += game.get_money()
            
            bets.append(game.get_bet())
            total_bet += game.get_bet()
            countings += game.shoe.count_history
            
            print("--- SHOE %d SUMMARY ---" % (g_num+1))
            enablePrint()
            print("SHOE-%d: Win:%s Lose:%s | %s Hands inc/Splits - $%s | $%s" % (g_num + 1, "{0}".format(game.get_wins()), "{0}".format(game.get_loss()),"{0}".format(game.get_hands()), "{0:.2f}".format(game.get_money()),"{0:.2f}".format(Player_Bank)))
            
            if w_away:
                print("   >>>> PLAYER WALKS AWAY: Hand %d  w/ Bank: %d <<<<" % (nb_hands[0],Player_Bank))
                break
            
        PC_win = nb_hands[1]/nb_hands[0]*100
        PC_lose = nb_hands[2]/nb_hands[0]*100
        PC_push = nb_hands[3]/nb_hands[0]*100
        PC_bust = nb_hands[4]/nb_hands[0]*100
        PC_bj = nb_hands[5]/nb_hands[0]*100
        PC_surr = nb_hands[6]/nb_hands[0]*100
        
        Avg_Bet = total_bet/nb_hands[0]
        
        print("\nWinnings: {} (win/bet = {} %)".format("{0:.2f}".format(total_win), "{0:.3f}".format(100.0*total_win/total_bet)))
        print("Max Bank: $%d at %d | Min Bank: $%d at %d" % (Player_Bank_Max[0],Player_Bank_Max[1],Player_Bank_Min[0],Player_Bank_Min[1]))
        print("Ending Bank: {}".format("{0:.2f}".format(Player_Bank)))
        print ("Average bet: %0.2f  Total bets: %0.2f" % (Avg_Bet,total_bet))
        print("\nWin: %s %s \nLose: %s %s %s \nSurr: %s %s \nPush: %s %s" % ("{0}".format(nb_hands[1]),"{0:.2f}".format(PC_win), "{0}".format(nb_hands[2]),"{0:.2f}".format(PC_lose),"{0:.2f}".format(PC_lose+PC_surr),"{0}".format(nb_hands[6]),"{0:.2f}".format(PC_surr),"{0}".format(nb_hands[3]),"{0:.2f}".format(PC_push)))
        
        print("\nBust: %s %s \nBJ: %s %s" % ("{0}".format(nb_hands[4]),"{0:.2f}".format(PC_bust), "{0}".format(nb_hands[5]),"{0:.2f}".format(PC_bj)))
        print ("Summary: %d Rounds, %d Rounds /Shoe Avg" % (nb_hands[0], nb_hands[0] / (g_num+1)))
        




# Chart Plots - 
    
#
#    moneys = sorted(moneys)
#    fit = stats.norm.pdf(moneys, np.mean(moneys), np.std(moneys))  # this is a fitting indeed
#    pl.plot(moneys, fit, '-o')
#    pl.hist(moneys, normed=True)
#    pl.show()
#
#    plt.ylabel('count')
#    plt.plot(countings, label='x')
#    plt.legend()
#    plt.show()
    