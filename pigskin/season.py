import logging
import requests
from collections import OrderedDict


class season(object):
    def __init__(self, store, season):
        self._store = store
        self._season = season

        self.logger = logging.getLogger(__name__)
        self._weeks = None


    @property
    def weeks(self):
        if self._weeks is None:
            self.logger.debug('``weeks`` not set. attempting to populate')
            self._weeks = self._get_weeks(self._season)

        return self._weeks


    def _get_weeks(self, season):
        """Get the weeks of a given season.

        Returns
        -------
        dict
            with the ``pre``, ``reg``, and ``post`` fields populated with dicts
            containing the week's number (key) and the week's abbreviation
            (value). None if there was a failure.
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
            season_types_list = [x['seasonTypes'] for x in giga_list if x.get('season') == season][0]

            # TODO: These need to be assigned in order, and the assigned dicts
            # need to be OrderedDict
            for st in season_types_list:
                if st['seasonType'] == 'pre':
                    weeks['pre'] = { str(w['number']) : w['weekNameAbbr'] for w in st['weeks'] }
                elif st['seasonType'] == 'reg':
                    weeks['reg'] = { str(w['number']) : w['weekNameAbbr'] for w in st['weeks'] }
                elif st['seasonType'] == 'post':
                    weeks['post'] = { str(w['number']) : w['weekNameAbbr'] for w in st['weeks'] }
                else:
                    self.logger.warning('found an unexpected season type')
        except KeyError:
            self.logger.error("unable to find the season's week-list")
            return None
        except Exception as e:
            raise e

        self.logger.debug('``weeks`` ready')
        return weeks
