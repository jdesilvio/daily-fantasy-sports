import requests
import lxml.html
import re
import csv
import time
from datetime import datetime
from bs4 import BeautifulSoup
import json
from itertools import combinations, product, chain
from operator import itemgetter
import numpy as np
from tqdm import tqdm

def time_delta(t1, t2):
    return str(int(abs(t2-t1) * 1000)) + "ms"

################################################################################
"""Scrape, transform and clean data""" #########################################
################################################################################

# Scrape bulk data from www.numberfire.com and returns a list of dicts
def get_nf_data(url):

    # Send request to URL and convert HTML
    r = requests.get(url).text
    doc = lxml.html.fromstring(r)

    # Grab the script element with the JSON var in it
    rows = doc.xpath('//script')
    data = rows[3].xpath('./text()')

    # Extract the JSON
    data = data[0].encode("utf-8").split("=")
    data = data[1].split(";")[0]

    return json.loads(data)

# Normalize key names and derive data; returns a list of dicts
def normalize_nf_data(data):

    # Get player_ids
    player_ids = [ player_id for player_id in data['players'] ]

    # Build player data from NumbersFire data
    nf_data = []
    for player_id in player_ids:
        player_dict = {}
        player_dict["id"] = player_id
        player_dict["slug"] = data['players'][player_id]['slug']
        last = data['players'][player_id]['last_name']
        first = data['players'][player_id]['first_name']
        for i in data['daily_projections']:
            if i['nba_player_id'] == player_id:
                player_dict["salary"] = i['fanduel_salary']
                player_dict["projection"] = i['fanduel_fp']
                try:
                    player_dict['ppd'] = i['fanduel_fp']/i['fanduel_salary']
                except:
                    pass
                player_dict['nerd'] = i['nerd']
                player_dict['play'] = i['game_play_probability']
                player_dict['uid'] = first[0:1].lower() + \
                last[0:3].lower() + last[len(last)-1: len(last)] + \
                str(i['fanduel_salary'])
                break
        nf_data.append(player_dict)

    return nf_data

# Integrate Fanduel data for specific contest; writes data to JSON
def fanduel_data(file, nf_data=None):

    # Read data from Fanduel file
    with open(file) as f:
        reader = csv.DictReader(f)
        fd_data = [ row for row in reader ]

    # Normalize player metadata
    for player in fd_data:
        player['uid'] = player['First Name'][0:1].lower() + \
        player['Last Name'][0:3].lower() + \
        player['Last Name'][len(player['Last Name'])-1: \
        len(player['Last Name'])] + str(player['Salary'])

    # Tie Fanduel data into NumbersFire data
    for player in nf_data:
        count = 0
        for i in fd_data:
            if player['uid'] == i['uid']:
                player['position'] = i['Position']
                count += 1
        if count == 0:
            print player['slug'] + " not found"
        if count > 1:
            print "More than 1 player found for " + player['uid']

    # Write data to JSON to allow manual editting
    with open('data/output/players.json', 'w') as f:
        json.dump(nf_data, f, indent=2)

################################################################################
""" Create lineups """ #########################################################
################################################################################

def create_position_lists(players_data, dpp_floor=300, point_floor = 270, exclude=[]):

    print "Total players: ", len(players_data)

    positions = { 'PG': [], 'SG': [], 'SF': [], 'PF': [], 'C': [] }

    removed_count = 0
    for player in players_data:
        if player['projection'] == 0 or player['slug'] in exclude or \
        player['salary']/player['projection'] > dpp_floor:
            removed_count += 1
            print player['slug'], "removed! $", \
            player['salary'], "-", player['projection']
        else:
            try:
                if (player['position'] == 'PG'):
                    positions['PG'].append(player)
                elif (player['position'] == 'SG'):
                    positions['SG'].append(player)
                elif (player['position'] == 'SF'):
                    positions['SF'].append(player)
                elif (player['position'] == 'PF'):
                    positions['PF'].append(player)
                elif (player['position'] == 'C'):
                    positions['C'].append(player)
            except:
                print "Position Error: ", player["slug"]
                removed_count += 1

    # Print stats
    print "----------------------------"
    print "Now there are", len(players_data) - removed_count, "players."
    print "----------------------------"
    print len(positions['PG']), "PGs"
    print len(positions['SG']), "SGs"
    print len(positions['SF']), "SFs"
    print len(positions['PF']), "PFs"
    print len(positions['C']), "Cs"

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
        str(i["projection"]) + "\t" + \
        str(i["salary"]) + "\t" + \
        i["slug"]

    # Create combinations
    combos = combinations(trimmed_pos_list, players_per_pos)
    return [ combo for combo in combos ]

def construct_lineups(positions, limit, selection_feature, point_floor):

    start_constructing_lineups = time.time()

    # Create position combos
    PG = create_position_combos(positions['PG'], selection_feature, limit, 2)
    SG = create_position_combos(positions['SG'], selection_feature, limit, 2)
    SF = create_position_combos(positions['SF'], selection_feature, limit, 2)
    PF = create_position_combos(positions['PF'], selection_feature, limit, 2)
    C = create_position_combos(positions['C'], selection_feature, limit, 1)

    # Create complete lineup combinations
    combos = product(PG, SG, SF, PF, C)
    combos = [list(chain(*combo)) for combo in combos]

    print "Possible Lineups: ", len(combos)

    end_constructing_lineups = time.time()

    print "Constructed lineups in: ", \
        str(time_delta(end_constructing_lineups, start_constructing_lineups))

    return combos

# Filter lineups by valid salaries and trimming by highest point totals
def filter_lineups(combos, limit, selection_feature, point_floor):

    start_filter = time.time()

    # Filter lineups by total salary
    combos.sort( \
        key=lambda x: sum(y['salary'] for y in x))

    ind = len(combos) / 2

    combos_filtered = []
    while len(combos) > 0 and len(combos_filtered) == 0:
        if sum(map(itemgetter("salary"), combos[ind])) == 60000:
            while sum(map(itemgetter("salary"), combos[ind])) == 60000:
                ind = ind + 1
            combos_filtered = combos[0:ind-1]
            break
        elif sum(map(itemgetter("salary"), combos[ind])) > 60000:
            ind = ind - ((len(combos) - ind) / 2)
        elif sum(map(itemgetter("salary"), combos[ind])) < 60000:
            ind = ind + ((len(combos) - ind) / 2)

    # Filter lineups by projected points
    combos_filtered.sort( \
        key=lambda x: sum(y['projection'] for y in x), reverse=True)

    try:
        combos_filtered = combos_filtered[0:100]
    except:
        pass

    end_filter = time.time()

    print "Filtered lineups in:", time_delta(start_filter, end_filter)

    return combos_filtered

def valid_lineups(combos, point_floor):

    count = 0
    count_valid = 0
    lineups = []

    for combo in combos:
        count_valid += 1
        lineup = {'lineup': combo,
            'salary': sum(map(itemgetter("salary"), combo)),
            'points': sum(map(itemgetter("projection"), combo)),
            'nerd': sum(float(player['nerd']) for player in combo)}
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
    combos = filter_lineups(combos, limit, selection_feature, point_floor)
    return valid_lineups(combos, point_floor)

################################################################################
""" Print lineups """ ##########################################################
################################################################################

# Print lineups
def lineup_print(lineups, n, sort_feature='points'):
    print "Lineups based on", sort_feature
    lineups = sorted(lineups, key=lambda lineups: lineups[sort_feature], \
    reverse = True)
    count = 1
    for lineup in lineups[0:n]:
        print 'Lineup #', count
        print "Points:", lineup['points'], "   Salary:", lineup['salary'], \
        "   nERD:", lineup['nerd']
        for player in lineup['lineup']:
            print "$" + str(player['salary']), \
            "\t" + str(player['projection']), \
            "\t" + str(player['position']), \
            "\t" + player['slug']
        count += 1
