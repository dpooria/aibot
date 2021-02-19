

from hijri_converter import convert
from aibot_utils import concatenate_bi, cleaning
import datetime
from aibot_date import gregorian_to_jalali
from vocab import shamsimonthes, miladimonthes, qamariMonthes, num2fa_gen


tr_jalali_month = {v: k for k, v in shamsimonthes.items()}
tr_gregorian_month = {v: k for k, v in miladimonthes.items()}
tr_hijri_month = {v: k for k, v in qamariMonthes.items()}


def tr_single_date(date_, force_date=False):
    if isinstance(date_, datetime.datetime):
        date_ = date_.date()
    today = datetime.datetime.today()
    if date_ == today.date() and not force_date:
        translation = "امروز"
    elif date_ == (today + datetime.timedelta(1)).date() and not force_date:
        translation = "فردا"
    elif date_ == (today - datetime.timedelta(1)).date() and not force_date:
        translation = "دیروز"
    else:
        j = gregorian_to_jalali(date_.year, date_.month, date_.day)
        today_j = gregorian_to_jalali(today.year, today.month, today.day)
        month = tr_jalali_month[j[1]]
        if j[0] == today_j[0]:
            translation = "{} {}".format(
                num2fa_gen[j[2]], month)
        elif j[0] == today_j[0] + 1:
            translation = "{} {} سال بعد".format(
                num2fa_gen[j[2]], month)
        elif j[0] == today_j[0] - 1:
            translation = "{} {} پارسال".format(
                num2fa_gen[j[2]], month)
        else:
            translation = "{} {} سال {}".format(
                num2fa_gen[j[2]], month, j[0] if j[0] >= 1400 else j[0] - 1300)
    return translation


def tr_gregorian_date(date_):
    if isinstance(date_, datetime.datetime):
        date_ = date_.date()
    month = tr_gregorian_date[date_.month]
    translation = "{} {} سال {}".format(
        num2fa_gen[date_.day], month, date_.year)
    return translation


def tr_hijri_date(date_):
    if isinstance(date_, datetime.datetime):
        date_ = date_.date()

    date_h = convert.Gregorian(date_.year, date_.month, date_.day).to_hijri()
    month = tr_gregorian_date[date_h.month]
    translation = "{} {} سال {}".format(
        num2fa_gen[date_h.day], month, date_h.year)
    return translation


def tr_date(date_list, tokens, labels):
    d_words = []
    if len(date_list) <= 2:
        for d in date_list:
            y = tr_single_date(d.date())
            d_words.append(cleaning(y))
    else:
        d_words = concatenate_bi(tokens, labels, "B_DAT", "I_DAT")
    return d_words


def tr_single_time(tim):
    now_time = datetime.datetime.now().time()
    if tim.hour == now_time.hour and tim.minute == now_time.minute:
        return "الآن"
    else:
        if tim.hour != 0:
            if tim.minute != 0:
                return "ساعت {} و {} دقیقه".format(tim.hour, tim.minute)
            else:
                return "ساعت {}".format(tim.hour)
        else:
            if tim.minute != 0:
                return "ساعت ۱۲ و {} دقیقه‌ی بامداد".format(tim.minute)
            else:
                return "۱۲ بامداد"


def tr_time(time_iso, tokens, labels):
    t_words = []
    if len(time_iso) <= 2:
        for t in time_iso:
            y = tr_single_time(t)
            t_words.append(cleaning(y))
    else:
        t_words = concatenate_bi(tokens, labels, "B_TIM", "I_TIM")
    return t_words


# def weather_minmax_question(question, tokens, labels, result, result_typeو, logicals, date_list, time_iso):
#     pass
