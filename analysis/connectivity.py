import numpy as np
import networkx as nx
from simplejson import load

# Load database from JSON
fname = '../dataCollection/historicalDB.json'
with open(fname) as fin:
    db = load(fin)

def getConnWk(year):
    # Generate list of teams for indexing adjacency matrix ...
    teams = [str(team) for team in sorted(db.iterkeys())
             if unicode(year) in db[team]]

    # Initialize list of graphs
    Gs = []

    # Populate list of graphs with graphs corresponding to the progression
    # through the season week-by-week
    G = nx.Graph()
    for wk in range(15):
        for i,team in enumerate(teams):
            games = db[team][unicode(year)]
            for game in games:
                if game[0] == wk:
                    opp = game[1]
                    G.add_edge(str(team), str(opp))
        Gs.append(G.copy())

    # Check for full connectivity
    for ig,G in enumerate(Gs):
        if nx.is_connected(G):
            conn_wk = ig
            break

    return conn_wk + 1

# Determine week that the CFB graph is fully connected over time
years = range(1992, 2012)
conn_wks = np.array([getConnWk(year) for year in years])

# Plot result
steelblue = (70./255., 130./255., 180./255.)
grey = (95./255., 95./255., 95./255.)
def formatting():
    from pylab import rc
    rc('font', **{'family': 'serif', 'serif': ['Palatino']})
    rc('xtick', labelsize=18, color=grey)
    rc('ytick', labelsize=18, color=grey)
    rc('axes', linewidth=1, facecolor='white', edgecolor=grey, axisbelow=True,
               titlesize=18)

import pylab as pl
formatting()
pl.figure(figsize=(9,6))
pl.plot(years, conn_wks, lw=6, color=steelblue,
        marker='o', markersize=10, mec='white', mew=3)
pl.yticks(range(1,7))
pl.xticks(years, rotation=45)

pl.title('Which week is the CFB graph connected?', color=grey)
pl.ylim(1,6)
pl.xlim(1991, 2012)
pl.savefig('connectivity.png')
