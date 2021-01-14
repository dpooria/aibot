"""All the functions related to dates and calender goes here"""

import ast
import numpy as np
import pandas as pd
import hazm
from hijri_converter import convert
import re
import datetime
from hazm import word_tokenize
from aibot_utils import cleaning
import os

abs_path = os.path.dirname(os.path.abspath(__file__))


perAnd = " و "
perstr_to_num = {"یک": 1, "دو": 2, "سه": 3, "چهار": 4, "پنج": 5, "شش": 6, "هفت": 7, "هشت": 8, "نه": 9, "ده": 10, "یازده": 11, "دوازده": 12, "سیزده": 13, "چهارده": 14, "پانزده": 15, "شانزده": 16, "هفده": 17, "هجده": 18, "نوزده": 19, "بیست": 20, "سی": 30,
                 "چهل": 40, "پنجاه": 50, "شصت": 60, "هفتاد": 70, "هشتاد": 80, "نود": 90, "صد": 100, "دویست": 200, "سیصد": 300, "چهارصد": 400, "پانصد": 500, "ششصد": 600, "هفتصد": 700, "هشتصد": 800, "نهصد": 900, "هزار": 1000, "میلیون": 1000000, "میلیارد": 1000000000, "صفر": 0}
num_to_perstr = {v: k for k, v in zip(
    perstr_to_num.keys(), perstr_to_num.values())}
new_dict = {}
for k, v in perstr_to_num.items():
    new_dict[k] = v
    if v == 3:
        new_dict["سوم"] = v
    else:
        new_dict[k + "م"] = v
    if v == 30:
        new_dict[hazm.Normalizer().normalize("سی‌ام")] = v
new_dict[hazm.Normalizer().normalize("اول")] = 1

perstr_to_num = new_dict

miladimonthes = {"ژانویه": 1, "فوریه": 2, "مارس": 3, "آوریل": 4, "آپریل": 4, "مارچ": 3, "مه": 5, "می": 5, "ژوئن": 6, "ژون": 6,
                 "ژوئیه": 7, "جولای": 7, "اوت": 8, "آگوست": 8, "سپتامبر": 9, "اکتبر": 10, "نوامبر": 11, "دسامبر": 12, "اپریل": 4, "اوریل": 4, "اگوست": 8}
shamsimonthes = {"فروردین": 1, "اردیبهشت": 2, "خرداد": 3, "تیر": 4, "مرداد": 5, "شهریور": 6,
                 "مهر": 7, "آبان": 8, "آذر": 9, "دی": 10, "بهمن": 11, "اسفند": 12, "ابان": 8, "اذر": 9, "اَمرداد": 5}
qamariMonthes = {"محرم": 1, "صفر": 2, "ربیع الاول": 3, "ربیع الثانی": 4, "جمادی الاول": 5,
                 "جمادی الثانی": 6, "رجب": 7, "شعبان": 8, "رمضان": 9, "شوال": 10, "ذیحجه": 11, "ذیقعده": 12,
                 "ذوالحجه": 11, "ذوالقعده": 12, "جمادی الثانیه": 6, }

tr_engnum_arabicnum = {"0": "۰", "1": "۱", "2": "۲", "3": "۳",
                       "4": "۴", "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹"}
tr_arabicnum_engnum = {v: k for k, v in tr_engnum_arabicnum.items()}

year_literals = {"سال پیش": -1, "سال قبل": -1, "سال گذشته": -
                 1, "سال آینده": 1, "سال بعد": 1, "سال پیش رو": 1, "امسال": 0,
                 "پارسال": -1,
                 "سال اینده": 1,
                 "سال جاری": 0}

day_literals = {"فردا": 1, "روز بعد": 1, "روز آینده": 1, "امروز": 0, "فردای": 1,
                "دیروز": -1, "روز پیش": -1, "روز گذشته": -1, "روز قبل": -1, "روز اینده": 1,
                "هفته‌ی آینده": 7,
                "هفته آینده": 7,
                "هفته اینده": 7,
                "هفته‌ی اینده": 7,
                "هفته بعد": 7,
                "هفته‌ی بعد": 7,
                "هفته دیگر": 7,
                "هفته‌ی دیگر": 7,
                "هفته‌ی گذشته": -7,
                "هفته گذشته": -7,
                "هفته قبل": -7,
                "هفته‌ی قبل": -7,
                "هفته پیش": -7,
                "هفته‌ی پیش": -7,
                "پس‌فردا": 2,
                "پریروز": -2,
                "پس فردا": 2,
                "پسفردا": 2
                }

week_literals = {"هفته‌ی آینده": 1,
                 "هفته آینده": 1,
                 "هفته اینده": 1,
                 "هفته‌ی اینده": 1,
                 "هفته بعد": 1,
                 "هفته‌ی بعد": 1,
                 "هفته دیگر": 1,
                 "هفته‌ی دیگر": 1,
                 "هفته‌ی گذشته": -1,
                 "هفته گذشته": -1,
                 "هفته قبل": -1,
                 "هفته‌ی قبل": -1,
                 "هفته پیش": -1,
                 "هفته‌ی پیش": -1,
                 "این هفته": 0,
                 "هفته‌ی جاری": 0
                 }

weeks_day_dict = {"شنبه": 0, "یکشنبه": 1, "دوشنبه": 2, "سه‌شنبه": 3, "چهارشنبه": 4, "پنج‌شنبه": 5, "جمعه": 6, "پنج شنبه": 5, "پنجشنبه": 5, "یک‌شنبه": 1, "یک شنبه": 1, "دو شنبه": 2, "دو‌شنبه": 2, "سه شنبه": 3, "چهار‌شنبه": 4, "آدینه": 6, "ادینه": 6
                  }


week_days_asked = ["چند شنبه", "چند شنبست",
                   "چه روز از هفته", "چه روزی از هفته", "چه روز هفته"]


def tr_isoweek_toperweekday(n): return n - 5 if n >= 5 else n + 2
def tr_perweekday_toisoweek(n): return n + 5 if n <= 1 else n - 2


month_literals = {"این ماه": 0, "ماه جاری": 0, "این برج": 0, "ماه آینده": 1, "برج بعد": 1, "ماه بعد": 1,
                  "ماه اینده": 1, "برج اینده": 1, "ماه بعد": 1, "برج قبل": -1, "ماه پیش": -1, "ماه گذشته": -1, "ماه قبل": -1}

calender_type_dict = {"شمسی": 0, "میلادی": 1,
                      "هجری قمری": 2, "قمری": 2, "جلالی": 0, "هجری شمسی": 0}


def format_jalali_date(j):
    fmt = "{}-{}-{}"
    month = "{}".format(j[1]) if j[1] >= 10 else "0{}".format(j[1])
    day = "{}".format(j[2]) if j[2] >= 10 else "0{}".format(j[2])
    return fmt.format(j[0], month, day)


def eng_num(stfa):
    sten = ""
    for c in stfa:
        if c in tr_arabicnum_engnum.keys():
            sten += tr_arabicnum_engnum[c]
        else:
            sten += c
    return sten


def convertNum2str(num):
    if num == 0:
        return num_to_perstr[0]
    n = int(np.log10(num)) + 1
    hund = np.zeros(n, dtype="i")
    for i in range(1, n + 1):
        hund[i - 1] = int(num / 10**(i-1)) % 10
    st = ""
    if num > 999999999:
        hund = np.pad(hund, (0, 12 - n))
        st += convertNum2str(hund[-1] * 100 + hund[-2] *
                             10 + hund[-3]) + " " + num_to_perstr[1000000000]
        a = 0
        for i in range(9):
            a += hund[i] * 10**i
        tmp = convertNum2str(a)
        if not tmp == num_to_perstr[0]:
            st += perAnd + tmp
    elif num > 999999:
        hund = np.pad(hund, (0, 9 - n))
        st += convertNum2str(hund[-1] * 100 + hund[-2]
                             * 10 + hund[-3]) + " " + num_to_perstr[1000000]
        a = 0
        for i in range(6):
            a += hund[i] * 10**i
        tmp = convertNum2str(a)
        if not tmp == num_to_perstr[0]:
            st += perAnd + tmp
    elif num > 999:
        hund = np.pad(hund, (0, 6 - n))
        st += convertNum2str(hund[-1] * 100 + hund[-2]
                             * 10 + hund[-3]) + " " + num_to_perstr[1000]
        a = 0
        for i in range(3):
            a += hund[i] * 10**i
        tmp = convertNum2str(a)
        if not tmp == num_to_perstr[0]:
            st += perAnd + tmp
    elif num > 99:
        st += num_to_perstr[hund[-1] * 100]
        tmp = convertNum2str(hund[0] + hund[1] * 10)
        if not tmp == num_to_perstr[0]:
            st += perAnd + tmp
    elif num >= 20:
        st += num_to_perstr[hund[1] * 10]
        tmp = convertNum2str(hund[0])
        if not tmp == num_to_perstr[0]:
            st += perAnd + tmp
    else:
        st = num_to_perstr[num]
    return st


def convertStr2num(st):
    st = cleaning(st)
    st_arr = np.array(st.split(" "))
    st_arr = st_arr[np.where(st_arr != "و")]
    thousand = np.where(st_arr == num_to_perstr[1000])[0]
    million = np.where(st_arr == num_to_perstr[1000000])[0]
    billion = np.where(st_arr == num_to_perstr[1000000000])[0]
    num = 0
    if thousand.shape[0] != 0 or million.shape[0] != 0 or billion.shape[0] != 0:
        if billion.shape[0] != 0:
            if billion[0] == 0:
                num += 1000000000
            else:
                num += convertStr2num(
                    " ".join(st_arr[:billion[0]])) * 1000000000
            if not st_arr[-1] == num_to_perstr[1000000000]:
                num += convertStr2num(" ".join(st_arr[billion[0] + 1:]))
        elif million.shape[0] != 0:
            if million[0] == 0:
                num += 1000000
            else:
                num += convertStr2num(" ".join(st_arr[:million[0]])) * 1000000
            if not st_arr[-1] == num_to_perstr[1000000]:
                num += convertStr2num(" ".join(st_arr[million[0] + 1:]))
        else:
            if thousand[0] == 0:
                num += 1000
            else:
                num += convertStr2num(" ".join(st_arr[:thousand[0]])) * 1000
            if not st_arr[-1] == num_to_perstr[1000]:
                num += convertStr2num(" ".join(st_arr[thousand[0] + 1:]))
    else:
        for s in st_arr:
            num += perstr_to_num[s]
    return num


# Gregorian & Jalali ( Hijri_Shamsi , Solar ) Date Converter  Functions
# Author: JDF.SCR.IR =>> Download Full Version :  http://jdf.scr.ir/jdf
# License: GNU/LGPL _ Open Source & Free :: Version: 2.80 : [2020=1399]
# ---------------------------------------------------------------------


def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if (gm > 2):
        gy2 = gy + 1
    else:
        gy2 = gy
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) //
                                                     100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if (days > 365):
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if (days < 186):
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return [jy, jm, jd]


def jalali_to_gregorian(jy, jm, jd):
    jy += 1595
    days = -355668 + (365 * jy) + ((jy // 33) * 8) + \
        (((jy % 33) + 3) // 4) + jd
    if (jm < 7):
        days += (jm - 1) * 31
    else:
        days += ((jm - 7) * 30) + 186
    gy = 400 * (days // 146097)
    days %= 146097
    if (days > 36524):
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if (days >= 365):
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if (days > 365):
        gy += ((days - 1) // 365)
        days = (days - 1) % 365
    gd = days + 1
    if ((gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)):
        kab = 29
    else:
        kab = 28
    sal_a = [0, 31, kab, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    while (gm < 13 and gd > sal_a[gm]):
        gd -= sal_a[gm]
        gm += 1
    return [gy, gm, gd]


df_event = pd.read_csv(os.path.join(abs_path, "database/event_data_full.csv"))
event_literals = ["روز جهانی", "شهادت", "عید", "ولادت", "سالگرد", "سالروز", "روز مادر", "روز پدر", "روز دختر", "روز پسر",
                  "جشن", "میلاد", "عاشورا", "تاسوعا"]
after_event = ["امسال", "چه روزی", "در ", "چه تاریخی", "چه روز"
               "است", "می‌باشد", "می باشد", "کی", "چه موقع", "سال", "چندم", "ماه ", "؟", ".", "!", " بود", "خواهد", "اتفاق", "افتاد", "قرار", "چه تاریخ", "چه", "روزیه"]


def event_exporter(question, tokens, labels):
    event_list = []
    # try matching exactly the names of the events:
    for i, e in enumerate(df_event["event"]):
        if e in question:
            event_list.append(df_event.iloc[i])
    if not event_list:
        print('here2')
        # try finding event_literals
        for el in event_literals:
            if el in question:
                el_loc = question.find(el)
                if el_loc == 0:
                    el_q = question
                else:
                    el_q = cleaning(question[el_loc - 1:])
                # el_q = el_q.replace(el, "")
                el_q = re.sub("\d+", "", el_q)
                el_q = re.sub(" | ".join(shamsimonthes.keys()), "", el_q)
                el_q = re.sub(" | ".join(miladimonthes.keys()), "", el_q)
                el_q = re.sub(" | ".join(qamariMonthes.keys()), "", el_q)
                el_q = cleaning(el_q)
                for ae in after_event:
                    if ae in el_q:
                        el_q = cleaning(el_q.replace(ae, ""))
                el_q = cleaning(el_q.replace("است", ""))
                for i, e in enumerate(df_event["event"]):
                    if (el_q in e) or (e in el_q):
                        event_list.append(df_event.iloc[i])
    if not event_list:
        event_tokens = list(np.array(tokens)[np.where(
            (labels == "B-event") | (labels == "I-event"))])
        person_tokens = list(np.array(tokens)[np.where(
            (labels == "B-person") | (labels == "I-person"))])
        organization_tokens = list(np.array(tokens)[np.where(
            (labels == "B-organization") | (labels == "I-organization"))])
        for t in [event_tokens, person_tokens, organization_tokens]:
            if len(t) > 0:
                if len(t) > 1:
                    st = " ".join(t)
                else:
                    st = t[0]
                for i, e in enumerate(df_event["event"]):
                    if st in e:
                        event_list.append(df_event.iloc[i])
    
    # form the data frame
    event_list = pd.DataFrame(event_list)
    if not event_list.empty:
        e_u = pd.unique(event_list["event"].to_numpy())
        if len(e_u) < len(event_list):
            e_l = []
            for e in e_u:
                e_l.append(event_list.iloc[np.where(
                    event_list["event"] == e)[0][0]])
            event_list = pd.DataFrame(e_l)
    return event_list


def check_event(question, tokens, labels, today_gregorian, today_hijri, today_jalali, calender_type):
    # try events:
    events = event_exporter(question, tokens, labels)
    if events.empty:
        return None, (True, True, True)
    year = year_exporter(
        question, today_gregorian, calender_type=calender_type)
    year_type = "j_d"
    if year is None:
        year = today_gregorian.year
        year_type = "g_d"
    elif year > 1420 and year < 1600:
        year_type = "h_d"
    elif year > 1600:
        year_type = "g_d"
    event_date = []
    for i in range(len(events)):
        if year_type == "g_d":
            a = re.findall("{}-\d+-\d+".format(year), events["g_d"].iloc[i])
        else:
            a = re.findall("[(]{}, \d+, \d+[)]".format(year),
                           events[year_type].iloc[i])
        if a:
            event_date.append(events.iloc[i])

    if event_date:
        print("we are here")
        if year_type == "j_d":
            dat = ast.literal_eval(event_date[-1]["j_d"])
            print(dat)
            d = jalali_to_gregorian(dat[0], dat[1], dat[2])
            print(d)
            d = datetime.datetime(d[0], d[1], d[2])
        elif year_type == "g_d":
            dat = ast.literal_eval(event_date[-1]["j_d"])
            d = convert.Hijri(dat[0], dat[1], dat[2]).to_gregorian()
            d = datetime.datetime(d.year, d.month, d.day)
        else:
            d = datetime.datetime.fromisoformat(event_date[-1]["g_d"])
        return d, (False, False, event_date[-1]["event"])

    else:
        print(events)
        if year > 1420 and year < 1600:
            dy = year - today_hijri.year
            year = today_gregorian.year + dy
        elif year <= 1420:
            dy = year - today_jalali.year
            year = today_gregorian.year + dy

        d = datetime.datetime.fromisoformat(
            events["g_d"].iloc[-1])
        if d.year == year:
            return d, (False, False, events["event"].to_numpy()[0])

        if events["calender_type"].iloc[-1] == "g":
            print("here")
            print(datetime.datetime(year, d.month, d.day),
                  (False, False, events["event"].to_numpy()[0]))
            return datetime.datetime(year, d.month, d.day), (False, False, events["event"].to_numpy()[0])
        elif events["calender_type"].iloc[-1] == "j":
            dj_event = ast.literal_eval(events["j_d"].iloc[-1])
            dy = year - d.year
            g_event = jalali_to_gregorian(
                dj_event[0] + dy, dj_event[1], dj_event[2])
            return datetime.datetime(
                g_event[0], g_event[1], g_event[2]), (False, False, events["events"].to_numpy()[0])
        else:
            dh_event = ast.literal_eval(events["h_d"].iloc[-1])
            dy = year - d.year
            g_event = convert.Hijri(
                dh_event[0] + dy - 1, dh_event[1], dh_event[2]).to_gregorian()
            return datetime.datetime(
                g_event.year, g_event.month, g_event.day), (False, False, events["event"].to_numpy()[0])


def build_date_fromisoformat(mtch, calender_type=-1):
    st_d = eng_num(mtch)
    d_args = st_d.split("-")
    year = int(d_args[0])
    month = int(d_args[1])
    day = int(d_args[2])
    if day > 31 and year <= 31:
        tmp = year
        year = day
        day = tmp
    if month > 12 and year < 12:
        tmp = year
        year = month
        month = tmp
    if month > 12 and day <= 12:
        tmp = day
        day = month
        month = tmp
    if year < 100 and year >= 30 and (calender_type == 0 or calender_type == -1):
        year += 1300
    elif year < 100 and year < 30 and (calender_type == 0 or calender_type == -1):
        year += 1400
    if calender_type == -1:
        if year > 1700:
            d_ = datetime.datetime(year, month, day)
        elif year > 1420:
            d_ = convert.Hijri(year, month, day).to_gregorian()
            d_ = datetime.datetime(d_.year, d_.month, d_.day)
        else:
            d_ = jalali_to_gregorian(year, month, day)
            d_ = datetime.datetime(d_[0], d_[1], d_[2])
    elif calender_type == 0:
        d_ = jalali_to_gregorian(year, month, day)
        d_ = datetime.datetime(d_[0], d_[1], d_[2])
    elif calender_type == 2:
        d_ = convert.Hijri(year, month, day).to_gregorian()
        d_ = datetime.datetime(d_.year, d_.month, d_.day)
    else:
        d_ = datetime.datetime(year, month, day)

    return d_


def year_exporter(st, today, calender_type=0):

    year = re.findall("\d{4}", st)
    try:
        if year:
            return int(year[0])
        else:
            # try year literals
            year_literal_ = []
            for l in year_literals.keys():
                if l in st:
                    year_literal_.append(l)

            if year_literal_:
                probable_year = cleaning(year_literal_[0])
                probable_year_num = st.find(probable_year)
                probable_year_num = st[:probable_year_num]
                pn = []
                for w in word_tokenize(probable_year_num):
                    if w in num_to_perstr.keys():
                        pn.append(w)
                if pn:
                    try:
                        n = convertStr2num(" ".join(pn))
                        if n > 20:
                            raise Exception
                        return today.year + n * year_literals[year_literal_[0]]
                    except Exception:
                        pass
                year = today.year + \
                    year_literals[year_literal_[0]]
                return year

            year = re.findall(" \d{2} ", st)
            if not year:
                year = re.findall("^\d{2} ", st)
            if not year:
                year = re.findall(" \d{2}$", st)
            if year and int(year[0]) > 31 and calender_type == 0:
                year = int(year[0])
                year += 1300
                return year
            else:
                # try writed numbers
                probable_year = []
                for w in word_tokenize(st):
                    if w in perstr_to_num.keys():
                        probable_year.append(w)
                if probable_year:
                    try:
                        year = convertStr2num(" ".join(probable_year))
                        if year < 1300:
                            if calender_type == 0 and year < 100 and year > 31:
                                year += 1300
                            else:
                                raise Exception
                        return year
                    except Exception:
                        pass

    except Exception:
        return None

    return None


def day_exporter(st, today):
    # try weeks days:
    d_d = []
    for l in weeks_day_dict.keys():
        if l in st:
            d_d.append(l)
    is_week_day_asked = False
    for w in week_days_asked:
        if w in st:
            is_week_day_asked = True

    if d_d and not is_week_day_asked:
        week_val = weeks_day_dict[d_d[-1]]
        today_week = tr_isoweek_toperweekday(today.weekday())
        d_w = []
        for l in week_literals.keys():
            if l in st:
                d_w.append(l)
        if not d_w:
            w_ = 0
        else:
            w_ = week_literals[d_w[0]]
        if w_ == 0:
            day = today + datetime.timedelta(week_val - today_week)
        else:
            day = today + \
                datetime.timedelta(w_ * 7 - w_ * (today_week - week_val))

        return day, True

    # try day literals
    d_d = []
    for l in day_literals.keys():
        if l in st:
            d_d.append(l)
    if d_d:
        val = day_literals[d_d[-1]]
        match_liter = st.find(d_d[-1])
        b_match_liter = st[:match_liter]
        n = re.findall("\d+", b_match_liter)
        if n:
            try:
                day = datetime.timedelta(int(n[0]) * val) + today
            except Exception:
                day = datetime.timedelta(val) + today
        else:
            try:
                s = []
                for w in word_tokenize(b_match_liter):
                    if w in perstr_to_num.keys():
                        s.append(w)
                if s:
                    day = today + datetime.timedelta(val *
                                                     convertStr2num(" ".join(s)))
                else:
                    day = today + datetime.timedelta(val)
            except Exception:
                day = today + datetime.datetime.timedelta(val)
        return day, True
    # try raw numbers
    day = re.findall(" \d{2} ", st)
    if not day:
        day = re.findall("^\d{2} ", st)
    if not day:
        day = re.findall(" \d{2}$", st)
    if not day:
        day = re.findall(" \d ", st)
    if not day:
        day = re.findall("^\d ", st)
    if not day:
        day = re.findall(" \d$", st)
    if day and int(day[0]) < 31:
        return int(day[0]), False
    # try writed numbers
    probable_day = []
    for w in word_tokenize(st):
        if w in perstr_to_num.keys():
            probable_day.append(w)

    if probable_day:
        try:
            day = convertStr2num(" ".join(probable_day))
            if day > 31:
                raise Exception
            return day, False
        except Exception:
            return None, False
    return None, False


def month_matched(st_space, month_place, today, calender_type=0):
    day_is_none = False
    year_is_none = False
    day, _ = day_exporter(st_space[:month_place], today)
    if _:
        day = day.day
    if not day:
        day, _ = day_exporter(st_space[month_place:], today)
        if _:
            day = day.day
    if not day:
        day, _ = day_exporter(st_space, today)
        if _:
            day = day.day
    if not day:
        day = today.day
        day_is_none = True
    year = year_exporter(st_space[:month_place], today, calender_type)
    if not year:
        year = year_exporter(st_space[month_place:], today, calender_type)
    if not year:
        year = year_exporter(st_space, today, calender_type)
    if not year:
        year = today.year
        year_is_none = True
    return (day, year, day_is_none, year_is_none)


def export_date_single(st_arr, today_list, calender_type_is_found, calender_type):

    today = today_list[calender_type]
    is_day_none = False
    is_month_none = False
    is_year_none = False
    st = "".join(st_arr).replace("/", "-").replace(",",
                                                   "-").replace(".", "-").replace("\\", "-")
    st = cleaning(st)
    st_space = cleaning(" ".join(st_arr))
    mtch = re.findall("\d+\-\d+\-\d+", st)
    if mtch:
        try:
            if calender_type_is_found:
                d_ = build_date_fromisoformat(mtch[0], calender_type)
            else:
                d_ = build_date_fromisoformat(mtch[0], -1)
            return d_, (is_day_none, is_month_none, is_year_none)
        except Exception:
            pass

    # try mm-dd format
    mtch = re.findall("\d+\-\d+", st)
    if mtch:
        try:
            mtch_n = mtch[0].split("-")
            day = int(mtch_n[1])
            month = int(mtch_n[0])
            if month > 12:
                tmp = day
                day = month
                month = tmp
            mtch_place = st_space.find(mtch_n[-1])
            year = year_exporter(
                st_space[mtch_place + len(mtch_n[-1]):], today)
            if not year:
                mtch_place = st.find(mtch[0])
                year = year_exporter(st_space[:mtch_place], today)
            if not year:
                year = year_exporter(st_space, today)
            if not year:
                year = today.year
            if calender_type == 0:
                year, month, day = jalali_to_gregorian(year, month, day)
            elif calender_type == 2:
                d_ = convert.Hijri(year, month, day).to_gregorian()
                year, month, day = d_.year, d_.month, d_.day
            d_ = datetime.datetime(year, month, day)
            return d_, (is_day_none, is_month_none, is_year_none)
        except Exception:
            pass

    st = st_space

    # try day literals
    day, is_day_literal = day_exporter(st, today_list[1])
    if day and is_day_literal:
        d_ = day
        is_month_none = True
        is_year_none = True
        return d_, (is_day_none, is_month_none, is_year_none)

    # try monthes name
    mtch = re.findall(" | ".join(shamsimonthes.keys()), st)
    if mtch:
        month = shamsimonthes[cleaning(mtch[0])]
        today = today_list[0]
        month_place = st_space.find(cleaning(mtch[0]))
        try:
            day, year, is_day_none, is_year_none = month_matched(
                st_space, month_place, today_list[0])
            year, month, day = jalali_to_gregorian(year, month, day)
            d_ = datetime.datetime(year, month, day)
            return d_, (is_day_none, is_month_none, is_year_none)
        except Exception:
            pass

    mtch = re.findall(" | ".join(miladimonthes.keys()), st)
    if mtch:
        month = miladimonthes[cleaning(mtch[0])]
        today = today_list[1]
        month_place = st_space.find(cleaning(mtch[0]))
        try:
            day, year, is_day_none, is_year_none = month_matched(
                st_space, month_place, today, 1)
            d_ = datetime.datetime(year, month, day)
            return d_, (is_day_none, is_month_none, is_year_none)
        except Exception:
            pass

    mtch = re.findall(" | ".join(qamariMonthes.keys()), st)
    if mtch:
        month = qamariMonthes[cleaning(mtch[0])]
        today = today_list[2]
        month_place = st_space.find(cleaning(mtch[0]))
        try:
            day, year, is_day_none, is_year_none = month_matched(
                st_space, month_place, today_list[2], 2)
            d_ = convert.Hijri(year, month, day).to_gregorian()
            d_ = datetime.datetime(d_.year, d_.month, d_.day)
            return d_, (is_day_none, is_month_none, is_year_none)
        except Exception:
            pass
    # try month literals
    d_m = []
    for l in month_literals.keys():
        if l in st:
            d_m.append(l)
    if d_m:
        is_month_none = False
        month = today.month + month_literals[d_m[0]]
        if month > 12:
            month = month - 12
        elif month < 1:
            month = 12 + month

        month_loc = st.find(d_m[0])
        try:
            day, year, is_day_none, is_year_none = month_matched(
                st_space, month_loc, today)
            if calender_type == 0:
                year, month, day = jalali_to_gregorian(year, month, day)
            if calender_type == 2:
                year, _, day = convert.Hijri(year, month, day)
            d_ = datetime.datetime(year, month, day)
            return d_, (is_day_none, is_month_none, is_year_none)
        except Exception:
            pass

    return None, (is_day_none, is_month_none, is_year_none)


def export_date(question, tokens, labels):

    labels = np.array(labels)
    b_date = np.where(labels == "B-date")[0]
    i_date = np.where(labels == "I-date")[0]
    # find calender type
    today_gregorian = datetime.datetime.today()
    today_jalali = gregorian_to_jalali(
        today_gregorian.year, today_gregorian.month, today_gregorian.day)
    today_jalali = datetime.datetime(
        today_jalali[0], today_jalali[1], today_jalali[2])
    today_hijri = convert.Gregorian(
        today_gregorian.year, today_gregorian.month, today_gregorian.day).to_hijri()
    today_hijri = datetime.datetime(
        today_hijri.year, today_hijri.month, today_hijri.day)
    today_list = [today_jalali, today_gregorian, today_hijri]
    calender_type_find = []
    for c in calender_type_dict.keys():
        if " " + c + " " in question:
            calender_type_find.append(c)
    calender_type = 0
    calender_type_is_found = False
    if calender_type_find:
        if question.find("به " + calender_type_find[0]) == -1:
            calender_type = calender_type_dict[calender_type_find[0]]
            calender_type_is_found = True

    n = len(b_date)
    if n == 0:
        st_arr = word_tokenize(question)
        d_single = export_date_single(
            st_arr, today_list, calender_type_is_found, calender_type)
        if d_single[0] != None:
            return [d_single]
        else:
            return [check_event(question, tokens, labels, today_gregorian, today_hijri, today_jalali, calender_type)]
    elif n >= 2:
        d_ = []
        false_ner = False
        for i in range(n):
            st_arr = []
            if i < n - 1:
                ida = i_date[np.where(
                    (i_date > b_date[i]) & (i_date < b_date[i + 1]))]
            else:
                ida = i_date[np.where(i_date > b_date[i])]
            for t in np.r_[b_date[i], ida]:
                st_arr.append(tokens[int(t)])
            d_.append(export_date_single(st_arr, today_list,
                                         calender_type_is_found, calender_type))
        for i, d in enumerate(d_):
            if d[0] == None:
                d_[i] = export_date_single(
                    tokens[b_date[i]:], today_list, calender_type_is_found, calender_type)
            if d_[i][0] == None:
                d_[i] = check_event(question, tokens, labels, today_gregorian,
                                    today_hijri, today_jalali, calender_type)
            if d_[i][0] == None:
                false_ner = True
        if false_ner and n == 2:
            d_ = [export_date_single(word_tokenize(
                question), today_list, calender_type_is_found, calender_type)]
        return d_
    else:
        st_arr = []
        for t in np.r_[b_date, i_date]:
            st_arr.append(tokens[int(t)])

        d_ = export_date_single(
            st_arr, today_list, calender_type_is_found, calender_type)
        if d_[0] == None or d_[1][0] or d_[1][1] or d_[1][2]:
            d_ = export_date_single(word_tokenize(
                question), today_list, calender_type_is_found, calender_type)
        if d_[0] == None:
            d_ = check_event(question, tokens, labels, today_gregorian,
                             today_hijri, today_jalali, calender_type)
        return [d_]
