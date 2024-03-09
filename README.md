# ottoneu-lineup-generator
This is a tool for ottoneu fantasy baseball to generate the best lineup each day for your team.

# V1
Scrape data from fangraphs for each hitter and pitcher on your team
Get the career splits - against lefties/righties
Get the daily lineups from ottoneu
Get the probable starters from ottoneu
Calculate hitters by taking the average of the hitter and the opposing pitcher for as long as the pitcher will be 

# V2
Use projections?
Move on to pitchers


# Future versions
Factor in home/away splits
Support other league types and flexible point values



Start with hard-coded values for hitting and pitching


Go to team lineup page:
https://ottoneu.fangraphs.com/1212/setlineups?team=8409

Find all position players:
grab the link to their page
grab their bat - R/L/S
grab their positions - (after team name, separated by slashes)
in the next field, see the team and pitcher they are against, the pitcher has a L or R next to their name (and a link to their page)
Go to the hitter pages and find the fangraphs player page (https://www.fangraphs.com/players/isaac-paredes/20036/splits?position=3B&season=0)
Go to splits and grab both the vs. L and vs. R. For now, just worry about using the opposing pitcher's hand.
Go to the pitcher pages and find the fangraphs player page (https://www.fangraphs.com/players/joe-musgrove/12970/splits?position=P&season=0)
Go to splits and grab both the vs. L and vs. R. For now, just worry about using the opposing hitter's hand.
Calculate the expected value by averaging pitcher and hitter
