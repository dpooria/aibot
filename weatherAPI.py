

import requests
from translate import translator
import numpy as np
import pandas as pd
import datetime
from aibot_date import export_date, gregorian_to_jalali, format_jalali_date
from aibot_time import export_time
from adhanAPI import Adhan
from copy import copy
from vocab import (
    USER_CITY, weather_description_asked,
    weather_temperature_asked,
    tr_weather_description,
    day_asked,
    time_asked,
    weather_logical,
    temp_asked)
from reply_gen import tr_date, tr_time, tr_single_date, tr_single_time
from aibot_utils import location_handler, unique_without_sort, cleaning


# Class to handle weather api
class Weather:
    def __init__(self):
        self.appid = "ee41144a3fc05599947c9ffe87e12bd4"
        self.openweatherapi_5dayforecast_url = "http://api.openweathermap.org/data/2.5/forecast?q={}&APPID=ee41144a3fc05599947c9ffe87e12bd4&units=metric&lang=fa"
        self.eng_openweatherapi = "http://api.openweathermap.org/data/2.5/forecast?q={}&APPID=ee41144a3fc05599947c9ffe87e12bd4&units=metric"
        self.adhan = Adhan()

    def get_city_5dayforecast_weather(self, cityName):
        try:
            data = requests.get(
                self.openweatherapi_5dayforecast_url.format(cityName)).json()
            print("allalal")
        except:
            return pd.DataFrame()
        if data["cod"] == "200":
            print("what??")
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
            try:
                print("fine")
                cityname_eng = translator("fa", "en", cityName)[0][0][0]
                print("ok:{}".format(cityname_eng))
                print("lalalllaal")
                print(self.eng_openweatherapi)
                print(self.eng_openweatherapi.format(cityname_eng))
                data = requests.get(
                    self.eng_openweatherapi.format(cityname_eng)).json()
                print("plps")
                if data["cod"] == "200":
                    print("allright")
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
            except:
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
        answer = {'type': ['1'], 'city': [], 'date': [],
                  'time': [], 'religious_time': [], 'calendar_type': [], 'event': [], 'api_url': [], 'result': []}
        generated_sentence = ""

        location = unique_without_sort(
            location_handler(question, tokens, labels, check_validation=False))
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
        today = datetime.datetime.today()
        if d_n == 0:
            date_list = [today]
            today_j = gregorian_to_jalali(today.year, today.month, today.day)
            answer["date"] = [format_jalali_date(today_j)]
            d_n = 1
            no_date = True
        date_list = unique_without_sort(date_list)
        date_list_jalali = []
        new_date_list = []
        next5day = today + datetime.timedelta(5)
        ignored_date = []
        for d in date_list:
            j = gregorian_to_jalali(d.year, d.month, d.day)
            date_list_jalali.append(format_jalali_date(j))
            if d.date() <= next5day.date() and d.date() >= today.date():
                new_date_list.append(d)
            else:
                ignored_date.append(d)

        if ignored_date:
            ig = []
            for d in ignored_date:
                ig.append(tr_single_date(d))
            generated_sentence = "دیتای بیشتر از ۵ روز آینده و روزهای گذشته وجود ندارد، از تاریخ {} صرف نظر شده است".format(
                " و ".join(ig))

        if len(new_date_list) == 0:
            new_date_list = [today]
            d_n = 1
        date_list = new_date_list
        d_n = len(date_list)
        answer["date"] = date_list_jalali

        l_n = len(location)
        # see if the cities are valid:
        if l_n == 0:
            location = [USER_CITY]
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
            if adhan_url:
                for au in adhan_url:
                    if au:
                        answer["api_url"].append(au)

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
            result, n_generated_sentence = self.logical_handler(question, tokens, labels,
                                                                logicals, time_iso, date_list, location)
            if generated_sentence:
                generated_sentence = generated_sentence + "." + n_generated_sentence
            else:
                generated_sentence = n_generated_sentence
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

            is_weather_description_asked = False
            for w in weather_description_asked:
                if w in question:
                    is_weather_description_asked = True
            for w in weather_temperature_asked:
                if w in question:
                    is_weather_description_asked = False

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
                    if is_weather_description_asked:
                        res = tr_weather_description[result["main"]]
                        answer["result"] = res
                        n_generated_sentence = "هوای {} {} {}، {} است".format(
                            location[0], tr_single_date(date_list[0]), tr_single_time(time_iso[0]), res)
                        if not generated_sentence:
                            generated_sentence = n_generated_sentence
                        else:
                            generated_sentence = generated_sentence + "." + n_generated_sentence
                    else:
                        res = str(result["temp"])
                        answer["result"] = res
                        n_generated_sentence = "دمای هوای {} {} {}، {} درجه سانتی‌گراد است".format(
                            location[0], tr_single_date(date_list[0]), tr_single_time(time_iso[0]), res)
                        if generated_sentence:
                            generated_sentence = generated_sentence + "." + n_generated_sentence
                        else:
                            generated_sentence = n_generated_sentence

            elif ln_d >= 2 and l_n == 1:
                answer["result"] = []
                if generated_sentence:
                    generated_sentence = generated_sentence + \
                        "." + "هوای {} ".format(location[0])
                else:
                    generated_sentence = "هوای {} ".format(location[0])
                s = 0
                for dat in date:
                    result = self.getCityWeather(location[0], dat)
                    if not result.empty:
                        if is_weather_description_asked:
                            res1 = tr_weather_description[result["main"]]
                            answer["result"].append(res1)
                            n_generated_sentence = "{} {}، {} ،است".format(tr_single_date(
                                dat.date()), tr_single_time(dat.time()), res1)
                        else:
                            res1 = str(result["temp"])
                            answer["result"].append(res1)
                            n_generated_sentence = "{} {}، {} ،درجه سانتی‌گراد است".format(tr_single_date(
                                dat.date()), tr_single_time(dat.time()), res1)
                        if s == 0:
                            generated_sentence = generated_sentence + " " + n_generated_sentence
                        else:
                            generated_sentence = generated_sentence + " و " + n_generated_sentence
                        s += 1

            elif l_n == ln_d:
                answer["result"] = []
                for lc, dat in zip(location, date):
                    result = self.getCityWeather(lc, dat)
                    if not result.empty:
                        if is_weather_description_asked:
                            res1 = tr_weather_description[result["main"]]
                            answer["result"].append(res1)
                            n_generated_sentence = "هوای {} {} {}، {} است".format(
                                lc, tr_single_date(dat), tr_single_time(dat.time()), res1)
                        else:
                            res1 = str(result["temp"])
                            answer["result"].append(res1)
                            n_generated_sentence = "دمای هوای {} {} {}، {} درجه سانتی‌گراد است".format(
                                lc, tr_single_date(dat), tr_single_time(dat.time()), res1)
                        if generated_sentence:
                            generated_sentence = generated_sentence + " و " + n_generated_sentence
                        else:
                            generated_sentence = n_generated_sentence

            elif l_n >= 2 and ln_d == 1:
                answer["result"] = []
                n_generated_sentence = "{} {} هوای".format(
                    tr_single_date(date[0]), tr_single_time(date[0].time()))
                if generated_sentence:
                    generated_sentence = generated_sentence + "." + n_generated_sentence
                else:
                    generated_sentence = n_generated_sentence
                s = 0
                for lc in location:
                    result = self.getCityWeather(lc, date[0])
                    if not result.empty:
                        if is_weather_description_asked:
                            res1 = tr_weather_description[result["main"]]
                            answer["result"].append(res1)
                            n_generated_sentence = "{} {} است".format(lc, res1)
                        else:
                            res1 = str(result["temp"])
                            answer["result"].append(res1)
                            n_generated_sentence = "{} {} درجه سانتی‌گراد است".format(
                                lc, res1)
                        if s == 0:
                            generated_sentence = generated_sentence + " " + n_generated_sentence
                        else:
                            generated_sentence = generated_sentence + " و " + n_generated_sentence
                        s += 1
            else:
                answer["result"] = []
                n_generated_sentence = "{} {} هوای".format(
                    tr_single_date(date[0]), tr_single_time(date[0].time()))
                if generated_sentence:
                    generated_sentence = generated_sentence + "." + n_generated_sentence
                else:
                    generated_sentence = n_generated_sentence
                s = 0
                for lc in location:
                    result = self.getCityWeather(lc, date[0])
                    if not result.empty:
                        if is_weather_description_asked:
                            res1 = tr_weather_description[result["main"]]
                            answer["result"].append(res1)
                            n_generated_sentence = "{} {} است".format(lc, res1)
                        else:
                            res1 = str(result["temp"])
                            answer["result"].append(res1)
                            n_generated_sentence = "{} {} درجه سانتی‌گراد است".format(
                                lc, res1)
                        if s == 0:
                            generated_sentence = generated_sentence + " " + n_generated_sentence
                        else:
                            generated_sentence = generated_sentence + " و " + n_generated_sentence
                        s += 1
        if not isinstance(answer["result"], list):
            answer["result"] = [answer["result"]]
        return answer, cleaning(generated_sentence).replace("٫", "/")

    @ staticmethod
    def get_city_info(cityName):
        openweatherapi_5dayforecast_url = "http://api.openweathermap.org/data/2.5/forecast?q={}&APPID=ee41144a3fc05599947c9ffe87e12bd4&units=metric&lang=fa&cnt=1"
        eng_openweatherapi = "http://api.openweathermap.org/data/2.5/forecast?q={}&APPID=ee41144a3fc05599947c9ffe87e12bd4&units=metric&cnt=1"
        try:
            data = requests.get(
                openweatherapi_5dayforecast_url.format(cityName)).json()
        except:
            return None
        if data["cod"] == "200":
            return data["city"]
        else:
            cityname_eng = translator("fa", "en", cityName)[0][0][0]
            try:
                data = requests.get(
                    eng_openweatherapi.format(cityname_eng)).json()
                if data["cod"] == "200":
                    return data["city"]
                else:
                    return None
            except Exception:
                return None

    @ staticmethod
    def check_logical(tokens):
        logicals = []
        for k, v in weather_logical.items():
            if k in tokens:
                logicals.append([k, v])
        return logicals

    def logical_handler(self, question, tokens, labels, logicals, time_iso, date_list, location):
        if len(logicals) == 1 or np.unique(np.array(logicals)[:, 1]).size == 1:
            if logicals[0][1] == "amin" or logicals[0][1] == "amin_abs":
                result, generated_sentence = self.min_max_handler(question, tokens, labels,
                                                                  np.argmin, time_iso, date_list, location)
                return result, generated_sentence
            if logicals[0][1] == "amax" or logicals[0][1] == "amax_abs":
                result, generated_sentence = self.min_max_handler(question, tokens, labels,
                                                                  np.argmax, time_iso, date_list, location)
                return result, generated_sentence
            if logicals[0][1] == "mean":
                return self.mean_handler(question, tokens, labels, np.mean, time_iso, date_list, location)
            if logicals[0][1] == "diff":
                return self.difference_handler(question, tokens, labels, time_iso, date_list, location)
        else:
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
                return self.mean_abs_q(question, tokens, labels, mean_abs, time_iso, date_list, location)
            else:
                return self.m1d1(question, tokens, labels, mean_abs, amax_amin_diff, time_iso, date_list, location)

    def m1d1(self, question, tokens, labels, mean_abs_list, diff_max_min, time_iso, date_list, location):
        generated_sentence = ""
        func_dict = {"amin_abs": np.argmin,
                     "amax_abs": np.argmax, "mean": np.mean, "amax": np.argmax, "amin": np.argmin, "diff": np.diff}
        wfunc_dict = {"amin_abs": self.min_max_handler,
                      "amax_abs": self.min_max_handler, "mean": self.mean_handler}
        t = len(time_iso)
        d = len(date_list)
        l = len(location)
        result = []
        res = []
        ta = False
        for ita in temp_asked:
            if ita in question:
                ta = True
        if len(mean_abs_list) == 1 or np.unique(mean_abs_list).size == 1:
            func = wfunc_dict[mean_abs_list[0]]
            if mean_abs_list[0] == "amin_abs":
                mabs_str = "کمینه"
            elif mean_abs_list[0] == "amax_abs":
                mabs_str = "بیشینه"
            else:
                mabs_str = "میانگین"
            if (t == 0 or t == 1) and d >= 2 and l == 1:
                for dat in date_list:
                    r, _ = func(question, tokens, labels, func_dict[mean_abs_list[0]], time_iso, [
                                dat], location, True)
                    res.append(r)

                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = ["%4.2f" % r for r in result]
                        generated_sentence = "اختلاف {} دمای {}، {}، {} درجه سانتی‌گراد است".format(
                            mabs_str, location[0], " و ".join(tr_date(date_list, tokens, labels)), " و ".join(result))
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                        if diff_max_min[0] == "amin":
                            dmn_str = "سردترین"
                        else:
                            dmn_str = "گرمترین"
                        generated_sentence = "{} {} دمای {} بین {}، {} درجه سانتی‌گراد است".format(
                            dmn_str, mabs_str, location[0], " و ".join(tr_date(date_list, tokens, labels)), result)
                else:
                    result_g = date_list[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]
                    result = gregorian_to_jalali(
                        result_g.year, result_g.month, result_g.day)
                    result = format_jalali_date(result)
                    if diff_max_min[0] == "amin":
                        dmn_str = "سردترین"
                    else:
                        dmn_str = "گرمترین"

                    generated_sentence = "{} {} دمای {}، بین {}، روز {} است".format(
                        dmn_str, mabs_str, location[0], " و ".join(tr_date(date_list, tokens, labels)), tr_single_date(result_g, True))

            elif (t == 0 or t == 1) and d == 1 and l >= 2:
                for lc in location:
                    r, _ = func(
                        question, tokens, labels, func_dict[mean_abs_list[0]], time_iso, date_list, [lc], True)
                    res.append(r)
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = ["%4.2f" % r for r in result]
                        generated_sentence = "اختلاف {} دمای {}، {}، {} درجه سانتی‌گراد است".format(
                            mabs_str, " و ".join(location), tr_single_date(date_list[0]), " و ".join(result))
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                        if diff_max_min[0] == "amin":
                            dmn_str = "سردترین"
                        else:
                            dmn_str = "گرمترین"

                        generated_sentence = "{} {} دمای {}، {}، {} درجه سانتی‌گراد است".format(dmn_str,
                                                                                                mabs_str, " و ".join(location), tr_single_date(date_list[0]), " و ".join(result))

                else:
                    result = location[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]
                    if diff_max_min[0] == "amin":
                        dmn_str = "سردترین"
                    else:
                        dmn_str = "گرمترین"
                    generated_sentence = "{} {} دمای {}، بین {}، روز {} است".format(
                        dmn_str, mabs_str, tr_single_date(date_list[0]), " و ".join(location), result)

            elif t >= 2 and l == 1 and d == 1:
                for tim in time_iso:
                    r, _ = func(question, func_dict[mean_abs_list[0]], [
                                tim], date_list, location, True)
                    res.append(r)
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = ["%4.2f" % r for r in result]
                        generated_sentence = "اختلاف {} دمای {}، {} {}، {} درجه سانتی‌گراد است".format(
                            mabs_str, location[0], tr_single_date(date_list[0]), " و ".join(tr_time(time_iso, tokens, labels)), " و ".join(result))

                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                        if diff_max_min[0] == "amin":
                            dmn_str = "سردترین"
                        else:
                            dmn_str = "گرمترین"

                        generated_sentence = "{} {} دمای {}، {} {}، {} درجه سانتی‌گراد است".format(dmn_str,
                                                                                                   mabs_str, location[0], tr_single_date(date_list[0]), " و ".join(tr_time(time_iso, tokens, labels)), result)

                else:
                    result_g = time_iso[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]
                    result = result_g.strftime("%H:%M")
                    if diff_max_min[0] == "amin":
                        dmn_str = "سردترین"
                    else:
                        dmn_str = "گرمترین"

                    generated_sentence = "{} {} دمای {}، {}، بین {}، در زمان {} است".format(dmn_str, mabs_str, location[0], tr_single_date(
                        date_list[0]), " و ".join(tr_time(time_iso, tokens, labels)), tr_single_time(result_g))

            ###
            elif (t == d) and l == 1:
                res_str = []
                for dat, tim in zip(date_list, time_iso):
                    r, _ = func(question, func_dict[mean_abs_list[0]], [
                                tim], [dat], location, True)
                    res.append(r)
                    res_str.append("{} {}".format(
                        tr_single_date(dat), tr_single_time(tim)))
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = ["%4.2f" % r for r in result]
                        generated_sentence = "اختلاف {} دمای هوای {} بین {}، {} درجه سانتی‌گراد است".format(
                            mabs_str, location[0], " و ".join(res_str), " و ".join(result))

                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                        if diff_max_min[0] == "amin":
                            dmn_str = "سردترین"
                        else:
                            dmn_str = "گرمترین"
                        generated_sentence = "{} {} دمای هوای {} بین {}، {} درجه سانتی‌گراد است".format(dmn_str,
                                                                                                        mabs_str, location[0], " و ".join(res_str), " و ".join(result))

                else:
                    result_g = date_list[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]
                    result = gregorian_to_jalali(
                        result_g.year, result_g.month, result_g.day)
                    result = format_jalali_date(result)
                    if diff_max_min[0] == "amin":
                        dmn_str = "سردترین"
                    else:
                        dmn_str = "گرمترین"
                    generated_sentence = "{} {} دمای هوا در {} بین {}، {} است".format(
                        dmn_str, mabs_str, location[0], " و ".join(res_str), tr_single_date(result_g))
            elif (t == 0 or t == 1) and d == l:
                res_str = []
                for lc, dat in zip(location, date_list):
                    r, _ = func(question, tokens, labels, func_dict[mean_abs_list[0]], time_iso, [
                                dat], [lc], True)
                    res_str.append("{} {}".format(tr_single_date(dat), lc))
                    res.append(r)
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = ["%4.2f" % r for r in result]
                        generated_sentence = "اختلاف {} دما بین {}، {} درجه سانتی‌گراد است".format(
                            mabs_str, " و ".join(res_str), " و ".join(result))
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                        if diff_max_min[0] == "amin":
                            dmn_str = "سردترین"
                        else:
                            dmn_str = "گرمترین"
                        generated_sentence = "{} {} دمای بین {}، {} درجه سانتی‌گراد است".format(
                            dmn_str, mabs_str, " و ".join(res_str), result)
                else:
                    result = location[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]
                    if diff_max_min[0] == "amin":
                        dmn_str = "سردترین"
                    else:
                        dmn_str = "گرمترین"

                    generated_sentence = "{} {}  دما بین {}، {} دارا میباشد".format(
                        dmn_str, mabs_str, " و ".join(res_str), result)
        else:
            lg = len(mean_abs_list)
            mabs_str = []
            if l == 1 and d == 1 and (t == 0 or t == 1):
                for mabs in mean_abs_list:
                    r, _ = wfunc_dict[mabs](
                        question, tokens, labels, func_dict[mabs], time_iso, date_list, location, True)
                    if mabs == "amin_abs":
                        mabs_str.append("حداقل")
                    elif mabs == "amax_abs":
                        mabs_str.append("حداکثر")
                    else:
                        mabs_str.append("میانگین")
                    res.append(r)
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = ["%4.2f" % r for r in result]
                        generated_sentence = "اختلاف {} دمای {} {}، {} درجه سانتی‌گراد است".format(
                            " و ".join(mabs_str), location[0], tr_single_date(date_list[0]), " و ".join(result))
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                        if diff_max_min[0] == "amin":
                            dmn_str = "سردترین"
                        else:
                            dmn_str = "گرمترین"
                        generated_sentence = "{} {} دمای {} {}، {} درجه سانتی‌گراد است".format(dmn_str,
                                                                                               " و ".join(mabs_str), location[0], tr_single_date(date_list[0]), result)

            elif lg == d and l == 1 and (t == 0 or t == 1):
                mabs_dat_str = []
                for mabs, dat in zip(mean_abs_list, date_list):
                    r, _ = wfunc_dict[mabs](question, tokens, labels, func_dict[mabs], time_iso, [
                                            dat], location, True)
                    d_str = tr_single_date(dat)
                    if mabs == "amin_abs":
                        mabs_dat_str.append("حداقل دمای {}".format(d_str))
                    elif mabs == "amax_abs":
                        mabs_dat_str.append("حداکثر دمای {}".format(d_str))
                    else:
                        mabs_dat_str.append("میانگین دمای {}".format(d_str))
                    res.append(r)
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = ["%4.2f" % r for r in result]
                        generated_sentence = "اختلاف دمای {} {}، {} درجه سانتی‌گراد است".format(
                            " و ".join(mabs_dat_str), location[0], " و ".join(result))
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                        if diff_max_min[0] == "amin":
                            dmn_str = "حداقل"
                        else:
                            dmn_str = "حداکثر"
                        generated_sentence = "اختلاف دمای {} {}، {} درجه سانتی‌گراد است".format(
                            " و ".join(mabs_dat_str), location[0], result)

                else:
                    result_g = date_list[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]
                    result = gregorian_to_jalali(
                        result_g.year, result_g.month, result_g.day)
                    result = format_jalali_date(result)
                    if diff_max_min[0] == "amin":
                        dmn_str = "سردترین"
                    else:
                        dmn_str = "گرمترین"
                    generated_sentence = "{} دما بین {}، {} روز {} است".format(
                        dmn_str, " و ".join(mabs_dat_str), location[0], tr_single_date(result_g))
            elif lg == l and d == 1 and (t == 0 or t == 1):
                mabs_lc_str = []
                for mabs, lc in zip(mean_abs_list, location):
                    r, _ = wfunc_dict[mabs](
                        question, tokens, labels, func_dict[mabs], time_iso, date_list, [lc], True)
                    res.append(r)
                    if mabs == "amin_abs":
                        mabs_lc_str.append("حداقل دمای {}".format(lc))
                    elif mabs == "amax_abs":
                        mabs_lc_str.append("حداکثر دمای {}".format(lc))
                    else:
                        mabs_lc_str.append("میانگین دمای {}".format(lc))
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = ["%4.2f" % r for r in result]
                        generated_sentence = "اختلاف دمای {}، {}، {} درجه سانتی‌گراد است".format(
                            " و ".join(mabs_lc_str), tr_single_date(date_list[0]), " و ".join(result))
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                        if diff_max_min == "amin":
                            dmn_str = "حداقل"
                        else:
                            dmn_str = "حداکثر"
                        generated_sentence = "{} دمای {}، {}، {} درجه سانتی‌گراد است".format(dmn_str,
                                                                                             " و ".join(mabs_lc_str), tr_single_date(date_list[0]), " و ".join(result))
                else:
                    result = location[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]
                    if diff_max_min == "amin":
                        dmn_str = "سردترین"
                    else:
                        dmn_str = "گرمترین"
                    generated_sentence = "{} دما {} بین {} را  {} دارد".format(
                        dmn_str, tr_single_date(date_list[0]), " و ".join(mabs_lc_str), result)
            elif lg == t and d == 1 and l == 1:
                mabs_str = []
                for mabs, tim in zip(mean_abs_list, time_iso):
                    r, _ = wfunc_dict[mabs](question, tokens, labels, func_dict[mabs], [
                        tim], date_list, location, True)
                    if mabs == "amin_abs":
                        mabs_str.append("حداقل دمای")
                    elif mabs == "amax_bas":
                        mabs_str.append("حداکثر دمای")
                    else:
                        mabs_str.append("میانگین")
                    res.append(r)
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = ["%4.2f" % r for r in result]
                        generated_sentence = "اختلاف دمای {}، {}، بین {} {}، {} درجه سانتی‌گراد میباشد".format(
                            " و ".join(mabs_str), location[0], " و ".join(tr_time(time_iso, tokens, labels)), tr_single_date(date_list[0]), " و ".join(result))
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                        if diff_max_min == "amin":
                            dmn_str = "حداقل"
                        else:
                            dmn_str = "حداکثر"
                        generated_sentence = "{} دمای {}، {}، بین {} {}، {} درجه سانتی‌گراد میباشد".format(dmn_str,
                                                                                                           " و ".join(mabs_str), location[0], " و ".join(tr_time(time_iso, tokens, labels)), tr_single_date(date_list[0]), result)

                else:
                    result_g = time_iso[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]
                    result = result_g.strftime("%H:%M")
                    if diff_max_min == "amin":
                        dmn_str = "سردترین"
                    else:
                        dmn_str = "گرمترین"
                    generated_sentence = "دمای {} {} {} {}، در زمان {} میباشد {}".format(dmn_str, " و ".join(
                        mabs_str), location[0], tr_single_date(date_list[0]), " و ".join(tr_time(time_iso, tokens, labels)), tr_single_time(result_g))
            elif (lg == l) and (l == d) and (t == 0 or t == 1):
                unk_list = []
                for i in range(l):
                    r, _ = wfunc_dict[mean_abs_list[i]](
                        question, tokens, labels, func_dict[mean_abs_list[i]], time_iso, date_list[i], location[i], True)
                    res.append(r)
                    if mean_abs_list[i] == "amax_abs":
                        unk_list.append("حداکثر دمای {} {}".format(
                            tr_single_date(date_list[i])), location[i])
                    elif mean_abs_list[i] == "amin_abs":
                        unk_list.append("حداقل دمای {} {}".format(
                            tr_single_date(date_list[i])), location[i])
                    else:
                        unk_list.append("میانگین دمای {} {}".format(
                            tr_single_date(date_list[i])), location[i])

                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = ["%4.2f" % r for r in result]
                        generated_sentence = 'اختلاف دمای {}، {} درجه سانتی‌گراد میباشد'.format(
                            " و ".join(unk_list), " و ".join(result))
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                        if diff_max_min[0] == "amin":
                            dmn_str = "سردترین"
                        else:
                            dmn_str = "گرمترین"
                        generated_sentence = '{} دمای {}، {} درجه سانتی‌گراد میباشد'.format(dmn_str,
                                                                                            " و ".join(unk_list), result)

                else:
                    result = location[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]
                    if diff_max_min[0] == "amin":
                        dmn_str = "سردترین"
                    else:
                        dmn_str = "گرمترین"
                    generated_sentence = "{} شهر بین {}، {} میباشد".format(
                        dmn_str, " و ".join(unk_list), result)
            elif (lg == l) and (l == t) and (d == 1):
                unk_list = []
                for i in range(l):
                    if mean_abs_list[i] == "amax_abs":
                        unk_list.append("حداکثر دمای {}".format(location[i]))
                    elif mean_abs_list[i] == "amin_abs":
                        unk_list.append("حداقل دمای {}".format(location[i]))
                    else:
                        unk_list.append("میانگین دمای {}".format(location[i]))

                    r, _ = wfunc_dict[mean_abs_list[i]](
                        question, tokens, labels, func_dict[mean_abs_list[i]], time_iso[i], date_list, location[i], True)
                    res.append(r)
                if ta or diff_max_min[0] == "diff":
                    if diff_max_min[0] == "diff":
                        result = np.diff(
                            np.array(res, dtype="d"))
                        result = ["%4.2f" % r for r in result]
                        generated_sentence = "اختلاف دمای {}، {}، {}، {} درجه سانتی‌گراد است".format(" و ".join(
                            unk_list), " و ".join(tr_time(time_iso, tokens, labels)), tr_single_date(date_list[0]), " و ".join(result))
                    else:
                        result = res[func_dict[diff_max_min[0]](
                            np.array(res, dtype="d"))]
                        if diff_max_min[0] == "amin":
                            dmn_str = "حداقل"
                        else:
                            dmn_str = "حداکثر"

                        generated_sentence = "{} دمای {}، {}، {}، {} درجه سانتی‌گراد است".format(dmn_str, " و ".join(
                            unk_list), " و ".join(tr_time(time_iso, tokens, labels)), tr_single_date(date_list[0]), result)
                else:
                    result = location[func_dict[diff_max_min[0]](
                        np.array(res, dtype="d"))]
                    if diff_max_min[0] == "amin":
                        dmn_str = "سردترین"
                    else:
                        dmn_str = "گرمترین"

                    generated_sentence = "{} بین {}، {}، {}، {} میباشد".format(dmn_str, " و ".join(
                        unk_list), " و ".join(tr_time(time_iso, tokens, labels)), tr_single_date(date_list[0]), result)

        return result, generated_sentence

    def mean_abs_q(self, question, tokens, labels, mean_abs_list, time_iso, date_list, location):
        func_dict = {"amin_abs": np.argmin,
                     "amax_abs": np.argmax, "mean": np.mean}
        t = len(time_iso)
        d = len(date_list)
        l = len(location)
        if len(mean_abs_list) == 2:
            if mean_abs_list[1] == "amin_abs" or mean_abs_list[1] == "amax_abs":
                func = self.min_max_handler
                if mean_abs_list == "amin_abs":
                    g_word2 = "حداقل"
                else:
                    g_word2 = "حداکثر"
            else:
                func = self.mean_handler
                g_word2 = "میانگین"
            res = []

            ta = False
            for ita in temp_asked:
                if ita in question:
                    ta = True
            if (t == 0 or t == 1) and d >= 2 and l == 1:
                for dat in date_list:
                    r, _ = func(question, tokens, labels, func_dict[mean_abs_list[1]], time_iso, [
                                dat], location, True)
                    res.append(r)
                if ta or mean_abs_list[0] == "mean":
                    if mean_abs_list[0] == "mean":
                        result = "%4.2f" % func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))
                        generated_sentence = "میانگین {} دماهای {} {}، {} درجه سانتی‌گراد است".format(
                            g_word2, location[0], " و ".join(tr_date(date_list, tokens, labels)), result)
                    else:
                        result = res[func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))]
                        if mean_abs_list[0] == "amax_abs":
                            g_word1 = "حداکثر"
                        else:
                            g_word1 = "حداقل"
                        generated_sentence = "{} {} دماهای {} {}، {} درجه سانتی‌گراد است".format(g_word1,
                                                                                                 g_word2, location[0], " و ".join(tr_date(date_list, tokens, labels)), result)
                else:
                    if mean_abs_list[0] == "amax_abs":
                        g_word1 = "گرمترین"
                    else:
                        g_word1 = "سردترین"

                    result_g = date_list[func_dict[mean_abs_list[0]](
                        np.array(res, dtype="d"))]
                    result = gregorian_to_jalali(
                        result_g.year, result_g.month, result_g.day)
                    result = format_jalali_date(result)
                    generated_sentence = "{} {} {} {}، {} در روز {} است".format(g_word1,
                                                                                g_word2, location[0], " و ".join(tr_date(date_list, tokens, labels)), tr_single_date(result_g))

            elif (t == 0 or t == 1) and d == 1 and l >= 2:
                for lc in location:
                    r, _ = func(
                        question, tokens, labels, func_dict[mean_abs_list[1]], time_iso, date_list, [lc], True)
                    res.append(r)
                if ta or mean_abs_list[0] == "mean":
                    if mean_abs_list[0] == "mean":
                        result = "%4.2f" % func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))
                        generated_sentence = "میانگین {} دماهای {} {}، {} درجه سانتی‌گراد است".format(
                            g_word2, tr_single_date(date_list[0]), " و ".join(location), result)
                    else:
                        result = res[func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))]
                        if mean_abs_list[0] == "amax_abs":
                            g_word1 = "حداکثر"
                        else:
                            g_word1 = "حداقل"
                        generated_sentence = "{} {} دماهای {} {}، {} درجه سانتی‌گراد است".format(g_word1,
                                                                                                 g_word2, tr_single_date(date_list[0]), " و ".join(location), result)

                else:
                    result = location[func_dict[mean_abs_list[0]](
                        np.array(res, dtype="d"))]
                    if mean_abs_list[0] == "amax_abs":
                        g_word1 = "گرمترین"
                    else:
                        g_word1 = "سردترین"

                    generated_sentence = "{} {} دما {} بین {} شهر {} است".format(g_word1,
                                                                                 g_word2, tr_single_date(date_list[0]), " و ".join(location), result)

            elif t >= 2 and l == 1 and d == 1:
                for tim in time_iso:
                    r, _ = func(question, tokens, labels, func_dict[mean_abs_list[1]], [
                        tim], date_list, location, True)
                    res.append(r)
                if ta or mean_abs_list[0] == "mean":
                    if mean_abs_list[0] == "mean":
                        result = "%4.2f" % func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))

                        generated_sentence = "میانگین {} دمای {} {} {}، {} درجه سانتی‌گراد است".format(
                            g_word2, location[0], " و ".join(tr_time(time_iso, tokens, labels)), tr_single_date(date_list[0]), result)

                    else:
                        if mean_abs_list[0] == "amax_abs":
                            g_word1 = "حداکثر"
                        else:
                            g_word1 = "حداقل"

                        result = res[func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))]
                        generated_sentence = "{} {} دمای {} {} {}، {} درجه سانتی‌گراد است".format(
                            g_word1, g_word2, location[0], " و ".join(tr_time(time_iso, tokens, labels)), tr_single_date(date_list[0]), result)
                else:
                    result_g = time_iso[func_dict[mean_abs_list[0]](
                        np.array(res, dtype="d"))]
                    result = result_g.strftime("%H:%M")
                    if mean_abs_list[0] == "amax_abs":
                        g_word1 = "گرمترین"
                    else:
                        g_word1 = "سردترین"
                    generated_sentence = "{} {} بین {} در {} {}، {} است".format(g_word1, g_word2, " و ".join(
                        tr_time(time_iso, tokens, labels)), location[0], tr_single_date(date_list[0]), tr_single_time(result_g))

            elif (t == 0 or t == 1) and d == l:
                for dat, lc in zip(date_list, location):
                    r, _ = func(question, tokens, labels, func_dict[mean_abs_list[1]], time_iso, [
                                dat], [lc], True)
                    res.append(r)
                if ta or mean_abs_list[0] == "mean":
                    if mean_abs_list[0] == "mean":
                        result = "%4.2f" % func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))
                        generated_sentence = "میانگین {} دمای شهرهای {} {}، {} درجه سانتی‌گراد است".format(
                            g_word2, " و ".join(location), " و ".join(tr_date(date_list, tokens, labels)), result)
                    else:
                        result = res[func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))]
                        if mean_abs_list[0] == "amax_abs":
                            g_word1 = "حداقل"
                        else:
                            g_word1 = "حداکثر"
                        generated_sentence = "{} {} دمای هوای شهرهای {} {}، {} درجه سانتی‌گراد است".format(
                            g_word1, g_word2, " و ".join(location), " و ".join(tr_date(date_list, tokens, labels)), result)
                else:
                    result = location[func_dict[mean_abs_list[0]](
                        np.array(res, dtype="d"))]
                    if mean_abs_list[0] == "amax_abs":
                        g_word1 = "گرمترین"
                    else:
                        g_word1 = "سردترین"
                    generated_sentence = "{} {} دمای هوا بین شهرهای {} {}، {} میباشد".format(
                        g_word1, g_word2, " و ".join(location), " و ".join(tr_date(date_list, tokens, labels)), result)

            elif t == l and d == 1:
                for tim, lc in zip(time_iso, location):
                    res.append(func(question, tokens, labels, func_dict[mean_abs_list[1]], [
                               tim], date_list, [lc], True))
                if ta or mean_abs_list[0] == "mean":
                    if mean_abs_list[0] == "mean":
                        result = "%4.2f" % func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))
                        generated_sentence = "میانگین {} دما در {} {} {}، {} درجه سانتی‌گراد است".format(g_word2, " و ".join(
                            location), " و ".join(tr_time(time_iso, tokens, labels)), tr_single_date(date_list[0]), result)
                    else:
                        result = res[func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))]
                        if mean_abs_list[0] == "amax_abs":
                            g_word1 = "حداقل"
                        else:
                            g_word1 = "حداکثر"
                        generated_sentence = "{} {} دمای هوا {} {} {}، {} درجه سانتیگراد هست".format()
                else:
                    result = location[func_dict[mean_abs_list[0]](
                        np.array(res, dtype="d"))]
                    if mean_abs_list[0] == "amax_abs":
                        g_word1 = "گرمترین"
                    else:
                        g_word1 = "سردترین"
                    generated_sentence = "{} {} دمای هوا بین {} {} در {} شهر {} دارا میباشد".format(g_word1, g_word2, " و ".join(
                        tr_time(time_iso, tokens, labels)), " و ".join(location), tr_single_date(date_list[0]), result)

            elif t == d and l == 1:
                for tim, dat in zip(time_iso, date_list):
                    res.append(func(question, tokens, labels, func_dict[mean_abs_list[1]], [
                               tim], [dat], location, True))
                if ta or mean_abs_list[0] == "mean":
                    if mean_abs_list[0] == "mean":
                        result = "%4.2f" % func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))
                        generated_sentence = "میانگین {} دمای هوای {} {} {}، {} درجه سانتی‌گراد است".format(g_word2, location[0], " و ".join(
                            tr_time(time_iso, tokens, labels)), " و ".join(tr_date(date_list, tokens, labels)), result)
                    else:
                        result = res[func_dict[mean_abs_list[0]](
                            np.array(res, dtype="d"))]
                        if mean_abs_list[0] == "amax_abs":
                            g_word1 = "حداقل"
                        else:
                            g_word1 = "حداکثر"
                        generated_sentence = "{} {} دمای هوای {} {} {}، {} درجه سانتی‌گراد است".format(g_word1, g_word2, location[0], " و ".join(
                            tr_time(time_iso, tokens, labels)), " و ".join(tr_date(date_list, tokens, labels)), result)
                else:
                    result_g = date_list[func_dict[mean_abs_list[0]](
                        np.array(res, dtype="d"))]
                    result = gregorian_to_jalali(
                        result_g.year, result_g.month, result_g.day)
                    result = format_jalali_date(result)
                    if mean_abs_list[0] == "amax_abs":
                        g_word1 = "گرمترین"
                    else:
                        g_word1 = "سردترین"
                    generated_sentence = "در بین {} {} {} {} دمای {}،را روز {} دارد".format(" و ".join(tr_date(
                        date_list, tokens, labels)), " و ".join(tr_time(time_iso, tokens, labels)), g_word1, g_word2, location[0], tr_single_date(result_g))
            return result, generated_sentence

    def min_max_handler(self, question, tokens, labels, min_max_func, time_iso, date_list, location, force_return_temp=False):
        t = len(time_iso)
        d = len(date_list)
        l = len(location)

        # t1 d1 l1 ---> this shouldn't happen but anyway!
        if t == 1 and d == 1 and l == 1:
            t = 0
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
                if min_max_func == np.argmax:
                    generated_sentence = "حداکثر دما {} در {} در ساعت {} رخ خواهد داد".format(
                        tr_date(date_list, tokens, labels)[0], location[0], result)
                else:
                    generated_sentence = "حداقل دما {} در {} در ساعت {} رخ خواهد داد".format(
                        tr_date(date_list, tokens, labels)[0], location[0], result)

            else:
                result = temp["temp"].iloc[result]
                generated_sentence = "temp_time"
                if min_max_func == np.argmin:
                    generated_sentence = "حداقل دمای {} در {} {} درجه سانتی گراد میباشد".format(
                        tr_date(date_list, tokens, labels)[0], location[0], result)
                else:
                    generated_sentence = "حداکثر دمای {} در {} {} درجه سانتی گراد میباشد".format(
                        tr_date(date_list, tokens, labels)[0], location[0], result)
            return str(result), cleaning(generated_sentence)
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
            result = location[min_max_func(res)]
            if t == 0:
                if min_max_func == np.argmin:
                    generated_sentence = "بین شهرهای {}،  {} دمای هوای {} سردتر است".format(
                        " و ".join(location), tr_date(date_list, tokens, labels)[0], result)
                else:
                    generated_sentence = "بین شهرهای {}، {} دمای هوای {} گرم‌تر است".format(
                        " و ".join(location), tr_date(date_list, tokens, labels)[0], result)
            else:
                if min_max_func == np.argmin:
                    generated_sentence = "بین شهرهای {}، {} {} دمای هوای {} سردتر است".format(
                        " و ".join(location), tr_date(date_list, tokens, labels)[0], tr_time(time_iso, tokens, labels)[0], result)
                else:
                    generated_sentence = "بین شهرهای {}، {} {} دمای هوای {} گرمتر است".format(
                        " و ".join(location), tr_date(date_list, tokens, labels)[0],  tr_time(time_iso, tokens, labels)[0], result)

            return result, cleaning(generated_sentence)
        # t0 d>=2 l1
        if t == 0 and d >= 2 and l == 1:
            res = self.getCityWeatherInDatePeriod(
                location[0], datetime.datetime.combine(
                    np.min(date_list).date(), datetime.time(1, 0)),
                datetime.datetime.combine(np.max(date_list).date(), datetime.time(23, 59)))
            if not res.empty:
                ta = False
                for ita in temp_asked:
                    if ita in question:
                        ta = True
                if ta or force_return_temp:
                    result = res["temp"].iloc[min_max_func(res["temp"])]
                    if min_max_func == np.argmax:
                        generated_sentence = "حداکثر دما در {}، {}، {} درجه سانتی‌گراد است".format(
                            " و ".join(tr_date(date_list, tokens, labels)), location[0], result)
                    else:
                        generated_sentence = "حداقل دما در ،{} {}، {} درجه سانتی‌گراد است".format(
                            " و ".join(tr_date(date_list, tokens, labels)), location[0], result)
                else:
                    result_g = res["dt_txt"].iloc[min_max_func(res["temp"])]
                    result = gregorian_to_jalali(
                        result_g.year, result_g.month, result_g.day)
                    result = format_jalali_date(result)
                    result_g = cleaning(tr_single_date(result_g))
                    if min_max_func == np.argmax:
                        generated_sentence = "گرمترین روز بین روزهای {} در {}، {} میباشد ".format(
                            " و ".join(tr_date(date_list, tokens, labels)), location[0], result_g)
                    else:
                        generated_sentence = "سردترین روز بین روزهای {} در {}، {} میباشد".format(
                            " و ".join(tr_date(date_list, tokens, labels)), location[0], result_g)
                return result, cleaning(generated_sentence)

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
                if min_max_func == np.argmax:
                    generated_sentence = "حداکثر دمای {} در {} در {}، {} درجه سانتی‌گراد است".format(location[0],
                                                                                                     " و ".join(tr_date(date_list, tokens, labels)), tr_single_time(time_iso[0]), result)
                else:
                    generated_sentence = "حداقل دمای {} در {} در {}، {} درجه سانتی‌گراد است".format(location[0],
                                                                                                    " و ".join(tr_date(date_list, tokens, labels)), tr_single_time(time_iso[0]), result)

            else:
                result_g = date_list[min_max_func(res)]
                result = gregorian_to_jalali(
                    result_g.year, result_g.month, result_g.day)
                result = format_jalali_date(result)
                result_g = cleaning(tr_single_date(result_g))
                if min_max_func == np.argmax:
                    generated_sentence = "گرمترین روز {} بین روزهای {} در {}، {} میباشد ".format(location[0],
                                                                                                 " و ".join(tr_date(date_list, tokens, labels)), tr_single_time(time_iso[0]), result_g)
                else:
                    generated_sentence = "سردترین روز {} بین روزهای {} در {}، {} میباشد".format(location[0],
                                                                                                " و ".join(tr_date(date_list, tokens, labels)), tr_single_time(time_iso[0]), result_g)

            return result, cleaning(generated_sentence)

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
                result = min_max_func(res)
                if min_max_func == np.argmax:
                    generated_sentence = "حداکثر دمای {} در {} در {}، {} درجه سانتی‌گراد است".format(location[0],
                                                                                                     tr_single_date(date_list[0]), " و ".join(tr_time(time_iso, tokens, labels)), result)
                else:
                    generated_sentence = "حداقل دمای {} در {} در {}، {} درجه سانتی‌گراد است".format(location[0],
                                                                                                    tr_single_date(date_list[0]), " و ".join(tr_time(time_iso, tokens, labels)), result)
            else:
                result_g = time_iso[min_max_func(res)]
                result = result_g.strftime("%H:%M")
                if min_max_func == np.argmax:
                    generated_sentence = "گرمترین زمان بین {} {} در {}، {} میباشد ".format(" و ".join(tr_time(
                        time_iso, tokens, labels)), tr_single_date(date_list[0]), location[0], tr_single_time(result_g))
                else:
                    generated_sentence = "سردترین زمان بین {}، {} در {}، {} میباشد ".format(" و ".join(tr_time(
                        time_iso, tokens, labels)), tr_single_date(date_list[0]), location[0], tr_single_time(result_g))
            return result, generated_sentence
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
                result = min_max_func(res)
                if min_max_func == np.argmax:
                    generated_sentence = "بین شهرهای {} در {} حداکثر دما {} درجه سانتی‌گراد میباشد".format(
                        " و ".join(location), " و ".join(tr_date(date_list, tokens, labels)), result)
                else:
                    generated_sentence = "بین شهرهای {} در {} حداکثر دما {} درجه سانتی‌گراد میباشد".format(
                        " و ".join(location), " و ".join(tr_date(date_list, tokens, labels)), result)
            else:
                result = location[min_max_func(res)]
                if min_max_func == np.argmax:
                    generated_sentence = "بین شهرهای {} در {} گرمترین شهر، {} است".format(
                        " و ".join(location), " و ".join(tr_date(date_list, tokens, labels)), result)
                else:
                    generated_sentence = "بین شهرهای {} در {} سردترین شهر، {} است".format(
                        " و ".join(location), " و ".join(tr_date(date_list, tokens, labels)), result)
            return result, generated_sentence
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
                result = min_max_func(res)
                if min_max_func == np.argmax:
                    generated_sentence = "حداکثر دمای {} در {}، {}، {} درجه سانتی‌گراد میباشد".format(
                        location[0], " و ".join(tr_date(date_list, tokens, labels)), " و ".join(tr_time(time_iso, tokens, labels)), result)
                else:
                    generated_sentence = "حداقل دمای {} در {}، {}، {} درجه سانتی‌گراد میباشد".format(
                        location[0], " و ".join(tr_date(date_list, tokens, labels)), " و ".join(tr_time(time_iso, tokens, labels)), result)
            else:
                result_g = date_list[min_max_func(res)]
                result = gregorian_to_jalali(
                    result_g.year, result_g.month, result_g.day)
                result = format_jalali_date(result)
                result_g = cleaning(tr_single_date(result_g))
                if min_max_func == np.argmax:
                    generated_sentence = "گرمترین زمان بین {}، {} در {} {} است".format(
                        " و ".join(tr_time(time_iso, tokens, labels)), " و ".join(tr_date(date_list, tokens, labels)), location[0], result_g)
                else:
                    generated_sentence = "سردترین زمان بین {}، {} در {} {} است".format(
                        " و ".join(tr_time(time_iso, tokens, labels)), " و ".join(tr_date(date_list, tokens, labels)), location[0], result_g)

            return result, generated_sentence
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
                result = min_max_func(res)
                if min_max_func == np.argmax:
                    generated_sentence = "حداکثر دمای شهرهای {} در {} {}، {} درجه سانتی‌گراد میباشد".format(" و ".join(
                        location), tr_single_date(date_list[0]), " و ".join(tr_time(time_iso, tokens, labels)), result)
                else:
                    generated_sentence = "حداقل دمای شهرهای {} در {} {}، {} درجه سانتی‌گراد میباشد".format(" و ".join(
                        location), tr_single_date(date_list[0]), " و ".join(tr_time(time_iso, tokens, labels)), result)
            else:
                result = location[min_max_func(res)]
                if min_max_func == np.argmax:
                    generated_sentence = "گرمترین شهر بین شهرهای {} در زمان {} در {}، {} است".format(" و ".join(
                        location), " و ".join(tr_time(time_iso, tokens, labels)), tr_single_date(date_list[0]), result)
                else:
                    generated_sentence = "سردترین شهر بین شهرهای {} در زمان {} در {}، {} است".format(" و ".join(
                        location), " و ".join(tr_time(time_iso, tokens, labels)), tr_single_date(date_list[0]), result)
            return result, generated_sentence

    def mean_handler(self, question, tokens, labels, mean_func, time_iso, date_list, location, force_temp=True):
        t = len(time_iso)
        d = len(date_list)
        l = len(location)
        # t1 d1 l1 ---> this shouldn't happen but anyway
        if t == 1 and d == 1 and l == 1:
            t = 0
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
            return "%4.2f" % mean_, "میانگین دمای هوای {} در {}، {} درجه سانتی‌گراد است".format(location[0], tr_single_date(date_list[0]), "%4.2f" % mean_)
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

            generated_sentence = []
            for i, lc in enumerate(location):
                res.append("%4.2f" % np.mean(self.getCityWeather(
                    lc, datetime.datetime.combine(date_list[0].date(), time_iso[0]))["temp"]))
                generated_sentence.append("میانگین دمای هوای {} {}، {} درجه سانتی‌گراد است".format(
                    lc, tr_single_date(date_list[0]), res[i]))
            return res, " و ".join(generated_sentence)

        # t0 d>=2 l1
        if t == 0 and d >= 2 and l == 1:
            res = self.getCityWeatherInDatePeriod(
                location[0], datetime.datetime.combine(
                    np.min(date_list).date(), datetime.time(1, 0)),
                datetime.datetime.combine(np.max(date_list).date(), datetime.time(23, 59)))["temp"]
            result = "%4.2f" % mean_func(res)
            return result, 'میانگین دمای هوای {} در {}، {} درجه سانتی‌گراد است'.format(location[0], " و ".join(tr_date(date_list, tokens, labels)), result)

        # t0 d>=2 l1
        if t == 1 and d >= 2 and l == 1:
            res = []
            for d in date_list:
                res.append(self.getCityWeather(
                    location[0], datetime.datetime.combine(d.date(), time_iso[0]))["temp"])
            result = "%4.2f" % mean_func(res)
            generated_sentence = 'میانگین دمای هوای {} {} {}، {} درجه سانتی‌گراد می‌باشد'.format(location[0], " و ".join(tr_date(date_list, tokens, labels)),
                                                                                                 tr_single_time(time_iso[0]), result)
            return result, generated_sentence
        # t>=2 d1 l1
        if t >= 2 and d == 1 and l == 1:
            res = []
            for tim in time_iso:
                res.append(self.getCityWeather(
                    location[0], datetime.datetime.combine(date_list[0].date(), tim))["temp"])
            result = "%4.2f" % mean_func(res)
            generated_sentence = 'میانگین دمای هوای {} {} {}، {} درجه سانتی‌گراد می‌باشد'.format(location[0], " و ".join(tr_time(time_iso, tokens, labels)),
                                                                                                 tr_single_date(date_list[0]), result)

            return result, generated_sentence
        # t0or1 d==l
        if (t == 0 or t == 1) and d == l:
            res = []
            for lc, dat in zip(location, date_list):
                res.append(self.getCityWeather(
                    lc, datetime.datetime.combine(dat.date(), time_iso[0]))["temp"])
            result = "%4.2f" % mean_func(res)
            generated_sentence = 'میانگین دمای هوای {} {} {}، {} درجه سانتی‌گراد می‌باشد'.format(" و ".join(location), " و ".join(tr_date(date_list, tokens, labels)),
                                                                                                 tr_single_date(date_list[0]), result)
            return mean_func(res)
        # t==d l1
        if (t == d) and l == 1:
            res = []
            for tim, dat in zip(time_iso, date_list):
                res.append(self.getCityWeather(
                    location[0], datetime.datetime.combine(dat.date(), tim))["temp"])
            result = "%4.2f" % mean_func(res)
            generated_sentence = "میانگین دمای هوای {} {} {}، {} درجه سانتی‌گراد است".format(location[0], " و ".join(tr_date(date_list, tokens, labels)),
                                                                                             " و ".join(tr_time(time_iso, tokens, labels)), result)
            return result, generated_sentence
        # t==l d1
        if (t == l) and d == 1:
            res = []
            for tim, lc in zip(time_iso, location):
                res.append(self.getCityWeather(
                    lc, datetime.datetime.combine(date_list[0].date(), tim))["temp"])
            result = "%4.2f" % mean_func(res)
            generated_sentence = "میانگین دمای هوای شهرهای {} {} {}، {} درجه سانتی‌گراد است".format(" و ".join(
                location), " و ".join(tr_time(time_iso, tokens, labels)), tr_single_date(date_list[0]), result)
            return result, generated_sentence

    def difference_handler(self, question, tokens, labels, time_iso, date_list, location):
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
                result = "%4.2f" % np.abs(np.diff(res))[0]
                generated_sentence = "اختلاف دمای شهرهای {} {} {} {} درجه سانتی‌گراد می‌باشد".format(" و ".join(
                    location), tr_single_date(date_list[0]), tr_single_time(time_iso[0]), result)
                return result, generated_sentence
            else:
                result = np.abs(np.diff(res))
                generated_sentence = "اختلاف دمای شهرهای {} {} {} {} درجه سانتی‌گراد می‌باشد".format(" و ".join(
                    location), tr_single_date(date_list[0]), tr_single_time(time_iso[0]), " و ".join(result))
                return result, generated_sentence

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
                result = "%4.2f" % np.abs(np.diff(res))[0]
                generated_sentence = "اختلاف دمای {} {} {}، {} درجه سانتی‌گراد است".format(" و ".join(
                    tr_date(date_list, tokens, labels)), location[0], tr_single_time(time_iso[0]), result)
                return result, generated_sentence
            else:
                result = np.abs(np.diff(res))
                generated_sentence = "اختلاف دمای {} {} {}، {} درجه سانتی‌گراد است".format(" و ".join(
                    tr_date(date_list, tokens, labels)), location[0], tr_single_time(time_iso[0]), " و ".join(result))
                return result, generated_sentence

        # t>=2 d1 l1
        if t >= 2 and d == 1 and l == 1:
            res = []
            for tim in time_iso:
                res.append(self.getCityWeather(
                    location[0], datetime.datetime.combine(date_list[0].date(), tim))["temp"])
            if t == 2:
                result = "%4.2f" % np.abs(np.diff(res))[0]
                generated_sentence = "اختلاف دمای {} {} {}، {} درجه سانتی‌گراد میباشد".format(" و ".join(
                    tr_time(time_iso, tokens, labels)), location[0], tr_single_date(date_list[0]), result)
                return result, generated_sentence
            else:
                result = np.abs(np.diff(res))
                generated_sentence = "اختلاف دمای {} {} {}، {} درجه سانتی‌گراد میباشد".format(" و ".join(
                    tr_time(time_iso, tokens, labels)), location[0], tr_single_date(date_list[0]), " و ".join(result))
                return result, generated_sentence
        # t0or1 d==l
        if (t == 0 or t == 1) and d == l:
            res = []
            for lc, dat in zip(location, date_list):
                res.append(self.getCityWeather(
                    lc, datetime.datetime.combine(dat.date(), time_iso[0]))["temp"])
            if d == 2:
                result = "%4.2f" % np.abs(np.diff(res))[0]
                generated_sentence = "اختلاف دمای {} {} {}، {} درجه سانتی‌گراد است".format(" و ".join(
                    tr_date(date_list, tokens, labels)), " و ".join(location), tr_single_time(time_iso[0]), result)
                return result, generated_sentence
            else:
                result = np.abs(np.diff(res))
                generated_sentence = "اختلاف دمای {} {} {}، {} درجه سانتی‌گراد است".format(" و ".join(
                    tr_date(date_list, tokens, labels)), " و ".join(location), tr_single_time(time_iso[0]), " و ".join(result))
            return result, generated_sentence
        # t==d l1
        if (t == d) and l == 1:
            res = []
            for tim, dat in zip(time_iso, date_list):
                res.append(self.getCityWeather(
                    location[0], datetime.datetime.combine(dat.date(), tim))["temp"])
            if t == 2:
                result = "%4.2f" % np.abs(np.diff(res))[0]
                generated_sentence = "اختلاف دمای {} {} {}، {} درجه سانتی‌گراد است".format(" و ".join(
                    tr_date(date_list, tokens, labels)), location[0], " و ".join(tr_time(time_iso, tokens, labels)), result)
                return result, generated_sentence
            else:
                result = np.abs(np.diff(res))
                generated_sentence = "اختلاف دمای {} {} {}، {} درجه سانتی‌گراد است".format(" و ".join(
                    tr_date(date_list, tokens, labels)), location[0], " و ".join(tr_time(time_iso, tokens, labels)), " و ".join(result))
            return result, generated_sentence
        # t==l d1

        if (t == l) and d == 1:
            res = []
            for tim, lc in zip(time_iso, location):
                res.append(self.getCityWeather(
                    lc, datetime.datetime.combine(date_list[0].date(), tim))["temp"])
            if t == 2:
                result = "%4.2f" % np.abs(np.diff(res))[0]
                generated_sentence = "اختلاف دمای {} {} {}، {} درجه سانتی‌گراد میباشد".format(" و ".join(
                    tr_time(time_iso, tokens, labels)), " و ".join(location), tr_single_date(date_list[0]), result)
                return result, generated_sentence
            else:
                result = np.abs(np.diff(res))
                generated_sentence = "اختلاف دمای {} {} {}، {} درجه سانتی‌گراد میباشد".format(" و ".join(
                    tr_time(time_iso, tokens, labels)), " و ".join(location), tr_single_date(date_list[0]), " و ".join(result))
                return result, generated_sentence
