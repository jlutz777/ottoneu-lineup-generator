import argparse
import math
import requests, os, datetime, json
import urllib.parse

from bs4 import BeautifulSoup
from pprint import pformat


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
        self.so = 0

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)

class OttoneuBatterPredictionData:
    def __init__(self):
        self.ab = 0.0
        self.h = 0.0
        self.x2b = 0.0
        self.x3b = 0.0
        self.hr = 0.0
        self.bb = 0.0
        self.hbp = 0.0
        self.sb = 0.0
        self.cs = 0.0
        self.totalPoints = 0.0

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)

class PitcherData:
    def __init__(self):
        self.ab = 0
        self.tbf = 0
        self.h = 0
        self.x2b = 0
        self.x3b = 0
        self.hr = 0
        self.r = 0
        self.er = 0
        self.bb = 0
        self.hbp = 0
        self.so = 0

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
        self.opposingPitcher: Pitcher = None
        self.bvsL: BatterData = None
        self.bvsR: BatterData = None
        self.predictionData: OttoneuBatterPredictionData = None

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
        self.pvsL: PitcherData = None
        self.pvsR: PitcherData = None

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)


# TODO: Get all of the pitchers eventually as well
def parseLineupPage(leagueNumber: str, teamNumber: str, lineupDate: str):
    data = requests.get(f'https://ottoneu.fangraphs.com/{leagueNumber}/setlineups?team={teamNumber}&date={lineupDate}')
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
    batterData.so = int(row["SO"])

    return batterData

def buildPitcherDataObj(row):
    pitcherData = PitcherData()

    # AB does not exist, so generate from H/AVG
    # Note, this is an estimate and could be off by a bit
    pitcherData.ab = math.ceil(int(row["H"])/float(row["AVG"]))

    pitcherData.tbf = int(row["TBF"])
    pitcherData.h = int(row["H"])
    pitcherData.x2b = int(row["2B"])
    pitcherData.x3b = int(row["3B"])
    pitcherData.hr = int(row["HR"])
    pitcherData.r = int(row["R"])
    pitcherData.er = int(row["ER"])
    pitcherData.bb = int(row["BB"])
    pitcherData.hbp = int(row["HBP"])
    pitcherData.so = int(row["SO"])

    return pitcherData

def getFangraphsPlayerPageFromOttoneuPlayerPage(ottoPage):
    ottoneuPlayerPage = requests.get(ottoPage)
    soup = BeautifulSoup(ottoneuPlayerPage.text, 'lxml')
    
    link = soup.find_all(lambda tag: tag.name == "a" and 'FanGraphs Player Page' == tag.text)
    return link[0].attrs.get('href', '')


def getBatterData(batters):
    for batterId in batters:
        batter = batters[batterId]
        
        if batter.fangraphsPlayerPage == '':
            batter.fangraphsPlayerPage = getFangraphsPlayerPageFromOttoneuPlayerPage(batter.ottoneuPlayerPage)
        
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

        #print(batter)

def getPitcherData(pitchers):
    for pitcherId in pitchers:
        pitcher = pitchers[pitcherId]
        
        if pitcher.fangraphsPlayerPage == '':
            pitcher.fangraphsPlayerPage = getFangraphsPlayerPageFromOttoneuPlayerPage(pitcher.ottoneuPlayerPage)
        
        pitcher.fangraphsSplitsLastYearAPIPage = generateFangraphsSplitsAPIUrl(pitcher.fangraphsPlayerPage, lastYear)

        r = requests.get(pitcher.fangraphsSplitsLastYearAPIPage)
        splitData = r.json()
        
        # If players don't have splits on a certain year, just skip
        if splitData is not None:
            for row in splitData:
                if row["Split"] == "vs L":
                    pitcher.pvsL = buildPitcherDataObj(row)
                elif row["Split"] == "vs R":
                    pitcher.pvsR = buildPitcherDataObj(row)
        else:
            pitcher.bvsR = PitcherData()
            pitcher.bvsL = PitcherData()

        #print(pitcher)

def getAverageForData(batterData, pitcherData, averageABs, stat):
    if getattr(batterData, "ab") != 0 and getattr(pitcherData, "ab") != 0:
        return averageABs*((getattr(batterData, stat)/getattr(batterData, "ab"))+(getattr(pitcherData, stat)/getattr(pitcherData, "ab")))/2.0
    elif getattr(batterData, "ab") != 0:
        return averageABs*getattr(batterData, stat)/getattr(batterData, "ab")
    elif getattr(pitcherData, "ab") != 0:
        return averageABs*getattr(pitcherData, stat)/getattr(pitcherData, "ab")
    else:
        # TODO: what do I do here if there's no data?
        return 0.0

def calculateBatterPredictionPoints(batterData: BatterData, pitcherData: PitcherData):
    calculatedPredictionData: OttoneuBatterPredictionData = OttoneuBatterPredictionData()

    # TODO: How do we calculate average abs?
    if batterData.ab == 0 and pitcherData.ab == 0:
        calculatedPredictionData.ab = 0.0
    else:
        calculatedPredictionData.ab = 4.0
    
    calculatedPredictionData.h = getAverageForData(batterData, pitcherData, calculatedPredictionData.ab, "h")
    calculatedPredictionData.x2b = getAverageForData(batterData, pitcherData, calculatedPredictionData.ab, "x2b")
    calculatedPredictionData.x3b = getAverageForData(batterData, pitcherData, calculatedPredictionData.ab, "x3b")
    calculatedPredictionData.hr = getAverageForData(batterData, pitcherData, calculatedPredictionData.ab, "hr")
    calculatedPredictionData.bb = getAverageForData(batterData, pitcherData, calculatedPredictionData.ab, "bb")
    calculatedPredictionData.hbp = getAverageForData(batterData, pitcherData, calculatedPredictionData.ab, "hbp")
    # SB and CS are only available for the hitter
    calculatedPredictionData.sb = getAverageForData(batterData, PitcherData(), calculatedPredictionData.ab, "sb")
    calculatedPredictionData.cs = getAverageForData(batterData, PitcherData(), calculatedPredictionData.ab, "cs")

    # Pull this from the ottoneu page at some point
    calculatedPredictionData.totalPoints = -1.0*calculatedPredictionData.ab
    calculatedPredictionData.totalPoints += 5.6*calculatedPredictionData.h
    calculatedPredictionData.totalPoints += 2.9*calculatedPredictionData.x2b
    calculatedPredictionData.totalPoints += 5.7*calculatedPredictionData.x3b
    calculatedPredictionData.totalPoints += 9.4*calculatedPredictionData.hr
    calculatedPredictionData.totalPoints += 3.0*calculatedPredictionData.bb
    calculatedPredictionData.totalPoints += 3.0*calculatedPredictionData.hbp
    calculatedPredictionData.totalPoints += 1.9*calculatedPredictionData.sb
    calculatedPredictionData.totalPoints += -2.8*calculatedPredictionData.cs

    return calculatedPredictionData

def createBatterPredictions(batter):
    for batterId in batters:
        batter: Batter = batters[batterId]

        bData: BatterData = None
        pData: PitcherData = None

        #TODO: Determine if a batter's team is not playing or if the batter is not in the lineup
        if batter.opposingPitcher is  None:
            # No pitcher data yet, so just use the batter
            # TODO: Get non-split data for this use case
            bData = BatterData()
            pData = PitcherData()
        else:
            if batter.opposingPitcher.handedness == 'R':
                if batter.handedness == 'R':
                    # pitcher v. R, batter v. R
                    bData = batter.bvsR
                    pData = batter.opposingPitcher.pvsR
                else:   # L or S
                    # pitcher v. L, batter v. R
                    bData = batter.bvsR
                    pData = batter.opposingPitcher.pvsL
            else:   # pitcher L
                if batter.handedness == 'L':
                    # pitcher v. L, batter v. L
                    bData = batter.bvsL
                    pData = batter.opposingPitcher.pvsL
                else:   # R or S
                    # pitcher v. R, batter v. L
                    bData = batter.bvsL
                    pData = batter.opposingPitcher.pvsR

        batter.predictionData = calculateBatterPredictionPoints(bData, pData)

def printBatterPredictions(batters):
    for batterId in batters:
        batter: Batter = batters[batterId]
        print(f"{batter.name}: {batter.predictionData.totalPoints}")

def getArgs():
    parser = argparse.ArgumentParser(description='Generate an ottoneu lineup')
    parser.add_argument('--league', dest='league', type=str, nargs='?', default='1212',
                        help='the league number in Ottoneu')
    parser.add_argument('--team', dest='team', type=str, nargs='?', default='8409',
                        help='the team number in Ottoneu')
    parser.add_argument('--date', dest='date', type=str, nargs='?', default=f'{thisYear}-{thisMonth}-{thisDay}',
                        help='the day for the lineup')
    return parser.parse_args()


if __name__ == "__main__":
    args = getArgs()
    leagueNumber = args.league
    teamNumber = args.team
    lineupDate = args.date
    (batters, pitchers) = parseLineupPage(leagueNumber, teamNumber, lineupDate)
    getBatterData(batters)
    getPitcherData(pitchers)
    createBatterPredictions(batters)
    printBatterPredictions(batters)
