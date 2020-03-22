# team.py
from nhl import api

class Team:

    def __init__(self, team_id='10', season=None):
        """
        Class providing an object-oriented approach to working with nhl team data.

        Parameters
        ----------
        team_id : str or int
            If int, must be the NHL API's numeric code for the desired team.

            If str, can either be a string of the numeric code, or the team's full
            name, or the team's three letter abbreviation; case insensitive. See
            Additional Information for a complete list of active teams and codes.

        season : str (default : None)
            The season to pull the team's roster from; if None, defaults to the
            current season.

        Attributes
        ----------
        self.roster : list of dicts
            Each dictionary maps a player's name to a tuple (id, number, position).

        self.offense : list of dicts
            Same format as self.roster, but contains exclusively offensemen

        self.defense : list of dicts
            Same format as self.roster, but contains exclusively defensemen

        self.goalies : list of dicts
            Same format as self.roster, but contains exclusively goalies


        Additional Information
        ----------------------
        The current nhl teams' names, abbreviations, and codes are as follows:
                    +-------------------------+------+-------+
                    |          NAME           | t_id | ABBRV |
                    +-------------------------+------+-------+
                    |   'New Jersey Devils'   |   1  |  NJD  |
                    |   'New York Islanders'  |   2  |  NYI  |
                    |   'New York Rangers'    |   3  |  NYR  |
                    |  'Philadelphia Flyers'  |   4  |  PHI  |
                    |  'Pittsburgh Penguins'  |   5  |  PIT  |
                    |     'Boston Bruins'     |   6  |  BOS  |
                    |     'Buffalo Sabres'    |   7  |  BUF  |
                    |   'Montreal Canadiens'  |   8  |  MTL  |
                    |    'Ottawa Senators'    |   9  |  OTT  |
                    |  'Toronto Maple Leafs'  |  10  |  TOR  |
                    |  'Carolina Hurricanes'  |  12  |  CAR  |
                    |   'Florida Panthers'    |  13  |  FLA  |
                    |  'Tampa Bay Lightning'  |  14  |  TBL  |
                    |  'Washington Capitals'  |  15  |  WSH  |
                    |  'Chicago Blackhawks'   |  16  |  CHI  |
                    |   'Detroit Red Wings'   |  17  |  DET  |
                    |  'Nashville Predators'  |  18  |  NSH  |
                    |    'St. Louis Blues'    |  19  |  STL  |
                    |     'Calgary Flames'    |  20  |  CGY  |
                    |   'Colorado Avalanche'  |  21  |  COL  |
                    |    'Edmonton Oilers'    |  22  |  EDM  |
                    |   'Vancouver Canucks'   |  23  |  VAN  |
                    |     'Anaheim Ducks'     |  24  |  ANA  |
                    |     'Dallas Stars'      |  25  |  DAL  |
                    |   'Los Angeles Kings'   |  26  |  LAK  |
                    |    'San Jose Sharks'    |  28  |  SJS  |
                    | 'Columbus Blue Jackets' |  29  |  CBJ  |
                    |    'Minnesota Wild'     |  30  |  MIN  |
                    |     'Winnipeg Jets'     |  52  |  WPG  |
                    |    'Arizona Coyotes'    |  53  |  ARI  |
                    | 'Vegas Golden Knights'  |  54  |  VGK  |
                    +-------------------------+------+-------+
        """
        self._base_url = 'https://statsapi.web.nhl.com/api/v1'
        self.season = season

        # case insensitive
        self._team_map = {
                        'new jersey devils': 1,         'njd': 1,
                        'new york islanders': 2,        'nyi': 2,
                        'new york rangers': 3,          'nyr': 3,
                        'philadelphia flyers': 4,       'phi': 4,
                        'pittsburgh penguins': 5,       'pit': 5,
                        'boston bruins': 6,             'bos': 6,
                        'buffalo sabres': 7,            'buf': 7,
                        'montreal canadiens': 8,        'mtl': 8,
                        'ottawa senators': 9,           'ott': 9,
                        'toronto maple leafs': 10,      'tor': 10,
                        'carolina hurricanes': 12,      'car': 12,
                        'florida panthers': 13,         'fla': 13,
                        'tampa bay lightning': 14,      'tbl': 14,
                        'washington capitals': 15,      'wsh': 15,
                        'chicago blackhawks': 16,       'chi': 16,
                        'detroit red wings': 17,        'det': 17,
                        'nashville predators': 18,      'nsh': 18,
                        'st. louis blues': 19,          'stl': 19,
                        'calgary flames': 20,           'cgy': 20,
                        'colorado avalanche': 21,       'col': 21,
                        'edmonton oilers': 22,          'edm': 22,
                        'vancouver canucks': 23,        'van': 23,
                        'anaheim ducks': 24,            'ana': 24,
                        'dallas stars': 25,             'dal': 25,
                        'los angeles kings': 26,        'lak': 26,
                        'san jose sharks': 28,          'sjs': 28,
                        'columbus blue jackets': 29,    'cbj': 29,
                        'minnesota wild': 30,           'min': 30,
                        'winnipeg jets': 52,            'wpg': 52,
                        'arizona coyotes': 53,          'ari': 53,
                        'vegas golden knights': 54,     'vgk': 54
                        }

        # convert teamID to proper format and save as attribute
        if type(team_id) is int:
            self.team_id = str(team_id)
        elif len(team_id) > 2:
            self.team_id = str(self._team_map[team_id.lower()])

        # request the roster and save as attribute
        self.roster = api.getTeamRoster(self.team_id, season=self.season,
                                        base_url=self._base_url)
        # reformat to be pretty
        self.roster = [{p['person']['fullName']: (p['person']['id'],
                        p['jerseyNumber'], p['position']['code'])} for p in self.roster]

        # define forward, defense, and goalie attributes
        self.offense = [player for player in self.roster if list(player.values())[0][2] in 'LCR']
        self.defense = [player for player in self.roster if list(player.values())[0][2]=='D']
        self.goalies = [player for player in self.roster if list(player.values())[0][2]=='G']

    def getSeasonData(self, season):
        """
        """
        pass


    # def makeDataFrames(self, season=None, updateData=False):
    #     """
    #
    #     """
    #     if self.goal_data is not None and not updateData:
    #         return self.goal_data
    #     else:
    #         self.goal_data = nhl.api.time_series.getGoals()
