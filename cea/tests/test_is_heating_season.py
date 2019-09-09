"""
 the implementation of #251 (move Heating/Cooling season to a non northern-hemisphere-based system).



the hours to start and stop (?) the heating season as explained in the reproduced method ``is_heating_season`` below.

New style: 6 attributes, ``heating_season_start``, ``heating_season_end``, ``cooling_season_start``,
``cooling_season_end``, ``has_heating_season``, ``has_cooling_season``.
"""
import unittest

import datetime


class TestIsHeatingSeasonReplacement(unittest.TestCase):
    def setUp(self):
        self.seasonhours = [3216, 6192]

    def test_is_heating_season(self):
        self.has_heating_season = True
        self.hour_zero = datetime.datetime(year=2017, month=1, day=1, hour=0, minute=0, second=0)
        self.heating_season_start = self.hour_zero + datetime.timedelta(hours=self.seasonhours[1])
        self.heating_season_end = self.hour_zero + datetime.timedelta(hours=self.seasonhours[0])
        print(((self.heating_season_start - self.hour_zero).total_seconds() / 3600,
               (self.heating_season_end - self.hour_zero).total_seconds() / 3600))
        for timestep in range(365 * 24):
            self.assertEqual(self.is_heating_season_old(timestep), self.is_heating_season_new(timestep),
                             self.msg(timestep))

    def msg(self, timestep):
        old = self.is_heating_season_old(timestep)
        new = self.is_heating_season_new(timestep)
        date = self.hour_zero + datetime.timedelta(hours=timestep)
        case = self.heating_season_start <= self.heating_season_end
        return 'timestep %(timestep)i: %(date)s - old=%(old)s, new=%(new)s (southern hemisphere: %(case)s)' % locals()

    def is_heating_season_new(self, timestep):
        now = self.hour_zero + datetime.timedelta(hours=timestep)
        if self.heating_season_start <= self.heating_season_end:
            # southern hemisphere
            is_hs = self.heating_season_start <= now < self.heating_season_end
        else:
            # northern hemisphere
            is_hs = not (self.heating_season_end < now < self.heating_season_start)
        return is_hs

    def is_heating_season_old(self, timestep):
        if self.seasonhours[0] + 1 <= timestep < self.seasonhours[1]:
            return False
        else:
            return True
