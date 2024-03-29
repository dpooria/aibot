
from cleantext.clean import clean
#from aryana import *
#from Audio_Rec import convert_speech_text
from transformers import TFBertForSequenceClassification, TFAutoModelForTokenClassification
from transformers import BertTokenizer, AutoTokenizer, AutoConfig

from weatherAPI import Weather
from adhanAPI import Adhan
from timeAPI import Time
from calenderAPI import Calender
from aibot_utils import cleaning, classify_question, ner_question


TR_ID_AIBOTID = {0: "1", 1: "2", 4: "3", 3: "4", 2: "-1"}
CLASSIFIER_PATH = "../models/classifier"
PARSBERTNER_PATH = "../models/ner_model"


class BOT:
    def __init__(self):
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

        # self.deepm = Deepmine()

    def is_modified(self):
        return self.modified

    '''
    This method takes an string as input, the string contains the string of question.
    If you are using this method, we presume that you want to use nevisa and ariana.

    :Param Question : an string containing the question.

    : return : A dictionary containing the type of question, corresponding arguments, api_url and result.
    '''

#     def aibot_voice(self, Address):
#         answer = {'type': ['-1'], 'city': [], 'date': [],
#                   'time': [], 'religious_time': [], 'calendar_type': [], 'event': [], 'api_url': '', 'result': []}
#         r, Question = convert_speech_text(Address)
#         if r == -1 or not Question:
#             # print("error in sound conversion")
#             response = aryana("مشکل در تشخیص صوت به وجود آمد")
#             return answer, response, Question, ""
#         # print("the sound has been converted to text {}".format(Question))

#         # Question = google(Address)
#         Question = cleaning(Question)
#         type_pred = TR_ID_AIBOTID[classify_question(
#             self.classifier_model, self.classifier_tokenizer, Question)]

#         tokens, labels = ner_question(
#             self.ner_model, self.ner_tokenizer, self.ner_config, Question)

#         if "خاموش" in tokens:
#             return None, None, 1
#         if ("آهنگ" in tokens or "اهنگ" in tokens):
#             return None, None, 2

#         if type_pred == "-1":
#             answer["type"] = ["-1"]
#             generated_sentence = "سوال پرسیده شده خارج از توان بات می‌باشد"
#         elif type_pred == "1":
#             answer, generated_sentence = self.weather_api.get_answer(
#                 Question, tokens, labels)
#             generated_sentence = cleaning(generated_sentence).replace("٫", "/")
#         elif type_pred == "2":
#             answer, generated_sentence = self.adhan_api.get_answer(
#                 Question, tokens, labels)
#             if not answer:
#                 answer, generated_sentence = self.weather_api.get_answer(
#                     Question, tokens, labels)
#         elif type_pred == "3":
#             answer, generated_sentence = self.time_api.get_answer(
#                 Question, tokens, labels)
#         else:
#             answer, generated_sentence = self.calender_api.get_answer(
#                 Question, tokens, labels)

#         if 'سلام' in tokens:
#             generated_sentence = "سلام، " + generated_sentence

#         if generated_sentence:
#             response = aryana(generated_sentence)
#         else:
#             response = aryana("متاسفانه پاسخی یافت نشد")

#         # print("answer has been generated: {}".format(generated_sentence))
#         # with open("test.txt", 'w') as ftest:
#         #     print(Question, file=ftest)
#         #     print(answer, file=ftest)
#         #     print(generated_sentence, file=ftest)

#         return answer, response, Question, generated_sentence

    '''
    This method takes an string as input, the string contains the address of a wav file.
    You can either use your own speech recognition or nevisa to extract the question from that file.
    Also you should call ariana to create an audio file as output.
    
    :Param Address : an string containing the the address of a wav file.

    : return : A dictionary containing the type of question, corresponding arguments, api_url and result.
    '''

    def aibot(self, Question):
        answer = {'type': ['-1'], 'city': [], 'date': [],
                  'time': [], 'religious_time': [], 'calendar_type': [], 'event': [], 'api_url': '', 'result': []}

        type_pred = TR_ID_AIBOTID[classify_question(
            self.classifier_model, self.classifier_tokenizer, Question)]

        tokens, labels = ner_question(
            self.ner_model, self.ner_tokenizer, self.ner_config, Question)

        Question = cleaning(Question)

        if type_pred == "-1":
            answer["type"] = ["-1"]
            generated_sentence = "سوال پرسیده شده خارج از توان بات می‌باشد"
        elif type_pred == "1":
            answer, generated_sentence = self.weather_api.get_answer(
                Question, tokens, labels)
            generated_sentence = cleaning(generated_sentence).replace("٫", "/")
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

        return answer, generated_sentence

    def AIBOT_Modified(self, Address):
        answer = {'type': '0', 'city': [], 'date': [],
                  'time': [], 'religous_time': [], 'calendar_type': [], 'event': [], 'api_url': '', 'result': ''}
        '''
        You should implement your code right here.
        '''
        return answer
