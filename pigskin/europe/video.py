import logging
import uuid
import json
import defusedxml.ElementTree as ET
from urllib.parse import urlencode
from .. import settings


class video(object):
    def __init__(self, pigskin_obj):
        self._pigskin = pigskin_obj
        self._store = self._pigskin._store
        self._auth = self._pigskin._auth
        self.logger = logging.getLogger(__name__)


    def get_broadcast_streams(self, name):
        """Return a dict of available stream formats and their URLs for a
        broadcast.

        Parameters
        ----------
        name : str
            The name of the broadcast. Currently accepts only ``nfl_network``
            and ``redzone``.

        Returns
        -------
        dict
            with the stream format (hls, chromecast, etc) as the key and the
            stream content_url as the value. None if there was a failure.
        """
        if name == 'nfl_network':
            return self._get_nfl_network_streams()
        elif name == 'redzone':
            return self._get_redzone_streams()
        else:
            return None


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
            stream content_url as the value. None if there was a failure.
        """
        diva_config_url = self._store.gp_config['modules']['DIVA']['HTML5']['SETTINGS']['VodNoData']
        if live:
            diva_config_url = self._store.gp_config['modules']['DIVA']['HTML5']['SETTINGS']['LiveNoData']

        streams = self._get_diva_streams(video_id=video_id, diva_config_url=diva_config_url)
        return streams


    def is_on_air(self, name):
        """Return whether a live broadcast is currently on the air.

        Parameters
        ----------
        name : str
            The name of the broadcast. Currently accepts only ``nfl_network``
            and ``redzone``.

        Returns
        -------
        bool
            Returns True if it is broadcasting, False if not, and None is there
            was a failure.
        """
        if name == 'nfl_network':
            # TODO: find a way to determine if NFL Network is broadcasting
            return True
        elif name == 'redzone':
            return self._is_redzone_on_air()
        else:
            return None


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
        other = '{0}|{1}|web|{2}|undefined|{3}'.format(unique_id, self._store.access_token, settings.user_agent, self._store.username)

        # NOTE: the official web UI posts a bit more data, but it seems to have
        #       no impact on the response.
        post_data = {
            'AssetState': 3,
            'Other': other,
            'PlayerType': 'HTML5',
            'Type': 1,
            'User': '',
            'VideoId': video_id,
            'VideoKind': '',
            'VideoSource': vs_url,
        }

        payload = json.dumps(post_data)
        return payload


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
            #self._log_request(r)
            data = r.text
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
        self._auth.refresh_tokens() # determine when we actually need this. I'm guessing when we post

        diva_config = self._get_diva_config(diva_config_url)
        try:
            video_data_url = diva_config['video_data_url'].replace('{V.ID}', video_id)
            processing_url = diva_config['processing_url']
        except KeyError:
            self.logger.error('_get_diva_streams: diva config was not set!')
            return {}

        try:
            r = self._store.s.get(video_data_url)
            #self._log_request(r)
            akamai_data = r.text
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
                vs_format = vs.attrib['name'].lower()
                vs_url = vs.find('uri').text
            except (KeyError, AttributeError):
                self.logger.warn('unable to extract stream info from akamai videoSource; skipping')
                continue

            payload = self._build_processing_url_payload(video_id, vs_url)

            try:
                r = self._store.s.post(url=processing_url, data=payload)
                #self._log_request(r)
                data = r.json()
                content_url = data['ContentUrl']
            except (KeyError, TypeError, ValueError):
                self.logger.error('_get_diva_streams: server response is invalid')
                continue

            if content_url:
                streams[vs_format] = content_url + '|' + urlencode(m3u8_header)
            else:
                self.logger.warn('_get_diva_streams: empty content url for videoSource')

        return streams


    def _get_nfl_network_streams(self):
        """Return a dict of available stream formats and their URLs for NFL
        Network Live.

        Returns
        -------
        dict
            with the stream format (hls, chromecast, etc) as the key and the
            stream content_url as the value. None if there was a failure.
        """
        url = self._store.gp_config['modules']['ROUTES_DATA_PROVIDERS']['network']
        diva_config_url = self._store.gp_config['modules']['DIVA']['HTML5']['SETTINGS']['Live24x7']
        self._auth.refresh_tokens()  # we aren't even told about the live video unless we have up-to-date tokens

        try:
            r = self._store.s.get(url)
            #self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('get_nfl_network_streams: server response is invalid')
            return None

        try:
            video_id = data['modules']['networkLiveVideo']['content'][0]['videoId']
        except KeyError:
            # TODO: move refresh_tokens() here and retry
            self.logger.error('could not parse the nfl network video_id data')
            return None

        streams = self._get_diva_streams(video_id=video_id, diva_config_url=diva_config_url)
        return streams


    def _get_redzone_streams(self):
        """Return a dict of available stream formats and their URLs for NFL Red
        Zone.

        Returns
        -------
        dict
            with the stream format (hls, chromecast, etc) as the key and the
            stream content_url as the value. None if there was a failure.
        """
        # TODO: do we need refresh_tokens() like get_nfl_network_streams()? likely
        url = self._store.gp_config['modules']['ROUTES_DATA_PROVIDERS']['redzone']
        diva_config_url = self._store.gp_config['modules']['DIVA']['HTML5']['SETTINGS']['Live24x7']

        try:
            r = self._store.s.get(url)
            #self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('get_redzone_streams: server response is invalid')
            return None

        try:
            video_id = data['modules']['redZoneLive']['content'][0]['videoId']
        except (KeyError, IndexError):
            self.logger.error('could not parse the redzone video_id data')
            return None

        streams = self._get_diva_streams(video_id=video_id, diva_config_url=diva_config_url)
        return streams


    def _is_redzone_on_air(self):
        """Is RedZone Live broadcasting.

        Returns
        -------
        bool
            Returns True if RedZone Live is broadcasting, False otherwise.
        """
        url = self._store.gp_config['modules']['ROUTES_DATA_PROVIDERS']['redzone']

        try:
            r = self._store.s.get(url)
            #self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('_is_redzone_on_air: server response is invalid')
            return None

        try:
            if data['modules']['redZoneLive']['content']:
                return True
        except KeyError:
            self.logger.error('could not parse RedZoneLive data')
            return None

        return False
