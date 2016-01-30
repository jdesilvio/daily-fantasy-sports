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

# Scrape bulk data from www.numberfire.com and
# Create JSON with necessary data for algorithm
def create_players_json():

    # Write the full JSON object
    with open('nfl.csv') as f:
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
def player_combos(players_list, dpp_floor=0, limit = 7, \
selection_feature='ppd', exclude=[]):

    print "Total players: ", len(players_list)

    QB = []
    RB = []
    WR = []
    TE = []
    K = []
    D = []

    removed_count = 0
    for player in players_list:
        if player['slug'] in exclude:
            removed_count += 1
            print player['slug'], "stinks! $", \
            player['salary'], "-", player['projection']
        else:
            try:
                if (player['position'] == 'QB'):
                    QB.append(player)
                elif (player['position'] == 'RB'):
                    RB.append(player)
                elif (player['position'] == 'WR'):
                    WR.append(player)
                elif (player['position'] == 'TE'):
                    TE.append(player)
                elif (player['position'] == 'K'):
                    K.append(player)
                elif (player['position'] == 'D'):
                    D.append(player)
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
    print len(K), "Ks"
    print len(D), "Ds"

    """ We need to limit the number of players for each position,
    otherwise the numbers of combinations would be in the trillions
    and not feasible to compute on a laptop"""
    QB = sorted(QB, key=itemgetter(selection_feature), reverse = True)[0:limit]
    RB = sorted(RB, key=itemgetter(selection_feature), reverse = True)[0:limit]
    WR = sorted(WR, key=itemgetter(selection_feature), reverse = True)[0:limit]
    TE = sorted(TE, key=itemgetter(selection_feature), reverse = True)[0:limit]
    K = sorted(K, key=itemgetter(selection_feature), reverse = True)[0:limit]
    D = sorted(D, key=itemgetter(selection_feature), reverse = True)[0:limit]

    ### Print players used in lineups
    for i in QB:
        print i["position"] + "\t" + str(i["projection"]) + "\t" + str(i["salary"]) + "\t" + i["slug"]
    for i in RB:
        print i["position"] + "\t" + str(i["projection"]) + "\t" + str(i["salary"]) + "\t" + i["slug"]
    for i in WR:
        print i["position"] + "\t" + str(i["projection"]) + "\t" + str(i["salary"]) + "\t" + i["slug"]
    for i in TE:
        print i["position"] + "\t" + str(i["projection"]) + "\t" + str(i["salary"]) + "\t" + i["slug"]
    for i in K:
        print i["position"] + "\t" + str(i["projection"]) + "\t" + str(i["salary"]) + "\t" + i["slug"]
    for i in D:
        print i["position"] + "\t" + str(i["projection"]) + "\t" + str(i["salary"]) + "\t" + i["slug"]

    # Create combinations for each position
    QBiter = combinations(QB, 1)
    QBcombos = [ combo for combo in QBiter ]

    RBiter = combinations(RB, 2)
    RBcombos = [ combo for combo in RBiter ]

    WRiter = combinations(WR, 3)
    WRcombos = [ combo for combo in WRiter ]

    TEiter = combinations(TE, 1)
    TEcombos = [ combo for combo in TEiter ]

    Kiter = combinations(K, 1)
    Kcombos = [ combo for combo in Kiter ]

    Diter = combinations(D, 1)
    Dcombos = [ combo for combo in Diter ]

    # Create complete lineup combinations
    combos = product(QBcombos, RBcombos, WRcombos, TEcombos, Kcombos, Dcombos)

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
            print count, "total lineups looked at -", len(lineups), "are valid"

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
                if lineup_salary <= 60000 and len(lineup) == 9:
                    count_valid += 1
                    if sum(s['projection'] for s in lineup) > 80:
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

    #create_players_json()

    with open('players.json') as f:
        data = json.load(f)

    lineups = player_combos(data, \
    dpp_floor=10000, \
    limit = 15, \
    selection_feature='ppd', \
    exclude=[\
    'Cody-Latimer',\
    'Andre-Ellington',\
    'Cameron-Artis-Payne',\
    'Brandon-Bolden',\
    'Mike-Tolbert',\
    'Kerwynn-Williams',\
    'Juwan-Thompson',\
    'Stepfan-Taylor',\
    'Jeremy-Stewart',\
    'Jermaine-Gresham',\
    'Cam-Newton',\
    'Tom-Brady',\
    'Carolina-Panthers',\
    'Brandon-LaFell',\
    'Keshawn-Martin',\
    'Danny-Amendola',\
    'Steven-Jackson',\
    'James-White',\
    'Graham-Gano',\
    'New England-Patriots',\
    '',\
    '',\
    '',\
    '',\
    'Emmanuel-Sanders',\
    'x Jamarcus-Nelson',\
    'x Corey (Philly)-Brown',\
    'x Devin-Funchess',\
    'x Jerricho-Cotchery',\
    'x Andre-Caldwell',\
    'x Bennie-Fowler',\
    'x Vernon-Davis',\
    'Darren-Fells',\
    'x Owen-Daniels',\
    'x Demaryius-Thomas',\
    'Ted-Ginn Jr.',\
    'x Foswhitt-Whittaker',\
    'x Owen-Daniels',\
    ])

    lineup_print(lineups, sort_feature='points', n=40)
