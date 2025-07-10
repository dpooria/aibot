import datetime
import re
from copy import copy

import numpy as np
from hazm import word_tokenize

from adhanAPI import Adhan
from aibot_date import convertStr2num, export_date
from aibot_utils import cleaning, location_handler, mix_tdl, unique_without_sort
from vocab import am_pm_dict, minute_literals, perstr_to_num, time_literals

adhan = Adhan()


def fix_hour_ampm(st, hour):
    ampm_list = []
    for ampm in am_pm_dict.keys():
        if " " + ampm + " " in st:
            ampm_list.append(ampm)
        elif re.findall("^{} ".format(ampm), st):
            ampm_list.append(ampm)
        elif re.findall(" {}$".format(ampm), st):
            ampm_list.append(ampm)
    if ampm_list:
        if am_pm_dict[ampm_list[0]] == 1:
            if hour < 12:
                hour += 12
            elif hour == 12:
                hour = 0
        elif ampm_list[0] == "بامداد" and hour == 12:
            hour = 0
    return hour


def hour_min_exporter(st, force_return=False):
    # try ساعت + num
    mtch = re.findall(r"ساعت \d+", st)
    if mtch:
        mtch_minute = st.find("دقیقه")
        minute = 0
        if mtch_minute == -1:
            # try minute_literals
            min_liter = []
            for m in minute_literals.keys():
                if m in st:
                    min_liter.append(m)
            if min_liter:
                minute = minute_literals[min_liter[0]]
        else:
            # try num + دقیقه
            mtch_min = re.findall(r"\d+ دقیقه", st)
            if mtch_min:
                try:
                    minute = int(mtch_min[0].strip("دقیقه"))
                except Exception:
                    pass
            else:
                # try writed number + دقیقه
                probable_min = cleaning(st[:mtch_minute])
                m_n = []
                for w in word_tokenize(probable_min):
                    if w in perstr_to_num.keys():
                        m_n.append(w)
                if m_n:
                    minute = convertStr2num(" ".join(m_n))

        try:
            hour = int(mtch[0].strip("ساعت"))
        except Exception:
            hour = 0
        return fix_hour_ampm(st, hour), minute

    # try ساعت + writed num
    mtch = st.find("ساعت")
    if mtch != -1:
        h_n = []
        probable_hour = st[mtch + len("ساعت") :]
        for w in word_tokenize(probable_hour):
            if w in perstr_to_num.keys():
                h_n.append(w)
        if h_n:
            h_n.append("صفر")
            mtch_minute = st.find("دقیقه")
            if mtch_minute == -1:
                minute = 0
                hour = convertStr2num(" ".join(h_n))
                # try minute literals
                m_l = []
                for m in minute_literals:
                    if m in st:
                        m_l.append(m)
                if m_l:
                    minute = minute_literals[m_l[0]]
                try:
                    if hour > 24:
                        raise Exception
                    return fix_hour_ampm(st, hour), minute
                except Exception:
                    pass
            # try num + دقیقه
            mtch_m = re.findall(r"\d+ دقیقه", st)
            if mtch_m:
                try:
                    minute = int(mtch_m[0].strip("دقیقه"))
                    hour = convertStr2num(" ".join(h_n))
                    if hour > 24:
                        raise Exception
                    return fix_hour_ampm(st, hour), minute
                except Exception:
                    pass
            # maybe the writed numbers are for minute too!
            if len(h_n) > 2:
                try:
                    hour = convertStr2num(h_n[0])
                    minute = convertStr2num(" ".join(h_n[1:]))
                    if hour > 24 or minute > 60:
                        raise Exception
                    return fix_hour_ampm(st, hour), minute
                except Exception:
                    try:
                        if len(h_n) >= 3:
                            h_n.append("صفر")
                            # hours are at maximum 2 numbers (<24)
                            hour = convertStr2num(" ".join(h_n[:2]))
                            minute = convertStr2num(" ".join(h_n[2:]))
                            if hour > 24:
                                raise Exception
                            return fix_hour_ampm(st, hour), minute
                        else:
                            raise Exception
                    except Exception:
                        try:
                            hour = convertStr2num(" ".join(h_n[:-2]))
                            minute = convertStr2num(" ".join(h_n[-2]))
                            if hour > 24:
                                raise Exception
                            return fix_hour_ampm(st, hour), minute
                        except Exception:
                            pass
            else:
                try:
                    hour = convertStr2num(" ".join(h_n[:-1]))
                    minute = 0
                    if hour > 24:
                        raise Exception
                    return fix_hour_ampm(hour), minute
                except Exception:
                    pass

    # try time literals
    t_l = []
    for tl in time_literals:
        if tl in st:
            t_l.append(tl)
    if t_l:
        # try num + tl
        mtch = re.findall(r"\d+ {}".format(t_l[0]), st)
        if mtch:
            try:
                h = int(mtch[0].strip(t_l[0]))
                t = datetime.datetime.now() + datetime.timedelta(
                    hours=h * time_literals[t_l[0]]
                )
                hour, minute = t.hour, t.minute
                return fix_hour_ampm(st, hour), minute
            except Exception:
                pass
        # try writed number + tl
        h_n = []
        probable_number = st[: st.find(t_l[0])]
        for n in perstr_to_num.keys():
            if n in word_tokenize(probable_number):
                h_n.append(n)
        if h_n:
            try:
                h = convertStr2num(" ".join(h_n))
                t = datetime.datetime.now() + datetime.timedelta(
                    hours=h * time_literals[t_l[0]]
                )
                hour, minute = t.hour, t.minute
                return fix_hour_ampm(st, hour), minute
            except Exception:
                pass
        # if none of the above return tl itself
        try:
            t = datetime.datetime.now() + datetime.timedelta(
                hours=time_literals[t_l[0]]
            )
            hour, minute = t.hour, t.minute
            return fix_hour_ampm(st, hour), minute
        except Exception:
            pass
    # let's just return a number as hour:
    if force_return:
        mtch = re.findall(r"\d+", st)
        if mtch:
            hour = int(mtch[0])
            return fix_hour_ampm(st, hour), 0
    return None, None


# check for adhan times
def adhan_handler(time_list, tokens, labels, question):
    res = []
    url = []
    if time_list is None or len(time_list) == 1:
        adhan_names = adhan.export_adhan_names(question)
        if adhan_names:
            exportdat = export_date(question, tokens, labels)
            date_list = []
            for d in exportdat:
                if d[0] is not None:
                    date_list.append(d[0])
            date_list = unique_without_sort(date_list)
            if not date_list:
                date_list.append(datetime.datetime.today())
            locs = location_handler(question, tokens, labels)
            mixture = mix_tdl(adhan_names, date_list, locs)
            if mixture:
                for m in mixture:
                    t, u = adhan.get_city_adhan_time(m[2], m[1], m[0])
                    res.append(t)
                    url.append(u)
            return res, url, adhan_names
        else:
            return None, None, None
    else:
        adhan_names = adhan.export_adhan_names(question)
        # for t in time_list:
        #     a = adhan.export_adhan_names(str(t))
        #     if a:
        #         adhan_names.append(a[0])
        a = len(adhan_names)
        if a == 0:
            return None, None, None
        if a == len(time_list):
            exportdat = export_date(question, tokens, labels)
            date_list = []
            for d in exportdat:
                if d[0] is not None:
                    date_list.append(d[0])
            if not date_list:
                date_list.append(datetime.datetime.today())
            locs = location_handler(question, tokens, labels)
            mixture = mix_tdl(adhan_names, date_list, locs)
            if mixture:
                for m in mixture:
                    t, u = adhan.get_city_adhan_time(m[2], m[1], m[0])
                    res.append(t)
                    url.append(u)
            return res, url, adhan_names
        if a < len(time_list):
            exportdat = export_date(question, tokens, labels)
            date_list = []
            for d in exportdat:
                if d[0] is not None:
                    date_list.append(d[0])
            if not date_list:
                date_list.append(datetime.datetime.today())
            locs = location_handler(question, tokens, labels)
            mixture = mix_tdl(time_list, date_list, locs)
            if mixture:
                for m in mixture:
                    if m[0] in adhan_names:
                        t, u = adhan.get_city_adhan_time(m[2], m[1], m[0])
                        res.append(t)
                        url.append(u)
                    else:
                        res.append(m[0])
            return res, url, adhan_names


def export_time_single(st_arr, st=None, force_return=False):
    not_st = False
    if not st:
        st = cleaning(
            "".join(st_arr)
            .replace("-", ":")
            .replace("/", ":")
            .replace("و", ":")
            .replace(",", ":")
        )
        not_st = True
    # try hh:mm format
    mtch = re.findall(r"\d+[:]\d+", st)
    if mtch:
        t = mtch[0].split(":")
        try:
            hour = int(t[0])
            minute = int(t[1])
            if hour > 24:
                temp = minute
                minute = hour
                hour = temp
            return datetime.time(fix_hour_ampm(" ".join(st_arr), hour), minute)
        except Exception:
            pass
    if not_st:
        st = cleaning(" ".join(st_arr))
    hour, minute = hour_min_exporter(st, force_return=force_return)
    if hour is None:
        # hour = datetime.datetime.now().hour
        return None
    if minute is None:
        # minute = datetime.datetime.now().minute
        return None
    return datetime.time(hour, minute)


def export_time(question, tokens, labels):
    labels = np.array(labels)
    b_time = np.where(labels == "B_TIM")[0]
    i_time = np.where(labels == "I_TIM")[0]
    url = None
    n = len(b_time)
    if n == 0:
        st_arr = word_tokenize(question)
        t_ = export_time_single(st_arr, question)

        if t_ is None:
            res, url, adhan_names = adhan_handler(None, tokens, labels, question)
            if res is not None:
                return res, True, url, adhan_names

        return [t_], False, None, None

    elif n >= 2:
        t_ = []
        time_texts = []
        for i in range(n):
            st_arr = []
            if i < n - 1:
                ida = i_time[np.where((i_time > b_time[i]) & (i_time < b_time[i + 1]))]
            else:
                ida = i_time[np.where(i_time > b_time[i])]
            for t in np.r_[b_time[i], ida]:
                st_arr.append(tokens[int(t)])
            time_texts.append(" ".join(st_arr))
            t_.append(export_time_single(st_arr, force_return=True))
        is_adhan_needed = False
        new_t = copy(t_)
        for i, t in enumerate(t_):
            if t_[i] is None:
                new_t[i] = time_texts[i]
                is_adhan_needed = True
        if is_adhan_needed:
            res, url, adhan_names = adhan_handler(new_t, tokens, labels, question)
            if res is not None:
                if None not in res:
                    return res, True, url, adhan_names
        return t_, False, None, None
    else:
        st_arr = []
        for t in np.r_[b_time, i_time]:
            st_arr.append(tokens[int(t)])
        t_ = export_time_single(st_arr, force_return=True)
        if t_ is None:
            t_ = export_time_single(word_tokenize(question), question)
        if t_ is None:
            res, url, adhan_names = adhan_handler(None, tokens, labels, question)
            if res is not None:
                return res, True, url, adhan_names
        return [t_], False, None, None
