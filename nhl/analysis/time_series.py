# time-series.py

import requests
import pandas as pd
import numpy as np
import time

from nhl.api import getSchedule, getBoxScore


def getGoals(team_id, season=None, include_pre=False, include_post=False,
             base_url='https://statsapi.web.nhl.com/api/v1'):
    """
    Gathers a goals for/against time series for team `team_id` and season `season`.

    Parameters
    ----------
        team_id : str
            NHL API teamId of the desired team.

        season : str (YYYYYYYY; default: None)
            Specifies which season to construct the time series for.
            When season=None, this defaults to the current season.

        include_pre : bool (default: False)
            Whether to include preseason games in the time series.

        include_post : bool (default: False)
            Whether to include postseason games in the time series.

        base_url : str
            URL to the NHL API base; used only if season is not specified.

    Returns
    -------
        goals_for : ndarray
            Goals for time series.

        goals_against : ndarray
            Goals against time series.
    """
    if type(team_id) is int:
        team_id = str(team_id)

    # if season is not specified, assume it is the current season
    if season is None:
        season = requests.get(base_url + '/seasons/current').json()['seasons']
        season = season[0]['seasonId']

    games = getSchedule(team_id, season=season, mongodb=False)
    games = games[team_id][season]

    goals_for = []
    goals_against = []

    for game in games:
        # drill down to the level we care about
        game = game['games'][0]

        # stop if we have reached games that have not been completed
        if game['status']['detailedState'] != 'Final':
            break

        # if include_pre is False, skip preseason games
        if not include_pre:
            if game['gameType'] == 'PR':
                continue

        # if include_post is False, skip preseason games
        if not include_post:
            if game['gameType'] == 'P':
                continue

        # check for home/away
        if str(game['teams']['home']['team']['id']) == team_id:
            goals_for.append(game['teams']['home']['score'])
            goals_against.append(game['teams']['away']['score'])
        else:
            goals_for.append(game['teams']['away']['score'])
            goals_against.append(game['teams']['home']['score'])

    # convert to numpy because that is better
    goals_for, goals_against = np.array(goals_for), np.array(goals_against)

    return goals_for, goals_against


def getTeamBoxScores(team_id, season=None, include_pre=False, include_post=False,
                     return_np=False, base_url='https://statsapi.web.nhl.com/api/v1',
                     wait=0):
    """
    Note, this will take some time to run.
    Constructs time series for each

    Parameters
    ----------
        team_id : str or int
            NHL API teamId of the desired team.

        season : str (YYYYYYYY; default: None)
            Specifies which season to construct the time series for.
            When season=None, this defaults to the current season.

        include_pre : bool (default: False)
            Whether to include preseason games in the time series.

        include_post : bool (default: False)
            Whether to include postseason games in the time series.

        return_np : bool (default: False)
            If False, returns a pandas dataframe; otherwise, returns an ndarray.

        base_url : str
            URL to the NHL API base.

        wait : float (nonnegative, defalut: 0)
            Specifies a wait time between requests to the API. Not needed unless
            you are making 1000+ requests per second (I think...?)

    Returns
    -------

    """
    # if season is not specified, assume it is the current season
    if season is None:
        season = requests.get(base_url + '/seasons/current').json()['seasons']
        season = season[0]['seasonId']

    # request raw schedule
    games = getSchedule(team_id, season=season, base_url=base_url)

    team_stats = []
    other_stats = []
    cols = None

    for game in games:
        if wait:
            time.sleep(wait)
        # grab the actual game dictionary
        game = game['games'][0]

        # stop if we have reached games that have not been completed
        if game['status']['detailedState'] != 'Final':
            break

        # if include_pre is False, skip preseason games
        if not include_pre and game['gameType'] == 'PR':
            continue

        # if include_post is False, skip postseason games
        if not include_post and game['gameType'] == 'P':
            continue

        # get boxscore data
        game_id = game['gamePk']    # game id
        try:
            team, other = getBoxScore(game_id)
        except KeyError:
            print(f'game_id: {game_id} failed')
            continue

        # grab team ids and find which is team_id
        home_id, away_id = str(team['team']['id']), str(other['team']['id'])
        if home_id != team_id:
            team, other = other, team

        team = team['teamStats']['teamSkaterStats']
        other = other['teamStats']['teamSkaterStats']

        if cols is None:
            # save column labels for future
            cols = list(team.keys())

        team_stats.append([float(team_id)] + [float(team[stat]) for stat in team.keys()])
        other_stats.append([float(away_id)] + [float(other[stat]) for stat in other.keys()])

    team_stats = np.array(team_stats)
    other_stats = np.array(other_stats)

    if return_np:
        return team_stats, other_stats

    team_stats = pd.DataFrame(team_stats[:, 1:], index=team_stats[:, 0], columns=cols)
    other_stats = pd.DataFrame(other_stats[:, 1:], index=other_stats[:, 0], columns=cols)

    return team_stats, other_stats


def goalsFor(team_id, season=None, include_pre=False, include_post=False,
             average=False, cumulative=False, base_url='https://statsapi.web.nhl.com/api/v1'):
    """
    Creates a goals for time series for the given team.

    Parameters
    ----------
        team_id : str
            NHL API teamId of the desired team.

        season : str (YYYYYYYY; default: None)
            Specifies which season to construct the time series for.
            When season=None, this defaults to the current season.

        include_pre : bool (default: False)
            Whether to include preseason games in the time series.

        include_post : bool (default: False)
            Whether to include postseason games in the time series.

        average : bool (default: False)
            If True, the ith element of the resulting time series will be the
            *average* goals for, averaged up through the ith game.

        cumulative : bool (default: False)
            If True, the time series will be the cumulative goals for.

        base_url : str
            URL to the NHL API base; used only if season is not specified.

    Returns
    -------
        goals_for : ndarray
            Goals for time series.
    """
    if type(team_id) is int:
        team_id = str(team_id)

    goals_for, _ = getGoals(team_id, season=season, include_pre=include_pre,
                            include_post=include_post, base_url=base_url)

    # if average/cumulative is requested
    if average:
        goals_for = np.cumsum(goals_for)/np.arange(1, goals_for.size+1)
    elif cumulative:
        goals_for = np.cumsum(goals_for)

    return goals_for


def goalsAgainst(team_id, season=None, include_pre=False, include_post=False,
                 average=False, cumulative=False, base_url='https://statsapi.web.nhl.com/api/v1'):
    """
    Creates a goals against time series for the given team.

    Parameters
    ----------
        team_id : str
            NHL API teamId of the desired team.

        season : str (YYYYYYYY; default: None)
            Specifies which season to construct the time series for.
            When season=None, this defaults to the current season.

        include_pre : bool (default: False)
            Whether to include preseason games in the time series.

        include_post : bool (default: False)
            Whether to include postseason games in the time series.

        average : bool (default: False)
            If True, the ith element of the resulting time series will be the
            *average* goals against, averaged up through the ith game.

        cumulative : bool (default: False)
            If True, the time series will be the cumulative goals against.

        base_url : str
            URL to the NHL API base; used only if season is not specified.

    Returns
    -------
        goals_against : ndarray
            Goals against time series.
    """
    if type(team_id) is int:
        team_id = str(team_id)

    _, goals_against = getGoals(team_id, season=season, include_pre=include_pre,
                                include_post=include_post, base_url=base_url)

    # if average/cumulative is requested
    if average:
        goals_against = np.cumsum(goals_against)/np.arange(1, goals_against.size+1)
    elif cumulative:
        goals_against = np.cumsum(goals_against)

    return goals_against


def goalDiff(team_id, season=None, include_pre=False, include_post=False,
             average=False, cumulative=False, base_url='https://statsapi.web.nhl.com/api/v1'):
    """
    Creates a goals against time series for the given team.

    Parameters
    ----------
        team_id : str
            NHL API teamId of the desired team.

        season : str (YYYYYYYY; default: None)
            Specifies which season to construct the time series for.
            When season=None, this defaults to the current season.

        include_pre : bool (default: False)
            Whether to include preseason games in the time series.

        include_post : bool (default: False)
            Whether to include postseason games in the time series.

        average : bool (default: False)
            If True, the ith element of the resulting time series will be the
            *average* goal differential, averaged up through the ith game.

        cumulative : bool (default: False)
            If True, the time series will be the cumulative goal differential.

        base_url : str
            URL to the NHL API base; used only if season is not specified.

    Returns
    -------
        goal_diff : ndarray
            Goal differential time series.
    """
    if type(team_id) is int:
        team_id = str(team_id)

    goals_for, goals_against = getGoals(team_id, season=season, include_pre=include_pre,
                                        include_post=include_post, base_url=base_url)

    # calculate the goal differential
    goal_diff = goals_for - goals_against

    # if average/cumulative is requested
    if average:
        goal_diff = np.cumsum(goal_diff)/np.arange(1, goal_diff.size+1)
    elif cumulative:
        goal_diff = np.cumsum(goal_diff)

    return goal_diff
