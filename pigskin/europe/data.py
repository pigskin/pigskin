import logging
from collections import OrderedDict


class data(object):
    def __init__(self, pigskin_obj):
        self._pigskin = pigskin_obj
        self._store = self._pigskin._store
        self.logger = logging.getLogger(__name__)


    def get_current_season_and_week(self):
        """Get the current season (year), season type, and week.

        Returns
        -------
        dict
            with the ``season``, ``season_type``, and ``week`` fields populated
            if successful. None if otherwise.
        """
        url = self._store.gp_config['modules']['ROUTES_DATA_PROVIDERS']['games']
        current = None

        try:
            r = self._store.s.get(url)
            #self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('current_season_and_week: server response is invalid')
            return None

        try:
            current = {
                'season': data['modules']['meta']['currentContext']['currentSeason'],
                'season_type': data['modules']['meta']['currentContext']['currentSeasonType'],
                'week': str(data['modules']['meta']['currentContext']['currentWeek'])
            }
        except KeyError:
            self.logger.error('could not determine the current season and week')
            return None

        return current


    def get_seasons(self):
        """Get a list of available seasons.

        Returns
        -------
        list
            a list of available seasons, sorted from the most to least recent;
            None if there was a failure.
        """
        url = self._store.gp_config['modules']['ROUTES_DATA_PROVIDERS']['games']
        seasons_list = None

        try:
            r = self._store.s.get(url)
            #self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('_get_seasons: invalid server response')
            return None

        try:
            self.logger.debug('parsing seasons')
            giga_list = data['modules']['mainMenu']['seasonStructureList']
            seasons_list = [str(x['season']) for x in giga_list if x.get('season') != None]
        except KeyError:
            self.logger.error('unable to parse the seasons data')
            return None

        return seasons_list


    def get_shows(self):
        shows = self._get_shows_nfl_network()
        # TODO: _get_shows_redzone()

        return shows


    def get_show_seasons(self, show_slug):
        # TODO: accept the show name rather than slug
        # TODO: This only support NFL Network, what's the situation with RedZone?
        # The 'seasons' list returned to _get_nfl_network_shows() cannot be
        # trusted (both incomplete and missing entries). Here, we loop over
        # every episode to build the list.
        url = self._store.gp_config['modules']['API']['NETWORK_EPISODES']
        url = url.replace(':seasonSlug/', '').replace(':tvShowSlug', show_slug)
        season_list = []

        try:
            r = self._store.s.get(url)
            #self._log_request(r)
            data = r.json()
            episodes_list = data['modules']['archive']['content']
        except (KeyError, TypeError, ValueError):
            self.logger.error('get_show_seasons: server response is invalid')
            return None

        for e in episodes_list:
            try:
                season = e['season'].replace('season-', '')
                season = int(season)
            except (AttributeError, ValueError):
                # sometime 'season' is empty, sometimes contains invalid,
                # non-season data.

                # TODO: this is such an ugly way of calling nfldate_to_datetime()
                dt = self._pigskin._utils.nfldate_to_datetime(e['scheduleDate'])

                # IMO, it's a safe guess that anything March 1st or later is the
                # broadcast year, otherwise the previous year
                try:
                    if dt.month >= 2:
                        season = dt.year
                    else:
                        season = dt.year - 1
                except AttributeError:
                    # sometimes 'scheduleDate' is empty
                    self.logger.info('get_show_seasons: cannot find episode season info; skipping:')
                    self.logger.debug(e)
                    # TODO: is there any other way to guess the season?
                    continue

            if season not in season_list:
                season_list.append(str(season))

        return sorted(season_list, reverse=True)


    def get_team_games(self, team, season):
        """Get the games (and metadata) for a given team and season.

        Parameters
        ----------
        season : str or int
            The season can be provided as either a ``str`` or ``int``.
        team : str
            Accepts the team ``seo_name``.

        Returns
        -------
        OrderedDict
            With the keys ``pre``, ``reg``, and ``post``. Each is an OrderedDict
            with the game name (e.g. Packers@Bears) and the value is a dict
            containing game metadata.

            Games are sorted according to their broadcast time and date.

        Notes
        -----
        See ``_extract_game_info()`` for a description of the metadata
        structure.

        See Also
        --------
        ``_get_team_games_easy()``
        ``_get_team_games_hard()``
        """
        games = self._get_team_games_easy(team, season)

        if not games:
            games = self._get_team_games_hard(team, season)

        if not games:
            return None

        return games


    def get_teams(self, season):
        """Get a list of teams for a given season.

        Parameters
        ----------
        season : str or int
            The season can be provided as either a ``str`` or ``int``.

        Returns
        -------
        OrderedDict
            With the key as the team name (e.g. Vikings) and value as a dict
            of the teams's metadata.

            Teams are sorted alphabetically.

        Notes
        -----
        TODO: describe metadata structure
        """
        # ['modules']['API']['TEAMS'] only provides the teams for the current
        # season. So, we ask for all the games of a non-bye-week of the regular
        # season to assemble a list of teams.
        no_bye_weeks = [1, 2, 3, 13, 14, 15, 16, 17]
        teams = OrderedDict()

        # loop over non-bye weeks until we find one with 16 games
        # The 1st week should always have 16 games, but week 1 of 2017 had only 15.
        for week in no_bye_weeks:
            games_list = self._fetch_games_list(str(season), 'reg', str(week))

            if len(games_list) == 16:
                break

        if len(games_list) != 16:
            return None

        try:
            teams_list = []
            for game in games_list:
                # Cities which have multiple teams include the team name with
                # the city name. We remove that.
                teams_list.append({
                    'abbr': game['homeTeamAbbr'],
                    'city': game['homeCityState'].replace(' ' + game['homeNickName'], ''),
                    'name': game['homeNickName'],
                })

                teams_list.append({
                    'abbr': game['visitorTeamAbbr'],
                    'city': game['visitorCityState'].replace(' ' + game['visitorNickName'], ''),
                    'name': game['visitorNickName'],
                })
        except KeyError:
            self.logger.error('get_teams: could not build the teams list')
            return None

        teams_list = sorted(teams_list, key=lambda x: x['name'])
        teams = OrderedDict((t['name'], t) for t in teams_list)

        return teams


    def get_week_games(self, season, season_type, week):
        """Get the games list and metadata for a given week.

        Parameters
        ----------
        season : str or int
            The season can be provided as either a ``str`` or ``int``.
        season_type : str
            The season_type can be either ``pre``, ``reg``, or ``post``.
        week : str or int
            The week can be provided as either a ``str`` or ``int``.

        Returns
        -------
        OrderedDict
            With the key as the game name (e.g. Packers@Bears) and value a dict
            of the game's metadata.

            Games are sorted according to their broadcast time and date.

        Notes
        -----
        See ``_extract_game_info()`` for a description of the metadata
        structure.
        """
        games = OrderedDict()
        games_list = self._fetch_games_list(str(season), season_type, str(week))

        if not games_list:
            return None

        try:
            games_list = sorted(games_list, key=lambda x: x['gameDateTimeUtc'])
        except KeyError:
            self.logger.error('get_week_games: could not parse/build the games list')
            return None

        for game in games_list:
            try:
                key = '{0}@{1}'.format(game['visitorNickName'],  game['homeNickName'])
                games[key] = self._extract_game_info(game)
            except KeyError:
                self.logger.warn('get_week_games: invalid record; skipping.')

        self.logger.debug('``games`` ready')
        return games


    def get_weeks(self, season):
        """Get the weeks of a given season.

        Returns
        -------
        OrderedDict
            with the ``pre``, ``reg``, and ``post`` fields populated with
            OrderedDicts containing the week's number (key) and the week's
            description (value) if it's a special week (Hall of Fame, Super
            Bowl, etc). None if there was a failure.
        """
        url = self._store.gp_config['modules']['ROUTES_DATA_PROVIDERS']['games']
        season = int(season)
        weeks = OrderedDict()

        try:
            r = self._store.s.get(url)
            #self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('_get_weeks: invalid server response')
            return None

        try:
            self.logger.debug('parsing weeks')
            giga_list = data['modules']['mainMenu']['seasonStructureList']
            season_data = [x['seasonTypes'] for x in giga_list if x.get('season') == season][0]

            for st in ['pre', 'reg', 'post']:
                # TODO: This is one long line. Either reformat it, or split the
                # check into a filter or function.
                weeks[st] = OrderedDict((str(w['number']), self._week_description(w['weekNameAbbr'])) for t in season_data if t.get('seasonType') == st for w in t['weeks'])
        except KeyError:
            self.logger.error('unable to parse the weeks data')
            return None

        return weeks


    @staticmethod
    def _extract_game_info(raw_game):
        """Return normalized game data.

        Parameters
        ----------
        raw_game : dict
            The raw dict for a game's data from Game Pass.

        Returns
        -------
        dict
            With the key as the game name (e.g. Packers@Bears) and value a dict
            of the game's metadata.

            Games are sorted according to their broadcast time and date.

        Notes
        -----
        TODO: 'home' and 'away' should just return the name of the teams, so a
              ``team`` handle can be attached there. And the scores should be
              moved to other keys.
        """
        try:
            game_info = {
                'city': raw_game['siteCity'],
                'stadium': raw_game['siteFullName'],
                'start_time': raw_game['gameDateTimeUtc'],
                'phase': raw_game['phase'],
                'home': {
                    'name': raw_game['homeNickName'],
                    'city': raw_game['homeCityState'],
                    'points': None,
                },
                'away': {
                    'name': raw_game['visitorNickName'],
                    'city': raw_game['visitorCityState'],
                    'points': None,
                },
                'versions' : {},
            }
        except KeyError:
            return None

        try:
            game_info['home']['points'] = raw_game['homeScore']['pointTotal']
            game_info['away']['points'] = raw_game['visitorScore']['pointTotal']
        except TypeError:
            pass

        # TODO: perhaps it would be nice for the version to be stored in
        # an OrderedDict. full, then condensed, then coaches. What I
        # assume to be in order of what users are most likely to want.
        version_types = {'condensed': 'condensedVideo' , 'coach': 'coachfilmVideo', 'full': 'video'}
        for v in version_types:
            try:
                game_info['versions'][v] = raw_game[version_types[v]]['videoId']
            except (KeyError, TypeError):
                pass

        return game_info


    def _fetch_games_list(self, season, season_type, week):
        """Get a list of games for a given week.

        Parameters
        ----------
        season : str or int
            The season can be provided as either a ``str`` or ``int``.
        season_type : str
            The season_type can be either ``pre``, ``reg``, or ``post``.
        week : str or int
            The week can be provided as either a ``str`` or ``int``.

        Returns
        -------
        list
            With a dict of metadata as the value. An empty list if there was a
            failure.
        """
        url = self._store.gp_config['modules']['ROUTES_DATA_PROVIDERS']['games_detail']
        url = url.replace(':seasonType', season_type).replace(':season', str(season)).replace(':week', str(week))
        games_list = []

        try:
            r = self._store.s.get(url)
            #self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('_fetch_games_list: invalid server response')
            return []

        try:
            games_list = [g for x in data['modules'] if data['modules'][x].get('content') for g in data['modules'][x]['content']]
        except KeyError:
            self.logger.error('_fetch_games_list: could not parse/build the games list')
            return []

        return games_list


    def _get_shows_nfl_network(self):
        # TODO: do we get a more complete response when logged in?
        url = self._store.gp_config['modules']['API']['NETWORK_PROGRAMS']
        shows_dict = OrderedDict()

        try:
            r = self._store.s.get(url)
            #self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('_get_nfl_network_shows: server response is invalid')
            return None

        try:
            shows_list = sorted(data['modules']['programs'], key=lambda x: x['title'])
        except KeyError:
            self.logger.error('_get_nfl_network_shows: could not parse nfl network shows list')
            return None

        for show in shows_list:
            # the 'seasons' entry cannot be trusted; so it is ignored
            try:
                # get the core data
                key = show['title']
                shows_dict[key] = {
                    'desc' : '',
                    'logo' : '',
                    'name': show['title'],
                    'slug': show['slug'],
                }
            except KeyError:
                self.logger.warn('_get_nfl_network_shows: invalid record; skipping.')
                continue

            # useful, but not crucial data
            if show.get('description'):
                shows_dict[key]['desc'] = show['description']

            try:
                shows_dict[key]['logo'] = show['thumbnail']['thumbnailUrl']
            except (KeyError, TypeError):
                self.logger.warn('_get_nfl_network_shows: cannot find logo')

        return shows_dict


    def _get_team_games_easy(self, team, season):
        """An OrderedDict of a team's games for a season and their game objects.

        Parameters
        ----------
        season : str or int
            The season can be provided as either a ``str`` or ``int``.
        team : str
            The name of the team (e.g. Dolphins).

        Returns
        -------
        OrderedDict
            With the keys ``pre``, ``reg``, and ``post``. Each is an OrderedDict
            with the game name (e.g. Packers@Bears) and the value is a dict
            containing game metadata.

            Games are sorted according to their broadcast time and date.

        Note
        ----
        The service API this talks to only supports the current season, but
        ``season`` is accepted and checked for, just in case the service
        changes..

        See Also
        --------
        ``_get_team_games_hard()``
        """
        url = self._store.gp_config['modules']['ROUTES_DATA_PROVIDERS']['team_detail']
        # TODO: make sure simply lower-casing is sufficient
        team_seo_name = team.lower()
        url = url.replace(':team', team_seo_name)

        games_dict = OrderedDict()
        for st in ['pre', 'reg', 'post']:
            games_dict[st] = OrderedDict()

        try:
            r = self._store.s.get(url)
            #self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('_get_team_games_easy: server response is invalid')
            return None

        try:
            games_list = data['modules']['gamesCurrentSeason']['content']
            games_list = sorted(games_list, key=lambda x: x['gameDateTimeUtc'])
        except KeyError:
            self.logger.error('_get_week_games_easy: could not parse/build the games list')
            return None

        for game in games_list:
            try:
                if int(game['season']) == int(season):
                    key = '{0}@{1}'.format(game['visitorNickName'], game['homeNickName'])
                    st = game['seasonType'].lower()
                    games_dict[st][key] = self._extract_game_info(game)
            except KeyError:
                self.logger.warn('_get_team_games_easy: invalid record; skipping.')

        # purge empty season types (the team may not have made the post season).
        games_dict = OrderedDict((st, games_dict[st]) for st in games_dict if games_dict[st])

        self.logger.debug('``games`` ready')
        return games_dict


    def _get_team_games_hard(self, team, season):
        """An OrderedDict of a team's games for a season and their game objects.

        Parameters
        ----------
        season : str or int
            The season can be provided as either a ``str`` or ``int``.
        team : str
            The name of the team (e.g. Dolphins).

        Returns
        -------
        OrderedDict
            With the keys ``pre``, ``reg``, and ``post``. Each is an OrderedDict
            with the game name (e.g. Packers@Bears) and the value is a dict
            containing game metadata.

            Games are sorted according to their broadcast time and date.

        Note
        ----
        This fallback exists because the API that ``_get_team_games_easy()``
        talks to only supports the current season.

        This method is quite slow and causes a lot of HTTP requests.
        """
        games_dict = OrderedDict()
        weeks_dict = self.get_weeks(str(season))

        for st in weeks_dict:
            games_dict[st] = OrderedDict()
            for week in weeks_dict[st]:
                weeks_games_dict = self.get_week_games(season, st, week)

                # TODO: this is quite un-Pythonic, but I don't know of an easier
                # way to check for a substring in a dict key
                for game_name in weeks_games_dict:
                    if team in game_name:
                        games_dict[st][game_name] = weeks_games_dict[game_name]

        # purge empty season types (the team may not have made the post season).
        games_dict = OrderedDict((st, games_dict[st]) for st in games_dict if games_dict[st])

        return games_dict


    @staticmethod
    def _week_description(abbr):
        descriptions = {
            'hof': 'Hall of Fame',
            'wc': 'Wild Card',
            'div': 'Divisional',
            'conf': 'Conference',
            'pro': 'Pro Bowl',
            'sb': 'Super Bowl',
        }

        try:
            return descriptions[abbr]
        except KeyError:
            return ''
