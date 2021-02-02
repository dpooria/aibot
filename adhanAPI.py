
import re
import datetime

import requests
import numpy as np
import pandas as pd

from aibot_date import export_date, format_jalali_date, gregorian_to_jalali
from aibot_utils import location_handler, read_dict

tr_adhan_names = read_dict("dictionary/tr_adhan_names.dict")
logical_question = read_dict("dictionary/logical_question.list")
hours_left_asked = read_dict("dictionary/hours_left_asked.list")


def get_city_info(cityName):
    openweatherapi_5dayforecast_url = "http://api.openweathermap.org/data/2.5/forecast?q={}&APPID=ee41144a3fc05599947c9ffe87e12bd4&units=metric&lang=fa&cnt=1"
    try:
        data = requests.get(
            openweatherapi_5dayforecast_url.format(cityName)).json()
    except:
        return None
    if data["cod"] == "200":
        return data["city"]
    else:
        return None


class Adhan:
    def __init__(self):
        self.get_city_info = get_city_info
        self.api_url = "http://api.aladhan.com/v1/calendar?latitude={lat}&longitude={long}&method=7&month={month}&year={year}"

    def get_city_adhanـoneMonth(self, cityName, date):
        city_coord = self.get_city_info(cityName)
        if city_coord == None:
            return pd.DataFrame(), None
        url = self.api_url.format(lat=city_coord["coord"]["lat"],
                                  long=city_coord["coord"]["lon"], month=date.month, year=date.year)
        try:
            data = requests.get(url).json()
        except Exception:
            return pd.DataFrame(), url
        refmt = re.compile("\d+[:]\d+")
        if data["code"] == 200:
            a_ = []
            for d in data["data"]:
                tmp = {}
                for k, v in d["timings"].items():
                    mtch = refmt.findall(v)
                    if mtch:
                        s = mtch[0].split(":")
                        hour = int(s[0])
                        minute = int(s[1])

                        if hour > 24:
                            tt = hour
                            hour = minute
                            tt = minute
                    else:
                        hour = 0
                        minute = 0
                    tmp[k] = datetime.time(hour, minute)
                    # tmp[k] = datetime.datetime.strptime(v, "%H:%M (%z)").time()
                tmp["date"] = datetime.datetime.fromtimestamp(
                    int(d["date"]["timestamp"])).date()
                a_.append(tmp)
            return pd.DataFrame(a_), url
        else:
            return pd.DataFrame(), url

    def get_city_adhan_oneDay(self, cityName, date):
        df_month, url = self.get_city_adhanـoneMonth(cityName, date)
        if df_month.empty:
            return pd.DataFrame(), url
        if type(date) == datetime.datetime:
            return df_month.loc[df_month["date"] == date.date()], url
        return df_month.iloc[np.where(df_month["date"] == date)], url

    def get_city_adhan_time(self, cityName, date, adhan):
        try:
            time, url = self.get_city_adhan_oneDay(cityName, date)
            if time.empty:
                return None, url
            return time[tr_adhan_names[adhan]].to_numpy()[0], url
        except Exception:
            try:
                time, url = self.get_city_adhan_oneDay(cityName, date)
                if time.empty:
                    return None, url
                return time[adhan].to_numpy()[0], url
            except Exception:
                return None, None

    @staticmethod
    def export_adhan_names(question):
        a_ = []
        for a in tr_adhan_names.keys():
            if a in question:
                a_.append(a)
        return a_

    def get_difference_adhan(self, city1, city2, date1, date2, adhan1, adhan2):
        url = ["", ""]
        res1, url[0] = self.get_city_adhan_time(city1, date1.date(), adhan1)
        res2, url[1] = self.get_city_adhan_time(city2, date2.date(), adhan2)
        url = list(np.unique(url))
        if res1 == None or res2 == None:
            return None, url
        res = abs(datetime.datetime.combine(date1.date(), res1) -
                  datetime.datetime.combine(date2.date(), res2))
        res = res.total_seconds()
        hours = res // 3600
        minutes = (res // 60) % 60
        return datetime.time(int(hours), int(minutes)).strftime("%H:%M"), url

    @staticmethod
    def format_time_delta(dt):
        totsec = dt.total_seconds()
        h = totsec // 3600
        m = (totsec // 60) % 60
        return datetime.time(
            int(h), int(m)).strftime("%H:%M")

    def get_answer(self, question, tokens, labels):
        answer = {'type': '2', 'city': [], 'date': [],
                  'time': [], 'religious_time': [], 'calendar_type': [], 'event': [], 'api_url': [''], 'result': ''}
        location = list(np.unique(location_handler(question, tokens, labels)))
        answer["city"] = location
        date_list = []
        date_list_jalali = []
        exportdate = export_date(question, tokens, labels)
        events = []
        for d in exportdate:
            if d[0]:
                date_list.append(d[0])
            if (not d[1][0]) and (not d[1][1]) and (type(d[1][2]) != bool):
                events.append(d[1][2])

        answer["event"] = events
        d_n = len(date_list)
        no_date = False
        if d_n == 0:
            today = datetime.datetime.today()
            date_list = [today]
            today_j = gregorian_to_jalali(today.year, today.month, today.day)
            answer["date"] = [format_jalali_date(today_j)]
            d_n = 1
            no_date = True

        date_list = list(np.unique(date_list))
        d_n = len(date_list)
        date_list_jalali = []
        for d in date_list:
            j = gregorian_to_jalali(d.year, d.month, d.day)
            date_list_jalali.append(format_jalali_date(j))
        answer["date"] = date_list_jalali
        l_n = len(location)
        if l_n == 0:
            answer["city"] = ["تهران"]
            location = ["تهران"]
            l_n = 1
        api_url = []
        exportedAdhan = self.export_adhan_names(question)
        n_adhan = len(exportedAdhan)
        if n_adhan == 0:
            return answer
        answer["religious_time"] = exportedAdhan
        res, url = self.get_city_adhan_time(
            location[0], date_list[0].date(), exportedAdhan[0])
        answer["api_url"] = [url]
        if n_adhan == 1 and l_n == 1 and d_n == 1:
            if res != None:
                answer["result"] = res.strftime("%H:%M")
            is_hour_lef_asked = False
            for h in hours_left_asked:
                if h in question:
                    is_hour_lef_asked = True
            if not is_hour_lef_asked:
                return answer
            else:
                tnow = datetime.datetime.now()
                dt = abs(
                    tnow - datetime.datetime.combine(date_list[0].date(), res))
                answer["result"] = self.format_time_delta(dt)

        else:
            # check if it's a logical question
            isLogical = False
            for l in logical_question:
                if l in tokens:
                    isLogical = True
            if isLogical:
                if n_adhan > 1 and l_n == 1 and d_n == 1:
                    answer["result"], answer["api_url"] = self.get_difference_adhan(
                        location[0], location[0], date_list[0], date_list[0], exportedAdhan[0], exportedAdhan[1])
                elif n_adhan == 1 and l_n > 1 and d_n == 1:
                    answer["result"], answer["api_url"] = self.get_difference_adhan(
                        location[0], location[1], date_list[0], date_list[0], exportedAdhan[0], exportedAdhan[0])
                elif n_adhan == 1 and l_n == 1 and d_n > 1:
                    answer["result"], answer["api_url"] = self.get_difference_adhan(
                        location[0], location[0], date_list[0], date_list[1], exportedAdhan[0], exportedAdhan[0])
                elif n_adhan == 2 and l_n == 2 and d_n == 1:
                    answer["result"], answer["api_url"] = self.get_difference_adhan(
                        location[0], location[1], date_list[0], date_list[0], exportedAdhan[0], exportedAdhan[1])
                elif n_adhan == 2 and l_n == 1 and d_n == 2:
                    answer["result"], answer["api_url"] = self.get_difference_adhan(
                        location[0], location[0], date_list[0], date_list[1], exportedAdhan[0], exportedAdhan[1])
                elif n_adhan == 1 and l_n == 2 and d_n == 2:
                    answer["result"], answer["api_url"] = self.get_difference_adhan(
                        location[0], location[1], date_list[0], date_list[0], exportedAdhan[0], exportedAdhan[1])

            return answer
        return answer
