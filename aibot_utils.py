
import ast
import hazm
import re
from cleantext import clean
import numpy as np
import tensorflow as tf
import pandas as pd
import os
import requests


abs_path = os.path.dirname(os.path.abspath(__file__))


def read_dict(file_path):
    with open(file_path, "r") as f_dict:
        st = f_dict.readlines()[0]
        new_dict = ast.literal_eval(st)
    return new_dict


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


def classifyQuestion(model, tokenizer, question):
    question = cleaning(question)
    token = tokenizer.tokenize(question)
    token_enc = tokenizer.encode_plus(token)

    xdata = [np.array([pad(token_enc["input_ids"])]), np.array([pad(token_enc["attention_mask"])]),
             np.array([pad(token_enc["token_type_ids"])])]
    p = model.predict(xdata)
    ypred = p[0].argmax(axis=-1)[0]

    return ypred


def nerQuestion(model, tokenizer, config, text):
    tokens = tokenizer.tokenize(tokenizer.decode(tokenizer.encode(text)))
    inputs = tokenizer.encode(text, return_tensors="tf")
    outputs = model(inputs)[0]
    predictions = tf.argmax(outputs, axis=2)
    labels = list(config.label2id.keys())
    p = [labels[pr] for pr in predictions[0].numpy()]
    return tokens, np.array(p)


df_capitals = pd.read_csv(os.path.join(abs_path, "database/capitals.csv"))
df_province = pd.read_csv(os.path.join(abs_path, "database/provinces.csv"))

loc_literals = read_dict("dictionary/loc_literals.list")


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


def location_fix(question, location):
    location_fixed = []
    for l in location:
        if (l in df_capitals["country"].to_numpy()) and ("پایتخت" in question):
            location_fixed.append(
                df_capitals["capital"].loc[df_capitals["country"] == l].to_numpy()[0])
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
    bloc = np.array(tokens)[labels == "B-location"]
    iloc = np.array(tokens)[labels == "I-location"]
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
        bloc_loc = np.where(labels == "B-location")[0]
        iloc_loc = np.where(labels == "I-location")[0]
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


def location_handler(question, tokens, labels):
    loc = location_(question, tokens, labels)
    if loc:
        problem_list = []
        for i, l in enumerate(loc):
            l_inf = get_city_info(l)
            problem = False
            if not l_inf:
                problem = True
            problem_list.append([i, problem])
        w_t = np.array(hazm.word_tokenize(question))
        bloc = np.where(labels == "B-location")[0] - 1
        iloc = np.where(labels == "I-location")[0] - 1
        if len(bloc) >= len(problem_list):
            for i in range(len(problem_list)):
                if problem_list[i][1]:
                    if i != len(problem_list) - 1:
                        il = iloc[(iloc > bloc[i]) & (iloc < bloc[i+1])]
                    else:
                        il = iloc[iloc > bloc[i]]
                    loc[i] = location_fix(
                        question, [" ".join(w_t[np.r_[bloc[i], il]])])[0]
                    # print(w_t[np.r_[bloc[i], il]])
    return loc
