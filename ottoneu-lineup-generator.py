import requests, os, datetime, json
from bs4 import BeautifulSoup
from pprint import pformat
#from collections import Counter
#import pandas as pd

month = datetime.date.today().strftime("%B")
day = datetime.date.today().strftime("%d")
date = month + day

# TODO: make a generic player both inherit from
class Batter:
    def __init__(self):
        self.id = ''
        self.name = ''
        self.team = ''
        self.positions = ''
        self.handedness = ''
        self.cost = ''
        self.link = ''
        self.homeOrAway = ''
        self.league = '' # MLB is empty
        self.opposingPitcher = None

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)


class Pitcher:
    def __init__(self):
        self.id = ''
        self.name = ''
        self.team = ''
        self.handedness = ''
        self.cost = ''
        self.link = ''
        self.homeOrAway = ''
        self.league = '' # MLB is empty
        self.opposingTeam = None

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)


# grab the link to their page
def parseLineupPage():
    # TODO: Make the league and team configurable
    data = requests.get('https://ottoneu.fangraphs.com/1212/setlineups?team=8409')
    soup = BeautifulSoup(data.text, 'lxml')
    positionTable = soup.find('table', {'class': 'lineup-table batter'})
    
    batters = {}
    pitchers = {}
    for tr in positionTable.findAll('tr'):
        if 'player_' in tr.attrs.get('id', ''):
            batter = Batter()

            playerInfo = tr.find('td', {'class': 'player-name'})
            playerLink = playerInfo.findAll('a')[0]
            batter.id  = playerLink.attrs.get('id', '')
            batter.link = 'https://ottoneu.fangraphs.com' + playerLink.attrs.get('href', '')
            batter.name = playerLink.get_text()
            additionalPlayerInfo = playerInfo.find('span', {'class': 'lineup-player-bio'})
            parts = additionalPlayerInfo.find('span', {'class', 'strong tinytext'}).get_text().split('\xa0')

            # If the player is in the minor leagues, it adds a space and the league
            [team, positions, handedness] = parts
            league = ''
            if ' ' in team:
                [team, league] = team.split(' ')
            
            batter.cost = additionalPlayerInfo.find('span', {'class', 'green tinytext strong'}).get_text()
            batter.team = team
            batter.league = league
            batter.positions = positions
            batter.handedness = handedness

            opponentInfo = playerInfo.find('span', {'class': 'lineup-opponent-info'})
            pitcherLink = opponentInfo.find('a')

            if pitcherLink is not None:
                pitcherId  = 'player_' + pitcherLink.attrs.get('href', '').split('/')[3]
                pitcher = None
                if pitcherId not in pitchers:
                    pitcher = Pitcher()
                    pitcher.id = pitcherId
                    pitcher.name = pitcherLink.get_text()
                    pitcher.link = 'https://ottoneu.fangraphs.com' + pitcherLink.attrs.get('href', '')
                    pitcher.handedness = opponentInfo.find('span', {'class': 'tinytext'}).get_text()

                    # TODO: grab the league of the pitcher
                    opponentTeam = opponentInfo.find('span', {'class': 'lineup-game-info'}).get_text().split(' ')[0]
                    if opponentTeam.startswith('@'):
                        pitcher.team = opponentTeam[1:]
                        pitcher.homeOrAway = 'home'
                        batter.homeOrAway = 'away'
                    else:
                        pitcher.team = opponentTeam
                        batter.homeOrAway = 'home'
                        pitcher.homeOrAway = 'away'
                    
                    pitcher.opposingTeam = batter.team
                    batter.opposingPitcher = pitcher
                    pitchers[pitcherId] = pitcher
                else:
                    pitcher = pitchers[pitcherId]
                    batter.opposingPitcher = pitcher
            
            batters[batter.id] = batter

    for batter in batters:
        print(batters[batter])



# Go to the hitter pages and find the fangraphs player page (https://www.fangraphs.com/players/isaac-paredes/20036/splits?position=3B&season=0)
# Go to splits and grab both the vs. L and vs. R. For now, just worry about using the opposing pitcher's hand.
# Go to the pitcher pages and find the fangraphs player page (https://www.fangraphs.com/players/joe-musgrove/12970/splits?position=P&season=0)
# Go to splits and grab both the vs. L and vs. R. For now, just worry about using the opposing hitter's hand.
# Calculate the expected value by averaging pitcher and hitter


parseLineupPage()