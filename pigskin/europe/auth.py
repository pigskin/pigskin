import logging
from .. import settings

class auth(object):
    def __init__(self, pigskin_obj):
        self._pigskin = pigskin_obj
        self._store = self._pigskin._store
        self.logger = logging.getLogger(__name__)


    def get_subscription(self):
        """Get the subscription (if any) of the user."""
        url = self._store.gp_config['modules']['API']['USER_ACCOUNT']
        headers = {'Authorization': 'Bearer {0}'.format(self._store.access_token)}

        try:
            r = self._store.s.get(url, headers=headers)
            #self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('get_subscription: unable to parse server response')
            return None

        try:
            # TODO: if multiple subscriptions are found, return a list of them,
            # though I have no idea if this actually happens in practice.
            return data['subscriptions'][0]['productTag']
        except KeyError:
            self.logger.error('No active NFL Game Pass Europe subscription was found.')
            return None


    def login(self, username, password, force=False):
        """Login to NFL Game Pass Europe."""
        # if the user already has access, just skip the entire auth process
        if not force:
            if self._store.subscription:
                self.logger.debug('No need to login; the user already has access.')
                return True

        for auth in [self._gp_auth, self._gigya_auth]:
            self.logger.debug('Trying {0} authentication.'.format(auth.__name__))
            data = auth(username, password)
            try:
                self._store.username = username
                # TODO: are these tokens provided for valid accounts without a subscription?
                self._store.access_token = data['access_token']
                self._store.refresh_token = data['refresh_token']
            except KeyError:
                self.logger.error('Could not acquire GP tokens')
                self._store.access_token = None
                self._store.refresh_token = None
            else:
                self.logger.debug('login was successful')
                return True

        self.logger.error('login failed')
        return False


    def refresh_tokens(self):
        """Refresh the tokens needed to access content."""
        url = self._store.gp_config['modules']['API']['REFRESH_TOKEN']
        post_data = {
            'client_id': self._store.gp_config['modules']['API']['CLIENT_ID'],
            'refresh_token': self._store.refresh_token,
            'grant_type': 'refresh_token'
        }

        try:
            r = self._store.s.post(url, data=post_data)
            #self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('token refresh: server response is invalid')
            return False

        try:
            self._store.access_token = data['access_token']
            self._store.refresh_token = data['refresh_token']
        except KeyError:
            self.logger.error('could not find GP tokens to refresh')
            return False

        # TODO: check for status codes, just in case

        self.logger.debug('successfully refreshed tokens')
        return True


    def _gigya_auth(self, username, password):
        """Authenticate to Game Pass by first going through Gigya's
        authentication servers.

        Parameters
        ----------
        username : str
            Your NFL Game Pass username.
        password : str
            The user's password.

        Returns
        -------
        dict
            A dict containing the authentication data; empty if there's an error

        See Also
        --------
        ``login()``
        ``_gp_auth()``
        """
        url = settings.gigya_auth_url
        api_key = self._store.gp_config['modules']['GIGYA']['JAVASCRIPT_API_URL'].split('apiKey=')[1]
        post_data = {
            'apiKey' : api_key,
            'loginID' : username,
            'includeUserInfo': 'false',
            'password' : password
        }

        try:
            r = self._store.s.post(url, data=post_data)
            #self._log_request(r)
            gigya_data = r.json()
        except ValueError:
            self.logger.error('_gigya_auth: server response is invalid')
            return {}

        # make sure auth data is there
        for key in ['UID', 'UIDSignature', 'signatureTimestamp']:
            if not gigya_data.get(key):
                self.logger.error('could not parse gigya auth response')
                return {}

        # now that we have our gigya keys, auth against GP servers
        data = self._gp_auth(username, password, gigya_data)

        return data


    def _gp_auth(self, username, password, gigya_data=False):
        """Authenticate to the Game Pass servers.

        Parameters
        ----------
        gigya : dict
            The data needed to authenticate using gigya auth data.

        Returns
        -------
        dict
            A dict containing the authentication data; empty if there's an error

        See Also
        --------
        ``_gigya_auth()``
        ``login()``
        """
        url = self._store.gp_config['modules']['API']['LOGIN']

        post_data = {
            'client_id': self._store.gp_config['modules']['API']['CLIENT_ID'],
            'username': username,
            'password': password,
            'grant_type': 'password'
        }

        if gigya_data:
            # TODO: audit if in fact all these fields are needed
            post_data = {
                'client_id' : self._store.gp_config['modules']['API']['CLIENT_ID'],
                'uuid' : gigya_data['UID'],
                'signature' : gigya_data['UIDSignature'],
                'ts' : gigya_data['signatureTimestamp'],
                'device_type' : 'web',
                'username' : username,
                'grant_type' : 'shield_authentication',
            }

        try:
            r = self._store.s.post(url, data=post_data)
            #self._log_request(r)
            data = r.json()
        except ValueError:
            self.logger.error('_gp_auth: server response is invalid')
            return {}

        # make sure auth data is there
        for key in ['access_token', 'refresh_token']:
            if not data.get(key):
                self.logger.error('could not parse auth response')
                return {}

        # TODO: check for status codes, just in case
        return data
