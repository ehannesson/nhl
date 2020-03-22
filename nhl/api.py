# collect_data.py
import requests
import numpy as np
import pandas as pd
import time


def getTeamIDs(base_url='https://statsapi.web.nhl.com/api/v1', active=True):
    """
    Queries the NHL API for (team_name, team_id) pairs.

    Parameters:
        base_url (str): base url to the nhl api
        active (bool): if True, only return data for active teams

    Returns:
        teams (list(tuples)): list containing (team-name, team-id) pairs
            for all (active) teams
    """
    # request teams data
    all_teams = requests.get(base_url + '/teams').json()['teams']

    # extract team names and ids
    if active:
        teams = {team['name']: team['id'] for team in all_teams if team['active']}
    else:
        teams = {team['name']: team['id'] for team in all_teams}

    return teams


def teamIDsDict():
    team_dict = {
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


def getTeamRoster(team_id, season=None, wait=0,
                    base_url='https://statsapi.web.nhl.com/api/v1'):
    """
    Queries the NHL API for roster information for a given team

    Parameters
    ----------
        team_id (int): nhl api team id number
        base_url (str): base url to the nhl api
        season (str): season to request roster; defaults to using active roster

        wait : float (nonnegative, default=0)
            Specifies the amount of time (in seconds) to wait before making the
            request to the API; not necessary unless making more then ~500+ requests
            a second.

    Returns
    -------
        team_roster (list(dicts)): list of dicts; each dictionary contains the
            following information
        {'person': {'id': int,
                    'fullName': str,
                    'link': str
            },
        'jerseyNumber': str,
        'position': {'code': str
                     'name': str
                     'type': str
                     'abbreviation': str
            }
        }
    """
    # if season is not specified, assume it is the current season
    if season is None:
        season = requests.get(base_url + '/seasons/current').json()['seasons']
        season = season[0]['seasonId']

    if wait:
        # wait a moment to request additional data
        time.sleep(wait)

    # endpoint to request data from
    endpoint_url = '/teams/{}/roster'.format(team_id)

    if  season:
        # if we want data from a specific season
        endpoint_url += '?expand=team.roster&season={}'.format(season)

    # get team roster
    team_roster = requests.get(base_url + endpoint_url).json()

    # extract player information
    return team_roster['roster']


def getGameIDs(team_id, season=None, include_pre=False, include_post=False,
                include_future=True, base_url='https://statsapi.web.nhl.com/api/v1'):
    """
    Queries the NHL API for a team's schedule and returns a list of each game_id.
    Basically just wraps getSchedule and extracts only the game IDs.

    Parameters
    ----------
    team_id : str or int
        Team's NHL API id number.

    season : str or list-like ('YYYYYYYY' or (start_date, end_date), default: None)
        Season to request data from (e.g. '20192020'). If None, defaults to the
        current season.

        If passing a list, should be of the form ("YYYY-MM-DD", "YYYY-MM-DD"),
        with the first entry being the start date and the second the end date.

    include_pre : bool (default: False)
        Whether to include preseason games.

    include_post : bool (default: False)
        Whether to include postseason games.

    include_future : bool (default : True)
        Whether to include future (i.e. unplayed/unfinished) games.

    Returns
    -------
    schedule : list(dicts)
        List containing one dictionary per scheduled game for the entire season.
    """
    # get the team's schedule
    schedule = getSchedule(team_id, season=season, include_pre=include_pre,
                           include_post=include_post, include_future=include_future,
                           base_url=base_url)

    # get the game id from each game
    game_ids = [game['games'][0]['gamePk'] for game in schedule]

    return game_ids


def getPlayerStats(player_id, season=None, report_type='statsSingleSeason',
                    wait=0, base_url='https://statsapi.web.nhl.com/api/v1'):
    """
    Queries the NHL API for the stats of a player.

    Parameters
    ----------
        player_id : int
            NHL API player id number

        report_type : str (see below for available options and explanations)
            Specifies what type of statistic/aggregation to request. Must be one
            of the options returned by the /statTypes endpoint.

        season : str ('YYYYYYYY', default: None)
            Season to request data from (e.g. '20192020'). If None, defaults to the
            current season.

        wait : float (nonnegative, default=0)
            Specifies the amount of time (in seconds) to wait before making the
            request to the API; not necessary unless making more then ~500+ requests
            a second.

        base_url : str (default: 'https://statsapi.web.nhl.com/api/v1')
            Base url to the NHL API

    Returns
    -------
        player_stats : dictionary
            Dictionary of requested stats. If the player has no recorded stats
            for the season requested, returns None.

    Additional Information
    ----------------------
    Note that this function automatically filters out the non-data stuff by
    applying `['stats'][0]['splits']` to the json returned from the API. So, if
    making requests directly to the API, just remember this.

    Option Details
    --------------
    report_type : str (see below for available options)
        Specifies what type of statistic/aggregation to request. Options are:

        Regular Season
        --------------
            gameLog             -   game by game stats, no aggregation

            statsSingleSeason   -   season aggregated stats
            homeAndAway         -   season aggregated stats split by home/away
            winLoss             -   season aggregated stats split by win/loss/OT
            byMonth             -   season aggregated stats split by month
            byDayOfWeek         -   season aggregated stats split by day
            vsDivision          -   season aggregated stats split by opponent's division
            vsConference        -   season aggregated stats split by opponent's conference
            vsTeam              -   season aggregated stats split by opponent

            yearByYear              -   stats aggregated yearly; (season argument ignored)
            yearByYearRank          -   player's yearly league wide stat rankings
            careerRegularSeason     -   stats aggregated over player's entire (NHL) career

            NOTE: the yearByYear and yearByYearRank include stats from other
            leagues the player has played in, though they will be in separate
            dictionaries. If a player played in multiple leagues during the same
            season, the returned list will contain one dictionary for each league.
            League information can be accessed with the 'league' key.

            regularSeasonStatRankings   -   player's league wide stat rankings
            goalsByGameSituation        -   goals scored in different situations
                                            NOTE: this counts each situation
                                                separately, so a single goal
                                                can be counted in multiple categories
            onPaceRegularSeason         -   projected stat totals (current season only)

        Postseason (playoffs)
        ---------------------
            playoffGameLog                  -   game by game stats, no aggregation

            statsSingleSeasonPlayoffs       -   playoff aggregated stats
            homeAndAwayPlayoffs             -   playoff aggregated stats split by home/away
            winLossPlayoffs                 -   playoff aggregated stats split by win/loss/OT
            byMonthPlayoffs                 -   playoff aggregated stats split by month
            byDayOfWeekPlayoffs             -   playoff aggregated stats split by day
            vsDivisionPlayoffs              -   playoff aggregated stats split by opponent's division
            vsConferencePlayoffs            -   playoff aggregated stats split by opponent's conference
            vsTeamPlayoffs                  -   playoff aggregated stats split by opponent

            yearByYearPlayoffs              -   playoff stats aggregated yearly
            yearByYearPlayoffsRank          -   player's yearly league wide playoff stat rankings
            careerPlayoffs                  -   playoff stats aggregated over player's entire (NHL) career

            See note above concerning `yearByYear` type options.

            playoffStatRankings             -   player's league wide playoffs stat rankings
            goalsByGameSituationPlayoffs    -   playoff goals scored in different situations
                                                NOTE: this counts each situation
                                                    separately, so a single goal
                                                    can be counted in multiple categories


        While each `report_type` will return a list, these lists look very different.
        Specifically, the function returns a list containing:

            statsSingleSeason           -   a single dictionary
            gameLog                     -   a dictionary for each game

            homeAndAway                 -   home and away dictionaries
            winLoss                     -   home, away, and OT dictionaries
            byMonth                     -   a dictionary for each month (that the player played a game in)
            byDayOfWeek                 -   a dictionary for each day of the week (that the player has played on)
            vsDivision                  -   a dictionary for each division (that has been played against)
            vsConference                -   a dictionary for each conference (that has been played against)
            vsTeam                      -   a dictionary for each team (that has been played against)

            regularSeasonStatRankings   -   a single dictionary
            goalsByGameSituation        -   a single dictionary
            onPaceRegularSeason         -   a single dictionary
    """

    # if season is not specified, assume it is the current season
    if season is None:
        season = requests.get(base_url + '/seasons/current').json()['seasons']
        season = season[0]['seasonId']

    time.sleep(wait)

    # endpoint to query
    endpoint_url = f'/people/{player_id}/stats?stats={report_type}&season={season}'

    # request player statistics
    player_stats = requests.get(base_url + endpoint_url).json()

    # return the requested stats splits
    return player_stats['stats'][0]['splits']


def getSchedule(team_id, season=None, include_pre=False, include_post=False,
                include_future=True, base_url='https://statsapi.web.nhl.com/api/v1'):
    """
    Queries the NHL API for a team's schedule.

    Parameters
    ----------
    team_id : str or int
        Team's NHL API id number.

    season : str or list-like ('YYYYYYYY' or (start_date, end_date), default: None)
        Season to request data from (e.g. '20192020'). If None, defaults to the
        current season.

        If passing a list, should be of the form ("YYYY-MM-DD", "YYYY-MM-DD"),
        with the first entry being the start date and the second the end date.

    include_pre : bool (default: False)
        Whether to include preseason games.

    include_post : bool (default: False)
        Whether to include postseason games.

    include_future : bool (default : True)
        Whether to include future (i.e. unplayed/unfinished) games.

    Returns
    -------
    schedule : list(dicts)
        List containing one dictionary per scheduled game for the entire season.
    """
    # if season is not specified, assume it is the current season
    if season is None:
        season = requests.get(base_url + '/seasons/current').json()['seasons']
        season = season[0]['seasonId']

    # request schedule information
    if type(season) is str:
        schedule = requests.get(base_url + f'/schedule?season={season}&teamId={team_id}')
    else:
        modifier = f'teamId={team_id}&startDate={season[0]}&endDate={season[1]}'
        schedule = requests.get(base_url + f'/schedule?{modifier}')

    schedule = schedule.json()['dates']

    # filter out preseason/postseason/future games based on parameters
    if not np.all([include_pre, include_post, include_future]):
        for game_num in range(len(schedule))[::-1]:
            # drill down to the level we care about
            game = schedule[game_num]['games'][0]

            # if we don't want to include future games
            if not include_future and game['status']['detailedState'] != 'Final':
                schedule.pop(game_num) # remove from schedule
                continue

            # if include_pre is False, skip preseason games
            if not include_pre and game['gameType'] == 'PR':
                schedule.pop(game_num)
                continue

            # if include_post is False, skip postseason games
            if not include_post and game['gameType'] == 'P':
                schedule.pop(game_num)
                continue

    return schedule


def getBoxScore(game_id, base_url='https://statsapi.web.nhl.com/api/v1'):
    """
    Queries the NHL API for the boxscore for game `game_id`.

    Parameters
    ----------
    game_id : str
        NHL API game_id number for the desired game.

    base_url : str
        URL to the base of the NHL API

    Returns
    -------
    home : dict
        dictionary containing home team information

    away : dict
        dictionary containing away team information
    """
    boxscore = requests.get(base_url + f'/game/{game_id}/boxscore').json()

    return boxscore['teams']['home'], boxscore['teams']['away']


def getLiveData(game_id, base_url='https://statsapi.web.nhl.com/api/v1'):
    """
    Queries the NHL API for the live data feed of a game.

    Parameters
    ----------
    game_id : str or int (YYYYGGGGGG)
        NHL API game_id. First four characters are the year the season started,
        the final six are unique to this game.

    Returns
    -------
    live_data : dict (json-like)
        Dictionary containing data for the specified game. The high level outline
        of the returned dictionary is given here. See the Additional Information
        section for a more detailed breakdown of each category.

        The top level of the dictionary has four keys:
            plays       -   play by play data (typically 10K+ lines)
            linescore   -   basic period information (a couple hundred lines)
            boxscore    -   basic team and skater stats (a couple thousand lines)
            decisions   -   winning/losing goaltender; 3 stars

    Additional Information
    ----------------------
    Detailed breakdown of live_data categories:

    plays: live_data['plays']

        allPlays        -   list of dicts; each dict is one play; every play is recorded here.
        scoringPlays    -   list of play numbers (indices) where a goal was scored
        penaltyPlays    -   list of play numbers (indices) where a penalty was called
        playsByPeriod   -   list of dicts, ordered by period; has keys "startIndex"
                                and "endIndex", which give the play numbers of the first
                                and final play of the period, respectively. Also has the
                                key "plays", which gives a list of integers from "startIndex"
                                to "endIndex", inclusive.
        currentPlay     -   dictionary with data about the current (i.e. live) play.
                            Has the same structure as each entry in "allPlays".

    allPlays: live_data['plays']['allPlays']
        NOTE: Events not involving players (i.e. stoppages) don't have "players" or "team" keys.

        players         -   list of dicts; each dict is a player involved in the event
        result          -   dict containing what the event was, the outcome, and a short description
        about           -   dict with basic game status info (period, time remaining, current score, etc.)
        coordinates     -   dict with keys "x" and "y"; (x, y) position where
                                the event happened. Center faceoff circle is (0, 0) TODO: which way is +/-??
        team            -   dict with information on one of the teams; it is unclear
                                what motivates the choice of one team vs. the other...

    players: live_data['plays']['allPlays']['players']


    """
    # request all the data
    live_data = requests.get(base_url + f'/game/{game_id}/feed/live')

    return live_data.json()['liveData']































"""
A schedule request returns json of the form
    {
        'copyright':    Copyright info,
        'totalItems:    int,
        'totalEvents':  int,
        'totalGames':   int,
        'totalMatches': int,
        'wait':         int,
        'dates':        list(dict)
    }

where each element of the 'dates' list is of the form
    {
        'date':         'YYYY-MM-DD'
        'totalItems:    int,
        'totalEvents':  int,
        'totalGames':   int,
        'totalMatches': int,
        'games':        list(dict)
        'events':       list(dict - usually empty)
        'matches':      list(dict - usually empty)
    }
where each element of 'games' (typically only the one game) is of the form
    {
    'gamePk':       game id number (?) with form YYYY------
    'link':         /api/v1/game/{gamePk}/feed/live
    'gameType':     string denoting game type (regular season: R, etc.)
    'season':       YYYYYYYY (season game is played in)
    'gameDate':     YYYY-MM-DDTHH:MM:SSZ
    'status':       {
                        'abstractGameState':    str 'Final', etc.
                        'codedGameState':       int (??)
                        'detailedState':        str 'Final', etc.
                        'statusCode':           int (??)
                        'startTimeTBD':         bool
                    }
    'teams':        {
                        'away': {
                                    'leagueRecord': {
                                                        'wins':     num of wins,
                                                        'losses':   num losses,
                                                        'ot':       ot losses,
                                                        'type':     league (as opposed to conference, etc.)
                                                    },
                                    'score':    goals for
                                    'team':     {
                                                    'id':       int - team id
                                                    'name':     str - team name
                                                    'link':     /api/v1/teams/{id}
                                                }
                                }
                        'home': {same as for away}
                    }
    'venue':        {
                        'name': arena name,
                        'link': /api/v1/venues/null
                    },
    'content':      /api/v1/game/{gamePk}/content
    }
"""
