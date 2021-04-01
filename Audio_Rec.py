

import speech_recognition as sr
from deepmine import Deepmine

dpm = Deepmine()


def convert_speech_text(file):
    # try google speech recognition
    try:
        r = sr.Recognizer()
        with sr.AudioFile(file) as source:
            data = r.record(source)
        text = r.recognize_google(data, language='fa-IR')
        return 0, text
    except Exception:
        # try Deepmine
        try:
            s, text = dpm.get_text(file)
            if s != 0:
                return 0, text
            else:
                raise Exception
        except Exception:
            return -1, None


"""
Created on Mon Nov 23 16:49:51 2020

@author: mahsa
"""


def google(file):
    r = sr.Recognizer()
    with sr.AudioFile(file) as source:
        data = r.record(source)
    text = r.recognize_google(data, language='fa-IR')
    return(text)  

