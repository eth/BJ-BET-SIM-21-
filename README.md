# BJ-BET-SIM-21-
BlackJack-SIM | Card Counting
==============================================
The Simulator takes a given basic strategy(BS) as input (defined in a .csv-file) and simulates the win/loss against a random shoe with user entered number of decks. The sim counts cards using one of  3 card counting systems selected by user. Depending on the current count, or other settings, simulation will adjust the bet size.  



Counting and Probabilities Strategies Courtesy of wizardofodds.com

### Written using python 3

    python3 BJ_SIM.py [optional Strategy File.csv]
    -- if no strategy file passed it will read BS_1 or BS_2.csv by default --

For explanation of counting card values see wizardofodds.com

User can Enable or Disable card counting under GAME_OPTIONS ('usecount')

### Definition of Terms

BJ_SIM definitions:
* A *Hand* is a single hand of Blackjack, consisting of two or more cards - it might include a split
* A *Round* is single round of Blackjack, which simulates your hand(s) against the dealer's hand
* A *Shoe* is multiple decks of cards equal to SHOE_SIZE ** 52 card decks (typically BJ is played with 2, 6 or 8 decks) at shuffle it is returned as SHOE#-[x]



### Result

The sim provides net winnings per shoe/game & simulation played w/ overall results summing up. The following output for example:  
        ######## SIMULATION no. 3 ########
        SHOE-1: Win:15 Lose:27 | 45 Hands inc/Splits - $-350.00 | $9650.00
        SHOE-2: Win:16 Lose:26 | 46 Hands inc/Splits - $525.00 | $10175.00
        SHOE-3: Win:15 Lose:25 | 44 Hands inc/Splits - $-450.00 | $9725.00
        SHOE-4: Win:22 Lose:19 | 45 Hands inc/Splits - $900.00 | $10625.00
        SHOE-5: Win:19 Lose:22 | 44 Hands inc/Splits - $-25.00 | $10600.00

### Plotting

Graphs and Plots are disabled by default, by importing external module you can plot/graph results

### HOUSE_RULES

SIM can enable/disable the following HOUSE_RULES:

* triple7 | 3 7's counted as a blackjack *
* hitsoft17 | house hits soft 17's *
* allowsurr | house allows Late Surrender *

These House Rules are Hard Coded:

* Double down after splitting hands on any 2 cards permitted
* No BlackJack after splitting hands
* Split aces only once

### User Set Variables

| Variable        | Description         |
| ------------- |-------------|
| *SIMULATIONS*  | The number of Sims that should run |
| *SHOES*  | The number of shoes to complete per Simulation before ending the sim |
| *SHOE_SIZE*   | The number of decks per shoe |
| *SHOE_PENETRATION*  | % of cards remaining in the shoe before reshuffle |
| *BET_MINIMUM* | The minimum bet for each hand |
| *BET_INCREMENT* | The bet unit for progressive betting |
| *BANK_START* | The players bank at start of each SIMULATION |
| *WIN_STREAK* | Used in conjuction with BET_INCREMENT |
| *BET_AFT_SURR*| When true, leaves 50% of prior bet for next hand |
| *WALK_AWAY* | A Preset amount to win that ENDS the SIMULATiON
| *BET_SPREAD*  | The multiplier for the bet size in a player favorable counting situation |
| *COUNT_TIER* | True Count Tier Values for raising bets |
| *COUNT_STRATEGY* | User Selected Strategy to use for Counting Cards
| *DEBUG_PRINT* | Prints to console details of every hand
| *CSV_OUTPUT* | Exports to CSV results

### Sample Configuration

    BET_MINIMUM = 100 # Minimum Bet 
    BANK_START = 10000 # Player Bank
    BET_AFT_SURR = False # False = BetMin | True = Bet greater of 50% or Min
    WALK_AWAY = 5000  # amount to win before Ending Simulation

    COUNT_STRATEGY = CC_OMEGA_II  
    BET_SPREAD = 10.0 #BET Multiplierr if truecount is favorable
    COUNT_TIER = [5,10,15] # TrueCount Values for setting bet level - Higher truecount = bet more
    
### Strategy

Any strategy can be passed as a sysarg into the simulator as a .csv file. The default strategy BS1 or BS2 that comes in directory will load if no sysarg is passed. 
png images of basic strategy included in /strategy directory

* The first column shows both player's cards added up
* The first row shows the dealers up-card
* S ... Stand
* H ... Hit
* Sr ... Surrender otherwise Hit
* RS ... Surrender; otherwise Stand
* D ... Double Down
* P ... Split
