
import datetime
from reply_gen import tr_single_date, tr_single_time, tr_time
import pytz
import pandas as pd
import numpy as np
import re

from aibot_utils import location_handler, unique_without_sort, cleaning
from aibot_time import export_time
from aibot_date import export_date, gregorian_to_jalali, format_jalali_date
from vocab import hours_left_asked, hours_difference_asked, USER_CITY, time_reverse_convert
from weatherAPI import Weather
import os
from copy import copy

abs_path = os.path.dirname(os.path.abspath(__file__))


class Time:
    def __init__(self):
        self.countries_df = pd.read_csv(
            os.path.join(abs_path, "database/Countries.csv"))
        self.zone_df = pd.read_csv(os.path.join(abs_path, "database/zone.csv"))
        tehran_tz = Weather.get_city_info(USER_CITY)
        if tehran_tz:
            tehran_tz = tehran_tz["timezone"]
        else:
            tehran_tz = "+12600"
        self.local_time = pytz.timezone(self.possible_timezones(tehran_tz)[0])

    @staticmethod
    def possible_timezones(tz_offset, common_only=True):
        # pick one of the timezone collections
        timezones = pytz.common_timezones if common_only else pytz.all_timezones
        null_delta = datetime.timedelta(0, 0)
        try:
            desired_delta = datetime.timedelta(seconds=tz_offset)
        except Exception:
            print(tz_offset)
            try:
                desired_delta = datetime.timedelta(seconds=int(tz_offset))
            except Exception:
                print("babbab")
                desired_delta = datetime.timedelta(3, 30)

        # Loop through the timezones and find any with matching offsets
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
        if h != 0:
            if m != 0:
                generated_text = "{} ساعت و {} دقیقه".format(int(h), int(m))
            else:
                generated_text = "{} ساعت".format(int(h))
        else:
            generated_text = "{} دقیقه".format(int(m))
        h_st = ""
        if abs(h) > 10:
            h_st = "{}".format(int(h))
        elif h < 0:
            h_st = "-0{}".format(int(abs(h)))
        else:
            h_st = "0{}".format(int(h))
        m_st = "{}".format(int(m)) if abs(m) > 10 else "0{}".format(int(m))
        return "%s:%s" % (h_st, m_st), generated_text

    def get_answer(self, question, tokens, labels):
        answer = {'type': ['3'], 'city': [], 'date': [],
                  'time': [], 'religious_time': [], 'calendar_type': [], 'event': [], 'api_url': [''], 'result': []}

        generated_sentence = ""
        date = datetime.datetime.today().date()
        exportd = export_date(question, tokens, labels)
        no_date = True
        if exportd[0][0] != None:
            date = exportd[0][0].date()
            answer["date"] = [format_jalali_date(
                gregorian_to_jalali(date.year, date.month, date.day))]
            no_date = False

        time_list = []
        time_iso = []
        exporttime, is_adhan, adhan_url, adhan_names = export_time(
            question, tokens, labels)
        if is_adhan:
            answer["religious_time"] = adhan_names
            answer["api_url"].append(adhan_url)

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
        location = list(unique_without_sort(
            location_handler(question, tokens, labels)))
        if len(location) == 1 and location[0] == USER_CITY:
            location = []
        answer["city"] = location
        if len(location) == 0:
            answer["result"].append(time_list[0])
            if no_time:
                generated_sentence = "الآن {} است".format(
                    tr_single_time(time_iso[0]))
            else:
                generated_sentence = "{} میباشد".format(
                    tr_single_time(time_iso[0]))
            is_hour_lef_asked = False
            for h in hours_left_asked:
                if h in question:
                    is_hour_lef_asked = True
            if is_hour_lef_asked:
                tnow = datetime.datetime.now()
                dt = abs(tnow - time_iso[0])
                r, gt = self.format_time_delta(dt)
                answer["result"] = [r]
                if no_date:
                    if time_iso[0] > tnow:
                        generated_sentence = "تا {}، {} مانده است".format(
                            tr_single_time(time_iso[0]), gt)
                    else:
                        generated_sentence = "از {}، {} گذشته است".format(
                            tr_single_time(time_iso[0]), gt)
                else:
                    if time_iso[0] > tnow:
                        generated_sentence = "تا {} {}، {} مانده است".format(
                            tr_single_time(time_iso[0]), tr_single_date(date), gt)
                    else:
                        generated_sentence = "از {} {}، {} گذشته است".format(
                            tr_single_time(time_iso[0]), tr_single_date(date), gt)

            return answer, cleaning(generated_sentence)

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
            location_country = list(unique_without_sort(location_country))
            for l in location_country:
                tz = self.zone_df["Europe/Andorra"].iloc[np.where(
                    self.zone_df["AD"] == l)].to_numpy()
                if len(tz) >= 1:
                    time_zone_list.append(tz[0])

        is_reversed_asked = False
        for r in time_reverse_convert:
            if r in question:
                is_reversed_asked = True

        if len(time_zone_list) == 1:
            new_location = copy(location)
            single_ans, generated_sentence = self.get_single_answer(
                question, [location[-1]], time_zone_list, time_iso)
            answer["result"] = single_ans if isinstance(
                single_ans, list) else [single_ans]
        elif len(time_zone_list) == 2 and is_reversed_asked:
            time_zone_list.remove("Asia/Tehran")
            timzon = pytz.timezone(time_zone_list[0])
            t = timzon.localize(time_iso[0], is_dst=None).astimezone(pytz.utc)
            t = t.astimezone(self.local_time)
            answer["result"] = [t.strftime("%H:%M")]
            new_location = copy(location)
            try:
                new_location.remove("تهران")
            except Exception:
                try:
                    new_location.remove("ایران")
                except Exception:
                    pass

            generated_sentence = "{} در {}، {} به وقتa تهران میباشد".format(tr_single_time(
                time_iso[0], literal=False), new_location[0], tr_single_time(t, literal=False))
        else:
            time_list = []
            for tz in time_zone_list:
                time_zone = pytz.timezone(tz)
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
                dt = abs(time_list[0] - time_list[-1])
                r, gt = self.format_time_delta(dt)
                generated_sentence = "اختلاف زمان {} و {}، {} است".format(
                    location[0], location[-1], gt)
                answer["result"] = [r]
            else:

                new_location = copy(location)
                if (len(time_zone_list) == 2 and "Asia/Tehran" in time_zone_list):
                    time_zone_list.remove("Asia/Tehran")
                    new_location.remove(USER_CITY)
                location = new_location
                t_s = []
                for t in time_list:
                    t_s.append(t.strftime("%H:%M"))
                if not len(t_s) == len(location):
                    t_s = unique_without_sort(t_s)
                l_n = len(location)
                if l_n == len(t_s):
                    generated_sentence = "{} ".format(
                        tr_single_time(time_iso[0], True))
                    for i, (t, lc) in enumerate(zip(time_list, location)):
                        if i != l_n - 1:
                            generated_sentence = generated_sentence + "در {}، {} و ".format(
                                lc, tr_single_time(t, True))
                        else:
                            generated_sentence = generated_sentence + "در {}، {} ".format(
                                lc, tr_single_time(t, True))

                    generated_sentence = generated_sentence + "میباشد"
                answer["result"] = t_s
        return answer, cleaning(generated_sentence)

    def get_single_answer(self, question, location, time_zone_list, time_iso):
        time_res = []
        generated_sentence = ""
        if len(time_iso) == 1:
            t = self.local_time.localize(
                time_iso[0], is_dst=None).astimezone(pytz.utc)
            is_hour_lef_asked = False
            for h in hours_left_asked:
                if h in question:
                    is_hour_lef_asked = True
            if not is_hour_lef_asked:
                time_res = t.astimezone(pytz.timezone(
                    time_zone_list[0]))
                generated_sentence = "{} در {} {} است".format(
                    tr_single_time(time_iso[0], True), location[0], tr_single_time(time_res))
                time_res = time_res.strftime("%H:%M")
            else:
                tnow = datetime.datetime.now()
                dt = abs(tnow - time_iso[0])
                time_res, gt = self.format_time_delta(dt)
                if tnow > time_iso[0]:
                    generated_sentence = "از {}، {} گذشته است".format(
                        tr_single_time(time_iso[0]), gt)
                else:
                    generated_sentence = "تا {}، {} مانده است".format(
                        tr_single_time(time_iso[0]), gt)

        else:
            time_res = []
            for to in time_iso:
                t = self.local_time.localize(
                    to, is_dst=None).astimezone(pytz.utc)
                timl = t.astimezone(pytz.timezone(time_zone_list[0]))
                generated_sentence = generated_sentence + "{} در {}، {}،".format(tr_single_time(
                    to, True), location[0], tr_single_time(timl))

                time_res.append(timl.strftime("%H:%M"))
            generated_sentence = generated_sentence + "میباشد "
        return time_res, generated_sentence
