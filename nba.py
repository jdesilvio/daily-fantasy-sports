if __name__ == "__main__":

    from lib.dfs import *

    url = 'https://www.numberfire.com/nba/fantasy/fantasy-basketball-projections'

    #data = get_nf_data(url)
    #nf_data = normalize_nf_data(data)

    #file = "data/input/fd.csv"
    #fanduel_data(file, nf_data)

    with open('data/output/players.json') as f:
        data = json.load(f)

    lineups = lines(data, \
    dpp_floor=300, \
    limit = 8, \
    selection_feature='ppd', \
    point_floor = 270, \
    exclude=[ \
    '', \
    '', \
    '', \
    '', \
    '', \
    '', \
    '', \
    '', \
    '', \
    '', \
    ])

    lineup_print(lineups, sort_feature='points', n=1)
