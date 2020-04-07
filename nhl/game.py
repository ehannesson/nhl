# game.py

from nhl import api
import numpy as np
import pandas as pd

class Game:

    def __init__(self, game_id):
        """
        Class providing a high level object-oriented approach to working with game data.

        Parameters
        ----------
        game_id : str or int (default : None)
            Integer or string of the unique game id (gamePk) for the desired game.

        Attributes
        ----------
        game_id : str
            NHL API's game id (gamePk) associated with this game.

        home : str
            Home team's triCode

        away : str
            Away team's triCode

        live_data : list of dicts
            Live feed data for the game. By default, this data is collected at instantiation.

        Methods
        -------
        getLiveData : gets all the live feed data associated with this game
        getShots : creates a nice dataframe of the shot data

        """
        self._base_url = 'https://statsapi.web.nhl.com/api/v1'

        # if integer was passed, convert to string
        if game_id is not None:
            game_id = str(game_id)

        self.game_id = game_id

        self.live_data = self.getLiveData()

        temp_home = self.live_data['boxscore']['teams']['home']
        temp_away = self.live_data['boxscore']['teams']['away']
        self.home = temp_home['team']['triCode']
        self.away = temp_away['team']['triCode']
        self.home_id = temp_home['team']['id']
        self.away_id = temp_away['team']['id']

        self.home_goals = self.live_data['linescore']['teams']['home']['goals']
        self.away_goals = self.live_data['linescore']['teams']['home']['goals']

        # bool for if the game is final (i.e. complete)
        temp_cur = self.live_data['plays']['currentPlay']
        # try:
        #     if temp_cur['result']['event'] == 'Game End':
        #         self.final = True
        #     else:
        #         self.final = False
        # except KeyError:
        #     self.final = False

        # TODO: figure out what is happening with the final status...
        self.final = True

        # set winner
        if not self.final:
            self.winner = None
        elif self.home_goals > self.away_goals:
            self.winner = self.home
        else:
            self.winner = self.away

        # TODO: this isn't always the correct date (sometimes one day after...)
        self.date = temp_cur['about']['dateTime'][:10]

        # create aggregate (boxscore) stats dataframe
        _stats = self.live_data['boxscore']['teams']
        _home = [self.date, self.home, self.home_id, self.away, True, self.winner==self.home]
        _away = [self.date, self.away, self.away_id, self.home, False, self.winner==self.away]

        for stat in _stats['home']['teamStats']['teamSkaterStats'].keys():
            # append the for and against stat for both home and away rows
            _home.append(_stats['home']['teamStats']['teamSkaterStats'][stat])
            _home.append(_stats['away']['teamStats']['teamSkaterStats'][stat])

            _away.append(_stats['away']['teamStats']['teamSkaterStats'][stat])
            _away.append(_stats['home']['teamStats']['teamSkaterStats'][stat])

        cols = ['date', 'team', 'team_id', 'opponent', 'home', 'win',
                'goals_for', 'goals_against', 'penalty_minutes_for',
                'penalty_minutes_against', 'shots_for', 'shots_against',
                'PPP_for', 'PPP_against', 'PPG_for', 'PPG_against',
                'PPO_for', 'PPO_against', 'faceoff_win_percentage_for',
                'faceoff_win_percentage_against', 'blocked_shots_for',
                'blocked_shots_against', 'takeaways_for', 'takeaways_against',
                'giveaways_for', 'giveaways_against', 'hits_for', 'hits_against']

        self.agg_stats = pd.DataFrame([_home, _away], columns=cols)

        # private attributes
        self._shotData = None
        self._DataFrame = None

    def getLiveData(self):
        """
        Method to request live* game data. Note that the game doesn't have to be
        *actually* live - it will just request the archived live feed data if it isn't.

        Returns
        -------
        self.live_data : list of dicts
            All the ugly data returned by nhl.api.getLiveData
        """

        # request data
        self.live_data = api.getLiveData(self.game_id, base_url=self._base_url)

        return self.live_data

    def shotData(self, updateLiveData=False):
        """
        Method for retrieving shots on goal data for the game.

        NOTE: this function automatically flips the coordinate for events
        during the second period (and even numbered OT periods).

        Parameters
        ----------
        updateLiveData : bool (default : False)
            If True, this runs getLiveData before getting the shot data.

        Returns
        -------
        shots : pd.DataFrame


        """
        # don't recompute the dataframe if we don't need to
        if not updateLiveData and self._shotData is not None:
            return self._shotData
        # if live data update is requested
        elif updateLiveData:
            self.getLiveData()

        # DataFrame column structure
        cols = ['shooter', 'result', 'other', 'shotType', 'coords', 'period',
                'periodTime', 'shooterTeam', 'otherTeam']

        _data = []

        shotIDs = ['SHOT', 'MISSED_SHOT', 'BLOCKED_SHOT', 'GOAL']
        # find all the shots
        for event in self.live_data['plays']['allPlays']:
            # reset everything to None so we don't have accidental carry over
            shooter, result, other, shotType, coords, period = [None]*6
            periodTime, shooterTeam, otherTeam = [None]*3

            # check if it is a shot
            if event['result']['eventTypeId'] in shotIDs:
                # get the shot result and make it lower case
                result = event['result']['eventTypeId'].split('_')[0].lower()

                # determine team affiliation
                if result == 'blocked':
                    otherTeam = event['team']['triCode']
                    if self.home == otherTeam:
                        shooterTeam = self.away
                    else:
                        shooterTeam = self.home
                else:
                    shooterTeam = event['team']['triCode']
                    if self.home == shooterTeam:
                        otherTeam = self.away
                    else:
                        otherTeam = self.home

                # get relevant shot data
                try:
                    # i.e. wrist shot, snap shot, etc.
                    shotType = event['result']['secondaryType']
                except KeyError:
                    shotType = None

                try:
                    coords = np.array(list(event['coordinates'].values()))
                except KeyError:
                    coords = None

                period = event['about']['period']
                periodTime = event['about']['periodTime']

                # find who the involved players were (excludes assists on goals)
                for p in event['players']:
                    # finding shooter
                    if p['playerType'] in ['Shooter', 'Scorer']:
                        shooter = p['player']['fullName']
                    # finding other player
                    if p['playerType'] in ['Goalie', 'Blocker']:
                        other = p['player']['fullName']

                # flip the coordinates if it is an even period number
                if period%2 == 0:
                    try:
                        coords = -coords
                    except IndexError or TypeError:
                        pass

                # append to list that will become the dataframe
                vals = [shooter, result, other, shotType, coords, period,
                        periodTime, shooterTeam, otherTeam]
                _data.append(vals)

        return pd.DataFrame(_data, columns=cols)

    def makeDataFrames(self, relabel=True, updateLiveData=False):
        """
        Method for sorting through basically all the relevant live data.

        NOTE: this function does NOT automatically flip the coordinates for events
        during the second period (or even numbered OT periods).

        Parameters
        ----------
        updateLiveData : bool (default : False)
            If True, this runs getLiveData before getting the data.

        Returns
        -------
        data : pd.DataFrame


        """
        # don't recompute the dataframe if we don't need to
        if not updateLiveData and self._DataFrame is not None:
            return self._DataFrame
        # if live data update is requested
        elif updateLiveData:
            self.getLiveData()

        # DataFrame column structure
        cols = ['event', 'secondary_type', 'player_one', 'player_one_role',
                'player_two', 'player_two_role', 'coords', 'period',
                'period_time_remaining', 'player_one_team', 'player_two_team',
                'home_team', 'home_team_id', 'away_team', 'away_team_id',
                'home_goals', 'away_goals', 'game_winning', 'empty_net',
                'player_one_id', 'player_two_id', 'game_id', 'winning_team',
                'date', 'description']

        weird_events = {'Unknown', 'Period Start', 'Period End', 'Game End', 'Game Scheduled',
                        'Period Ready', 'Period Official', 'Early Intermission Start',
                        'Early Intermission End', 'Game Official', 'Shootout Complete'}

        other_events = {'Stoppage', 'Sub', 'Fight', 'Emergency Goaltender', 'Official Challenge'}

        game_events = {'Faceoff', 'Hit', 'Giveaway', 'Goal', 'Shot', 'Missed Shot', 'Penalty',
                       'Takeaway', 'Blocked Shot'}

        _data = []
        for play in self.live_data['plays']['allPlays']:
            if play['result']['event'] in weird_events:
                continue
            elif play['result']['event'] in other_events:
                # for now just ignore these
                continue
            # just so we do not have any accidental carry over
            event, secondary_type, player_one, player_two = [None]*4
            player_one_role, player_two_role, coords, period = [None]*4
            period_time_remaining, player_one_team, player_two_team = [None]*3
            description, home_goals, away_goals, game_winning, empty_net = [None]*5
            player_one_id, player_two_id = None, None

            # now collect and organize the data......
            event = play['result']['eventTypeId'].lower()
            description = play['result']['description']
            period = play['about']['period']
            period_time_remaining = play['about']['periodTimeRemaining']
            _score = play['about']['goals']
            home_goals, away_goals = _score['home'], _score['away']

            try:
                coords = np.array(list(play['coordinates'].values()))
            except KeyError:
                coords = np.nan
            try:
                empty_net = play['result']['emptyNet']
                game_winning = play['result']['gameWinningGoal']
            except KeyError:
                empty_net = None
                game_winning = None

            try:
                strength = play['result']['strength']['name'].lower()
            except KeyError:
                strength = None

            try:
                secondary_type = play['result']['secondaryType']
            except KeyError:
                secondary_type = None

            try:
                player_one = play['players'][0]['player']['fullName']
                player_one_id = int(play['players'][0]['player']['id'])
                player_one_role = play['players'][0]['playerType']

                if empty_net:
                    pass
                elif play['players'][-1]['player']['fullName'] == player_one:
                    player_two = None
                    player_two_id = None
                    player_two_role = None
                else:
                    _temp = play['players'][-1]['player']
                    player_two = _temp['fullName']
                    player_two_id = int(_temp['id'])
                    player_two_role = play['players'][-1]['playerType']

            except KeyError:
                player_one, player_one_id, player_one_role = [None]*3
                player_two, player_two_id, player_two_role = [None]*3

            player_one_team = play['team']['triCode']
            if self.home == player_one_team:
                player_two_team = self.away
            else:
                player_two_team = self.home


            vals = [event, secondary_type, player_one, player_one_role]
            vals += [player_two, player_two_role, coords, period]
            vals += [period_time_remaining, player_one_team, player_two_team]
            vals += [self.home, self.home_id, self.away, self.away_id]
            vals += [home_goals, away_goals, game_winning, empty_net]
            vals += [player_one_id, player_two_id, self.game_id, self.winner]
            vals += [self.date, description]

            _data.append(vals)

        self._DataFrame = pd.DataFrame(_data, columns=cols)

        # filter for shots
        _shot_events = ['shot', 'missed_shot', 'blocked_shot', 'goal']
        _shot_data = [self._DataFrame[self._DataFrame.event == event].copy()
                        for event in _shot_events]
        self.shot_data = pd.concat(_shot_data)

        # filter for penalties
        self.penalty_data = self._DataFrame[self._DataFrame.event == 'penalty'].copy()
        self.penalty_data.drop(['empty_net', 'game_winning'], axis=1, inplace=True)

        if relabel:
            col_relabel = {'secondary_type': 'penalty', 'player_one': 'penalty_on',
                           'player_two': 'drew_by', 'player_one_team': 'penalty_team',
                           'player_two_team': 'drew_by_team', 'player_one_id': 'penalty_on_id',
                           'player_two_id': 'drew_by_id'}

            self.penalty_data.rename(columns=col_relabel, inplace=True)
            self.penalty_data.drop(['player_one_role', 'player_two_role'], axis=1, inplace=True)


        # filter for giveaways and takeaways
        _turnover = [self._DataFrame[self._DataFrame.event == _].copy()
                        for _ in ['giveaway', 'takeaway']]
        self.turnover_data = pd.concat(_turnover)
        self.turnover_data.drop(['secondary_type', 'empty_net', 'game_winning',
                                 'player_one_role', 'player_two', 'player_two_role',
                                 'player_two_id'], axis=1, inplace=True)
        self.turnover_data.rename({'player_two_team': 'other_team'}, inplace=True)


        # extract hit data
        self.hit_data = self._DataFrame[self._DataFrame.event == 'hit'].copy()
        self.hit_data.drop(['secondary_type', 'empty_net', 'game_winning'], axis=1, inplace=True)

        if relabel:
            col_relabel = {'player_one': 'hitter', 'player_two': 'hittee',
                           'player_one_team': 'hitter_team', 'player_two_team': 'hittee_team',
                           'player_one_id': 'hitter_id', 'player_two_id': 'hittee_id'}

            self.hit_data.rename(columns=col_relabel, inplace=True)
            self.hit_data.drop(['player_one_role', 'player_two_role'], axis=1, inplace=True)

        return None
