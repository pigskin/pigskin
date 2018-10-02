"""
A Python library for NFL Game Pass
"""
import json
import logging
from collections import OrderedDict
try:
    from urllib.parse import urlencode
except ImportError:  # Python 2.7
    from urllib import urlencode

import requests
import m3u8

from . import settings
from .europe.auth import auth
from .europe.data import data
from .europe.utils import utils
from .europe.video import video


class store(object):
    def __init__(self):
        self.s = None  # a requests session
        self.gp_config = None
        self.access_token = None
        self.refresh_token = None
        self.username = None


class pigskin(object):
    def __init__(
            self,
            proxy_url=None
        ):
        self.logger = logging.getLogger(__name__)
        self.ch = logging.StreamHandler()
        self.ch.setLevel(logging.INFO)
        self.logger.addHandler(self.ch)

        self._store = store()
        self._store.s = requests.Session()
        self._store.s.proxies['http'] = proxy_url
        self._store.s.proxies['https'] = proxy_url
        self._store.gp_config = self.populate_config()

        self._store.access_token = None
        self._store.refresh_token = None
        self._store.subscription = None

        self._seasons = None
        self._current = None
        self.nfln_shows = {}
        self.episode_list = []

        self._auth = auth(self)
        self._data = data(self)
        self._utils = utils()
        self._video = video(self)


    class GamePassError(Exception):
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return repr(self.value)


    @property
    def current(self):
        """A Dict of the current season and week.

        Returns
        -------
        Dict
            With the ``season``, ``season_type``,  and ``week`` keys set.
            ``None`` if there was a failure.
        """

        if self._current is None:
            self.logger.debug('``current`` not set. attempting to populate')
            self._current = self._data.get_current_season_and_week()
            self.logger.debug('``current`` ready')

        return self._current


    @property
    def seasons(self):
        """An OrderedDict of available seasons and their season objects.

        Returns
        -------
        OrderedDict
            Sorted from most to least recent, with a season object as the value.
            ``None`` if there was a failure.
        """

        if self._seasons is None:
            self.logger.debug('``seasons`` not set. attempting to populate')
            seasons_list = self._data.get_seasons()
            self._seasons = OrderedDict((s, season(self, s)) for s in seasons_list)
            self.logger.debug('``seasons`` ready')

        return self._seasons


    def populate_config(self):
        url = settings.base_url + '/api/en/content/v1/web/config'
        r = self._store.s.get(url)
        return r.json()


    def _log_request(self, r):
        """Log (at the debug level) everything about a provided HTTP request.

        Note
        ----
        TODO: optional password filtering

        Parameters
        ----------
        r : requests.models.Response
            The handle of a Requests request.

        Returns
        -------
        bool
            True if successful

        Examples
        --------
        >>> r = self._store.s.get(url)
        >>> self._log_request(r)
        """
        request_dict = {}
        response_dict = {}
        if type(r) == requests.models.Response:
            request_dict['body'] = r.request.body
            request_dict['headers'] = dict(r.request.headers)
            request_dict['method'] = r.request.method
            request_dict['uri'] = r.request.url

            try:
                response_dict['body'] = r.json()
            except ValueError:
                # TODO: it would be nice handle XML too, but I have been unable
                # to find a solution within the standard library to convert XML
                # to a python object.
                response_dict['body'] = str(r.content)
            response_dict['headers'] = dict(r.headers)
            response_dict['status_code'] = r.status_code

        self.logger.debug('request:')
        try:
            self.logger.debug(json.dumps(request_dict, sort_keys=True, indent=4))
        except UnicodeDecodeError:  # python 2.7
            request_dict['body'] = 'BINARY DATA'
            self.logger.debug(json.dumps(request_dict, sort_keys=True, indent=4))

        self.logger.debug('response:')
        try:
            self.logger.debug(json.dumps(response_dict, sort_keys=True, indent=4))
        except UnicodeDecodeError:  # python 2.7
            response_dict['body'] = 'BINARY DATA'
            self.logger.debug(json.dumps(response_dict, sort_keys=True, indent=4))

        return True
    def login(self, username, password, force=False):
        """Login to NFL Game Pass.

        Parameters
        ----------
        username : str
            Your NFL Game Pass username.
        password : str
            The user's password.
        force : bool
            Skip checking if access is already granted, and instead always
            authenticate.

        Returns
        -------
        bool
            True if successful, False otherwise.

        Note
        ----
        A successful login does not necessarily mean that access to content is
        granted (i.e. has a valid subscription). Use ``subscription``
        to determine if a valid subscription (and thus access) is been granted.

        See Also
        --------
        ``subscription``
        """
        return self._auth.login(username, password, force)


    @property
    def subscription(self):
        """The subscription type.

        Returns
        -------
        str
            None if false.
        """

        if self._store.subscription is None:
            self.logger.debug('``subscription`` not set. attempting to populate')
            self._store.subscription = self._auth.get_subscription()
            self.logger.debug('``subscription`` ready')

        return self._store.subscription


    def refresh_tokens(self):
        """Refresh the ``access`` and ``refresh`` tokens to access content.

        Returns
        -------
        bool
            True if successful, False otherwise.

        Note
        ----
        TODO: Exception should be raised on failure so people can catch and
              attempt to login again
        """
        return self._auth.refresh_tokens()


    def m3u8_to_dict(self, manifest_url):
        """Return a dict of available bitrates and their respective stream. This
        is especially useful if you need to pass a URL to a player that doesn't
        support adaptive streaming."""
        streams = {}
        m3u8_header = {
            'Connection': 'keep-alive',
            'User-Agent': settings.user_agent
        }

        try:
            r = self._store.s.get(manifest_url)
            self._log_request(r)
            m3u8_manifest = r.content
        except ValueError:
            self.logger.error('m3u8_to_dict: server response is invalid')
            return None

        m3u8_obj = m3u8.loads(m3u8_manifest)
        for playlist in m3u8_obj.playlists:
            bitrate = int(playlist.stream_info.bandwidth) / 1000
            streams[bitrate] = manifest_url[:manifest_url.rfind('/manifest') + 1] + playlist.uri + '?' + manifest_url.split('?')[1] + '|' + urlencode(m3u8_header)

        return streams


    def is_redzone_on_air(self):
        """Return whether RedZone Live is currently broadcasting.

        Returns
        -------
        bool
            Returns True if RedZone Live is broadcasting, False otherwise.
        """
        url = self._store.gp_config['modules']['ROUTES_DATA_PROVIDERS']['redzone']

        try:
            r = self._store.s.get(url)
            self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('is_redzone_on_air: server response is invalid')
            return None

        try:
            if data['modules']['redZoneLive']['content']:
                return True
        except KeyError:
            self.logger.error('could not parse RedZoneLive data')
            return None

        return False


    def nfldate_to_datetime(self, nfldate, localize=False):
        """Return a datetime object from an NFL Game Pass date string.

        Parameters
        ----------
        nfldate : str
            The DIVA config URL that you need parsed.
        localize : bool
            Whether the datetime object should be localized.

        Returns
        -------
        datetime
            A datetime object when successful, None otherwise.
        """
        return self._utils.nfldate_to_datetime(nfldate, localize)


class season(object):
    def __init__(self, pigskin_obj, season):
        self._pigskin = pigskin_obj
        self._data = self._pigskin._data
        self._season = season

        self.logger = logging.getLogger(__name__)
        self._teams = None
        self._weeks = None


    @property
    def teams(self):
        """An OrderedDict of teams and their team objects.

        Returns
        -------
        OrderedDict
            With the keys as the team name (e.g. "Vikings") and value as the
            team object.
        """
        if self._teams is None:
            self.logger.debug('``teams`` not set. attempting to populate')
            teams_dict = self._data.get_teams(self._season)

            teams_dict = OrderedDict((t, team(self, teams_dict[t])) for t in teams_dict)

            self._teams = teams_dict
            self.logger.debug('``teams`` ready')

        return self._teams


    @property
    def weeks(self):
        """An OrderedDict of weeks and their week objects.

        Returns
        -------
        OrderedDict
            With the keys ``pre``, ``reg``, and ``post``. Each is an OrderedDict
            with the week number as the key and a week object as the value.
        """
        if self._weeks is None:
            self.logger.debug('``weeks`` not set. attempting to populate')
            weeks_dict = self._data.get_weeks(self._season)

            for st in weeks_dict:
                weeks_dict[st] = OrderedDict((w, week(self, st, w, weeks_dict[st][w])) for w in weeks_dict[st])

            self._weeks = weeks_dict
            self.logger.debug('``weeks`` ready')

        return self._weeks


class team(object):
    def __init__(self, season_obj, team_info):
        self._pigskin = season_obj._pigskin
        self._data = self._pigskin._data
        self._season = season_obj._season
        self._team_info = team_info
        self._games = None

        self.logger = logging.getLogger(__name__)


    @property
    def abbr(self):
        """The team's abbreviation (e.g. GBP).

        Returns
        -------
        str
        """
        return self._team_info['abbr']


    @property
    def city(self):
        """The name team's home city (e.g. Houston).

        Returns
        -------
        str
        """
        return self._team_info['city']


    @property
    def games(self):
        """An OrderedDict of weeks and their week objects.

        Returns
        -------
        OrderedDict
            With the keys ``pre``, ``reg``, and ``post``. Each is an OrderedDict
            with the game name (e.g. Packers@Bears) and a game object as the
            value.

        TODO
        ----
        The game class currently does not contain information about the week it
        belongs to.
        """
        # NOTE: Currently this only fetches once.
        if self._games is None:
            self.logger.debug('``games`` not set. attempting to populate')

            games_dict = self._data.get_team_games(self.name, self._season)
            for st in games_dict:
                games_dict[st] = OrderedDict((g, game(self, games_dict[st][g])) for g in games_dict[st])

            self._games = games_dict
            self.logger.debug('``games`` ready')

        return self._games


    # TODO: add logo
    #@property
    #def logo(self):
    #    """A url for the team's logo.

    #    Returns
    #    -------
    #    str
    #    """
    #    return self._team_info['logo']


    @property
    def name(self):
        """The name of the team (e.g. Bears).

        Returns
        -------
        str
        """
        return self._team_info['name']


class week(object):
    def __init__(self, season_obj, season_type, week, desc):
        self._pigskin = season_obj._pigskin
        self._data = self._pigskin._data
        self._season = season_obj._season
        self._season_type = season_type
        self._week = week
        self._description = desc

        self.logger = logging.getLogger(__name__)
        self._games = None


    @property
    def desc(self):
        """The description of a week if it's special (such as Hall of Fame,
            Super Bowl, etc).

        Returns
        -------
        str
            The description of the week if it's special. Otherwise an empty string.
        """
        return self._description


    @property
    def games(self):
        # NOTE: Currently this only fetches once.
        # TODO: caching: any data that is in the past, won't change, data in
        # future weeks won't change any time soon. So, if what is requested is
        # /not/ the current week and season, then we can safely return a cached
        # result. If it is the current week, then we should fetch a fresh copy.
        # However, we don't want a request to get_current_season_and_week()
        # every time. That info should be grabbed from the parent pigskin
        # instance, where it is cached.
        if self._games is None:
            self.logger.debug('``games`` not set. attempting to populate')

            games_dict = self._data.get_week_games(self._season, self._season_type, self._week)
            games_dict = OrderedDict((g, game(self, games_dict[g])) for g in games_dict)
            self._games = games_dict
            self.logger.debug('``games`` ready')

        return self._games


class game(object):
    def __init__(self, week_obj, game_info):
        self._pigskin = week_obj._pigskin
        self._data = self._pigskin._data
        #self._season = season
        #self._season_type = season_type
        #self._week = week
        #self._description = desc
        # TODO: add reference to week object; this helps especially teams.games
        #       to know what week this game belongs to
        self._game_info = game_info

        self.logger = logging.getLogger(__name__)
        self._versions = None


    @property
    def away(self):
        """Information about the away team.

        Returns
        -------
        dict
            With the keys ``name``, ``city``, and ``points``.
        """
        # TODO: perhaps it's better to return a ``team`` object here with all
        # team info and move the points to different property.
        return self._game_info['away']


    @property
    def city(self):
        """The city the game is played in.

        Returns
        -------
        str
        """
        return self._game_info['city']


    @property
    def home(self):
        """Information about the home team.

        Returns
        -------
        dict
            With the keys ``name``, ``city``, and ``points``.
        """
        # TODO: perhaps it's better to return a ``team`` object here with all
        # team info and move the points to different property.
        return self._game_info['home']


    @property
    def phase(self):
        return self._game_info['phase']


    @property
    def stadium(self):
        """The stadium/field the game is played at.

        Returns
        -------
        str
        """
        return self._game_info['stadium']


    @property
    def start_time(self):
        """The UTC start date and time of the game.

        Returns
        -------
        str

        See Also
        --------
        nfldate_to_datetime()
        """
        return self._game_info['start_time']


    @property
    def versions(self):
        """Stream versions available for a game.

        Returns
        -------
        dict
            Possible keys are ``full``, ``condensed``, and ``coach``. The values
            are ``stream`` objects.
        """
        if self._versions is None:
            self.logger.debug('``versions`` not set. attempting to populate')
            # TODO: OrderedDict
            versions_dict = OrderedDict((v, version(self, v, self._game_info['versions'][v])) for v in self._game_info['versions'])
            self._versions = versions_dict
            self.logger.debug('``versions`` ready')

        return self._versions


class version(object):
    def __init__(self, game_obj, desc_key, video_id):
        self._pigskin = game_obj._pigskin
        self._video = self._pigskin._video
        self._desc_key = desc_key
        self._video_id = video_id

        self.logger = logging.getLogger(__name__)
        self._descriptions = {'full': 'Full Game', 'condensed': 'Condensed Game', 'coach': 'Coaches Tape'}
        self._streams = None


    @property
    def desc(self):
        """The description of a game version.

        Returns
        -------
        str
            The description of the game version.
        """
        try:
            return self._descriptions[self._desc_key]
        except KeyError:
            return self._desc_key


    @property
    def streams(self):
        if self._streams is None:
            self.logger.debug('``streams`` not set. attempting to populate')
            # TODO: support live streams
            self._streams = self._video.get_game_streams(self._video_id, live=False)
            self.logger.debug('``streams`` ready')

        return self._streams
