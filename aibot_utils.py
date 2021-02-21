
import hazm
import re
from cleantext import clean
import numpy as np
from numpy.lib.function_base import append
import tensorflow as tf
import pandas as pd
import os
import requests
from translate.translator import translator
from vocab import USER_CITY, loc_literals

abs_path = os.path.dirname(os.path.abspath(__file__))


def cleaning(text):
    text = text.strip()

    # regular cleaning
    text = clean(text,
                 fix_unicode=True,
                 to_ascii=False,
                 lower=True,
                 no_line_breaks=True,
                 no_urls=True,
                 no_emails=True,
                 no_phone_numbers=True,
                 no_numbers=False,
                 no_digits=False,
                 no_currency_symbols=True,
                 no_punct=False,
                 replace_with_url="",
                 replace_with_email="",
                 replace_with_phone_number="",
                 replace_with_number="",
                 replace_with_digit="0",
                 replace_with_currency_symbol="",
                 )

   # normalizing
    normalizer = hazm.Normalizer()
    text = normalizer.normalize(text)

    # removing wierd patterns
    wierd_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               u"\U0001f926-\U0001f937"
                               u'\U00010000-\U0010ffff'
                               u"\u200d"
                               u"\u2640-\u2642"
                               u"\u2600-\u2B55"
                               u"\u23cf"
                               u"\u23e9"
                               u"\u231a"
                               u"\u3030"
                               u"\ufe0f"
                               u"\u2069"
                               u"\u2066"
                               # u"\u200c"
                               u"\u2068"
                               u"\u2067"
                               "]+", flags=re.UNICODE)

    text = wierd_pattern.sub(r'', text)

    # removing extra spaces, hashtags
    text = re.sub("#", "", text)
    text = re.sub("\s+", " ", text)

    return text


def pad(v, MAX_LEN=128):
    return np.pad(v, pad_width=(0, MAX_LEN - len(v)))


def classify_question(model, tokenizer, question):
    question = cleaning(question)
    token = tokenizer.tokenize(question)
    token_enc = tokenizer.encode_plus(token)

    xdata = [np.array([pad(token_enc["input_ids"])]), np.array([pad(token_enc["attention_mask"])]),
             np.array([pad(token_enc["token_type_ids"])])]
    p = model.predict(xdata)
    ypred = p[0].argmax(axis=-1)[0]

    return ypred


def ner_question(model, tokenizer, config, sentence):
    MAX_LEN = 50
    id2label = config.id2label
    token_enc = tokenizer(sentence)
    def pad(v): return np.pad(v, pad_width=(0, MAX_LEN - len(v)))
    xdata = [np.array([pad(token_enc["input_ids"])]), np.array([pad(token_enc["attention_mask"])]),
             np.array([pad(token_enc["token_type_ids"])])]
    p = model.predict(xdata)
    ypred = p[0].argmax(axis=-1)[0]
    labels = [id2label[pr] for pr in ypred]
    tokens = tokenizer.tokenize(sentence, add_special_tokens=True)
    labels = np.array(labels[:len(tokens)])

    if len(np.where(labels == "B_DAT")[0]) == 1 and len(np.where(labels == "B_TIM")[0]) == 0 and len(np.where(labels == "I_TIM")[0]) != 0:
        labels[labels == "I_DAT"] = "I_TIM"
        labels[labels == "B_DAT"] = "B_TIM"

    return tokens, labels


df_capitals = pd.read_csv(os.path.join(abs_path, "database/capitals.csv"))
df_province = pd.read_csv(os.path.join(abs_path, "database/provinces.csv"))


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
        try:
            cityname_eng = translator("fa", "en", cityName)
            cityname_eng = cityname_eng[0][0][0]
            data = requests.get(
                eng_openweatherapi.format(cityname_eng)).json()
            if data["cod"] == "200":
                return data["city"]
            else:
                return None
        except Exception:
            return None


def location_fix(question, location):
    location_fixed = []
    for l in location:
        lc = cleaning(re.sub("پایتخت", "", l))
        if (lc in df_capitals["country"].to_numpy()) and ("پایتخت" in question):
            location_fixed.append(
                df_capitals["capital"].loc[df_capitals["country"] == lc].to_numpy()[0])
        elif (cleaning(l.replace("استان", "")) in df_province["name"].to_numpy()) and ("مرکز" in question):
            location_fixed.append(
                df_province["center"].loc[df_province["name"] == cleaning(l.replace("استان", ""))].to_numpy()[0])
        else:
            location_fixed.append(l)
    for ll in loc_literals:
        if ll in location_fixed:
            location_fixed.remove(ll)
    return location_fixed


def location_(question, tokens, labels):
    bloc = np.array(tokens)[labels == "B_LOC"]
    iloc = np.array(tokens)[labels == "I_LOC"]
    if len(bloc) == 0 and len(iloc) == 0:
        return []
    if len(bloc) == 0 and len(iloc) != 0:
        return location_fix(question, [cleaning(" ".join(list(iloc)))])
    if len(bloc) == 1:
        if bloc[0] in loc_literals:
            return location_fix(question, [cleaning(" ".join(list(iloc)))])
        return location_fix(question, [cleaning(" ".join(np.r_[bloc, iloc]))])
    if len(iloc) == 0:
        return location_fix(question, bloc)
    else:
        bloc_loc = np.where(labels == "B_LOC")[0]
        iloc_loc = np.where(labels == "I_LOC")[0]
        locs = []
        new_bloc_loc = []
        new_bloc = []
        for i, b in enumerate(bloc_loc):
            if not tokens[b] in loc_literals:
                new_bloc_loc.append(b)
                new_bloc.append(bloc[i])
            else:
                new_bloc_loc.append(iloc_loc[iloc_loc > b][0])
                new_bloc.append(iloc[iloc_loc > b][0])
        bloc_loc = np.array(new_bloc_loc)
        bloc = np.array(new_bloc)
        for i in range(len(bloc)):
            if i == len(bloc) - 1:
                iloc_ = iloc[(iloc_loc > bloc_loc[i])]
            else:
                iloc_ = iloc[(iloc_loc > bloc_loc[i]) &
                             (iloc_loc < bloc_loc[i + 1])]
            locs.append(location_fix(question,
                                     [cleaning(" ".join(np.r_[[bloc[i]], iloc_]))])[0])
        if locs:
            for i, l in enumerate(locs):
                locs[i] = l.replace(" ", "‌")
        return locs


def location_handler(question, tokens, labels, check_validation=True):
    loc = location_(question, tokens, labels)
    if loc:
        if check_validation:
            problem_list = []
            for i, l in enumerate(loc):
                l_inf = get_city_info(l)
                problem = False
                if not l_inf:
                    if l in ["تهرون", "ترون"]:
                        loc[i] = "تهران"
                    elif l in ["گم"]:
                        loc[i] = "قم"
                    elif l in ["اصفان", "اصفون"]:
                        loc[i] = "اصفهان"
                    else:
                        problem = True
                problem_list.append([i, problem])
            w_t = np.array(hazm.word_tokenize(question))
            bloc = np.where(labels == "B_LOC")[0] - 1
            iloc = np.where(labels == "I_LOC")[0] - 1
            if len(bloc) >= len(problem_list):
                for i in range(len(problem_list)):
                    if problem_list[i][1]:
                        if i != len(problem_list) - 1:
                            il = iloc[(iloc > bloc[i]) & (iloc < bloc[i+1])]
                        else:
                            il = iloc[iloc > bloc[i]]
                        loc[problem_list[i][0]] = location_fix(
                            question, [" ".join(w_t[np.r_[bloc[i], il]])])[0]
            else:
                loc = [USER_CITY]
    return loc


def mix_tdl(times, dates, locations):
    t = len(times)
    d = len(dates)
    l = len(locations)
    if t == 1 and l == 1 and d == 1:
        return [[times[-1], dates[-1], locations[-1]]]
    elif t >= 2 and l == 1 and d == 1:
        mixture = []
        for tim in times:
            mixture.append([tim, dates[-1], locations[-1]])
        return mixture
    elif t == 1 and l == 1 and d >= 2:
        mixture = []
        for dat in dates:
            mixture.append([times[-1], dat, locations[-1]])
        return mixture
    elif t == 1 and l >= 2 and d == 1:
        mixture = []
        for lc in locations:
            mixture.append([times[-1], dates[-1], lc])
        return mixture
    elif t == d and l == 1:
        mixture = []
        for dat, tim in zip(dates, times):
            mixture.append([tim, dat, locations[-1]])
        return mixture
    elif t == l and d == 1:
        mixture = []
        for tim, lc in zip(times, locations):
            mixture.append([tim, dates[-1], lc])
        return mixture
    elif t == 1 and l == d:
        mixture = []
        for dat, lc in zip(dates, locations):
            mixture.append([times[-1], dat, lc])
        return mixture
    elif t == l and l == d:
        mixture = []
        for i in range(t):
            mixture.append([times[i], dates[i], locations[i]])
        return mixture
    else:
        return None


def unique_without_sort(arr):
    arr = list(np.array(arr).flatten())
    indexes = np.unique(arr, return_index=True)[1]
    return [arr[index] for index in sorted(indexes)]


def concatenate_bi(tokens, labels, b_label, i_label):
    nptokens = np.array(tokens)
    if not isinstance(labels, np.ndarray):
        labels = np.array(labels)
    bs_ = np.where(labels == b_label)[0]
    is_ = np.where(labels == i_label)[0]
    if len(bs_) == 0 and len(is_) == 0:
        return []
    if len(bs_) == 0 and len(is_) != 0:
        return [cleaning(" ".join(list(nptokens[is_])))]
    if len(bs_) == 1:
        return [cleaning(" ".join(list(nptokens[np.r_[bs_, is_]])))]
    if len(is_) == 0:
        return nptokens[bs_]
    n = len(bs_)
    texts_ = []
    for i in range(n):
        st_arr = []
        if i < n - 1:
            ida = is_[np.where(
                (is_ > bs_[i]) & (is_ < bs_[i + 1]))[0]]
        else:
            ida = is_[np.where(is_ > bs_[i])[0]]
        for t in np.r_[bs_[i], ida]:
            st_arr.append(tokens[int(t)])
        texts_.append(" ".join(st_arr))
    return texts_
