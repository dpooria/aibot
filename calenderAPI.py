
import numpy as np
import pandas as pd
import datetime
from hijri_converter import convert
from timeAPI import Time
from aibot_date import export_date, format_jalali_date, gregorian_to_jalali, tr_isoweek_toperweekday, df_event


convert_asked = {"به قمری": 2,
                 "به شمسی": 0,
                 "به میلادی": 1,
                 "به تاریخ هجری": 2,
                 "به تاریخ شمسی": 0,
                 "به تاریخ میلادی": 1}

week_days_asked = ["چند شنبه", "چند شنبست",
                   "چه روز از هفته", "چه روزی از هفته", "چه روز هفته"]

week_days = {0: "شنبه",
                6: "جمعه",
                1: "یکشنبه",
                2: "دوشنبه",
                3: "سه‌شنبه",
                4: "چهارشنبه",
                5: "پنجشنبه"}


event_asked = ["مناسبت", "اتفاق", "مناسبتها", "چه روزی است"]

time_asked = ["تا ساعت", "چند ساعت", "اختلاف زمان",
              "چه ساعت", "به وقت ", "ساعت چند"]


class Calender:
    def __init__(self):
        self.time = Time()

    def get_answer(self, question, tokens, labels):
        answer = {'type': '4', 'city': [], 'date': [],
                  'time': [], 'religious_time': [], 'calendar_type': [], 'event': [], 'api_url': [''], 'result': ''}

        is_time_asked = False
        for t in time_asked:
            if t in question:
                is_time_asked = True

        if is_time_asked:
            return self.time.get_answer(question, tokens, labels)

        date_list = []
        date_list_jalali = []
        exportdate = export_date(question, tokens, labels)
        no_date = False
        events = []
        is_there_any_events = False
        for d in exportdate:
            if d[0]:
                date_list.append(d[0])
            if (not d[1][0]) and (not d[1][1]) and (type(d[1][2]) != bool):
                is_there_any_events = True
                events.append(d[1][2])

        d_n = len(date_list)
        if d_n == 0:
            today = datetime.datetime.today()
            date_list = [today]
            d_n = 1
            no_date = True
        date_list = list(np.unique(date_list))
        d_n = len(date_list)
        date_list_jalali = []
        for d in date_list:
            j = gregorian_to_jalali(d.year, d.month, d.day)
            date_list_jalali.append(format_jalali_date(j))

        answer["date"] = date_list_jalali
        answer["result"] = date_list_jalali[0]
        event_list = list(np.unique(list(np.array(tokens)[np.where(
            (labels == "B-event") | (labels == "I-event")[0])])))
        if event_list:
            event_list = np.r_[event_list, events]
        else:
            event_list = events
        answer["event"] = list(event_list)
        convert_list = []
        is_weeks_day_asked = False
        for w in week_days_asked:
            if w in question:
                is_weeks_day_asked = True
        if is_weeks_day_asked:
            wd = date_list[0].weekday()
            answer["result"] = week_days[tr_isoweek_toperweekday(wd)]
            return answer

        if d_n == 1:
            # check if converting date is asked:
            for k in convert_asked.keys():
                if k in question:
                    convert_list.append(k)
            if convert_list:
                a = convert_asked[convert_list[0]]
                if a == 0:
                    res = answer["date"][0]
                    answer["calendar_type"] = ["شمسی"]
                elif a == 1:
                    res = date_list[0].strftime("%Y-%m-%d")
                    answer["calendar_type"] = ["میلادی"]
                else:
                    res = convert.Gregorian(
                        date_list[0].year, date_list[0].month, date_list[0].day).to_hijri()
                    res = format_jalali_date([res.year, res.month,
                                              res.day])
                    answer["calendar_type"] = ["قمری"]
                answer["result"] = res
                return answer
            # check if events is asked
            if not is_there_any_events:
                is_event_asked = False
                for ea in event_asked:
                    if ea in question:
                        is_event_asked = True
                if is_event_asked:
                    d_j = gregorian_to_jalali(
                        date_list[0].year, date_list[0].month, date_list[0].day)
                    d_str = "({}, {}, {})".format(d_j[0], d_j[1], d_j[2])
                    f_event = df_event["event"].loc[df_event["j_d"]
                                                     == d_str].to_numpy()
                    if not len(f_event) == 0:
                        answer["result"] = f_event[0].replace(
                            " و ", "-").replace("؛", "-").replace("،", "-")
                    else:
                        answer["result"] = "مناسبتی وجود ندارد"
                    return answer
        if not is_there_any_events:
            result = []
            for d in date_list:
                is_event_asked = False
                for ea in event_asked:
                    if ea in question:
                        is_event_asked = True
                if is_event_asked:
                    d_j = gregorian_to_jalali(
                        d.year, d.month, d.day)

                    d_str = "({}, {}, {})".format(d_j[0], d_j[1], d_j[2])
                    f_event = df_event["event"].loc[df_event["j_d"]
                                                     == d_str].to_numpy()
                    if not len(f_event) == 0:
                        result.append(f_event[0].replace(
                            " و ", "-").replace("؛", "-").replace("،", "-"))
            if result:
                answer["result"] = "-".join(result)
        return answer
