
import re
import datetime

import requests
import numpy as np
import pandas as pd
from transformers.utils.dummy_pt_objects import ElectraForMaskedLM

from aibot_date import export_date, format_jalali_date, gregorian_to_jalali
from aibot_utils import location_handler, get_city_info, unique_without_sort, cleaning
from vocab import hours_left_asked, adhan_logical_question, tr_adhan_names, weather_logical
from copy import copy
from reply_gen import tr_date, tr_time, tr_single_date, tr_single_time


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
                            minute = tt
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
        if minutes != 0:
            generated_text = "{} ساعت و {} دقیقه".format(
                int(hours), int(minutes))
        else:
            generated_text = "{} ساعت".format(int(hours))
        if minutes != 0:
            generated_text = "{} ساعت و {} دقیقه".format(
                int(hours), int(minutes))
        else:
            generated_text = "{} ساعت".format(int(hours))
        h_st = ""
        if abs(hours) > 10:
            h_st = "{}".format(int(hours))
        elif hours < 0:
            h_st = "-0{}".format(int(abs(hours)))
        else:
            h_st = "0{}".format(int(hours))
        m_st = "{}".format(int(minutes)) if abs(
            minutes) > 10 else "0{}".format(int(minutes))
        return "%s:%s" % (h_st, m_st), url, generated_text

    @staticmethod
    def format_time_delta(dt):
        totsec = dt.total_seconds()
        h = totsec // 3600
        m = (totsec // 60) % 60
        if m != 0:
            generated_text = "{} ساعت و {} دقیقه".format(int(h), int(m))
        else:
            generated_text = "{} ساعت".format(int(h))
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
        answer = {'type': ['2'], 'city': [], 'date': [],
                  'time': [], 'religious_time': [], 'calendar_type': [], 'event': [], 'api_url': [''], 'result': []}
        generated_sentence = ""
        is_wrong_classifier = False
        for k in ["سردتر", "گرمتر", "سردترین", "گرمترین", "اختلاف دمای", "میانگین دما"]:
            if k in question:
                is_wrong_classifier = True
                break
        if is_wrong_classifier:
            return False
        location = unique_without_sort(
            location_handler(question, tokens, labels))
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

        date_list = unique_without_sort(date_list)
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
        exportedAdhan = self.export_adhan_names(question)
        n_adhan = len(exportedAdhan)
        if n_adhan == 0:
            return answer, generated_sentence
        answer["religious_time"] = copy(exportedAdhan)
        new_adhan_names = []
        for e in exportedAdhan:
            if tr_adhan_names[e] == "All":
                new_adhan_names.append("اذان صبح")
                new_adhan_names.append("اذان ظهر")
                new_adhan_names.append("اذان مغرب")
                new_adhan_names.append("نیمه شب شرعی")
            else:
                new_adhan_names.append(e)
        exportedAdhan = new_adhan_names
        n_adhan = len(exportedAdhan)
        res, url = self.get_city_adhan_time(
            location[0], date_list[0].date(), exportedAdhan[0])
        answer["api_url"] = [url]
        if n_adhan == 1 and l_n == 1 and d_n == 1:
            if res != None:
                answer["result"] = [res.strftime("%H:%M")]
                generated_sentence = "زمان {} {} {}، {} میباشد".format(
                    exportedAdhan[0], tr_single_date(date_list[0]), location[0], tr_single_time(res))
            is_hour_lef_asked = False
            ihla = []
            for h in hours_left_asked:
                if h in question:
                    is_hour_lef_asked = True
                    ihla.append(h)
            if not is_hour_lef_asked:
                return answer, cleaning(generated_sentence)
            else:
                tnow = datetime.datetime.now()
                dadhan = datetime.datetime.combine(date_list[0].date(), res)
                if ihla[0] != "گذشته":
                    if dadhan < tnow:
                        dadhan = dadhan + datetime.timedelta(1)
                        date_list[0] = date_list[0] + datetime.timedelta(1)
                    generated_sentence = "تا {} {} {}، {} مانده است"
                else:
                    generated_sentence = "از {} {} {}، {} گذشته است"
                dt = tnow - dadhan if tnow > dadhan else dadhan - tnow
                answer["result"], gd = self.format_time_delta(dt)
                answer["result"] = [answer["result"]]
                generated_sentence = generated_sentence.format(
                    exportedAdhan[0], tr_single_date(date_list[0]), location[0], gd)
        else:
            # check if it's a logical question
            isLogical = False
            for l in adhan_logical_question:
                if l in tokens:
                    isLogical = True
            if isLogical:
                if n_adhan > 1 and l_n == 1 and d_n == 1:
                    answer["result"], answer["api_url"], gd = self.get_difference_adhan(
                        location[0], location[0], date_list[0], date_list[0], exportedAdhan[0], exportedAdhan[1])
                    generated_sentence = "اختلاف {} و {} {} {}، {} است".format(
                        exportedAdhan[0], exportedAdhan[1], tr_single_date(date_list[0]), location[0], gd)
                elif n_adhan == 1 and l_n > 1 and d_n == 1:
                    answer["result"], answer["api_url"], gd = self.get_difference_adhan(
                        location[0], location[1], date_list[0], date_list[0], exportedAdhan[0], exportedAdhan[0])
                    generated_sentence = "اختلاف {} {} {}، {} میباشد".format(
                        exportedAdhan[0], tr_single_date(date_list[0]), " و ".join(location), gd)
                elif n_adhan == 1 and l_n == 1 and d_n > 1:
                    answer["result"], answer["api_url"], gd = self.get_difference_adhan(
                        location[0], location[0], date_list[0], date_list[1], exportedAdhan[0], exportedAdhan[0])
                    generated_sentence = "اختلاف {} {} {}، {} است".format(
                        exportedAdhan[0], " و ".join(tr_date(date_list, tokens, labels)), location[0], gd)
                elif n_adhan == 2 and l_n == 2 and d_n == 1:
                    answer["result"], answer["api_url"], gd = self.get_difference_adhan(
                        location[0], location[1], date_list[0], date_list[0], exportedAdhan[0], exportedAdhan[1])
                    generated_sentence = "اختلاف زمان {} {} و {} {} {}، {} میباشد".format(
                        exportedAdhan[0], location[0], exportedAdhan[1], location[1], tr_single_date(date_list[0]), gd)
                elif n_adhan == 2 and l_n == 1 and d_n == 2:
                    answer["result"], answer["api_url"], gd = self.get_difference_adhan(
                        location[0], location[0], date_list[0], date_list[1], exportedAdhan[0], exportedAdhan[1])
                    generated_sentence = "اختلاف زمان {} {} و {} {} {}، {} میباشید".format(exportedAdhan[0], tr_single_date(
                        date_list[0]), exportedAdhan[1], tr_single_date(date_list[1]), location[0], gd)
                elif n_adhan == 1 and l_n == 2 and d_n == 2:
                    answer["result"], answer["api_url"], gd = self.get_difference_adhan(
                        location[0], location[1], date_list[0], date_list[0], exportedAdhan[0], exportedAdhan[1])
                    generated_sentence = "اختلاف زمان {} {} {} و {} {}، {} است".format(exportedAdhan[0], tr_single_date(
                        date_list[0]), location[0], tr_single_date(date_list[1]), location[1], gd)
            else:
                res_list = []
                url_list = []
                if n_adhan >= 2 and l_n == 1 and d_n == 1:
                    generated_sentence = "{} به افق {} ".format(
                        tr_single_date(date_list[0]), location[0])
                    for i, ad in enumerate(exportedAdhan):
                        res, url = self.get_city_adhan_time(
                            location[0], date_list[0].date(), ad)
                        if res != None and url != None:
                            res_list.append(res.strftime("%H:%M"))
                            url_list.append(url)
                            if i < n_adhan - 2:
                                generated_sentence = generated_sentence + \
                                    "{} ،{} ، ".format(ad, tr_single_time(res))
                            elif i == n_adhan - 2:
                                generated_sentence = generated_sentence + \
                                    "{} ،{} و ".format(ad, tr_single_time(res))
                            else:
                                generated_sentence = generated_sentence + \
                                    "{} ،{} ".format(ad, tr_single_time(res))
                    generated_sentence = generated_sentence + "میباشد"
                elif n_adhan == 1 and l_n >= 2 and d_n == 1:
                    generated_sentence = "{} ".format(
                        tr_single_date(date_list[0]))
                    for i, lc in enumerate(location):
                        res, url = self.get_city_adhan_time(
                            lc, date_list[0].date(), exportedAdhan[0])
                        if res != None and url != None:
                            res_list.append(res.strftime("%H:%M"))
                            url_list.append(url)
                            if i < l_n - 2:
                                generated_sentence = generated_sentence + \
                                    "{} به افق {}، {} ،".format(
                                        exportedAdhan[0], lc, tr_single_time(res))
                            elif i == l_n - 2:
                                generated_sentence = generated_sentence + \
                                    "{} به افق {}، {} و ".format(
                                        exportedAdhan[0], lc, tr_single_time(res))
                            else:
                                generated_sentence = generated_sentence + \
                                    "{} به افق {}، {} ".format(
                                        exportedAdhan[0], lc, tr_single_time(res))
                    generated_sentence = generated_sentence + " میباشد"
                elif n_adhan == 1 and l_n == 1 and d_n >= 2:
                    generated_sentence = "{} {}، ".format(
                        exportedAdhan[0], location[0])

                    for i, dat in enumerate(date_list):
                        res, url = self.get_city_adhan_time(
                            location[0], dat.date(), exportedAdhan[0])
                        if res != None and url != None:
                            res_list.append(res.strftime("%H:%M"))
                            url_list.append(url)
                            if i < d_n - 2:
                                generated_sentence = generated_sentence + \
                                    "{}، {}، ".format(tr_single_date(
                                        dat), tr_single_time(res))
                            elif i == d_n - 2:
                                generated_sentence = generated_sentence + \
                                    "{}، {} و ".format(tr_single_date(
                                        dat), tr_single_time(res))
                            else:
                                generated_sentence = generated_sentence + \
                                    "{}، {}، ".format(tr_single_date(
                                        dat), tr_single_time(res))
                    generated_sentence = generated_sentence + " میباشد"

                elif n_adhan == l_n and d_n == 1:
                    generated_sentence = "{}، ".format(
                        tr_single_date(date_list[0]))
                    s = 0
                    for ad, lc in zip(exportedAdhan, location):
                        res, url = self.get_city_adhan_time(
                            lc, date_list[0].date(), ad)
                        if res != None and url != None:
                            res_list.append(res.strftime("%H:%M"))
                            url_list.append(url)
                            if s < l_n - 2:
                                generated_sentence = generated_sentence + \
                                    "{} {}، {}، ".format(
                                        ad, lc, tr_single_time(res))
                            elif s == l_n - 2:
                                generated_sentence = generated_sentence + \
                                    "{} {}، {} و ".format(
                                        ad, lc, tr_single_time(res))
                            else:
                                generated_sentence = generated_sentence + \
                                    "{} {}، {} ".format(
                                        ad, lc, tr_single_time(res))
                            s += 1
                    generated_sentence = generated_sentence + "میباشد"
                elif n_adhan == 1 and l_n == d_n:
                    generated_sentence = ""
                    s = 0
                    for lc, dat in zip(location, date_list):
                        res, url = self.get_city_adhan_time(
                            lc, dat.date(), exportedAdhan[0])
                        if res != None and url != None:
                            res_list.append(res.strftime("%H:%M"))
                            url_list.append(url)
                            if s < l_n - 2:
                                generated_sentence = generated_sentence + \
                                    "{} {}، {}، {}، ".format(
                                        exportedAdhan[0], lc, tr_single_date(dat), tr_single_time(res))
                            elif s == l_n - 2:
                                generated_sentence = generated_sentence + \
                                    "{} {}، {}، {} و ".format(
                                        exportedAdhan[0], lc, tr_single_date(dat), tr_single_time(res))
                            else:
                                generated_sentence = generated_sentence + \
                                    "{} {}، {}، {} ".format(
                                        exportedAdhan[0], lc, tr_single_date(dat), tr_single_time(res))
                            s += 1
                    generated_sentence = generated_sentence + "میباشد"

                elif n_adhan == d_n and l_n == 1:
                    generated_sentence = ""
                    s = 0
                    for ad, dat in zip(exportedAdhan, date_list):
                        res, url = self.get_city_adhan_time(
                            location[0], dat.date(), ad)
                        if res != None and url != None:
                            res_list.append(res.strftime("%H:%M"))
                            url_list.append(url)
                            if s < d_n - 2:
                                generated_sentence = generated_sentence + \
                                    "{} {}، {}، ".format(
                                        tr_single_date(dat), ad, tr_single_time(res))
                            elif s == d_n - 2:
                                generated_sentence = generated_sentence + \
                                    "{} {}، {} و ".format(
                                        tr_single_date(dat), ad, tr_single_time(res))
                            else:
                                generated_sentence = generated_sentence + \
                                    "{} {}، {} ".format(
                                        tr_single_date(dat), ad, tr_single_time(res))
                            s += 1

                    generated_sentence = generated_sentence + \
                        "به افق {} میباشد".format(location[0])

                elif (n_adhan == d_n) and (l_n == d_n):
                    generated_sentence = ""
                    s = 0
                    for i in range(d_n):
                        res, url = self.get_city_adhan_time(
                            location[i], date_list[i].date(), exportedAdhan[i])
                        if res != None and url != None:
                            res_list.append(res.strftime("%H:%M"))
                            url_list.append(url)
                            if s < l_n - 2:
                                generated_sentence = generated_sentence + \
                                    "{}، {} {}، {}، ".format(tr_single_date(
                                        date_list[i]), exportedAdhan[i], location[i], tr_single_time(res))
                            elif s == l_n - 2:
                                generated_sentence = generated_sentence + \
                                    "{} {}، {}، {} و ".format(tr_single_date(
                                        date_list[i]), exportedAdhan[i], location[i], tr_single_time(res))
                            else:
                                generated_sentence = generated_sentence + \
                                    "{} {}، {} {} ".format(tr_single_date(
                                        date_list[i]), exportedAdhan[i], location[i], tr_single_time(res))
                            s += 1
                    generated_sentence = generated_sentence + "میباشد"

                answer["result"] = res_list
                answer["api_url"] = url_list
                return answer, cleaning(generated_sentence)

        return answer, cleaning(generated_sentence)
