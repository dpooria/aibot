
from aibot_utils import location_handler
import requests
import numpy as np
import pandas as pd
import datetime
from aibot_date import export_date, gregorian_to_jalali, format_jalali_date
from aibot_time import export_time
from adhanAPI import Adhan
from vocab import weather_description_asked, weather_temperature_asked, tr_weather_description, day_asked, time_asked

weather_logical1 = {"سردترین": np.argmin, "سرد ترین": np.argmin, "سرد‌ترین": np.argmin, "گرم ترین": np.argmax, "گرمترین": np.argmax,
                    "گرم‌ترین": np.argmax, "میانگین دما": np.mean, "اختلاف دما": np.diff, "حداقل دما": np.min, "حداکثر دما": np.argmax, "بیشترین": np.argmax,
                    "بیشینه": np.argmax, "کمینه": np.argmin, "کمترین": np.argmin, "کم‌ترین": np.argmin, "سردتر": np.argmin, "گرم‌تر": np.argmax, "گرمتر": np.argmax, "اختلاف": np.diff}

weather_logical2 = {"سردترین": np.min, "سرد ترین": np.min, "سرد‌ترین": np.min, "گرم ترین": np.max, "گرمترین": np.max,
                    "گرم‌ترین": np.max, "میانگین دما": np.mean, "اختلاف دما": np.diff, "حداقل دما": np.min, "حداکثر دما": np.max, "بیشترین": np.max,
                    "بیشینه": np.max, "کمینه": np.min, "کمترین": np.min, "کم‌ترین": np.min, "سردتر": np.min, "گرم‌تر": np.max, "گرمتر": np.max, "اختلاف": np.diff}

# Class to handle weather api
class Weather:
    def __init__(self):
        self.appid = "ee41144a3fc05599947c9ffe87e12bd4"
        self.openweatherapi_5dayforecast_url = "http://api.openweathermap.org/data/2.5/forecast?q={}&APPID=ee41144a3fc05599947c9ffe87e12bd4&units=metric&lang=fa"
        self.adhan = Adhan()

    def get_city_5dayforecast_weather(self, cityName):
        try:
            data = requests.get(
                self.openweatherapi_5dayforecast_url.format(cityName)).json()
        except:
            return pd.DataFrame()
        if data["cod"] == "200":
            weathers = []
            for w_list in data["list"]:
                tmp = w_list["main"]
                tmp["dt_txt"] = datetime.datetime.fromisoformat(
                    w_list["dt_txt"])
                tmp["description"] = w_list["weather"][0]["description"]
                tmp["main"] = w_list["weather"][0]["main"]
                weathers.append(tmp)
            return pd.DataFrame(weathers)
        else:
            return pd.DataFrame()

    def getCityWeather(self, city, date):
        today = datetime.datetime.today()
        if date < today - datetime.timedelta(hours=1):
            date = today
        city_weather = self.get_city_5dayforecast_weather(city)
        if city_weather.empty:
            return pd.DataFrame()

        closest = np.argmin(np.abs(city_weather["dt_txt"] - date))
        return city_weather.iloc[closest]

    def getCityWeatherInDatePeriod(self, city, d1, d2):
        city_weather = self.get_city_5dayforecast_weather(city)
        if city_weather.empty:
            return pd.DataFrame()
        c1 = np.argmin(np.abs(city_weather["dt_txt"] - d1))
        c2 = np.argmin(np.abs(city_weather["dt_txt"] - d2))
        if c1 > c2:
            tmp = c2
            c2 = c1
            c1 = tmp
        return city_weather.iloc[c1:c2]

    def get_answer(self, question, tokens, labels):
        answer = {'type': '1', 'city': [], 'date': [],
                  'time': [], 'religious_time': [], 'calendar_type': [], 'event': [], 'api_url': [''], 'result': ''}
        location = list(np.unique(location_handler(question, tokens, labels)))
        date_list = []
        date_list_jalali = []
        exportdate = export_date(question, tokens, labels)
        no_date = False
        events = []
        for d in exportdate:
            if d[0]:
                date_list.append(d[0])
            if (not d[1][0]) and (not d[1][1]) and (type(d[1][2]) != bool):
                is_there_any_events = True
                events.append(d[1][2])
        answer["event"] = events
        d_n = len(date_list)
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
        # see if the cities are valid:
        if l_n != 0:
            for l in location:
                cinfo = self.get_city_info(l)
                if cinfo == None:
                    location.remove(l)
        l_n = len(location)
        if l_n == 0:
            location = ["تهران"]
            l_n = 1

        api_url = []
        for l in location:
            api_url.append(self.openweatherapi_5dayforecast_url.format(l))
        answer["api_url"] = api_url
        answer["city"] = location

        time_list = []
        time_iso = []
        exporttime = export_time(question, tokens, labels)
        for t in exporttime:
            if t != None:
                time_list.append(t.strftime("%H:%M"))
                time_iso.append(t)
        exportedAdhanNames = self.adhan.export_adhan_names(question)
        answer["religious_time"] = exportedAdhanNames
        if exportedAdhanNames:
            if len(exportedAdhanNames) == len(location):
                for e, l in zip(exportedAdhanNames, location):
                    t_adhan, adhan_url = self.adhan.get_city_adhan_time(
                        l, date_list[0], e)
                    if t_adhan:
                        api_url.append(adhan_url)
                        time_iso.append(t_adhan)
                        time_list.append(t_adhan.strftime("%H:%M"))
            else:
                for e in exportedAdhanNames:
                    for l in location:
                        t_adhan, adhan_url = self.adhan.get_city_adhan_time(
                            l, date_list[0], e)
                        if t_adhan:
                            api_url.append(adhan_url)
                            time_iso.append(t_adhan)
                            time_list.append(t_adhan.strftime("%H:%M"))

        t_n = len(time_iso)
        no_time = False
        if t_n == 0:
            if "صبح" in question:
                time_list.append("8:00")
                time_iso.append(datetime.time(8, 0))
            elif "شب " in question:
                time_list.append("21:00")
                time_iso.append(datetime.time(21, 0))
            else:
                time_list.append("12:00")
                time_iso.append(datetime.time(12, 0))
            t_n = 1
            no_time = True
        time_iso = list(np.unique(time_iso))
        time_list = list(np.unique(time_list))
        t_n = len(time_iso)
        answer["time"] = time_list

        date = []
        if t_n == d_n:
            for i in range(t_n):
                date.append(datetime.datetime.combine(
                    date_list[i].date(), time_iso[i]))
        elif d_n > t_n and t_n == 1:
            for i in range(d_n):
                date.append(datetime.datetime.combine(
                    date_list[i].date(), time_iso[0]))
        elif t_n > d_n and d_n == 1:
            for i in range(t_n):
                date.append(datetime.datetime.combine(
                    date_list[0].date(), time_iso[i]))
        else:
            date.append(datetime.datetime.combine(
                date_list[0].date(), time_iso[0]))
        if l_n == 1:
            # find out if it is a logical question
            logical = []
            for l in weather_logical2.keys():
                if l in question:
                    logical.append(l)
            result = pd.DataFrame()
            if logical:
                if len(date) == 1:
                    if no_time:
                        result = self.getCityWeatherInDatePeriod(location[0],
                                                                 datetime.datetime.today(),
                                                                 datetime.datetime.combine(date[0].date(), datetime.time(23, 59)))
                    elif no_date:
                        result = self.getCityWeatherInDatePeriod(location[0], datetime.datetime.today(),
                                                                 datetime.datetime.combine(datetime.datetime.today(), date[0].time()))
                    else:
                        result = self.getCityWeatherInDatePeriod(location[0],
                                                                 datetime.datetime.combine(
                                                                     date[0].date(), datetime.time(0, 0)),
                                                                 datetime.datetime.combine(date[0].date(), datetime.time(23, 59)))

                elif len(date) == 2:
                    result = self.getCityWeatherInDatePeriod(
                        location[0], date[0], date[1])
                else:
                    result = self.getCityWeatherInDatePeriod(
                        location[0], date[0], date[-1])
                if not result.empty:
                    if "اختلاف" in logical[0]:
                        res = np.abs(
                            result["temp"].iloc[0] - result["temp"].iloc[-1])
                    else:
                        res = weather_logical2[logical[0]](
                            result["temp"])
                    is_day_asked = False
                    is_time_asked = False
                    for d_n in day_asked:
                        if d_n in question:
                            is_day_asked = True
                    for t_n in time_asked:
                        if t_n in question:
                            is_time_asked = True
                    if is_day_asked:
                        r_loc = np.where(result["temp"] == res)[0]
                        if len(r_loc) > 0:
                            answer["type"] = "4"
                            res = result["dt_txt"].iloc[r_loc[0]].date()
                            res = gregorian_to_jalali(
                                res.year, res.month, res.day)
                            answer["result"] = datetime.date(
                                res[0], res[1], res[2]).strftime("%Y-%m-%d")
                        else:
                            answer["result"] = str(res)
                    elif is_time_asked:
                        r_loc = np.where(result["temp"] == res)[0]
                        if len(r_loc) > 0:
                            answer["type"] = "3"
                            answer["result"] = result["dt_txt"].iloc[r_loc[0]].time().strftime(
                                "%H:%M")
                        else:
                            answer["result"] = str(res)
                    else:
                        answer["result"] = str(res)
                return answer
            if len(date) == 1:
                result = self.getCityWeather(location[0], date[0])
                if not result.empty:
                    is_weather_description_asked = False
                    for w in weather_description_asked:
                        if w in question:
                            is_weather_description_asked = True
                    for w in weather_temperature_asked:
                        if w in question:
                            is_weather_description_asked = False
                    if is_weather_description_asked:
                        answer["result"] = tr_weather_description[result["main"]]
                    else:
                        answer["result"] = str(result["temp"])
        elif l_n >= 2:
            # find out if it is a logical question
            logical = []
            for l in weather_logical1.keys():
                if l in question:
                    logical.append(l)
            result = []
            if logical:
                if len(date) == 1:
                    for l in location:
                        r = self.getCityWeather(l, date[0])
                        if not r.empty:
                            result.append(r)
                elif len(date) == l_n:
                    for i, l in enumerate(location):
                        r = self.getCityWeather(l, date[i])
                        if not r.empty:
                            result.append(r)
                if result:
                    temps = []
                    for r in result:
                        temps.append(r["temp"])
                    if temps:
                        try:
                            res = location[weather_logical1[logical[0]](temps)]
                            answer["result"] = str(res)
                        except:
                            res = weather_logical1[logical[0]](temps)
                            answer["result"] = str(res)

                return answer
        return answer

    @ staticmethod
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
