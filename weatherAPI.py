
from aibot_utils import location_handler, mix_tdl, unique_without_sort
import requests
import numpy as np
import pandas as pd
import datetime
from aibot_date import export_date, gregorian_to_jalali, format_jalali_date, jalali_to_gregorian
from aibot_time import export_time
from adhanAPI import Adhan
from copy import copy
from vocab import (
    weather_description_asked,
    weather_temperature_asked,
    tr_weather_description,
    day_asked,
    time_asked,
    weather_logical1,
    weather_logical2,
    weather_logical,
    temp_asked)


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
        location = unique_without_sort(
            location_handler(question, tokens, labels))
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
        date_list = unique_without_sort(date_list)
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
        exporttime, is_adhan, adhan_url, adhan_names = export_time(
            question, tokens, labels)
        if is_adhan:
            answer["religious_time"] = adhan_names
            answer["api_url"].append(adhan_url)

        for t in exporttime:
            if t != None:
                time_list.append(t.strftime("%H:%M"))
                time_iso.append(t)

        answer["time"] = time_list
        t_n = len(time_iso)
        time_iso = unique_without_sort(time_iso)
        time_list = unique_without_sort(time_list)
        logicals = self.check_logical(tokens)
        if not logicals:
            logicals = self.check_logical(question)
        if logicals:
            result = self.logical_handler(question,
                                          logicals, time_iso, date_list, location)
            answer["result"] = result
        else:
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
            t_n = len(time_iso)
            answer["time"] = time_list
            date = []
            if t_n == d_n:
                for i in range(t_n):
                    date.append(datetime.datetime.combine(
                        date_list[i].date(), time_iso[i]))
            elif d_n > t_n:
                for i in range(d_n):
                    date.append(datetime.datetime.combine(
                        date_list[i].date(), time_iso[0]))
            else:
                for i in range(t_n):
                    date.append(datetime.datetime.combine(
                        date_list[0].date(), time_iso[i]))
            ln_d = len(date)
            if l_n == 1 and ln_d == 1:
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
            elif ln_d >= 2 and l_n == 1:
                answer["result"] = []
                for dat in date:
                    result = self.getCityWeather(location[0], dat)
                    if not result.empty:
                        is_weather_description_asked = False
                        for w in weather_description_asked:
                            if w in question:
                                is_weather_description_asked = True
                        for w in weather_temperature_asked:
                            if w in question:
                                is_weather_description_asked = False
                        if is_weather_description_asked:
                            answer["result"].append(
                                tr_weather_description[result["main"]])
                        else:
                            answer["result"].append(str(result["temp"]))
            elif l_n == ln_d:
                answer["result"] = []
                for lc, dat in zip(location, date):
                    result = self.getCityWeather(lc, dat)
                    if not result.empty:
                        is_weather_description_asked = False
                        for w in weather_description_asked:
                            if w in question:
                                is_weather_description_asked = True
                        for w in weather_temperature_asked:
                            if w in question:
                                is_weather_description_asked = False
                        if is_weather_description_asked:
                            answer["result"].append(
                                tr_weather_description[result["main"]])
                        else:
                            answer["result"].append(str(result["temp"]))
            elif l_n >= 2 and ln_d == 1:
                answer["result"] = []
                for lc in location:
                    result = self.getCityWeather(lc, date[0])
                    if not result.empty:
                        is_weather_description_asked = False
                        for w in weather_description_asked:
                            if w in question:
                                is_weather_description_asked = True
                        for w in weather_temperature_asked:
                            if w in question:
                                is_weather_description_asked = False
                        if is_weather_description_asked:
                            answer["result"].append(
                                tr_weather_description[result["main"]])
                        else:
                            answer["result"].append(str(result["temp"]))
            else:
                answer["result"] = []
                for lc in location:
                    result = self.getCityWeather(lc, date[0])
                    if not result.empty:
                        is_weather_description_asked = False
                        for w in weather_description_asked:
                            if w in question:
                                is_weather_description_asked = True
                        for w in weather_temperature_asked:
                            if w in question:
                                is_weather_description_asked = False
                        if is_weather_description_asked:
                            answer["result"].append(
                                tr_weather_description[result["main"]])
                        else:
                            answer["result"].append(str(result["temp"]))
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

    @ staticmethod
    def check_logical(tokens):
        logicals = []
        for k, v in weather_logical.items():
            if k in tokens:
                logicals.append([k, v])
        return logicals

    def logical_handler(self, question, logicals, time_iso, date_list, location):
        if len(logicals) == 1 or np.unique(np.array(logicals)[:, 1]).size == 1:
            if logicals[0][1] == "amin" or logicals[0][1] == "amin_abs":
                result = self.min_max_handler(question,
                                              np.argmin, time_iso, date_list, location)
                return str(result)
            if logicals[0][1] == "amax" or logicals[0][1] == "amax_abs":
                result = self.min_max_handler(question,
                                              np.argmax, time_iso, date_list, location)
                return str(result)
            if logicals[0][1] == "mean":
                return self.mean_handler(question, np.mean, time_iso, date_list, location)
            if logicals[0][1] == "diff":
                return self.difference_handler(question, time_iso, date_list, location)
        else:
            zi = question.find(logicals[0][0])
            oi = question.find(logicals[1][0])
            if zi > oi:
                tmp = copy(logicals[0])
                logicals[0] = copy(logicals[1])
                logicals[1] = tmp
            pos = []
            for logc in logicals:
                pos.append(question.find(logc[0]))
            sorted_logicals = []
            for p in np.argsort(pos):
                sorted_logicals.append(logicals[p])
            logicals = sorted_logicals
            mean_abs = []
            amax_amin_diff = []
            logics = []
            for lg in logicals:
                logics.append(lg[1])
                if lg[1] == "amax" or lg[1] == "amin" or lg[1] == "diff":
                    amax_amin_diff.append(lg[1])
                elif lg[1] == "mean" or lg[1] == "amax_abs" or lg[1] == "amin_abs":
                    mean_abs.append(lg[1])

            if len(amax_amin_diff) == 0 and len(mean_abs) >= 2:
                return self.mean_abs_q(question, mean_abs, time_iso, date_list, location)
            else:
                return self.m1d1(question, mean_abs, amax_amin_diff, time_iso, date_list, location)

    def m1d1(self, question, mean_abs_list, diff_max_min, time_iso, date_list, location):
        func_dict = {"amin_abs": np.argmin,
                     "amax_abs": np.argmax, "mean": np.mean, "amax": np.argmax, "amin": np.argmin, "diff": np.diff}
        wfunc_dict = {"amin_abs": self.min_max_handler,
                      "amax_abs": self.min_max_handler, "mean": self.mean_handler}
        t = len(time_iso)
        d = len(date_list)
        l = len(location)
        res = []
        ta = False
        for ita in temp_asked:
            if ita in question:
                ta = True
        if len(mean_abs_list) == 1 or np.unique(mean_abs_list).size == 1:

            func = wfunc_dict[mean_abs_list[0]]
            if (t == 0 or t == 1) and d >= 2 and l == 1:
                for dat in date_list:
                    res.append(
                        func(question, func_dict[mean_abs_list[0]], time_iso, [dat], location, True))
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = "%4.2f" % result if len(
                            result) == 1 else result
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                else:
                    result = date_list[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]
                    result = gregorian_to_jalali(
                        result.year, result.month, result.day)
                    result = format_jalali_date(result)
            elif (t == 0 or t == 1) and d == 1 and l >= 2:
                for lc in location:
                    res.append(
                        func(question, func_dict[mean_abs_list[0]], time_iso, date_list, [lc], True))
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = "%4.2f" % result if len(
                            result) == 1 else result
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                else:
                    result = location[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]
            elif t >= 2 and l == 1 and d == 1:
                for tim in time_iso:
                    res.append(func(question, func_dict[mean_abs_list[0]], [
                        tim], date_list, location, True))
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = "%4.2f" % result if len(
                            result) == 1 else result
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                else:
                    result = time_iso[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))].strftime("%H:%M")
            ###
            elif (t == d) and l == 1:
                for dat, tim in zip(date_list, time_iso):
                    res.append(
                        func(question, func_dict[mean_abs_list[0]], [tim], [dat], location, True))
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = "%4.2f" % result if len(
                            result) == 1 else result
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                else:
                    result = date_list[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]
                    result = gregorian_to_jalali(
                        result.year, result.month, result.day)
                    result = format_jalali_date(result)
            elif (t == 0 or t == 1) and d == l:
                for lc, dat in zip(location, date_list):
                    res.append(
                        func(question, func_dict[mean_abs_list[0]], time_iso, [dat], [lc], True))
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = "%4.2f" % result if len(
                            result) == 1 else result
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                else:
                    result = location[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]
        else:
            lg = len(mean_abs_list)
            if l == 1 and d == 1 and (t == 0 or t == 1):
                for mabs in mean_abs_list:
                    res.append(wfunc_dict[mabs](
                        question, func_dict[mabs], time_iso, date_list, location, True))
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = "%4.2f" % result if len(
                            result) == 1 else result
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]

            elif lg == d and l == 1 and (t == 0 or t == 1):
                for mabs, dat in zip(mean_abs_list, date_list):
                    res.append(
                        wfunc_dict[mabs](question, func_dict[mabs], time_iso, [dat], location, True))
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = "%4.2f" % result if len(
                            result) == 1 else result
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                else:
                    result = date_list[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]
                    result = gregorian_to_jalali(
                        result.year, result.month, result.day)
                    result = format_jalali_date(result)
            elif lg == l and d == 1 and (t == 0 or t == 1):
                for mabs, lc in zip(mean_abs_list, location):
                    res.append(
                        wfunc_dict[mabs](question, func_dict[mabs], time_iso, date_list, [lc], True))
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = "%4.2f" % result if len(
                            result) == 1 else result
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                else:
                    result = location[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]
            elif lg == t and d == 1 and l == 1:
                for mabs, tim in zip(mean_abs_list, time_iso):
                    res.append(wfunc_dict[mabs](question, func_dict[mabs], [
                        tim], date_list, location, True))
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = "%4.2f" % result if len(
                            result) == 1 else result
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                else:
                    result = time_iso[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))].strftime("%H:%M")
            elif (lg == l) and (l == d) and (t == 0 or t == 1):
                for i in range(l):
                    res.append(
                        wfunc_dict[mean_abs_list[i]](question, func_dict[mean_abs_list[i]], time_iso, date_list[i], location[i], True))
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = "%4.2f" % result if len(
                            result) == 1 else result
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                else:
                    result = location[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]
            elif (lg == l) and (l == t) and (d == 1):
                for i in range(l):
                    res.append(
                        wfunc_dict[mean_abs_list[i]](question, func_dict[mean_abs_list[i]], time_iso[i], date_list, location[i], True))
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = "%4.2f" % result if len(
                            result) == 1 else result
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                else:
                    result = location[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]

        return result

    def mean_abs_q(self, question, mean_abs_list, time_iso, date_list, location):
        func_dict = {"amin_abs": np.argmin,
                     "amax_abs": np.argmax, "mean": np.mean}
        t = len(time_iso)
        d = len(date_list)
        l = len(location)
        if len(mean_abs_list) == 2:
            func = None
            if mean_abs_list[1] == "amin_abs" or mean_abs_list[1] == "amax_abs":
                func = self.min_max_handler
            else:
                func = self.mean_handler
            res = []
            dlt_max = np.argmax([d, l, t])

            ta = False
            for ita in temp_asked:
                if ita in question:
                    ta = True
            if (t == 0 or t == 1) and d >= 2 and l == 1:
                for dat in date_list:
                    res.append(
                        func(question, func_dict[mean_abs_list[1]], time_iso, [dat], location, True))
                if ta or mean_abs_list[0] == "mean":
                    if mean_abs_list[0] == "mean":
                        result = "%4.2f" % func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))
                    else:
                        result = res[func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))]
                else:
                    result = date_list[func_dict[mean_abs_list[0]](
                        np.array(res, dtype="d"))]
                    result = gregorian_to_jalali(
                        result.year, result.month, result.day)
                    result = format_jalali_date(result)

            elif (t == 0 or t == 1) and d == 1 and l >= 2:
                for lc in location:
                    res.append(
                        func(question, func_dict[mean_abs_list[1]], time_iso, date_list, [lc], True))
                if ta or mean_abs_list[0] == "mean":
                    if mean_abs_list[0] == "mean":
                        result = "%4.2f" % func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))
                    else:
                        result = res[func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))]
                else:
                    result = location[func_dict[mean_abs_list[0]](
                        np.array(res, dtype="d"))]

            elif t >= 2 and l == 1 and d == 1:
                for tim in time_iso:
                    res.append(func(question, func_dict[mean_abs_list[1]], [
                               tim], date_list, location, True))
                if ta or mean_abs_list[0] == "mean":
                    if mean_abs_list[0] == "mean":
                        result = "%4.2f" % func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))
                    else:
                        result = res[func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))]
                else:
                    result = time_iso[func_dict[mean_abs_list[0]](
                        np.array(res, dtype="d"))].strftime("%H:%M")
            elif (t == 0 or t == 1) and d == l:
                for dat, lc in zip(date_list, location):
                    res.append(
                        func(question, func_dict[mean_abs_list[1]], time_iso, [dat], [lc], True))
                if ta or mean_abs_list[0] == "mean":
                    if mean_abs_list[0] == "mean":
                        result = "%4.2f" % func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))
                    else:
                        result = res[func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))]
                else:
                    result = location[func_dict[mean_abs_list[0]](
                        np.array(res, dtype="d"))]
            elif t == l and d == 1:
                for tim, lc in zip(time_iso, location):
                    res.append(func(question, func_dict[mean_abs_list[1]], [
                               tim], date_list, [lc], True))
                if ta or mean_abs_list[0] == "mean":
                    if mean_abs_list[0] == "mean":
                        result = "%4.2f" % func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))
                    else:
                        result = res[func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))]
                else:
                    result = location[func_dict[mean_abs_list[0]](
                        np.array(res, dtype="d"))]

            elif t == d and l == 1:
                for tim, dat in zip(time_iso, date_list):
                    res.append(func(question, func_dict[mean_abs_list[1]], [
                               tim], [dat], location, True))
                if ta or mean_abs_list[0] == "mean":
                    if mean_abs_list[0] == "mean":
                        result = "%4.2f" % func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))
                    else:
                        result = res[func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))]
                else:
                    result = date_list[func_dict[mean_abs_list[0]](
                        np.array(res, dtype="d"))]
                    result = gregorian_to_jalali(
                        result.year, result.month, result.day)
                    result = format_jalali_date(result)

            return result

    def min_max_handler(self, question, min_max_func, time_iso, date_list, location, force_return_temp=False):
        t = len(time_iso)
        d = len(date_list)
        l = len(location)
        # t0 d1 l1
        if t == 0 and d == 1 and l == 1:
            # get the the temperature of the entire day
            temp = self.getCityWeatherInDatePeriod(
                location[-1],
                datetime.datetime.combine(date_list[-1].date(),
                                          datetime.time(1, 0)),
                datetime.datetime.combine(date_list[-1].date(),
                                          datetime.time(23, 0)),
            )
            # find out if it's the temperature or the time that the question wants
            is_time_asked = False
            for ta in time_asked:
                if ta in question:
                    is_time_asked = True

            result = min_max_func(temp["temp"].to_numpy())
            if is_time_asked:
                result = temp["dt_txt"].iloc[result].time().strftime("%H:%M")
            else:
                result = temp["temp"].iloc[result]
            return result
        # t1 d1 l1 ---> this shouldn't happen but anyway!
        if t == 1 and d == 1 and l == 1:
            return self.getCityWeather(location[0], datetime.datetime.combine(date_list[0].date(), time_iso[0]))["temp"]
        # t0or1 d1 l>=2
        if (t == 0 or t == 1) and d == 1 and l >= 2:
            if t == 0:
                if "صبح" in question:
                    time_iso.append(datetime.time(8, 0))
                elif "شب " in question:
                    time_iso.append(datetime.time(21, 0))
                else:
                    time_iso.append(datetime.time(12, 0))
            res = []
            for lc in location:
                res.append(self.getCityWeather(
                    lc, datetime.datetime.combine(date_list[0].date(), time_iso[0]))["temp"])
            return location[min_max_func(res)]
        # t0 d>=2 l1
        if t == 0 and d >= 2 and l == 1:
            res = self.getCityWeatherInDatePeriod(
                location[0], datetime.datetime.combine(
                    np.min(date_list).date(), datetime.time(1, 0)),
                datetime.datetime.combine(np.max(date_list).date(), datetime.time(23, 59)))["temp"]
            ta = False
            for ita in temp_asked:
                if ita in question:
                    ta = True
            if ta or force_return_temp:
                result = min_max_func(res)
            else:
                result = date_list[min_max_func(res)]
                result = gregorian_to_jalali(
                    result.year, result.month, result.day)
                result = format_jalali_date(result)
            return result

        # t1 d>=2 l1
        if t == 1 and d >= 2 and l == 1:
            res = []
            for dat in date_list:
                res.append(self.getCityWeather(
                    location[0], datetime.datetime.combine(dat.date(), time_iso[0]))["temp"])

            ta = False
            for ita in temp_asked:
                if ita in question:
                    ta = True
            if ta or force_return_temp:
                result = min_max_func(res)
            else:
                result = date_list[min_max_func(res)]
                result = gregorian_to_jalali(
                    result.year, result.month, result.day)
                result = format_jalali_date(result)
            return result

        # t>=2 d1 l1
        if t >= 2 and d == 1 and l == 1:
            res = []
            for time in time_iso:
                res.append(self.getCityWeather(
                    location[0], datetime.datetime.combine(date_list[0].date(), time))["temp"])
            ta = False
            for ita in temp_asked:
                if ita in question:
                    ta = True
            if ta or force_return_temp:
                return min_max_func(res)
            return time_iso[min_max_func(res)].strftime("%H:%M")
        # t0or1 d==l
        if (t == 0 or t == 1) and d == l:
            if t == 0:
                if "صبح" in question:
                    time_iso.append(datetime.time(8, 0))
                elif "شب " in question:
                    time_iso.append(datetime.time(21, 0))
                else:
                    time_iso.append(datetime.time(12, 0))
            res = []
            for lc, dat in zip(location, date_list):
                res.append(self.getCityWeather(
                    lc, datetime.datetime.combine(dat.date(), time_iso[0]))["temp"])
            ta = False
            for ita in temp_asked:
                if ita in question:
                    ta = True
            if ta or force_return_temp:
                return min_max_func(res)
            return location[min_max_func(res)]
        # t==d l1
        if (t == d) and l == 1:
            res = []
            for time, dat in zip(time_iso, date_list):
                res.append(self.getCityWeather(
                    location[0], datetime.datetime.combine(dat.date(), time))["temp"])
            ta = False
            for ita in temp_asked:
                if ita in question:
                    ta = True
            if ta or force_return_temp:
                return min_max_func(res)
            return date_list[min_max_func(res)]
        # t==l d1
        if (t == l) and d == 1:
            res = []
            for time, lc in zip(time_iso, location):
                res.append(self.getCityWeather(
                    lc, datetime.datetime.combine(date_list[0].date(), time))["temp"])
            ta = False
            for ita in temp_asked:
                if ita in question:
                    ta = True
            if ta or force_return_temp:
                return min_max_func(res)
            return location[min_max_func(res)]

    def mean_handler(self, question, mean_func, time_iso, date_list, location, force_temp=True):
        t = len(time_iso)
        d = len(date_list)
        l = len(location)
        # t0 d1 l1
        if t == 0 and d == 1 and l == 1:
            temp = self.getCityWeatherInDatePeriod(
                location[-1],
                datetime.datetime.combine(date_list[-1].date(),
                                          datetime.time(1, 0)),
                datetime.datetime.combine(date_list[-1].date(),
                                          datetime.time(23, 0)),
            )
            mean_ = mean_func(temp["temp"].to_numpy())
            return "%4.2f" % mean_
        # t1 d1 l1 ---> this shouldn't happen but anyway
        if t == 1 and d == 1 and l == 1:
            return self.getCityWeather(location[0], datetime.datetime.combine(date_list[0].date(), time_iso[0]))["temp"]
        # t0or1 d1 l>=2
        if (t == 0 or t == 1) and d == 1 and l >= 2:
            res = []
            if t == 0:
                if "صبح" in question:
                    time_iso.append(datetime.time(8, 0))
                elif "شب " in question:
                    time_iso.append(datetime.time(21, 0))
                else:
                    time_iso.append(datetime.time(12, 0))

            for lc in location:
                res.append("%4.2f" % np.mean(self.getCityWeather(
                    lc, datetime.datetime.combine(date_list[0].date(), time_iso[0]))["temp"]))
            return res

        # t0 d>=2 l1
        if t == 0 and d >= 2 and l == 1:
            res = self.getCityWeatherInDatePeriod(
                location[0], datetime.datetime.combine(
                    np.min(date_list).date(), datetime.time(1, 0)),
                datetime.datetime.combine(np.max(date_list).date(), datetime.time(23, 59)))["temp"]
            return "%4.2f" % mean_func(res)

        # t0 d>=2 l1
        if t == 1 and d >= 2 and l == 1:
            res = []
            for d in date_list:
                res.append(self.getCityWeather(
                    location[0], datetime.datetime.combine(d.date(), time_iso[0]))["temp"])
            return "%4.2f" % mean_func(res)
        # t>=2 d1 l1
        if t >= 2 and d == 1 and l == 1:
            res = []
            for tim in time_iso:
                res.append(self.getCityWeather(
                    location[0], datetime.datetime.combine(date_list[0].date(), tim))["temp"])
            return "%4.2f" % mean_func(res)
        # t0or1 d==l
        if (t == 0 or t == 1) and d == l:
            res = []
            for lc, dat in zip(location, date_list):
                res.append(self.getCityWeather(
                    lc, datetime.datetime.combine(dat.date(), time_iso[0]))["temp"])
            return mean_func(res)
        # t==d l1
        if (t == d) and l == 1:
            res = []
            for tim, dat in zip(time_iso, date_list):
                res.append(self.getCityWeather(
                    location[0], datetime.datetime.combine(dat.date(), tim))["temp"])
            return "%4.2f" % mean_func(res)
        # t==l d1
        if (t == l) and d == 1:
            res = []
            for tim, lc in zip(time_iso, location):
                res.append(self.getCityWeather(
                    lc, datetime.datetime.combine(date_list[0].date(), tim))["temp"])
            return "%4.2f" % mean_func(res)

    def difference_handler(self, question, time_iso, date_list, location):
        t = len(time_iso)
        d = len(date_list)
        l = len(location)
        # t0or1 d1 l>=2
        if (t == 0 or t == 1) and d == 1 and l >= 2:
            res = []
            if t == 0:
                if "صبح" in question:
                    time_iso.append(datetime.time(8, 0))
                elif "شب " in question:
                    time_iso.append(datetime.time(21, 0))
                else:
                    time_iso.append(datetime.time(12, 0))

            for lc in location:
                res.append(self.getCityWeather(
                    lc, datetime.datetime.combine(date_list[0].date(), time_iso[0]))["temp"])
            if l == 2:
                return "%4.2f" % np.abs(np.diff(res))[0]
            else:
                return np.abs(np.diff(res))

        # t0 d>=2 l1
        if (t == 0 or t == 1) and d >= 2 and l == 1:
            if t == 0:
                if "صبح" in question:
                    time_iso.append(datetime.time(8, 0))
                elif "شب " in question:
                    time_iso.append(datetime.time(21, 0))
                else:
                    time_iso.append(datetime.time(12, 0))

            res = []
            for dat in date_list:
                res.append(self.getCityWeather(
                    location[0], datetime.datetime.combine(dat.date(), time_iso[0]))["temp"])
            if d == 2:
                return "%4.2f" % np.abs(np.diff(res))[0]
            else:
                return np.abs(np.diff(res))

        # t>=2 d1 l1
        if t >= 2 and d == 1 and l == 1:
            res = []
            for tim in time_iso:
                res.append(self.getCityWeather(
                    location[0], datetime.datetime.combine(date_list[0].date(), tim))["temp"])
            if t == 2:
                return "%4.2f" % np.abs(np.diff(res))[0]
            else:
                return np.abs(np.diff(res))
        # t0or1 d==l
        if (t == 0 or t == 1) and d == l:
            res = []
            for lc, dat in zip(location, date_list):
                res.append(self.getCityWeather(
                    lc, datetime.datetime.combine(dat.date(), time_iso[0]))["temp"])
            if d == 2:
                return "%4.2f" % np.abs(np.diff(res))[0]
            else:
                return np.abs(np.diff(res))
        # t==d l1
        if (t == d) and l == 1:
            res = []
            for tim, dat in zip(time_iso, date_list):
                res.append(self.getCityWeather(
                    location[0], datetime.datetime.combine(dat.date(), tim))["temp"])
            if t == 2:
                return "%4.2f" % np.abs(np.diff(res))[0]
            else:
                return np.abs(np.diff(res))
        # t==l d1
        if (t == l) and d == 1:
            res = []
            for tim, lc in zip(time_iso, location):
                res.append(self.getCityWeather(
                    lc, datetime.datetime.combine(date_list[0].date(), tim))["temp"])
            if t == 2:
                return "%4.2f" % np.abs(np.diff(res))[0]
            else:
                return np.abs(np.diff(res))
