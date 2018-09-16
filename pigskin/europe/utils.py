import logging
try:
    from datetime import datetime, timezone
except ImportError:  # Python 2.7
    import calendar
    from datetime import datetime, timedelta

from .. import settings


class utils(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)


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
        # TODO: this could be moved to pigskin/utils.py with an additional
        # argument of ``nfldate_format`` provided by a service-specific
        # constants file.
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
                return self._utc_to_local(dt_utc)
            except Exception:
                self.logger.error('unable to localize the nfl datetime object')
                return None

        return dt_utc


    @staticmethod
    def _utc_to_local(dt_utc):
        """Convert UTC time to local time."""
        # get integer timestamp to avoid precision lost
        timestamp = calendar.timegm(dt_utc.timetuple())
        dt_local = datetime.fromtimestamp(timestamp)
        assert dt_utc.resolution >= timedelta(microseconds=1)
        return dt_local.replace(microsecond=dt_utc.microsecond)
