import requests
import lxml.html
import re
import csv
import time
from bs4 import BeautifulSoup
import json
from itertools import combinations, product, chain
from operator import itemgetter
import numpy as np
from tqdm import tqdm

# Integrate Fanduel data for specific contest
def fanduel_data():

    # Read data from Fanduel file
    with open("cbb.csv") as f:
        reader = csv.DictReader(f)
        fd_data = [ row for row in reader ]

    # Normalize player metadata
    for player in fd_data:
        player["id"] = player["Id"]
        player["slug"] = player['First Name'] + "-" + player['Last Name']
        player["salary"] = float(player['Salary'])
        player["projection"] = float(player['FPPG'])
        player["position"] = player["Position"]
        try:
            player['ppd'] = player['projection']/player['salary']
        except:
            player["ppd"] = 0

    # Tie Fanduel data into NumbersFire data
    for player in fd_data:
        map(player.pop, ['Salary', 'First Name', 'Last Name', 'FPPG', \
        'Position', 'Id'])

    with open('data/output/playersCBB.json', 'w') as f:
        json.dump(fd_data, f, indent=2)

def create_position_lists(players_data, dpp_floor=300, point_floor = 270, exclude=[]):

    print "Total players: ", len(players_data)

    positions = { 'F': [], 'G': [] }

    removed_count = 0
    for player in players_data:
        if player['projection'] == 0 or player['slug'] in exclude or \
        player['salary']/player['projection'] > dpp_floor:
            removed_count += 1
            print player['slug'], "removed! $", \
            player['salary'], "-", player['projection']
        else:
            try:
                if (player['position'] == 'F'):
                    positions['F'].append(player)
                elif (player['position'] == 'G'):
                    positions['G'].append(player)
            except:
                print "Position Error: ", player["slug"]
                removed_count += 1

    # Print stats
    print "----------------------------"
    print "Now there are", len(players_data) - removed_count, "players."
    print "----------------------------"
    print len(positions['F']), "Fs"
    print len(positions['G']), "Gs"

    return positions

""" We need to limit the number of players for each position,
otherwise the numbers of combinations would be in the trillions
and not feasible to compute on a laptop"""
def create_position_combos(position_list, selection_feature, limit, \
players_per_pos):

    # Trim players list
    trimmed_pos_list = sorted(position_list, \
    key=itemgetter(selection_feature), reverse = True)[0:limit]

    # Print players in trimmed list
    for i in trimmed_pos_list:
        print i["position"] + "\t" + \
        str(int(i["projection"])) + "\t" + \
        str(int(i["salary"])) + "\t" + \
        i["slug"]

    # Create combinations
    combos = combinations(trimmed_pos_list, players_per_pos)
    return [ combo for combo in combos ]

def construct_lineups(positions, limit, selection_feature, point_floor):

    print "Start Time: ", time.strftime("%x"), time.strftime("%X")

    # Create position combos
    F = create_position_combos(positions['F'], selection_feature, limit, 5)
    G = create_position_combos(positions['G'], selection_feature, limit, 4)

    # Create complete lineup combinations
    combos = tqdm(product(F, G))
    combos = tqdm([list(chain(*combo)) for combo in combos])
    print "Possible Lineups: ", len(combos)
    combos = tqdm([combo for combo in combos if sum(map(itemgetter("salary"), combo)) <= 60000])
    combos = tqdm([combo for combo in combos if sum(map(itemgetter("projection"), combo)) >= point_floor])

    return combos

def valid_lineups(combos, point_floor):

    count = 0
    count_valid = 0
    lineups = []

    for combo in tqdm(combos):
        count_valid += 1
        lineup = {'lineup': combo,
            'salary': sum(map(itemgetter("salary"), combo)),
            'points': sum(map(itemgetter("projection"), combo))}
        lineups.append(lineup)

    ### Status
    print "Total lineups: ", len(lineups)
    print "End Time: ", time.strftime("%x"), time.strftime("%X")

    return lineups

# Create valid lineups based on parameters
def lines(players_data, dpp_floor=300, point_floor=270, exclude=[], \
limit=7, selection_feature='ppd'):
    positions = create_position_lists(players_data, dpp_floor, point_floor, exclude)
    combos = construct_lineups(positions, limit, selection_feature, point_floor)
    return valid_lineups(combos, point_floor)

# Print lineups
def lineup_print(lineups, n, sort_feature='points'):
    print "Lineups based on", sort_feature
    lineups = sorted(lineups, key=lambda lineups: lineups[sort_feature], \
    reverse = True)
    count = 1
    for lineup in lineups[0:n]:
        print 'Lineup #', count
        print "Points:", lineup['points'], "   Salary:", lineup['salary']
        for player in lineup['lineup']:
            print "$" + str(int(player['salary'])), \
            "\t" + str(int(player['projection'])), \
            "\t" + str(player['position']), \
            "\t" + player['slug']
        count += 1
