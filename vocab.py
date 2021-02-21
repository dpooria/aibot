
USER_CITY = "تهران"

# weather_logical1 = {"سردترین": np.argmin, "سرد ترین": np.argmin, "سرد‌ترین": np.argmin, "گرم ترین": np.argmax, "گرمترین": np.argmax,
#                     "گرم‌ترین": np.argmax, "میانگین دما": np.mean, "اختلاف دما": np.diff, "حداقل دما": np.min, "حداکثر دما": np.argmax, "بیشترین": np.argmax,
#                     "بیشینه": np.argmax, "کمینه": np.argmin, "کمترین": np.argmin, "کم‌ترین": np.argmin, "سردتر": np.argmin, "گرم‌تر": np.argmax, "گرمتر": np.argmax, "اختلاف": np.diff, "بیشتر": np.max, "کمتر": np.min, "میانگین": np.mean}

# weather_logical2 = {"سردترین": np.min, "سرد ترین": np.min, "سرد‌ترین": np.min, "گرم ترین": np.max, "گرمترین": np.max,
#                     "گرم‌ترین": np.max, "میانگین دما": np.mean, "اختلاف دما": np.diff, "حداقل دما": np.min, "حداکثر دما": np.max, "بیشترین": np.max,
#                     "بیشینه": np.max, "کمینه": np.min, "کمترین": np.min, "کم‌ترین": np.min, "سردتر": np.min, "گرم‌تر": np.max, "گرمتر": np.max, "اختلاف": np.diff, "بیشتر": np.max, "کمتر": np.min, "میانگین": np.mean}

weather_logical = {"سردترین": "amin_abs", "سرد ترین": "amin_abs", "سردتر": "amin", "سرد‌تر": "amin", "کمترین": "amin_abs", "کم‌ترین": "amin_abs",
                   "کم تر": "amin", "کم‌تر": "amin", "سرد تر": "amin", "کمتر": "amin", "کمینه": "amin_abs", "حداقل": "amin_abs",
                   "گرمترین": "amax_abs", "گرم‌ترین": "amax_abs", "گرم ترین": "amax_abs", "گرمتر": "amax", "گرم‌تر": "amax", "گرم تر": "amax",
                   "بیشترین": "amax_abs", "بیشتر": "amax", "بیشینه": "amax_abs", "حداکثر": "amax_abs", "ماکسیمم": "amax_abs", "ماکزیمم": "amax_abs",
                   "مینیمم": "amin", "حد بالا": "amax", "حد پایین": "amin", "بالا": "amax", "پایین": "amin", "میانگین": "mean",
                   "متوسط": "mean", "حد وسط": "mean", "اختلاف": "diff", "تفاوت": "diff"}

year_literals = {'سال پیش': -1, 'سال قبل': -1, 'سال گذشته': -1, 'سال آینده': 1, 'سال بعد': 1,
                 'سال پیش رو': 1, 'امسال': 0, 'پارسال': -1, 'سال اینده': 1, 'سال جاری': 0, 'سال دیگه': 1, 'سال دیگر': 1}

weeks_day_dict = {'شنبه': 0, 'یکشنبه': 1, 'دوشنبه': 2, 'سه\u200cشنبه': 3, 'چهارشنبه': 4, 'پنج\u200cشنبه': 5, 'جمعه': 6, 'پنج شنبه': 5,
                  'پنجشنبه': 5, 'یک\u200cشنبه': 1, 'یک شنبه': 1, 'دو شنبه': 2, 'دو\u200cشنبه': 2, 'سه شنبه': 3, 'چهار\u200cشنبه': 4, 'آدینه': 6, 'ادینه': 6}

week_literals = {'هفته\u200cی پیش رو': 1, 'هفته\u200cی آینده': 1, 'هفته آینده': 1, 'هفته اینده': 1, 'هفته\u200cی اینده': 1, 'هفته بعد': 1, 'هفته\u200cی بعد': 1, 'هفته دیگر': 1,
                 'هفته\u200cی دیگر': 1, 'هفته\u200cی گذشته': -1, 'هفته گذشته': -1, 'هفته قبل': -1, 'هفته\u200cی قبل': -1, 'هفته پیش': -1, 'هفته\u200cی پیش': -1, 'این هفته': 0, 'هفته\u200cی جاری': 0}

perstr_to_num = {'یک': 1, 'یکم': 1, 'یکمین': 1, 'دو': 2, 'دوم': 2, 'دومین': 2, 'سه': 3, 'سوم': 3, 'سومین': 3, 'سهمین': 3, 'چهار': 4, 'چهارم': 4, 'چهارمین': 4, 'پنج': 5, 'پنجم': 5, 'پنجمین': 5, 'شش': 6, 'ششم': 6, 'ششمین': 6, 'هفت': 7, 'هفتم': 7, 'هفتمین': 7, 'هشت': 8, 'هشتم': 8, 'هشتمین': 8, 'نه': 9, 'نهم': 9, 'نهمین': 9, 'ده': 10, 'دهم': 10, 'دهمین': 10, 'یازده': 11, 'یازدهم': 11, 'یازدهمین': 11, 'دوازده': 12, 'دوازدهم': 12, 'دوازدهمین': 12, 'سیزده': 13, 'سیزدهم': 13, 'سیزدهمین': 13, 'چهارده': 14, 'چهاردهم': 14, 'چهاردهمین': 14, 'پانزده': 15, 'پانزدهم': 15, 'پانزدهمین': 15, 'شانزده': 16, 'شانزدهم': 16, 'شانزدهمین': 16, 'هفده': 17, 'هفدهم': 17, 'هفدهمین': 17, 'هجده': 18, 'هجدهم': 18, 'هجدهمین': 18, 'نوزده': 19, 'نوزدهم': 19, 'نوزدهمین': 19, 'بیست': 20, 'بیستم': 20, 'بیستمین': 20, 'سی': 30, 'سیم': 30, 'سیمین': 30, 'سی\u200cام': 30, 'سی\u200cامین': 30, 'چهل': 40,
                 'چهلم': 40, 'چهلمین': 40, 'پنجاه': 50, 'پنجاهم': 50, 'پنجاهمین': 50, 'شصت': 60, 'شصتم': 60, 'شصتمین': 60, 'هفتاد': 70, 'هفتادم': 70, 'هفتادمین': 70, 'هشتاد': 80, 'هشتادم': 80, 'هشتادمین': 80, 'نود': 90, 'نودم': 90, 'نودمین': 90, 'صد': 100, 'صدم': 100, 'صدمین': 100, 'دویست': 200, 'دویستم': 200, 'دویستمین': 200, 'سیصد': 300, 'سیصدم': 300, 'سیصدمین': 300, 'چهارصد': 400, 'چهارصدم': 400, 'چهارصدمین': 400, 'پانصد': 500, 'پانصدم': 500, 'پانصدمین': 500, 'ششصد': 600, 'ششصدم': 600, 'ششصدمین': 600, 'هفتصد': 700, 'هفتصدم': 700, 'هفتصدمین': 700, 'هشتصد': 800, 'هشتصدم': 800, 'هشتصدمین': 800, 'نهصد': 900, 'نهصدم': 900, 'نهصدمین': 900, 'هزار': 1000, 'هزارم': 1000, 'هزارمین': 1000, 'میلیون': 1000000, 'میلیونم': 1000000, 'میلیونمین': 1000000, 'میلیارد': 1000000000, 'میلیاردم': 1000000000, 'میلیاردمین': 1000000000, 'صفر': 0, 'صفرم': 0, 'صفرمین': 0, 'اول': 1, 'اولین': 1}

week_days = {0: 'شنبه', 6: 'جمعه', 1: 'یکشنبه', 2: 'دوشنبه',
             3: 'سه\u200cشنبه', 4: 'چهارشنبه', 5: 'پنجشنبه'}

week_days_asked = ['چند شنبه', 'چند شنبست', 'چه روز از هفته',
                   'چه روزی از هفته', 'چه روز هفته', 'چند شنبس', 'چندشنبه']

weather_temperature_asked = ['چند درجه', 'درجه هوا', 'درجه\u200cی هوا', 'دمای هوا',
                             'میزان دما', 'مقدار دما', 'درجه هوا', 'میزان دما', 'چقدر است', 'چقدر می\u200cباشد']

weather_description_asked = ['چطور', 'چگونه', 'چه طور', 'چه\u200cطور', 'بارانی',
                             'برفی', 'ابری', 'آفتابی', 'طوفانی', 'چه وضعی', 'چه\u200cصورت', 'چه صورت', "افتابیه", "برفه", "بارونیه", "بارونه", "بارون میاد", "بارانیه", "باران میاد", "باد میاد", "آفتابیه", "هوای صافه"]

tr_weather_description = {'Clear': 'آفتابی', 'Clouds': 'ابری',
                          'Rain': 'بارانی', 'Snow': 'برفی', 'Extreme': 'طوفانی'}

tr_engnum_arabicnum = {'0': '۰', '1': '۱', '2': '۲', '3': '۳',
                       '4': '۴', '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'}

tr_arabicnum_engnum = {'۰': '0', '۱': '1', '۲': '2', '۳': '3',
                       '۴': '4', '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'}

tr_adhan_names = {'اذان صبح': 'Fajr', 'اذان فجر': 'Fajr', 'طلوع آفتاب': 'Sunrise', 'طلوع افتاب': 'Sunrise', 'اذان ظهر': 'Dhuhr', 'اذان عصر': 'Asr', 'اذان مغرب': 'Maghrib', 'اذون صبح': 'Fajr', 'اذون فجر': 'Fajr', 'اذون ظهر': 'Dhuhr', 'اذون عصر': 'Asr', 'اذون مغرب': 'Maghrib', 'اذون عشا': 'Isha', "آذان صبح": "Fajr", "آذان ظهر": "Dhuhr", "آذان مغرب": "Maghrib",
                  'غروب آفتاب': 'Sunset', 'غروب افتاب': 'Sunset', 'نیمه شب شرعی': 'Midnight', 'نیمه\u200cشب شرعی': 'Midnight', 'امساک': 'Imsak', 'طلوع خورشید': 'Sunrise', 'غروب خورشید': 'Sunset', 'نماز صبح': 'Fajr', 'نماز ظهر': 'Dhuhr', 'نماز عصر': 'Asr', 'نماز مغرب': 'Maghrib', 'نماز عشا': 'Isha', 'نصف شب': 'Isha', "خورشید طلوع": "Sunrise", "خورشید غروب": "Sunset", "اذان‌صبح": "Fajr", "اذان‌ظهر": "Dhuhr", "اوقات شرعی": "All"}

time_literals = {'ساعت قبل': -1, 'ساعت گذشته': -1, 'ساعت پیش': -1, 'ساعت آینده': 1, 'ساعت اینده': 1, 'ساعت بعد': 1, 'ساعت دیگر': 1, 'دقیقه بعد': 0.016666666666666666, 'دقیقه آینده': 0.016666666666666666, 'دقیقه اینده': 0.016666666666666666, 'دقیقه\u200cی بعد': 0.016666666666666666, 'دقیقه\u200cی آینده': 0.016666666666666666, 'دقیقه\u200cی اینده': 0.016666666666666666, 'دقیقه قبل': -
                 0.016666666666666666, 'دقیقه گذشته': -0.016666666666666666, 'دقیقه پیش': -0.016666666666666666, 'دقیقه\u200cی گذشته': -0.016666666666666666, 'دقیقه\u200cی قبل': -0.016666666666666666, 'دقیقه\u200cی پیش': -0.016666666666666666, 'دقیقه\u200cی دیگر': 0.016666666666666666, 'دقیقه دیگر': 0.016666666666666666, 'الان': 0, 'همین الآن': 0, 'همین حالا': 0, 'همین الان': 0, 'این لحظه': 0, 'این ساعت': 0}

time_asked = ['تا ساعت', 'چند ساعت',
              'اختلاف زمان', 'چه ساعت', 'به وقت', 'ساعت چند', "کدام ساعت", "کدام زمان", "در چه موقع"]

shamsimonthes = {'فروردین': 1, 'اردیبهشت': 2, 'خرداد': 3, 'تیر': 4, 'مرداد': 5, 'شهریور': 6,
                 'مهر': 7, 'آبان': 8, 'آذر': 9, 'دی': 10, 'بهمن': 11, 'اسفند': 12, 'ابان': 8, 'اذر': 9, 'امرداد': 5}

qamariMonthes = {'محرم': 1, 'صفر': 2, 'ربیع الاول': 3, 'ربیع الثانی': 4, 'جمادی الاول': 5, 'جمادی الثانی': 6, 'رجب': 7,
                 'شعبان': 8, 'رمضان': 9, 'شوال': 10, 'ذیحجه': 11, 'ذیقعده': 12, 'ذوالحجه': 11, 'ذوالقعده': 12, 'جمادی الثانیه': 6}

num_to_perstr = {1: 'یک', 2: 'دو', 3: 'سه', 4: 'چهار', 5: 'پنج', 6: 'شش', 7: 'هفت', 8: 'هشت', 9: 'نه', 10: 'ده', 11: 'یازده', 12: 'دوازده', 13: 'سیزده', 14: 'چهارده', 15: 'پانزده', 16: 'شانزده', 17: 'هفده', 18: 'هجده', 19: 'نوزده', 20: 'بیست', 30: 'سی',
                 40: 'چهل', 50: 'پنجاه', 60: 'شصت', 70: 'هفتاد', 80: 'هشتاد', 90: 'نود', 100: 'صد', 200: 'دویست', 300: 'سیصد', 400: 'چهارصد', 500: 'پانصد', 600: 'ششصد', 700: 'هفتصد', 800: 'هشتصد', 900: 'نهصد', 1000: 'هزار', 1000000: 'میلیون', 1000000000: 'میلیارد', 0: 'صفر'}

month_literals = {'این ماه': 0, 'ماه جاری': 0, 'این برج': 0, 'ماه آینده': 1, 'برج بعد': 1, 'ماه بعد': 1,
                  'ماه اینده': 1, 'برج اینده': 1, 'برج قبل': -1, 'ماه پیش': -1, 'ماه گذشته': -1, 'ماه قبل': -1}

minute_literals = {'و نیم': 30, 'و ربع': 15}

miladimonthes = {'ژانویه': 1, 'فوریه': 2, 'مارس': 3, 'آوریل': 4, 'آپریل': 4, 'مارچ': 3, 'مه': 5, 'می': 5, 'ژوئن': 6, 'ژون': 6,
                 'ژوئیه': 7, 'جولای': 7, 'اوت': 8, 'آگوست': 8, 'سپتامبر': 9, 'اکتبر': 10, 'نوامبر': 11, 'دسامبر': 12, 'اپریل': 4, 'اوریل': 4, 'اگوست': 8}

adhan_logical_question = ['اختلاف', 'تفاوت', 'فاصله', 'فاصله\u200cی']

loc_literals = ['روستای', 'شهرستان', 'شهر', 'کشور', 'استان',
                'مکان', 'ده', 'دهکده', 'دهات', 'منطقه', 'بندر', 'روستا', 'جزیره']

hours_left_asked = ['تا ساعت', 'چقدر زمان', 'مانده',
                    'چند ساعت گذشته', 'چقدر زمان گذشته', 'باقی است', 'باقیست', "گذشته"]

hours_difference_asked = ['اختلاف زمان', 'اختلاف ساعت',
                          'فاصله ساعت', 'فاصله زمان', 'تفاوت زمان', "مانده", "گذشته"]

event_literals = ['روز جهانی', 'شهادت', 'عید', 'ولادت', 'سالگرد', 'سالروز',
                  'روز مادر', 'روز پدر', 'روز دختر', 'روز پسر', 'جشن', 'میلاد', 'عاشورا', 'تاسوعا']

event_asked = ['مناسبت', 'اتفاق', 'مناسبتها', 'چه روزی است', 'وقایع']

day_literals = {'روز پیش رو': 1, 'فردا': 1, 'روز بعد': 1, 'روز آینده': 1j, 'امروز': 0, 'فردای': 1, 'دیروز': -1, 'روز پیش': -1, 'روز گذشته': -1, 'روز قبل': -1, 'روز اینده': 1j, 'هفته\u200cی آینده': 7j, 'هفته آینده': 7j, 'هفته اینده': 7j, 'هفته\u200cی اینده': 7j, 'هفته بعد': 7j, 'هفته\u200cی بعد': 7j, 'هفته دیگر': 7j,
                'هفته\u200cی دیگر': 7j, 'هفته\u200cی گذشته': (-0-7j), 'هفته گذشته': (-0-7j), 'هفته قبل': (-0-7j), 'هفته\u200cی قبل': (-0-7j), 'هفته پیش': (-0-7j), 'هفته\u200cی پیش': (-0-7j), 'پس\u200cفردا': 2, 'پریروز': -2, 'پس فردا': 2, 'پسفردا': 2, 'روز دیگر': 1, 'روز دیگه': 1, 'روز دیگ': 1, 'شب پیش رو': 1, 'روز آتی': 1, 'امشب': 0, "این هفته": 0j,
                "هفته دیگه": 7j}

day_asked = ['کدام روز', 'چه روز', 'چه روزی', 'چه\u200cروزی', 'چه\u200cروز']

convert_asked = {'به قمری': 2, 'به شمسی': 0, 'به میلادی': 1, 'به تاریخ هجری': 2, 'به تاریخ شمسی': 0, 'به تاریخ میلادی': 1, 'چندم قمری': 2, 'چندم شمسی': 0, 'چندم میلادی': 1,
                 'تاریخ شمسی': 0, 'تاریخ قمری': 2, 'تاریخ میلادی': 1, 'چندم هجری قمری': 2, 'تاریخ هجری قمری': 2, 'روز میلادی': 1, 'روز شمسی': 0, 'روز هجری قمری': 2, 'روز قمری': 2, 'روز هجری': 2, "به هجری قمری": 2, 0: "به هجری شمسی"}

calender_type_dict = {'شمسی': 0, 'میلادی': 1,
                      'هجری قمری': 2, 'قمری': 2, 'جلالی': 0, 'هجری شمسی': 0}

am_pm_dict = {'صبح': 0, 'بعد از ظهر': 1, 'عصر': 1, 'غروب': 1, 'شب': 1,
              'بامداد': 0, 'قبل از ظهر': 0, 'قبل ظهر': 0, 'امشب': 1}

after_event = ['چه روزی', 'چه تاریخی', 'چه تاریخ', 'چه روز', 'است', 'می\u200cباشد', 'می\u200cباشد', 'کیه', 'کی', 'چه موقع',
               'امسال', 'سال', 'چندم', 'ماه', '؟', '.', '!', 'بود', 'خواهد', 'اتفاق', 'افتاد', 'قرار', 'چه', 'روزیه', 'روزی', 'در ه', "در چه", "در", "چه"]

wrong_date = ["روز", "شب", "امسال"]

temp_asked = ["چقدر", "چند درجه", "چه قدر", "چه‌قدر", "چه میزان", "چه اندازه"]


num2fa_gen = {1: "یکمِ", 2: "دوم", 3: "سوم", 4: "چهارم", 5: "پنجم", 6: "ششم", 7: "هفتم", 8: "هشتم", 9: "نهم", 10: "دهم", 11: "یازدهم", 12: "دوازدهم", 13: "سیزدهم", 14: "چهاردهم", 15: "پانزدهم", 16: "شانزدهم", 17: "هفدهم", 18: "هجدهم",
              19: "نوزدهم", 20: "بیستم", 21: "بیست و یکم", 22: "بیست و دوم", 23: "بیست و سوم", 24: "بیست و چهارم", 25: "بیست و پنجم", 26: "بیست و ششم", 27: "بیست و هفتم", 28: "بیست و هشتم", 29: "بیست و نهم", 30: "سی‌ام", 31: "سی و یکم", }
