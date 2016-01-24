import requests
import lxml.html
import re
import csv
import time
from mechanize import Browser
from bs4 import BeautifulSoup
import json
from itertools import combinations, product
from operator import itemgetter

url = 'https://www.numberfire.com/nba/fantasy/fantasy-basketball-projections'

# Scrape bulk data from www.numberfire.com and
# Create JSON with necessary data for algorithm
def create_players_json(url):

    # Write the full JSON object
    with open('ncaaf.csv') as f:
        reader = csv.DictReader(f)
        JSON = [row for row in reader]

    # Get player_ids
    player_ids = [ player['Id'] for player in JSON ]

    # Build player data
    for player in JSON:
        player["id"] = player["Id"]
        player["slug"] = player['First Name'] + "-" + player['Last Name']
        player["salary"] = float(player['Salary'])
        player["projection"] = float(player['FPPG'])
        player["position"] = player["Position"]
        try:
            player['ppd'] = player['projection']/player['salary']
        except:
            player["ppd"] = 0

    for player in JSON:
        map(player.pop, ['Salary', 'First Name', 'Last Name', 'FPPG', \
        'Position', 'Id'])

    with open('players.json', 'w') as f:
        json.dump(JSON, f, indent=2)

# Create player combinations
### Make more efficient
def player_combos(players_list, dpp_floor=300, limit = 7, \
selection_feature='ppd', exclude=[]):
    print "Total players: ", len(players_list)
    QB = []
    RB = []
    WR = []
    TE = []

    removed_count = 0
    for player in players_list:
        if player['projection'] == 0 or player['slug'] in exclude or \
        player['salary']/player['projection'] > dpp_floor:
            removed_count += 1
            print player['slug'], "stinks! $", \
            player['salary'], "-", player['projection']
        else:
            try:
                if (player['position'] == 'QB' and player['projection'] > 10):
                    QB.append(player)
                elif (player['position'] == 'RB' and player['projection'] > 10):
                    RB.append(player)
                elif (player['position'] == 'WR' and player['projection'] > 5):
                    WR.append(player)
                elif (player['position'] == 'TE' and player['projection'] > 3):
                    TE.append(player)
            except:
                print "Position Error: ", player
                removed_count += 1

    ### Status
    print "----------------------------"
    print "Now there are", len(players_list) - removed_count, "players."
    print "----------------------------"
    print len(QB), "QBs"
    print len(RB), "RBs"
    print len(WR), "WRs"
    print len(TE), "TEs"

    """ We need to limit the number of players for each position,
    otherwise the numbers of combinations would be in the trillions
    and not feasible to compute on a laptop"""
    QB = sorted(QB, key=itemgetter(selection_feature), reverse = True)[0:limit]
    RB = sorted(RB, key=itemgetter(selection_feature), reverse = True)[0:limit]
    WR = sorted(WR, key=itemgetter(selection_feature), reverse = True)[0:limit]
    TE = sorted(TE, key=itemgetter(selection_feature), reverse = True)[0:limit]

    ### Print players used in lineups
    for i in QB:
        print i
    for i in RB:
        print i
    for i in WR:
        print i
    for i in TE:
        print i

    # Create combinations for each position
    QBiter = combinations(QB, 1)
    QBcombos = [ combo for combo in QBiter ]

    RBiter = combinations(RB, 2)
    RBcombos = [ combo for combo in RBiter ]

    WRiter = combinations(WR, 3)
    WRcombos = [ combo for combo in WRiter ]

    TEiter = combinations(TE, 1)
    TEcombos = [ combo for combo in TEiter ]

    # Create complete lineup combinations
    combos = product(QBcombos, RBcombos, WRcombos, TEcombos)

    ### Status
    print "Start Time: ", time.strftime("%x"), time.strftime("%X")

    # Iterate through lineup combos
    count = 0
    count_valid = 0
    lineups = []
    for combo in combos:

        ### Status
        count += 1
        if count % 100000 == 0:
            print count, "total lineups looked at -", count_valid, "are valid"

        # Iterate through position tuples
        lineup = []
        lineup_salary = 0
        for position in combo:

            # Map tuples to create list of dictionaries
            position_dict = map(dict, position)

            # Iterate through players to find valid lineups under $60,000
            for player in position_dict:
                lineup_salary += player['salary']
                lineup.append(player)
                # Only add if a complete and valid lineup
                if lineup_salary <= 45000 and len(lineup) == 7:
                    count_valid += 1
                    if sum(s['projection'] for s in lineup) > 100:
                        lineup_desc = {'lineup': lineup, \
                        'salary': sum(s['salary'] for s in lineup), \
                        'points': sum(s['projection'] for s in lineup)}

                        lineups.append(lineup_desc)

    ### Status
    print "Total lineups: ", len(lineups)
    print "End Time: ", time.strftime("%x"), time.strftime("%X")

    return lineups

def lineup_print(lineups, n, sort_feature='points'):
    print "Lineups based on", sort_feature
    lineups = sorted(lineups, key=lambda lineups: lineups[sort_feature], \
    reverse = True)
    count = 1
    for lineup in lineups[0:n]:
        print 'Lineup #', count
        print "Points:", lineup['points'], "   Salary:", lineup['salary']
        for player in lineup['lineup']:
            print "$" + str(player['salary']), \
            "\t" + str(player['projection']), \
            "\t" + str(player['position']), \
            "\t" + player['slug']
        count += 1

def bestbets(exclude, n):
    print "Start Time: ", time.strftime("%x"), time.strftime("%X")
    players_list = import_predictions()
    players_list = exclude_players(exclude, players_list)
    all_combos = player_combos(players_list)
    lineups_comp = lineup(all_combos)
    lineup_print(lineups_comp, n)
    print "End Time: ", time.strftime("%x"), time.strftime("%X")

### MAIN #######################################################################

if __name__ == "__main__":

    create_players_json(url)

    with open('players.json') as f:
        data = json.load(f)

    lineups = player_combos(data, \
    dpp_floor=900, \
    limit = 20, \
    selection_feature='ppd', \
    exclude=['Chad-Kelly', 'C.J.-Beathard', 'Joshua-Dobbs', 'DeShone-Kizer', \
    'Kevin-Hogan'])

    lineup_print(lineups, sort_feature='points', n=100)

# kelly - 'Evan-Engram','Marcell-Ateman'
