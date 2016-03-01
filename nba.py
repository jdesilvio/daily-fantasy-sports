if __name__ == "__main__":

    from lib.dfs import *

    url = 'https://www.numberfire.com/nba/fantasy/fantasy-basketball-projections'

    data = get_nf_data(url)
    nf_data = normalize_nf_data(data)

    file = "data/input/fd.csv"
    fanduel_data(file, nf_data)

    with open('data/output/players.json') as f:
        data = json.load(f)

    lineups = lines(data, \
    dpp_floor=300, \
    limit = 10, \
    selection_feature='ppd', \
    point_floor = 280, \
    exclude=[ \
    'shelvin-mack', 'shane-larkin', \
    'marco-belinelli', 'oj-mayo', \
    'dion-waiters', 'bojan-bogdanovic', \
    'vince-carter', 'omri-casspi', \
    'josh-smith', 'emmanuel-mudiay', \
    'timofey-mozgov', 'steven-adams', \
    'miles-plumlee', 'greg-monroe', \
    't-j-mcconnell', 'wayne-ellington', \
    'robert-covington', 'corey-brewer', \
    'willie-cauley-stein', 'tyler-zeller', \
    'marcin-gortat', 'nikola-jokic', \
    'jordan-hill', 'enes-kanter', \
    'iman-shumpert', 'paul-george', \
    'jeff-green', 'richaun-holmes', \
    'markieff-morris', 'myles-turner', \
    'isaiah-canaan', 'ben-mclemore', \
    'wesley-johnson', '', \
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
