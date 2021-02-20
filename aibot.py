
from transformers import TFBertForSequenceClassification, TFAutoModelForTokenClassification
from transformers import BertTokenizer, AutoTokenizer, AutoConfig
from speechRec import google
from aryana import *
from weatherAPI import Weather
from adhanAPI import Adhan
from timeAPI import Time
from calenderAPI import Calender
from aibot_utils import cleaning, classify_question, ner_question
import os

TR_ID_AIBOTID = {0: "1", 1: "2", 4: "3", 3: "4", 2: "-1"}
# CLASSIFIER_PATH = "/var/www/AIBot/media/codes/user_dpooria75@gmail.com/classifier"
# PARSBERTNER_PATH = "/var/www/AIBot/media/parsbert"
CLASSIFIER_PATH = "../models/classifier"
PARSBERTNER_PATH = "../models/ner_model"


class BOT:
    def __init__(self):
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        self.modified = False
        # load models
        self.classifier_tokenizer = BertTokenizer.from_pretrained(
            CLASSIFIER_PATH)
        self.classifier_config = AutoConfig.from_pretrained(CLASSIFIER_PATH)
        self.classifier_model = TFBertForSequenceClassification.from_pretrained(
            CLASSIFIER_PATH)

        self.ner_tokenizer = AutoTokenizer.from_pretrained(PARSBERTNER_PATH)
        self.ner_config = AutoConfig.from_pretrained(PARSBERTNER_PATH)
        self.ner_model = TFAutoModelForTokenClassification.from_pretrained(
            PARSBERTNER_PATH)
        self.weather_api = Weather()
        self.adhan_api = Adhan()
        self.time_api = Time()
        self.calender_api = Calender()

    def is_modified(self):
        return self.modified

    '''
    This method takes an string as input, the string contains the string of question.
    If you are using this method, we presume that you want to use nevisa and ariana.

    :Param Question : an string containing the question.

    : return : A dictionary containing the type of question, corresponding arguments, api_url and result.
    '''

    def AIBOT(self, Question):
        answer = {'type': ['0'], 'city': [], 'date': [],
                  'time': [], 'religious_time': [], 'calendar_type': [], 'event': [], 'api_url': '', 'result': []}
        Question = cleaning(Question)
        type_pred = TR_ID_AIBOTID[classify_question(
            self.classifier_model, self.classifier_tokenizer, Question)]

        if type_pred == "-1":
            answer["type"] = "-1"
            return answer, ""
        tokens, labels = ner_question(
            self.ner_model, self.ner_tokenizer, self.ner_config, Question)
        if type_pred == "1":
            return self.weather_api.get_answer(Question, tokens, labels)
        elif type_pred == "2":
            res = self.adhan_api.get_answer(Question, tokens, labels)
            if res:
                return res
            else:
                return self.weather_api.get_answer(Question, tokens, labels)
        elif type_pred == "3":
            return self.time_api.get_answer(Question, tokens, labels)
        else:
            return self.calender_api.get_answer(Question, tokens, labels)

    '''
    This method takes an string as input, the string contains the address of a wav file.
    You can either use your own speech recognition or nevisa to extract the question from that file.
    Also you should call ariana to create an audio file as output.
    
    :Param Address : an string containing the the address of a wav file.

    : return : A dictionary containing the type of question, corresponding arguments, api_url and result.
    '''

    def AIBOT_Modified(self, Address):
        # self.deepm = Deepmine()
        answer = {'type': ['0'], 'city': [], 'date': [],
                  'time': [], 'religious_time': [], 'calendar_type': [], 'event': [], 'api_url': '', 'result': []}
        # r, Question = self.deepm.get_text(Address)
        # if r == 0:
        #     generated_sentence = "ارور تبدیل صوت به تکست!"
        #     response = aryana(generated_sentence)
        #     return answer, response

        # file = open(Address, mode='rb')
        # comment = "1130377539"
        # text = nevisa(file, comment)
        # print(text)
        text = google(Address)
        Question = text
        Question = cleaning(Question)
        type_pred = TR_ID_AIBOTID[classify_question(
            self.classifier_model, self.classifier_tokenizer, Question)]

        if type_pred == "-1":
            answer["type"] = ["-1"]
            generated_sentence = "سوال پرسیده شده خارج از توان بات می‌باشد"
        tokens, labels = ner_question(
            self.ner_model, self.ner_tokenizer, self.ner_config, Question)
        if type_pred == "1":
            answer, generated_sentence = self.weather_api.get_answer(
                Question, tokens, labels)
        elif type_pred == "2":
            answer, generated_sentence = self.adhan_api.get_answer(
                Question, tokens, labels)
            if not answer:
                answer, generated_sentence = self.weather_api.get_answer(
                    Question, tokens, labels)
        elif type_pred == "3":
            answer, generated_sentence = self.time_api.get_answer(
                Question, tokens, labels)
        else:
            answer, generated_sentence = self.calender_api.get_answer(
                Question, tokens, labels)

        response = aryana(generated_sentence)

        return answer, response, Question, generated_sentence
