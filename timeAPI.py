
import datetime
import pytz
import pandas as pd
import numpy as np
import re

from aibot_utils import location_handler
from aibot_time import export_time
from aibot_date import export_date, gregorian_to_jalali, format_jalali_date

from weatherAPI import Weather
import os

abs_path = os.path.dirname(os.path.abspath(__file__))

hours_left_asked = ["تا ساعت", "چقدر زمان",
                    "مانده", "چند ساعت گذشته", "چقدر زمان گذشته"]
hours_difference_asked = ["اختلاف زمان", "اختلاف ساعت",
                          "فاصله ساعت", "فاصله زمان", "تفاوت زمان"]


class Time:
    def __init__(self):
        self.countries_df = pd.read_csv(
            os.path.join(abs_path, "database/Countries.csv"))
        self.zone_df = pd.read_csv(os.path.join(abs_path, "database/zone.csv"))
        tehran_tz = Weather.get_city_info("تهران")
        if tehran_tz:
            tehran_tz = tehran_tz["timezone"]
        else:
            tehran_tz = "+12600"
        self.local_time = pytz.timezone(self.possible_timezones(tehran_tz)[0])

    @staticmethod
    def possible_timezones(tz_offset, common_only=True):
        # pick one of the timezone collections
        timezones = pytz.common_timezones if common_only else pytz.all_timezones
        desired_delta = datetime.timedelta(seconds=tz_offset)

        # Loop through the timezones and find any with matching offsets
        null_delta = datetime.timedelta(0, 0)
        results = []
        for tz_name in timezones:
            tz = pytz.timezone(tz_name)
            non_dst_offset = getattr(
                tz, '_transition_info', [[null_delta]])[-1]
            if desired_delta == non_dst_offset[0]:
                results.append(tz_name)

        return results

    @staticmethod
    def format_time_delta(dt):
        totsec = dt.total_seconds()
        h = totsec // 3600
        m = (totsec // 60) % 60
        h_st = ""
        if abs(h) > 10:
            h_st = "{}".format(int(h))
        elif h < 0:
            h_st = "-0{}".format(int(abs(h)))
        else:
            h_st = "0{}".format(int(h))
        m_st = "{}".format(int(m)) if abs(m) > 10 else "0{}".format(int(m))
        return "%s:%s" % (h_st, m_st)

    def get_answer(self, question, tokens, labels):
        answer = {'type': '3', 'city': [], 'date': [],
                  'time': [], 'religious_time': [], 'calendar_type': [], 'event': [], 'api_url': [''], 'result': ''}

        exporttime = export_time(question, tokens, labels)
        time_list = []
        time_iso = []
        date = datetime.datetime.today().date()
        exportd = export_date(question, tokens, labels)
        if exportd[0][0] != None:
            date = exportd[0][0].date()
            answer["date"] = [format_jalali_date(
                gregorian_to_jalali(date.year, date.month, date.day))]
        for t in exporttime:
            if t != None:
                time_list.append(t.strftime("%H:%M"))
                time_iso.append(datetime.datetime.combine(date, t))
        t_n = len(time_iso)
        no_time = False
        if t_n == 0:
            now = datetime.datetime.now()
            time_list.append(now.strftime("%H:%M"))
            time_iso.append(datetime.datetime.combine(date, now.time()))
            t_n = 1
            no_time = True

        answer["time"] = time_list
        location = list(np.unique(location_handler(question, tokens, labels)))
        answer["city"] = location
        if len(location) == 0:
            answer["result"] = time_list[0]
            is_hour_lef_asked = False
            for h in hours_left_asked:
                if h in question:
                    is_hour_lef_asked = True
            if is_hour_lef_asked:
                tnow = datetime.datetime.now()
                dt = abs(tnow - time_iso[0])
                answer["result"] = self.format_time_delta(dt)
            return answer

        location_country = []
        for l in location:
            c = self.countries_df["summary"].iloc[np.where(
                self.countries_df["title"] == l)].to_numpy()
            if len(c) > 0:
                location_country.append(c[0][:-1])

        time_zone_list = []
        if len(location) > len(location_country):
            for l in location:
                if l in location_country:
                    continue
                city_info = Weather.get_city_info(l)
                if city_info == None:
                    s = re.sub("^ا", "آ", l)
                    city_info = Weather.get_city_info(s)
                if city_info != None:
                    p_tz = self.possible_timezones(city_info["timezone"])
                    if not p_tz:
                        p_tz = self.possible_timezones(
                            city_info["timezone"], False)
                    if p_tz:
                        time_zone_list.append(p_tz[0])

        if location_country:
            location_country = list(np.unique(location_country))
            for l in location_country:
                tz = self.zone_df["Europe/Andorra"].iloc[np.where(
                    self.zone_df["AD"] == l)].to_numpy()
                tz = tz[0]
                time_zone_list.append(tz)

        if len(time_zone_list) == 1:
            time_res = []
            if len(time_iso) == 1:
                t = self.local_time.localize(
                    time_iso[0], is_dst=None).astimezone(pytz.utc)
                is_hour_lef_asked = False
                for h in hours_left_asked:
                    if h in question:
                        is_hour_lef_asked = True
                if not is_hour_lef_asked:
                    time_res = t.astimezone(pytz.timezone(
                        time_zone_list[0])).strftime("%H:%M")
                else:
                    tnow = datetime.datetime.now()
                    dt = abs(tnow - time_iso[0])
                    time_res = self.format_time_delta(dt)

            else:
                time_res = []
                for to in time_iso:
                    t = self.local_time.localize(
                        to, is_dst=None).astimezone(pytz.utc)
                    time_res.append(t.astimezone(
                        pytz.timezone(time_zone_list[0])).strftime("%H:%M"))
                time_res = "-".join(time_res)
            answer["result"] = time_res
            return answer
        else:
            time_list = []
            for tz in time_zone_list:
                time_zone = pytz.timezone(tz)
                if len(time_iso) == 1:
                    t = self.local_time.localize(
                        time_iso[0], is_dst=None).astimezone(pytz.utc)
                    t = t.astimezone(time_zone)
                    d = datetime.datetime(
                        t.year, t.month, t.day, t.hour, t.minute)
                    time_list.append(d)
            is_hours_difference_asked = False
            for h in hours_difference_asked:
                if h in question:
                    is_hours_difference_asked = True

            if is_hours_difference_asked:
                dt = abs(time_list[-2] - time_list[-1])
                answer["result"] = self.format_time_delta(dt)
            return answer
