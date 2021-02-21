
import hazm
from reply_gen import tr_gregorian_date, tr_hijri_date, tr_single_date, tr_date
from aibot_utils import concatenate_bi, unique_without_sort
import numpy as np
import datetime
from hijri_converter import convert
from timeAPI import Time
from aibot_date import export_date, format_jalali_date, gregorian_to_jalali, jalali_to_gregorian, tr_isoweek_toperweekday, df_event
from aibot_utils import cleaning
from vocab import convert_asked, week_days, week_days_asked, event_asked, time_asked

# TODO : fix the convert asked to also use calender_type passed from export_date function


class Calender:
    def __init__(self):
        self.time = Time()
        self.bii = None

    def get_answer(self, question, tokens, labels):
        answer = {'type': ['4'], 'city': [], 'date': [],
                  'time': [], 'religious_time': [], 'calendar_type': [], 'event': [], 'api_url': [''], 'result': []}
        generated_sentence = ""
        is_time_asked = False
        for t in time_asked:
            if t in question:
                is_time_asked = True

        if is_time_asked:
            return self.time.get_answer(question, tokens, labels)

        date_list = []
        date_list_jalali = []
        exportdate = export_date(question, tokens, labels, True)
        events = []
        which_date_is_event = []
        for i, d in enumerate(exportdate):
            if d[0]:
                date_list.append(d[0])
            if (not d[1][0]) and (not d[1][1]) and (type(d[1][2]) != bool):
                events.append(d[1][2])
                which_date_is_event.append(i)

        d_n = len(date_list)
        today = datetime.datetime.today()
        if d_n == 0:
            date_list = [today]
            d_n = 1
            no_date = True
        date_list = unique_without_sort(date_list)
        d_n = len(date_list)
        date_list_jalali = []
        for d in date_list:
            j = gregorian_to_jalali(d.year, d.month, d.day)
            date_list_jalali.append(format_jalali_date(j))

        answer["date"] = date_list_jalali
        event_list = events
        answer["event"] = list(event_list)
        self.bii = concatenate_bi(tokens, labels, "B_DAT", "I_DAT")

        if d_n == 1:
            asingle, generated_sentence = self.get_single_answer(
                question, answer, date_list, events)
            if asingle != None:
                answer = asingle
            else:
                answer["result"] = date_list_jalali
                trsd = tr_single_date(date_list[0], True)
                if self.bii:
                    if date_list[0].date() >= today.date():
                        generated_sentence = "{}، {} میباشد".format(" ".join(self.bii),
                                                                    trsd)
                    else:
                        generated_sentence = "{}، {} بوده است".format(" ".join(self.bii),
                                                                      trsd)
                else:
                    if date_list[0].date() >= today.date():
                        generated_sentence = "تاریخ داده شده {} است".format(
                            trsd)
                    else:
                        generated_sentence = "تاریخ داده شده {} بوده".format(
                            trsd)
        else:
            answer["result"] = []
            tokenize_questions = hazm.sent_tokenize(question)
            if len(tokenize_questions) == 1:
                tokenize_questions = question.split(" و ")
            if d_n == len(tokenize_questions):
                generated_sentence = ""
                if d_n != len(events):
                    s = 0
                    for i, (d, tk) in enumerate(zip(date_list, tokenize_questions)):
                        if i in which_date_is_event:
                            n_answer, n_generated_sentence = self.get_single_answer(
                                tk, answer, [d], [events[which_date_is_event[s]]], self.bii[i] if len(self.bii) == d_n else None)
                            s += 1
                        else:
                            n_answer, n_generated_sentence = self.get_single_answer(
                                tk, answer, [d], None, self.bii[i] if len(self.bii) == d_n else None)
                        if n_answer != None:
                            answer = n_answer
                            if generated_sentence:
                                generated_sentence = generated_sentence + " و " + n_generated_sentence
                            else:
                                generated_sentence = n_generated_sentence
                        else:
                            n_answer, n_generated_sentence = self.get_single_answer(
                                question, answer, [d], events, self.bii[i] if len(self.bii) == d_n else None)
                            if n_answer != None:
                                answer = n_answer
                                if generated_sentence:
                                    generated_sentence = generated_sentence + " و " + n_generated_sentence
                                else:
                                    generated_sentence = n_generated_sentence
                            else:
                                n_generated_sentence = "تاریخ داده شده {} میباشد".format(
                                    tr_single_date(d))

                                j = gregorian_to_jalali(d.year, d.month, d.day)
                                answer["result"].append(format_jalali_date(j))
                                if generated_sentence:
                                    generated_sentence = generated_sentence + " و " + n_generated_sentence
                                else:
                                    generated_sentence = n_generated_sentence
                else:
                    for i in range(d_n):
                        n_answer, n_generated_sentence = self.get_single_answer(
                            tokenize_questions[i], answer, [date_list[i]], [events[i]], self.bii[i] if len(self.bii) == d_n else None)
                        if n_answer != None:
                            answer = n_answer
                            if generated_sentence:
                                generated_sentence = generated_sentence + " و " + n_generated_sentence
                            else:
                                generated_sentence = n_generated_sentence
                        else:
                            n_answer, n_generated_sentence = self.get_single_answer(
                                question, answer, [date_list[i]], [events[i]], self.bii[i] if len(self.bii) == d_n else None)
                            if n_answer != None:
                                answer = n_answer
                                if generated_sentence:
                                    generated_sentence = generated_sentence + " و " + n_generated_sentence
                                else:
                                    generated_sentence = n_generated_sentence
                            else:
                                j = gregorian_to_jalali(
                                    date_list[i].year, date_list[i].month, date_list[i].day)
                                answer["result"].append(format_jalali_date(j))
                                n_generated_sentence = "تاریخ داده شده {} است".format(
                                    tr_single_date(date_list[i]))
                                if generated_sentence:
                                    generated_sentence = generated_sentence + " و " + n_generated_sentence
                                else:
                                    generated_sentence = n_generated_sentence

            else:
                for d in date_list:
                    n_answer, n_generated_sentence = self.get_single_answer(
                        question, answer, [d], events, self.bii[i] if len(self.bii) == d_n else None)
                    if n_answer != None:
                        answer = n_answer
                        if generated_sentence:
                            generated_sentence = generated_sentence + " و " + n_generated_sentence
                        else:
                            generated_sentence = n_generated_sentence
        return answer, cleaning(generated_sentence)

    def get_single_answer(self, question, answer, date_list, events, bii=None):
        today = datetime.datetime.today()
        is_weeks_day_asked = False
        generated_sentence = ""
        for w in week_days_asked:
            if w in question:
                is_weeks_day_asked = True
        if is_weeks_day_asked:
            wd = date_list[0].weekday()
            result = week_days[tr_isoweek_toperweekday(wd)]
            answer["result"].append(result)
            if not events:
                if date_list[0].date() >= today.date():
                    generated_sentence = "{}، {} است".format(
                        tr_single_date(date_list[0]), result)
                else:
                    generated_sentence = "{}، {} بوده".format(
                        tr_single_date(date_list[0]), result)
            else:
                if date_list[0].date() >= today.date():
                    generated_sentence = "{} مصادف با {}، {} است".format(" ".join(events),
                                                                         tr_single_date(date_list[0]), result)
                else:
                    generated_sentence = "{} مصادف با {}، {} بوده".format(" ".join(events),
                                                                          tr_single_date(date_list[0]), result)

            return answer, generated_sentence

        # check if converting date is asked:
        convert_list = []
        for k in convert_asked.keys():
            if k in question:
                convert_list.append(k)
        if convert_list:
            a = convert_asked[convert_list[0]]
            if a == 0:
                res = answer["date"][0]
                answer["calendar_type"].append("شمسی")
                generated_sentence = "تاریخ داده شده به شمسی، {} میباشد".format(
                    tr_single_date(date_list[0]))
            elif a == 1:
                res = date_list[0].strftime("%Y-%m-%d")
                answer["calendar_type"].append("میلادی")
                generated_sentence = "تاریخ داده شده به میلادی، {} میباشد".format(
                    tr_gregorian_date(date_list[0]))
            else:
                new_date = date_list[0] - datetime.timedelta(1)
                res = convert.Gregorian(
                    new_date.year, new_date.month, new_date.day).to_hijri()

                res = format_jalali_date([res.year, res.month,
                                          res.day])
                answer["calendar_type"].append("قمری")
                generated_sentence = "تاریخ داده شده به قمری، {} میباشد".format(
                    tr_hijri_date(date_list[0]))
            answer["result"].append(res)
            return answer, generated_sentence

        # check if events is asked
        if not events:
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
                    res = []
                    for e in f_event:
                        res.append(e.replace(
                            " و ", "-").replace("؛", "-").replace("،", "-"))
                    res = np.unique(res)
                    answer["result"].append("-".join(res))
                    generated_sentence = "{} {} است".format(
                        tr_single_date(date_list[0]), " و ".join(res))
                else:
                    answer["result"].append("مناسبتی وجود ندارد")
                    generated_sentence = "{} مناسبتی وجود ندارد".format(
                        tr_single_date(date_list[0]))
                return answer, generated_sentence
        if events:
            j = gregorian_to_jalali(
                date_list[0].year, date_list[0].month, date_list[0].day)
            answer["result"].append(format_jalali_date(j))
            generated_sentence = "{} مصادف با {} میباشد".format(
                " ".join(events), tr_single_date(date_list[0]))
            return answer, generated_sentence
        if bii:
            j = gregorian_to_jalali(
                date_list[0].year, date_list[0].month, date_list[0].day)
            answer["result"].append(format_jalali_date(j))
            generated_sentence = "{}، {} است".format(
                bii, tr_single_date(date_list[0], True))
            return answer, generated_sentence
        return None, generated_sentence
