import logging
import requests
from collections import OrderedDict


class week(object):
    def __init__(self, store, season, season_type, week):
        self._store = store
        self._season = season
        self._season_type = season_type
        self._week = week

        self.logger = logging.getLogger(__name__)
        self._games = None


    @property
    def games(self):
        if self._games is None:
            self.logger.debug('``games`` not set. attempting to populate')
            self._games = self._get_games(self._season, self._season_type, self._week)

        return self._games


    def _get_games(self, season, season_type, week):
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
