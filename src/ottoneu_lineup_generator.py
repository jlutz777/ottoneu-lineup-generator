import argparse
import math
import requests, datetime
import urllib.parse

from dataobjects.general import PredictionType, ProjectionType
from dataobjects.batter import Batter, BatterData, OttoneuBatterPredictionData
from dataobjects.pitcher import Pitcher, PitcherData

from bs4 import BeautifulSoup

now = datetime.datetime.now()
thisMonth = now.month
thisYear = now.year
thisDay = now.day
lastYear = thisYear-1

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

def generateFangraphsAPIUrl(fangraphsPlayerPage, apiTemplate, year=''):
    r = requests.get(fangraphsPlayerPage)
        
    parsed_url = urllib.parse.urlparse(r.url)

    # Extract player ID from path components
    player_id = parsed_url.path.split("/")[-2]

    # Build the new URL with API endpoint and parameters
    fangraphsSplitsLastYearAPIPage = apiTemplate.format(player_id=player_id, year=year)

    # Add any existing query parameters from original URL
    query_string = parsed_url.query
    if query_string:
        fangraphsSplitsLastYearAPIPage += f"&{query_string}"
    
    return fangraphsSplitsLastYearAPIPage

def generateFangraphsSplitsAPIUrl(fangraphsPlayerPage, year):
    apiTemplate = "https://www.fangraphs.com/api/players/splits?playerid={player_id}&split=&season={year}"
    return generateFangraphsAPIUrl(fangraphsPlayerPage, apiTemplate, year)

def generateFangraphsStatsAPIUrl(fangraphsPlayerPage):
    apiTemplate = "https://www.fangraphs.com/api/players/stats?playerid={player_id}"
    return generateFangraphsAPIUrl(fangraphsPlayerPage, apiTemplate)


def buildBatterDataObj(row, predictionType: PredictionType, projectionType: ProjectionType):
    batterData = BatterData(predictionType, projectionType)

    batterData.g = int(row["G"])
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

def buildPitcherDataObj(row, predictionType: PredictionType, projectionType: ProjectionType):
    pitcherData = PitcherData(predictionType, projectionType)

    # AB does not exist, so generate from H/AVG
    # Note, this is an estimate and could be off by a bit
    pitcherData.ab = math.ceil(int(row["H"])/float(row["AVG"]))

    pitcherData.tbf = int(row["TBF"])
    pitcherData.h = int(row["H"])
    pitcherData.x2b = int(row.get("2B", "0"))
    pitcherData.x3b = int(row.get("3B", "0"))
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


def getBatterData(batters, predictionYear):
    for batterId in batters:
        batter: Batter = batters[batterId]
        
        if batter.fangraphsPlayerPage == '':
            batter.fangraphsPlayerPage = getFangraphsPlayerPageFromOttoneuPlayerPage(batter.ottoneuPlayerPage)
        
        batter.fangraphsSplitsYearAPIPage = generateFangraphsSplitsAPIUrl(batter.fangraphsPlayerPage, predictionYear)

        # TODO: potentially use other data in the player call
        batter.fangraphsStatsYearAPIPage = generateFangraphsStatsAPIUrl(batter.fangraphsPlayerPage)
        r = requests.get(batter.fangraphsStatsYearAPIPage)
        statsData = r.json()

        for dataPoint in statsData["data"]:
            # Type 0 seems to be regular season
            if dataPoint.get("aseason", "") == predictionYear and dataPoint.get("type", -1) == 0 and dataPoint.get("AbbLevel", "") == "MLB":
                batter.bOverall = buildBatterDataObj(dataPoint, PredictionType.MajorsOverall, ProjectionType.Empty)
        
        r = requests.get(batter.fangraphsSplitsYearAPIPage)
        splitData = r.json()
        
        # If players don't have splits on a certain year, just skip
        if splitData is not None:
            for row in splitData:
                if row["Split"] == "vs L":
                    batter.bvsL = buildBatterDataObj(row, PredictionType.MajorsSplit, ProjectionType.Empty)
                elif row["Split"] == "vs R":
                    batter.bvsR = buildBatterDataObj(row, PredictionType.MajorsSplit, ProjectionType.Empty)
        
        if batter.bvsR is None:
            batter.bvsR = batter.bOverall
        if batter.bvsL is None:
            batter.bvsL = batter.bOverall

        #break # temp so we don't go through every batter

def getPitcherData(pitchers: dict[str, Pitcher], predictionYear: str):
    for pitcherId in pitchers:
        pitcher: Pitcher = pitchers[pitcherId]
        
        if pitcher.fangraphsPlayerPage == '':
            pitcher.fangraphsPlayerPage = getFangraphsPlayerPageFromOttoneuPlayerPage(pitcher.ottoneuPlayerPage)
        
        pitcher.fangraphsSplitsYearAPIPage = generateFangraphsSplitsAPIUrl(pitcher.fangraphsPlayerPage, predictionYear)

        # TODO: potentially use other data in the player call
        pitcher.fangraphsStatsYearAPIPage = generateFangraphsStatsAPIUrl(pitcher.fangraphsPlayerPage)
        r = requests.get(pitcher.fangraphsStatsYearAPIPage)
        statsData = r.json()

        for dataPoint in statsData["data"]:
            # Type 0 seems to be regular season
            if dataPoint.get("aseason", "") == predictionYear and dataPoint.get("type", -1) == 0 and dataPoint.get("AbbLevel", "") == "MLB":
                pitcher.pOverall = buildPitcherDataObj(dataPoint, PredictionType.MajorsOverall, ProjectionType.Empty)
        
        if pitcher.pOverall is None:
            pitcher.pOverall = PitcherData(PredictionType.Empty, ProjectionType.Empty)

        r = requests.get(pitcher.fangraphsSplitsYearAPIPage)
        splitData = r.json()
        
        # If players don't have splits on a certain year, just skip
        if splitData is not None:
            for row in splitData:
                if row["Split"] == "vs L":
                    pitcher.pvsL = buildPitcherDataObj(row, PredictionType.MajorsSplit, ProjectionType.Empty)
                elif row["Split"] == "vs R":
                    pitcher.pvsR = buildPitcherDataObj(row, PredictionType.MajorsSplit, ProjectionType.Empty)

        if pitcher.pvsR is None:
            pitcher.pvsR = pitcher.pOverall
        if pitcher.pvsL is None:
            pitcher.pvsL = pitcher.pOverall
        
        # Overall data doesn't have 2B and 3B, so hack it in
        pitcher.pOverall.x2b = pitcher.pvsL.x2b + pitcher.pvsR.x2b
        pitcher.pOverall.x3b = pitcher.pvsL.x3b + pitcher.pvsR.x3b

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

def calculateBatterPredictionPoints(batterData: BatterData, pitcherData: PitcherData, overallBatterData: BatterData):
    calculatedPredictionData: OttoneuBatterPredictionData = OttoneuBatterPredictionData()

    #TODO: If there are no abs, then use either minor league stats or projections
    if batterData.ab == 0 and pitcherData.ab == 0:
        calculatedPredictionData.ab = 0.0
    else:
        calculatedPredictionData.ab = overallBatterData.ab/overallBatterData.g
    
    calculatedPredictionData.batterPredictionType = batterData.predictionType
    calculatedPredictionData.pitcherPredictionType = pitcherData.predictionType
    
    calculatedPredictionData.h = getAverageForData(batterData, pitcherData, calculatedPredictionData.ab, "h")
    calculatedPredictionData.x2b = getAverageForData(batterData, pitcherData, calculatedPredictionData.ab, "x2b")
    calculatedPredictionData.x3b = getAverageForData(batterData, pitcherData, calculatedPredictionData.ab, "x3b")
    calculatedPredictionData.hr = getAverageForData(batterData, pitcherData, calculatedPredictionData.ab, "hr")
    calculatedPredictionData.bb = getAverageForData(batterData, pitcherData, calculatedPredictionData.ab, "bb")
    calculatedPredictionData.hbp = getAverageForData(batterData, pitcherData, calculatedPredictionData.ab, "hbp")
    # SB and CS are only available for the hitter
    calculatedPredictionData.sb = getAverageForData(batterData, PitcherData(PredictionType.Empty, ProjectionType.Empty), calculatedPredictionData.ab, "sb")
    calculatedPredictionData.cs = getAverageForData(batterData, PitcherData(PredictionType.Empty, ProjectionType.Empty), calculatedPredictionData.ab, "cs")

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

def chooseBatterPrediction(options):
    for option in options:
        if option is not None and getattr(option, "ab") > 0:
            return option
    return BatterData(PredictionType.Empty, ProjectionType.Empty)
    

def createBatterPredictions(batters: dict[str, Batter], preferredPredictionType: PredictionType, predictionYear: str, projectionType: ProjectionType):
    for batterId in batters:
        batter: Batter = batters[batterId]

        print(f'Name: {batter.name}')

        predictionType: PredictionType = PredictionType.Empty

        bData: BatterData = None
        pData: PitcherData = None

        possiblePredictionType = PredictionType.Empty
        if batter.league == "":
            if batter.opposingPitcher is not None:
                possiblePredictionType = PredictionType.MajorsSplit
            else:
                possiblePredictionType = PredictionType.MajorsOverall
        else:
            possiblePredictionType = PredictionType.Projection
        
        if possiblePredictionType <= preferredPredictionType:
            predictionType = possiblePredictionType
        else:
            predictionType = preferredPredictionType
        
        # TODO: Determine if a batter's team is not playing or if the batter is not in the lineup, give them zero
        if predictionType == PredictionType.Projection or predictionType == PredictionType.Minors:
            # TODO: Replace with projection or minor league stats
            bData = BatterData(PredictionType.Empty, ProjectionType.Empty)
            pData = PitcherData(PredictionType.Empty, ProjectionType.Empty)
        elif predictionType == PredictionType.MajorsOverall:
            bData = batter.bOverall
            if batter.opposingPitcher is None:
                pData = PitcherData(PredictionType.Empty, ProjectionType.Empty)
            else:
                pData = batter.opposingPitcher.pOverall
        elif predictionType == PredictionType.MajorsSplit:
            if batter.opposingPitcher.handedness == 'R':
                if batter.handedness == 'R':
                    # pitcher v. R, batter v. R
                    bData = chooseBatterPrediction([batter.bvsR, batter.bOverall]) # add projection and minors when I have them
                    pData = batter.opposingPitcher.pvsR
                else:   # L or S
                    # pitcher v. L, batter v. R
                    bData = chooseBatterPrediction([batter.bvsR, batter.bOverall]) # add projection and minors when I have them
                    pData = batter.opposingPitcher.pvsL
            else:   # pitcher L
                if batter.handedness == 'L':
                    # pitcher v. L, batter v. L
                    bData = chooseBatterPrediction([batter.bvsL, batter.bOverall]) # add projection and minors when I have them
                    pData = batter.opposingPitcher.pvsL
                else:   # R or S
                    # pitcher v. R, batter v. L
                    bData = chooseBatterPrediction([batter.bvsL, batter.bOverall]) # add projection and minors when I have them
                    pData = batter.opposingPitcher.pvsR
        else:
            raise Exception("Invalid prediction type?")
        
        batter.predictionData = calculateBatterPredictionPoints(bData, pData, batter.bOverall)

        #break # temp so we don't go through every batter

def printBatterPredictions(batters):
    for batterId in batters:
        batter: Batter = batters[batterId]
        print(f"{batter.name}: {batter.predictionData.totalPoints}, {batter.predictionData.batterPredictionType}, {batter.predictionData.pitcherPredictionType}")

def getArgs():
    parser = argparse.ArgumentParser(description='Generate an ottoneu lineup')
    parser.add_argument('--league', dest='league', type=str, nargs='?', default='1212',
                        help='the league number in Ottoneu')
    parser.add_argument('--team', dest='team', type=str, nargs='?', default='8409',
                        help='the team number in Ottoneu')
    parser.add_argument('--date', dest='date', type=str, nargs='?', default=f'{thisYear}-{thisMonth}-{thisDay}',
                        help='the day for the lineup')
    parser.add_argument('--preferred-prediction-type', dest='preferredPredictionType', type=str, nargs='?', default='MajorsSplit',
                        help='the type of prediction to use if available')
    parser.add_argument('--prediction-year', dest='predictionYear', type=str, nargs='?', default='lastYear',
                        help='the year to use if available')
    parser.add_argument('--projection-type', dest='projectionType', type=str, nargs='?', default='Zips',
                        help='if a projection is used, use this specific type')
    args = parser.parse_args()

    # Allow special strings for lastYear and thisYear
    if args.predictionYear == "lastYear":
        args.predictionYear = lastYear
    elif args.predictionYear == "thisYear":
        args.predictionYear = thisYear
    else:
        args.predictionYear = int(args.predictionYear)
    
    # Parse the prediction type and projection type
    args.preferredPredictionType = PredictionType[args.preferredPredictionType]
    args.projectionType = ProjectionType[args.projectionType]

    return args


if __name__ == "__main__":
    args = getArgs()
    (batters, pitchers) = parseLineupPage(args.league, args.team, args.date)
    getBatterData(batters, args.predictionYear)
    getPitcherData(pitchers, args.predictionYear)
    createBatterPredictions(batters, args.preferredPredictionType, args.predictionYear, args.projectionType)
    printBatterPredictions(batters)
