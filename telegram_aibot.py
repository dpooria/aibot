#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from aibot import BOT


type_dict = {"-1": "پرسش خارج از توان",
             "1": "آب و هوا",
             "2": "اوقات شرعی",
             "3": "ساعت",
             "4": "تقویم"}

# build the bot
bot = BOT()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.


def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text(""" سلام. ممنون از شما که وقت میزارید و در تست این ربات به من کمک می‌کنید!
     سوال های شما باید از چهار نوع 
     آب و هوا
     اوقات شرعی
     ساعت
     تقویم
     باشند. اگر سوال مربوط به این ۴ نوع نبود ربات عبارت <<خارج از توان>> را برمیگردونه. لطفا در صورت هرگونه مشکل منو در جریان بزارید.
     @dpooria75
     یا از طریق <<گزارش خطا>> گزارش دهید.
        """)


def report(update, context):
    """Send a message when the command /report is issued."""
    with open("report/reports.txt", "a") as freport:
        print(update.message.text, file=freport)
    update.message.reply_text('ممنون. گزارش شما ثبت شد')


st_res_show = "نوع سوال: {} \n نام شهرها: {} \n تاریخ: {} \n زمان: {} \n اوقات شرعی: {} \n نوع تقویم: {} \n مناسبت‌ها: {} \n جواب شما: {}"


def echo(update, context):
    """on text message"""
    res = bot.AIBOT(update.message.text)
    res_str = st_res_show.format(type_dict[res["type"]], res["city"], res["date"],
                                 res["time"], res["religious_time"], res["calendar_type"], res["event"], res["result"])
    update.message.reply_text(res_str)
    with open("collect/userID{}Question{}.txt".format(update.message.chat.username, res["result"]), "a") as f_res:
        print(update.message.text, file=f_res)
        print("\n", file=f_res)
        print(res_str, file=f_res)
        print("\n", file=f_res)
        print(res, file=f_res)
        print("\n\n\n", file=f_res)


def help(update, context):
    """on help"""
    helpText = """سوال‌های شما باید به صورت جمله کامل و در مورد یکی از موضوع‌های آب و هوا، تقویم، ساعت و اوقات شرعی باشند؛ 
        نمونه‌ای از سوالات:
        *آب و هوا
        -هوای تهران در اول بهمن ماه ساعت ۸ شب چند درجه است
        -دمای هوای اصفهان الان چقدر است؟
        -وضعیت هوای مشهد فردا ساعت ۱۱ چطور است؟
        -امروز تبریز در چه ساعتی سردتر است 
        -اختلاف دمای تهران و اصفهان در موقع اذان ظهر چه قدر است؟
        *تقویم
        -امروز چه مناسبتی وجود دارد
        -چهارشنبه هفته بعد چندم است
        -روز ۱۲-۱۰-۱۳۹۹ چند شنبه بود
        -عاشورای حسینی سال بعد چندم است
        *ساعت
        -الان ساعت در برلین چند است
        -تا ساعت ۵ بعد از ظهر فردا چند ساعت مانده است
        -اختلاف ساعت مسکو و تهران چند ساعت است
        *اوقات شرعی
        -اذان صبح به افق تهران چه موقع است
        -زمان طلوع آفتاب در اصفهان را بگو
        -نیمه شب شرعی پس فردا شب در مشهد چه زمانی است
        -فاصله بین اذان مغرب و غروب آفتاب امروز در تبریز چقدر است"""
    update.message.reply_text(helpText)


def error(update, context):
    """Log Errors caused by Updates."""
    with open("errorlog.txt", "a") as ferr:
        logger.warning('Update "%s" caused error "%s"', update, context.error)
        print('Update "%s" caused error "%s"' %
              (update, context.error), file=ferr)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary

    REQUEST_KWARGS = {'proxy_url': 'http://127.0.0.1:8118'}
    updater = Updater(
        "1400856218:AAGt6WPlRxL-FmcB3dhO7PS-7ErVxCIni9c", use_context=True, request_kwargs=REQUEST_KWARGS)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("report", report))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("question", echo))  

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
