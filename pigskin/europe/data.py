import logging
import requests
from collections import OrderedDict


class data(object):
    def __init__(self, store):
        self._store = store
        self.logger = logging.getLogger(__name__)


    def get_games(self, season, season_type, week):
        """Get the raw game data for a given season (year), season type, and week.

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
            of dicts with the metadata for each game

        Note
        ----
        TODO: the data returned really should be normalized, rather than a
              (nearly) straight dump of the raw data.
        """
        url = self._store.gp_config['modules']['ROUTES_DATA_PROVIDERS']['games_detail']
        url = url.replace(':seasonType', season_type).replace(':season', str(season)).replace(':week', str(week))
        games = None

        try:
            r = self._store.s.get(url)
            #self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('_get_games: invalid server response')
            return None
        except Exception as e:
            raise e

        try:
            games = [g for x in data['modules'] if data['modules'][x].get('content') for g in data['modules'][x]['content']]
            games = sorted(games, key=lambda x: x['gameDateTimeUtc'])
        except KeyError:
            self.logger.error('could not parse/build the games list')
            return None
        except Exception as e:
            raise e

        self.logger.debug('``games`` ready')
        return games


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
        except Exception as e:
            raise e

        try:
            self.logger.debug('parsing seasons')
            giga_list = data['modules']['mainMenu']['seasonStructureList']
            seasons_list = [str(x['season']) for x in giga_list if x.get('season') != None]
        except KeyError:
            self.logger.error('unable to parse the seasons data')
            return None
        except Exception as e:
            raise e

        return seasons_list


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
        except Exception as e:
            raise e

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
        except Exception as e:
            raise e

        return weeks


    def _week_description(self, abbr):
        desc = ''
        if abbr == 'hof':
            desc = 'Hall of Fame'
        elif abbr == 'wc':
            desc = 'Wild Card'
        elif abbr == 'div':
            desc = 'Divisional'
        elif abbr == 'conf':
            desc = 'Conference'
        elif abbr == 'pro':
            desc = 'Pro Bowl'
        elif abbr == 'sb':
            desc = 'Super Bowl'

        return desc
