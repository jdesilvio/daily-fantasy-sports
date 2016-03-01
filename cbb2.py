### MAIN #######################################################################

from lib.cbb import *

if __name__ == "__main__":

    #fanduel_data()

    with open('data/output/playersCBB.json') as f:
        data = json.load(f)

    lineups = lines(data, \
    dpp_floor=350, \
    limit = 19, \
    selection_feature='ppd', \
    point_floor = 220, \
    exclude=[ \
    'Jameel-McKay', 'Ricardo-Gathers', \
    'Dorian-Finney-Smith', 'Jonathan-Holton', \
    'Joel-Berry II', 'Justin-Jackson', \
    'Shembari-Phillips', 'Jabril-Durham', \
    'Allerik-Freeman', '', \
    '', '', \
    '', '', \
    '', '', \
    'Taurean-Waller-Prince', 'Barry-Brown', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    '', '', \
    ])

    lineup_print(lineups, sort_feature='points', n=4)
