
import datetime
import re
from aibot_date import convertStr2num, perstr_to_num
import numpy as np
from aibot_utils import cleaning
from hazm import word_tokenize

am_pm_dict = {"صبح": 0, "بعد از ظهر": 1, "عصر": 1,
              "غروب": 1, "شب": 1, "بامداد": 0, "قبل از ظهر": 0, "قبل ظهر": 0, "امشب": 1}

time_literals = {
    "ساعت قبل": -1,
    "ساعت گذشته": -1,
    "ساعت پیش": -1,
    "ساعت آینده": 1,
    "ساعت اینده": 1,
    "ساعت بعد": 1,
    "ساعت دیگر": 1,
    "دقیقه بعد": 1.0/60,
    "دقیقه آینده": 1.0/60,
    "دقیقه اینده": 1.0/60,
    "دقیقه‌ی بعد": 1.0/60,
    "دقیقه‌ی آینده": 1.0/60,
    "دقیقه‌ی اینده": 1.0/60,
    "دقیقه قبل": -1.0/60,
    "دقیقه گذشته": -1.0/60,
    "دقیقه پیش": -1.0/60,
    "دقیقه‌ی گذشته": -1.0/60,
    "دقیقه‌ی قبل": -1.0/60,
    "دقیقه‌ی پیش": -1.0/60,
    "دقیقه‌ی دیگر": 1.0/60,
    "دقیقه دیگر": 1.0/60,
    "الان": 0,
    "همین الآن": 0,
    "همین حالا": 0,
    "همین الان": 0,
    "این لحظه": 0,
    "این ساعت": 0}

minute_literals = {"و نیم": 30, "و ربع": 15}


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


def hour_min_exporter(st):
    # try ساعت + num
    mtch = re.findall("ساعت \d+", st)
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
            mtch_min = re.findall("\d+ دقیقه", st)
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
        probable_hour = st[mtch + len("ساعت"):]
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
            else:
                # try num + دقیقه
                mtch_m = re.findall("\d+ دقیقه", st)
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
        mtch = re.findall("\d+ {}".format(t_l[0]), st)
        if mtch:
            try:
                h = int(mtch[0].strip(t_l[0]))
                t = datetime.datetime.now() + datetime.timedelta(hours=h *
                                                                 time_literals[t_l[0]])
                hour, minute = t.hour, t.minute
                return fix_hour_ampm(st, hour), minute
            except Exception:
                pass
        # try writed number + tl
        h_n = []
        probable_number = st[:st.find(t_l[0])]
        for n in perstr_to_num.keys():
            if n in word_tokenize(probable_number):
                h_n.append(n)
        if h_n:
            try:
                h = convertStr2num(" ".join(h_n))
                t = datetime.datetime.now() + datetime.timedelta(hours=h *
                                                                 time_literals[t_l[0]])
                hour, minute = t.hour, t.minute
                return fix_hour_ampm(st, hour), minute
            except Exception:
                pass
        # if none of the above return tl itself
        try:
            t = datetime.datetime.now() + \
                datetime.timedelta(hours=time_literals[t_l[0]])
            hour, minute = t.hour, t.minute
            return fix_hour_ampm(st, hour), minute
        except Exception:
            pass

    return None, None


def export_time_single(st_arr, st=None):
    not_st = False
    if not st:
        st = cleaning("".join(st_arr).replace("-", ":").replace("/",
                                                                ":").replace("و", ":").replace(",", ":"))
        not_st = True
    # try hh:mm format
    mtch = re.findall("\d+[:]\d+", st)
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
    hour, minute = hour_min_exporter(st)
    if hour == None:
        # hour = datetime.datetime.now().hour
        return None
    if minute == None:
        # minute = datetime.datetime.now().minute
        return None
    return datetime.time(hour, minute)


def export_time(question, tokens, labels):
    labels = np.array(labels)
    b_time = np.where(labels == "B-time")[0]
    i_time = np.where(labels == "I-time")[0]
    n = len(b_time)
    if n == 0:
        st_arr = word_tokenize(question)
        return [export_time_single(st_arr, question)]

    elif n >= 2:
        t_ = []
        for i in range(n):
            st_arr = []
            if i < n - 1:
                ida = i_time[np.where(
                    (i_time > b_time[i]) & (i_time < b_time[i + 1]))]
            else:
                ida = i_time[np.where(i_time > b_time[i])]
            for t in np.r_[b_time[i], ida]:
                st_arr.append(tokens[int(t)])
            t_.append(export_time_single(st_arr))
        for i, t in enumerate(t_):
            if t == None:
                t_[i] = export_time_single(tokens[b_time[i]:])
        return t_
    else:
        st_arr = []
        for t in np.r_[b_time, i_time]:
            st_arr.append(tokens[int(t)])
        t_ = export_time_single(st_arr)
        if t_ == None:
            t_ = export_time_single(word_tokenize(question), question)
        return [t_]
