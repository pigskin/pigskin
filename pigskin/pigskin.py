"""
A Python library for NFL Game Pass
"""
import uuid
import sys
import json
import logging
from collections import OrderedDict
import xml.etree.ElementTree as ET
try:
    from urllib.parse import urlencode
except ImportError:  # Python 2.7
    from urllib import urlencode
try:
    from datetime import datetime, timezone
except ImportError:  # Python 2.7
    import calendar
    from datetime import datetime, timedelta

import requests
import m3u8

from . import settings
from .europe.auth import auth
from .europe.data import data


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

        self._seasons = None
        self._current = None
        self.nfln_shows = {}
        self.episode_list = []

        self._auth = auth(self._store)
        self._data = data(self._store)

        self.logger.debug('Python Version: %s' % sys.version)


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
            self._seasons = OrderedDict((s, season(self._data, s)) for s in seasons_list)
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


    def make_request(self, url, method, params=None, payload=None, headers=None):
        """Make an HTTP request. Return the response."""
        self.logger.debug('Request URL: %s' % url)
        self.logger.debug('Method: %s' % method)
        if params:
            self.logger.debug('Params: %s' % params)
        if payload:
            if 'password' in payload:
                password = payload['password']
                payload['password'] = 'xxxxxxxxxxxx'
            self.logger.debug('Payload: %s' % payload)
            if 'password' in payload:
                payload['password'] = password
        if headers:
            self.logger.debug('Headers: %s' % headers)

        # requests session implements connection pooling, after being idle for
        # some time the connection might be closed server side.
        # In case it's the servers being very slow, the timeout should fail fast
        # and retry with longer timeout.
        failed = False
        for t in [3, 22]:
            try:
                if method == 'get':
                    req = self._store.s.get(url, params=params, headers=headers, timeout=t)
                elif method == 'put':
                    req = self._store.s.put(url, params=params, data=payload, headers=headers, timeout=t)
                else:  # post
                    req = self._store.s.post(url, params=params, data=payload, headers=headers, timeout=t)
                # We made it without error, exit the loop
                break
            except requests.Timeout:
                self.logger.warning('Timeout condition occurred after %i seconds' % t)
                if failed:
                    # failed twice while sending request
                    # TODO: this should be raised so the user can be informed.
                    pass
                else:
                    failed = True
            except:
                # something else went wrong, not a timeout
                # TODO: raise this
                pass

        self.logger.debug('Response code: %s' % req.status_code)
        self.logger.debug('Response: %s' % req.content)

        return self.parse_response(req)

    def parse_response(self, req):
        """Try to load JSON data into dict and raise potential errors."""
        try:
            response = json.loads(req.content)
        except ValueError:  # if response is not json
            response = req.content

        if isinstance(response, dict):
            for key in response.keys():
                if key.lower() == 'message':
                    if response[key]:  # raise all messages as GamePassError if message is not empty
                        raise self.GamePassError(response[key])

        return response


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
        granted (i.e. has a valid subscription). Use ``check_for_subscription()``
        to determine if access has been granted.

        See Also
        --------
        ``check_for_subscription()``
        """
        return self._auth.login(username, password, force)


    def check_for_subscription(self):
        """Check if the user has a valid subscription.

        Returns
        -------
        bool
            Returns True on the presence of a subscription, False otherwise.

        Note
        ----
        There are different types of subscriptions.
        TODO: This (or another function) should return the type of subscription.

        See Also
        --------
        ``login()``
        """
        return self._auth.check_for_subscription()


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


    def get_team_games(self, season, team):
        """Get the raw game data for a given season (year) and team.

        Parameters
        ----------
        season : str or int
            The season can be provided as either a ``str`` or ``int``.
        team : str
            Accepts the team ``seo_name``. For a list of team seo names, see
            self._store.gp_config['modules']['ROUTES_DATA_PROVIDERS']['team_detail'].

        Returns
        -------
        list
            of dicts with the metadata for each game

        Note
        ----
        TODO: the data returned really should be normalized, rather than a
              (nearly) straight dump of the raw data.
        TODO: currently only the current season is supported
        TODO: create a ``get_team_seo_name()`` helper

        See Also
        --------
        ``get_current_season_and_week()``

        Examples
        --------
        >>> games = gp.get_team_games(2018, '49ers')
        >>> print(games[2]['weekName'])
        Preseason Week 3
        """
        url = self._store.gp_config['modules']['ROUTES_DATA_PROVIDERS']['team_detail']
        url = url.replace(':team', team)
        games = []

        # TODO: bail if ``season`` isn't the current season

        try:
            r = self._store.s.get(url)
            self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('get_team_games: server response is invalid')
            return []
        except Exception as e:
            raise e

        try:
            # currently, only data for the current season is available
            games = [x for x in data['modules']['gamesCurrentSeason']['content']]
            games = sorted(games, key=lambda x: x['gameDateTimeUtc'])
        except KeyError:
            self.logger.error('could not parse/build the team_games list')
            return []
        except Exception as e:
            raise e

        return games


    def get_game_versions(self, game_id, season):
        """Return a dict of available game versions (full, condensed, coaches,
        etc) for a game.

        Parameters
        ----------
        season : str or int
            The season can be provided as either a ``str`` or ``int``.
        game_id : str or int
            A game's ``game_id`` can be found in the metadata returned by either
            ``get_games()`` or ``get_team_games()``.

        Returns
        -------
        dict
            with the ``key`` as game version and its ``value`` being the
            ``video_id`` of the corresponding stream.

        NOTE
        ----
        TODO: it seems that they return a schload of info with get_games(),
              including the video_id. Verify that they actually provide that for
              all games, and perhaps this entire function can be retired.

        See Also
        --------
        ``get_games()``
        ``get_team_games()``

        Examples
        --------
        >>> versions = gp.get_game_versions('2017090700', '2017')
        >>> print(versions.keys())
        dict_keys(['Coach film', 'Condensed game', 'Game video'])
        """
        url = self._store.gp_config['modules']['ROUTES_DATA_PROVIDERS']['game_page']
        url = url.replace(':gameslug', str(game_id)).replace(':season', str(season))
        versions = {}

        try:
            r = self._store.s.get(url)
            self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('get_game_versions: server response is invalid')
            return {}
        except Exception as e:
            raise e

        try:
            game_data = data['modules']['singlegame']['content'][0]
            for key in game_data:
                try:
                    versions[game_data[key]['kind']] = game_data[key]['videoId']
                except (KeyError, TypeError):
                    pass
        except KeyError:
            self.logger.error('could not parse/build the game versions data')
            return {}
        except Exception as e:
            raise e

        self.logger.debug('Game versions found for {0}: {1}'.format(game_id, ', '.join(versions.keys())))
        return versions


    def get_nfl_network_streams(self):
        """Return a dict of available stream formats and their URLs for NFL
        Network Live.

        Returns
        -------
        dict
            with the stream format (hls, chromecast, etc) as the key and the
            stream content_url as the value.
        """
        url = self._store.gp_config['modules']['ROUTES_DATA_PROVIDERS']['network']
        diva_config_url = self._store.gp_config['modules']['DIVA']['HTML5']['SETTINGS']['Live24x7']
        self.refresh_tokens()  # we aren't even told about the live video unless we have up-to-date tokens
        streams = {}

        try:
            r = self._store.s.get(url)
            self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('get_nfl_network_streams: server response is invalid')
            return {}
        except Exception as e:
            raise e

        try:
            video_id = data['modules']['networkLiveVideo']['content'][0]['videoId']
        except KeyError:
            # TODO: move refresh_tokens() here and retry
            self.logger.error('could not parse the nfl network video_id data')
            return {}
        except Exception as e:
            raise e

        streams = self._get_diva_streams(video_id=video_id, diva_config_url=diva_config_url)
        return streams


    def get_redzone_streams(self):
        """Return a dict of available stream formats and their URLs for NFL Red
        Zone.

        Returns
        -------
        dict
            with the stream format (hls, chromecast, etc) as the key and the
            stream content_url as the value.
        """
        # TODO: do we need refresh_tokens() like get_nfl_network_streams()? likely
        url = self._store.gp_config['modules']['ROUTES_DATA_PROVIDERS']['redzone']
        diva_config_url = self._store.gp_config['modules']['DIVA']['HTML5']['SETTINGS']['Live24x7']
        streams = {}

        try:
            r = self._store.s.get(url)
            self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('get_redzone_streams: server response is invalid')
            return {}
        except Exception as e:
            raise e

        try:
            video_id = data['modules']['redZoneLive']['content'][0]['videoId']
        except (KeyError, IndexError):
            self.logger.error('could not parse the redzone video_id data')
            return {}
        except Exception as e:
            raise e

        streams = self._get_diva_streams(video_id=video_id, diva_config_url=diva_config_url)
        return streams


    def get_game_streams(self, video_id, live=False):
        """Return a dict of available stream formats and their URLs for a game.

        Parameters
        ----------
        video_id : str
            The video_id of a game
        live : bool
            Whether the game is live or not

        Returns
        -------
        dict
            with the stream format (hls, chromecast, etc) as the key and the
            stream content_url as the value.

        See Also
        --------
        ``get_game_versions()``

        Examples
        --------
        >>> games = gp.get_games('2017', 'reg', '1')
        >>> versions = gp.get_game_versions(games[1]['gameId'], '2017')
        >>> streams = gp.get_game_streams(versions['Condensed game'])
        >>> print(streams.keys())
        dict_keys(['hls', 'chromecast', 'connecttv'])
        """
        diva_config_url = self._store.gp_config['modules']['DIVA']['HTML5']['SETTINGS']['VodNoData']
        if live:
            diva_config_url = self._store.gp_config['modules']['DIVA']['HTML5']['SETTINGS']['LiveNoData']

        streams = self._get_diva_streams(video_id=video_id, diva_config_url=diva_config_url)
        return streams


    def _get_diva_config(self, diva_config_url):
        """Return the parsed DIVA config.

        Parameters
        ----------
        diva_config_url : str
            The DIVA config URL that you need parsed.

        Returns
        -------
        dict
            with the keys ``processing_url`` and ``video_data_id`` set.
        """
        url = diva_config_url.replace('device', 'html5')
        diva_config = {}

        try:
            r = self._store.s.get(url)
            self._log_request(r)
            data = r.content
        except Exception as e:
            raise e

        try:
            data_xml = ET.fromstring(data)
        except (ET.ParseError, TypeError):
            self.logger.error('_get_diva_config: server response is invalid')
            return {}

        try:
            diva_config['processing_url'] = data_xml.find(".//parameter[@name='processingUrlCallPath']").get('value')
            diva_config['video_data_url'] = data_xml.find(".//parameter[@name='videoDataPath']").get('value')
        except AttributeError:
            self.logger.error('_get_diva_config: unable to parse the diva XML')
            return {}

        return diva_config


    def _get_diva_streams(self, video_id, diva_config_url):
        """Return a dict of available stream formats and their URLs.

        Parameters
        ----------
        video_id : str
            The video_id of a game/show
        diva_config_url : str
            The DIVA config URL that you need parsed.

        Returns
        -------
        dict
            with the stream format (hls, chromecast, etc) as the key and the
            stream content_url as the value.
        """
        streams = {}
        self.refresh_tokens() # determine when we actually need this. I'm guessing when we post

        diva_config = self._get_diva_config(diva_config_url)
        try:
            video_data_url = diva_config['video_data_url'].replace('{V.ID}', video_id)
            processing_url = diva_config['processing_url']
        except KeyError:
            self.logger.error('_get_diva_streams: diva config was not set!')
            return {}

        try:
            r = self._store.s.get(video_data_url)
            self._log_request(r)
            akamai_data = r.content
        except Exception as e:
            raise e

        try:
            akamai_xml = ET.fromstring(akamai_data)
        except (ET.ParseError, TypeError):
            self.logger.error('_get_diva_streams: server response is invalid')
            return {}

        # TODO: is this how the service even works anymore? It seems arcane.
        # TODO: allow user-agent override
        m3u8_header = {
            'Connection': 'keep-alive',
            'User-Agent': settings.user_agent
        }
        for vs in akamai_xml.iter('videoSource'):
            try:
                vs_format = vs.attrib['format'].lower()
                vs_url = vs.find('uri').text
            except (KeyError, AttributeError):
                continue

            payload = self._build_processing_url_payload(video_id, vs_url)

            try:
                r = self._store.s.post(url=processing_url, data=payload)
                self._log_request(r)
                data = r.json()
            except ValueError:
                self.logger.error('_get_diva_streams: server response is invalid')
                continue
            except Exception as e:
                raise e

            streams[vs_format] = data['ContentUrl'] + '|' + urlencode(m3u8_header)

        return streams


    def _build_processing_url_payload(self, video_id, vs_url):
        """Return the payload needed to request a content URL from a
        processing_url.

        Parameters
        ----------
        video_id : str
            The video_id of a game/show
        vs_url : str
            The URL to a given video source

        Returns
        -------
        str
            a JSON string (suitable for passing as a post payload)

        See Also
        --------
        ``_get_diva_streams()``
        """
        # TODO: take a look at the official client and determine if we can move
        # the unique_id gen to __init__, login(), or refresh_tokens() rather
        # than regenerating for each request.
        unique_id = str(uuid.uuid4())
        # TODO: This does not look right, and doesn't even use the username
        other = '{0}|{1}|web|{1}|undefined|{2}'.format(unique_id, self._store.access_token, settings.user_agent, self._store.username)
        post_data = {
            'Type': '1',
            'User': '',
            'VideoId': video_id,
            'VideoSource': vs_url,
            'VideoKind': 'Video',
            'AssetState': '3',
            'PlayerType': 'HTML5',
            'other': other,
        }

        payload = json.dumps(post_data)
        return payload


    def m3u8_to_dict(self, manifest_url):
        """Return a dict of available bitrates and their respective stream. This
        is especially useful if you need to pass a URL to a player that doesn't
        support adaptive streaming."""
        streams = {}
        m3u8_header = {
            'Connection': 'keep-alive',
            'User-Agent': settings.user_agent
        }

        m3u8_manifest = self.make_request(manifest_url, 'get')
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
        except Exception as e:
            raise e

        try:
            if data['modules']['redZoneLive']['content']:
                return True
        except KeyError:
            self.logger.error('could not parse RedZoneLive data')
            return None
        except Exception as e:
            raise e

        return False


    def parse_shows(self):
        """Dynamically parse the NFL Network shows into a dict."""
        show_dict = {}
        self.episode_list = []

        # NFL Network shows
        url = self._store.gp_config['modules']['API']['NETWORK_PROGRAMS']
        response = self.make_request(url, 'get')
        current_season = self.get_current_season_and_week()['season']

        for show in response['modules']['programs']:
            # Unfortunately, the 'seasons' list for each show cannot be trusted.
            # So we loop over every episode for every show to build the list.
            # TODO: this causes a lot of network traffic and slows down init
            #       quite a bit. Would be nice to have a better workaround.
            request_url = self._store.gp_config['modules']['API']['NETWORK_EPISODES']
            episodes_url = request_url.replace(':seasonSlug/', '').replace(':tvShowSlug', show['slug'])
            episodes_data = self.make_request(episodes_url, 'get')['modules']['archive']['content']

            # 'season' is often left unset. It's impossible to know for sure,
            # but the year of the current Season seems like a sane best guess.
            season_list = set([episode['season'].replace('season-', '')
                               if episode['season'] else current_season
                               for episode in episodes_data])

            show_dict[show['title']] = season_list

            # Adding NFL-Network as a List of dictionary containing oher dictionaries.
            # episode_thumbnail = {videoId, thumbnail}
            # episode_id_dict = {episodename, episode_thumbnail{}}
            # episode_season_dict = {episode_season, episode_id_dict{}}
            # show_season_dict = {show_title, episode_season_dict{}}
            # The Function returns all Season and Episodes
            for episode in episodes_data:
                episode_thumbnail = {}
                episode_id_dict = {}
                episode_season_dict = {}
                show_season_dict = {}
                episode_name = episode['title']
                episode_id = episode['videoId']
                if episode['season']:
                    episode_season = episode['season'].replace('season-', '')
                else:
                    episode_season = current_season
                # Using Episode Thumbnail if not present use theire corresponding Show Thumbnail
                if episode['videoThumbnail']['templateUrl']:
                    episode_thumbnail[episode_id] = episode['videoThumbnail']['templateUrl']
                else:
                    episode_thumbnail[episode_id] = show['thumbnail']['templateUrl']
                episode_id_dict[episode_name] = episode_thumbnail
                episode_season_dict[episode_season] = episode_id_dict
                show_season_dict[show['title']] = episode_season_dict
                self.episode_list.append(show_season_dict)

        # Adding RedZone as a List of dictionary containing oher dictionaries.
        # episode_thumbnail = {videoId, thumbnail}
        # episode_id_dict = {episodename, episode_thumbnail{}}
        # episode_season_dict = {episode_season, episode_id_dict{}}
        # show_season_dict = {show_title, episode_season_dict{}}
        # The Function returns all Season and Episodes
        url = self._store.gp_config['modules']['ROUTES_DATA_PROVIDERS']['redzone']
        response = self.make_request(url, 'get')

        season_list = []
        for episode in response['modules']['redZoneVod']['content']:
            season_name = episode['season'].replace('season-', '')
            season_list.append(season_name)
            episode_thumbnail = {}
            episode_id_dict = {}
            episode_season_dict = {}
            show_season_dict = {}
            episode_name = episode['title']
            episode_id = episode['videoId']
            if episode['season']:
                episode_season = episode['season'].replace('season-', '')
            else:
                episode_season = current_season
            # Using Episode Thumbnail if not present use theire corresponding Show Thumbnail
            if episode['videoThumbnail']['templateUrl']:
                episode_thumbnail[episode_id] = episode['videoThumbnail']['templateUrl']
            else:
                episode_thumbnail[episode_id] = ''
            episode_id_dict[episode_name] = episode_thumbnail
            episode_season_dict[episode_season] = episode_id_dict
            show_season_dict['RedZone'] = episode_season_dict
            self.episode_list.append(show_season_dict)

        show_dict['RedZone'] = season_list
        self.nfln_shows.update(show_dict)

    def get_shows(self, season):
        """Return a list of all shows for a season."""
        seasons_shows = []

        for show_name, years in self.nfln_shows.items():
            if season in years:
                seasons_shows.append(show_name)

        return sorted(seasons_shows)

    def get_shows_episodes(self, show_name, season=None):
        """Return a list of episodes for a show. Return empty list if none are
        found or if an error occurs."""
        # Create a List of all games related to a specific show_name and a season.
        # The returning List contains episode name, episode id and episode thumbnail
        episodes_data = []
        for episode in self.episode_list:
            for dict_show_name, episode_season_dict in episode.items():
                if dict_show_name == show_name:
                    for episode_season, episode_id_dict in episode_season_dict.items():
                        if episode_season == season:
                            episodes_data.append(episode_id_dict)

        return episodes_data


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
        nfldate_format = '%Y-%m-%dT%H:%M:%S.%fZ'

        try:
            dt_utc = datetime.strptime(nfldate, nfldate_format)
        except ValueError:
            self.logger.error('unable to parse the nfldate string')
            return None

        if localize:
            try:
                return dt_utc.replace(tzinfo=timezone.utc).astimezone(tz=None)
            except NameError:  # Python 2.7
                return self.utc_to_local(dt_utc)
            except Exception:
                self.logger.error('unable to localize the nfl datetime object')
                return None

        return dt_utc


    @staticmethod
    def utc_to_local(dt_utc):
        """Convert UTC time to local time."""
        # get integer timestamp to avoid precision lost
        timestamp = calendar.timegm(dt_utc.timetuple())
        dt_local = datetime.fromtimestamp(timestamp)
        assert dt_utc.resolution >= timedelta(microseconds=1)
        return dt_local.replace(microsecond=dt_utc.microsecond)


class season(object):
    def __init__(self, data, season):
        self._data = data
        self._season = season

        self.logger = logging.getLogger(__name__)
        self._weeks = None


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
                weeks_dict[st] = OrderedDict((w, week(self._data, self._season, st, w, weeks_dict[st][w])) for w in weeks_dict[st])

            self._weeks = weeks_dict
            self.logger.debug('``weeks`` ready')

        return self._weeks


class week(object):
    def __init__(self, data, season, season_type, week, desc):
        self._data = data
        self._season = season
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

            games_dict = self._data.get_games(self._season, self._season_type, self._week)
            games_dict = OrderedDict((g, game(self._data, games_dict[g])) for g in games_dict)
            self._games = games_dict
            self.logger.debug('``games`` ready')

        return self._games


class game(object):
    def __init__(self, data, game_info):
        self._data = data
        #self._season = season
        #self._season_type = season_type
        #self._week = week
        #self._description = desc
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
        if self._versions is None:
            self.logger.debug('``versions`` not set. attempting to populate')
            self._versions = {}
            self.logger.debug('``versions`` ready')

        return self._versions
