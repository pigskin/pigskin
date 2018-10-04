import logging
try:
    from datetime import datetime, timezone
except ImportError:  # Python 2.7
    import calendar
    from datetime import datetime, timedelta


class utils(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)


    def nfldate_to_datetime(self, nfldate, localize=False):
        """Return a datetime object from an NFL Game Pass date string.

        Parameters
        ----------
        nfldate : str
            The date time string.
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
        nfldate_formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%d %H:%M:%SZ',
        ]
        dt = None

        for f in nfldate_formats:
            try:
                dt = datetime.strptime(nfldate, f)
            except ValueError:
                pass
            else:
                break

        if not dt:
            self.logger.error('unable to parse the nfldate string')
            return None

        if localize:
            try:
                dt.replace(tzinfo=timezone.utc).astimezone(tz=None)
            except NameError:  # Python 2.7
                dt = self._utc_to_local(dt)
            except Exception:
                self.logger.error('unable to localize the nfl datetime object')
                return None

        return dt


    @staticmethod
    def _utc_to_local(dt_utc):
        """Convert UTC time to local time."""
        # get integer timestamp to avoid precision lost
        timestamp = calendar.timegm(dt_utc.timetuple())
        dt_local = datetime.fromtimestamp(timestamp)
        assert dt_utc.resolution >= timedelta(microseconds=1)
        return dt_local.replace(microsecond=dt_utc.microsecond)
