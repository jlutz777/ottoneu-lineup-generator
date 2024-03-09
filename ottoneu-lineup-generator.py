import requests, os, datetime, json
from bs4 import BeautifulSoup
from pprint import pformat
import urllib.parse

now = datetime.datetime.now()
thisMonth = now.month
thisYear = now.year
thisDay = now.day
lastYear = thisYear-1

class BatterData:
    def __init__(self):
        self.ab = 0
        self.h = 0
        self.x2b = 0
        self.x3b = 0
        self.hr = 0
        self.bb = 0
        self.hbp = 0
        self.sb = 0
        self.cs = 0

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)

# TODO: make a generic player both inherit from
class Batter:
    def __init__(self):
        self.id = ''
        self.name = ''
        self.team = ''
        self.positions = ''
        self.handedness = ''
        self.cost = ''
        self.ottoneuPlayerPage = ''
        self.fangraphsPlayerPage  = ''
        self.fangraphsSplitsLastYearAPIPage = ''
        self.homeOrAway = ''
        self.league = '' # MLB is empty
        self.opposingPitcher = None
        self.bvsL = None
        self.bvsR = None

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)


class Pitcher:
    def __init__(self):
        self.id = ''
        self.name = ''
        self.team = ''
        self.handedness = ''
        self.cost = ''
        self.ottoneuPlayerPage = ''
        self.fangraphsPlayerPage  = ''
        self.homeOrAway = ''
        self.league = '' # MLB is empty
        self.opposingTeam = None
        self.bvsL = None
        self.bvsR = None

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)


# grab the link to their page
# TODO: Get all of the pitchers eventually as well
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
            batter.ottoneuPlayerPage = 'https://ottoneu.fangraphs.com' + playerLink.attrs.get('href', '')
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
                    pitcher.ottoneuPlayerPage = 'https://ottoneu.fangraphs.com' + pitcherLink.attrs.get('href', '')
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

    return (batters, pitchers)

def generateFangraphsSplitsAPIUrl(fangraphsPlayerPage, year):
    r = requests.get(fangraphsPlayerPage)
        
    parsed_url = urllib.parse.urlparse(r.url)

    # Extract player ID from path components
    player_id = parsed_url.path.split("/")[-2]

    # Build the new URL with API endpoint and parameters
    fangraphsSplitsLastYearAPIPage = f"https://www.fangraphs.com/api/players/splits?playerid={player_id}&split=&season=" + str(year)

    # Add any existing query parameters from original URL
    query_string = parsed_url.query
    if query_string:
        fangraphsSplitsLastYearAPIPage += f"&{query_string}"

    return fangraphsSplitsLastYearAPIPage

def buildBatterDataObj(row):
    batterData = BatterData()

    batterData.ab = int(row["AB"])
    batterData.h = int(row["H"])
    batterData.x2b = int(row["2B"])
    batterData.x3b = int(row["3B"])
    batterData.hr = int(row["HR"])
    batterData.bb = int(row["BB"])
    batterData.hbp = int(row["HBP"])
    batterData.sb = int(row["SB"])
    batterData.cs = int(row["CS"])

    return batterData

def getBatterData(batters):
    for batterId in batters:
        batter = batters[batterId]

        if batter.name != "Termarr Johnson":
            continue
        
        if batter.fangraphsPlayerPage == '':
            ottoneuPlayerPage = requests.get(batter.ottoneuPlayerPage)
            soup = BeautifulSoup(ottoneuPlayerPage.text, 'lxml')
            
            link = soup.find_all(lambda tag: tag.name == "a" and 'FanGraphs Player Page' == tag.text)
            batter.fangraphsPlayerPage = link[0].attrs.get('href', '')
        
        batter.fangraphsSplitsLastYearAPIPage = generateFangraphsSplitsAPIUrl(batter.fangraphsPlayerPage, lastYear)
        
        #TODO: Use the splits tool eventually - it does multiple splits at once
        r = requests.get(batter.fangraphsSplitsLastYearAPIPage)
        splitData = r.json()
        
        # If players don't have splits on a certain year, just skip
        if splitData is not None:
            for row in splitData:
                if row["Split"] == "vs L":
                    batter.bvsL = buildBatterDataObj(row)
                elif row["Split"] == "vs R":
                    batter.bvsR = buildBatterDataObj(row)
        else:
            batter.bvsR = BatterData()
            batter.bvsL = BatterData()

        print(batter)



# Go to the pitcher pages and find the fangraphs player page (https://www.fangraphs.com/players/joe-musgrove/12970/splits?position=P&season=0)
# Go to splits and grab both the vs. L and vs. R. For now, just worry about using the opposing hitter's hand.
# Calculate the expected value by averaging pitcher and hitter


(batters, pitchers) = parseLineupPage()
getBatterData(batters)