from django.test import TestCase
from .models import Log

class LogModelTests(TestCase):
    def test_sleep_duration(self):
        log = Log(sleep_time="2021-01-01 00:00:00", wakeup_time="2021-01-01 01:00:00")
        self.assertEqual(log.sleep_duration().seconds, 3600)
        log = Log(sleep_time="2021-01-01 00:00:00", wakeup_time="2021-01-01 02:30:00")
        self.assertEqual(log.sleep_duration().seconds, 9000)
        log = Log(sleep_time="2021-01-01 00:00:00", wakeup_time="2021-01-01 00:30:00")
        self.assertEqual(log.sleep_duration().seconds, 1800)
        log = Log(sleep_time="2021-01-01 00:00:00", wakeup_time="2021-01-01 00:00:00")
        self.assertEqual(log.sleep_duration().seconds, 0)
        log = Log(sleep_time=None, wakeup_time="2021-01-01 00:00:00")
        self.assertEqual(log.sleep_duration().seconds, 0)
        log = Log(sleep_time="2021-01-01 00:00:00", wakeup_time=None)
        self.assertEqual(log.sleep_duration().seconds, 0)
        log = Log(sleep_time=None, wakeup_time=None)
        self.assertEqual(log.sleep_duration().seconds, 0)
        log = Log(sleep_time="2021-01-01 01:00:00", wakeup_time="2021-01-01 00:00:00")
        self.assertEqual(log.sleep_duration().seconds, -3600)
        log = Log(sleep_time="2021-01-01 02:30:00", wakeup_time="2021-01-01 00:00:00")
        self.assertEqual(log.sleep_duration().seconds, -9000)
        log = Log(sleep_time="2021-01-01 00:30:00", wakeup_time="2021-01-01 00:00:00")
        self.assertEqual(log.sleep_duration().seconds, -1800)
        log = Log(sleep_time="2021-01-01 00:00:00", wakeup_time=None)
        self.assertEqual(log.sleep_duration().seconds, 0)
        log = Log(sleep_time=None, wakeup_time="2021")