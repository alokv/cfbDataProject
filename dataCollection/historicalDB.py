#
# filename : historicalDB.py
# author   : Alok Vasudev
# date     : 10/21/2012
#
# scrape a historical college football database [1]
# and aggregate it into a JSON that can be used
# for further data analysis and visualization
#
# [1] http://www.jhowell.net/cf/scores/ScoresIndex.htm
#

from requests import get
from bs4 import BeautifulSoup
from simplejson import dump
import datetime

# Base URL for scraping
urlbase = 'http://www.jhowell.net/cf/scores/'

# Scrape index to build a dictionary of teams
# program_index = { name1: link1, name2: link2, ... }
program_index = {}

index = get(urlbase + 'byName.htm')
index_soup = BeautifulSoup(index.content)
programs = index_soup.findAll('a')[1:-1]

for program in programs:
    try:
        name = program.contents[0].rsplit(' (', 1)[0]
        link = program['href']
        program_index[name] = link
    except:
        pass # shit gets weird for school names with apostrophes,
             # so ignore those schools for now (eg. St. Mary's)

# Define some functions to parse the scraped data
def getDate(info, year):
    raw_date = info[0].contents[0]
    year = int(year)
    month_day = raw_date.split('/') # [month, day]
    if int(month_day[0]) == 1: year += 1 # change year for bowl games in Jan.
    date = datetime.date(year, int(month_day[0]), int(month_day[1]))

    return date

def getOpponent(info):
    try:
        # be sure to remove '*' indicating conference opponent
        opponent = info[2].contents[0].contents[0].strip('*')
    except:
        # non-IA teams do not have a href to read
        opponent = info[2].contents[0].rstrip(' (non-IA)')

    return opponent

def getScore(info):
    team_score = info[4].contents[0]
    opp_score = info[5].contents[0]

    return int(team_score), int(opp_score)

def getGameList(info, year):
    '''
    Returns a list with the relevant info for a game
    [date (datetime obj.), opponent (unicode str.), score (int. tuple)]
    '''
    date = getDate(info, year)
    opponent = getOpponent(info)
    score = getScore(info)

    return [date, opponent, score]

# Create dictionary to hold historical schedules of each program
# Note: this dictionary will contain the COMPLETE list of programs
#       which we will later filter down to only the relevant teams
# db = { team1: { 2012: [...], 2011: [...]}, team2: { ... } }
db = dict.fromkeys(program_index)

cnt = 0.
for team in db.iterkeys():
    print 'Scraping data for ' + team,
    print '(%g percent complete)' % (100*cnt/len(db))
    team_url = urlbase + program_index[team]
    team_page = get(team_url)
    team_soup = BeautifulSoup(team_page.content)

    # Years to scrape
    years = range(1992, 2012)

    # Iterate through seasons
    seasons_dict = {}
    seasons = team_soup.findAll('table')
    for season in seasons[1:]:
        game_data = season.findAll('tr')
        year = game_data[0].find('a').contents[0][0:4]
        # Only look at desired seasons
        if int(year) in years:
            # Get game data
            games = []
            for game in game_data[1:-1]:
                info = game.findAll('td')
                games.append(getGameList(info, year))
            seasons_dict[year] = games

    db[team] = seasons_dict
    cnt += 1

# Remove teams without games in the years of interest
# i.e. keys with a value of None
db_temp = {k:v for k,v in db.iteritems() if db[k]}
db = db_temp

# Convert dates of games into week number

# Build up dict of Week 1 Saturday dates for every year
# Assume Texas plays on EVERY opening Saturday
wk1sats = {unicode(year): db[u'Texas'][unicode(year)][0][0] for year in years}

def convertDateToWeek(db):
    for team, data in db.iteritems():
        for year in years:
            wk1sat = wk1sats[unicode(year)]
            try:
                games = db[team][unicode(year)]
                for ig,game in enumerate(games):
                    gamedate = game[0]
                    wknum = int(round((gamedate - wk1sat).days / 7.))
                    db[team][unicode(year)][ig][0] = wknum
            except:
                pass # No games for team in year

    return db

db2 = convertDateToWeek(db)

# Save database into JSON
fname = 'historicalDB.json'
with open(fname, 'w') as fout:
    dump(db2, fout)
