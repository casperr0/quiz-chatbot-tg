#!/usr/bin/env python3
import logging
from typing import Dict

import telegram
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler,Filters, MessageHandler
from telegram.ext.dispatcher import run_async
from bot.reply import reply_msg, judge_msg, prob_markup
from bot.user import User
from bot.config import TOKEN
from bot import backend
from random import randrange

request = telegram.utils.request.Request(con_pool_size=20)
bot = telegram.Bot(token=TOKEN, request=request)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
ENTITY: Dict[str, User] = {}

def send_new_problem(user_id,chat_id):
    global ENTITY
    uid = str(user_id)
    prob = ENTITY[uid].get_problem()
    if prob:
        bot.send_message(
            chat_id=chat_id,
            text=prob.text(),
            parse_mode='HTML',
            reply_markup=prob_markup(prob.quiz_uuid, hint=prob.hint)
        )
    else:
        bot.send_message(chat_id=chat_id, text=reply_msg('finish'))
        bot.send_message(
            chat_id=chat_id,
            text="""You have completed all the questions!！\n
                 If you want to continue practicing, you can enter /start to continue answering (no points will be counted)
                 If you want to know your score type /status"""
        )

def send_new_problem_with_photo(user_id, chat_id):
    global ENTITY
    uid = str(user_id)
    prob = ENTITY[uid].get_problem()
    print(prob)
    if prob:
        bot.send_message(
            chat_id=chat_id,
            parse_mode='HTML',
            text=prob.text(),
        )
        #photo = photos[randrange(len(photos))]
        with open(prob.photo_name, 'rb') as f:
            bot.send_photo(
                chat_id=chat_id,
                parse_mode='HTML',
                photo=f,
                reply_markup=prob_markup(prob.quiz_uuid, hint=prob.hint)
        )
    else:
        bot.send_message(chat_id=chat_id, text=reply_msg('finish'))
        bot.send_message(
            chat_id=chat_id,
            text="""You have completed all the questions!！\n
                 If you want to continue practicing, you can enter /start to continue answering (no points will be counted)
                 If you want to know your score type /status"""
        )


def company_name_handler(update, _):
    #update.message.reply_text(update.message.text)
    #message_text = update.message.text
    global ENTITY

    chat_id = update.message.chat_id
    user_id = update.message.chat.id
    uid = str(user_id)
    nickname = update.message.from_user.username

    user = User(nickname, uid)

    if user.is_registered():
        ENTITY[uid] = user
        send_new_problem_with_photo(user_id, chat_id)
        return

    if not user.register(bot, chat_id, update):
        reply = 'Unable to create an account！'
        bot.send_message(chat_id=chat_id, text=reply)
        return

    logger.info(f'User {nickname}({uid}) registered')
    ENTITY[uid] = user
    bot.send_message(chat_id=chat_id, text=reply_msg('welcome'))
    send_new_problem_with_photo(user_id, chat_id)


def start_handler(update, _):
    global ENTITY
    chat_id = update.message.chat_id
    user_id = update.message.chat.id
    uid = str(user_id)
    #nickname = update.message.from_user.username

    if uid in ENTITY:
        send_new_problem_with_photo(user_id, chat_id)
        return

    reg = backend.search(user_id)
    if reg:
        return

    bot.send_message(
        chat_id=chat_id,
        text="""Please enter your company name """
    )

def callback_handler(update, _):
    global ENTITY

    ans, quiz_uuid = update.callback_query.data.split(' ')
    msg = update.callback_query.message
    user_id = update.callback_query.message.chat.id


    uid = str(user_id)
    if uid not in ENTITY:
        return

    user = ENTITY[uid]

    # ignore any intend to answer old problems
    if quiz_uuid != user.prob.quiz_uuid:
        update.callback_query.answer()
        return

    if ans == '__HINT__':
        bot.edit_message_reply_markup(
            chat_id=msg.chat_id,
            message_id=msg.message_id,
            reply_markup=prob_markup(quiz_uuid)
        )
        reply = f'Hint: {ENTITY[uid].prob.hint}'
        bot.send_message(chat_id=msg.chat_id, text=reply)
    else:
        bot.edit_message_reply_markup(
            chat_id=msg.chat_id,
            message_id=msg.message_id
        )
        result = user.check_answer(ans)
        bot.send_message(chat_id=msg.chat_id, text=judge_msg(result))

        send_new_problem_with_photo(user_id, msg.chat_id)

def status_handler(update, _):
    global ENTITY
    chat_id = update.message.chat_id
    user_id = update.message.chat.id
    uid = str(user_id)

    if uid not in ENTITY:
        reply = 'Something went wrong, try to re-enter /start to see'
        bot.send_message(chat_id=chat_id, text=reply)
        return

    user = ENTITY[uid]
    stat = user.get_status()
    remain = stat['no_answer_count']
    score = stat['correct_count']
    reply = f"score: {score} \n"

    if remain > 0:
        reply += f'Remaining questions: {remain} '
    else:
        reply += 'Game Completed!'

    bot.send_message(chat_id=chat_id, text=reply)


def feedback_handler(update, _):
    reply = '''Contact us '''

    bot.send_message(
        chat_id=update.message.chat_id,
        text=reply
    )

def error_handler(update, context):
    logger.error('Update "%s" caused error "%s"', update, context.error)

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CallbackQueryHandler(callback_handler, run_async=True))
    dispatcher.add_handler(CommandHandler('start', start_handler, run_async=True))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, company_name_handler))
    dispatcher.add_handler(CommandHandler('status', status_handler, run_async=True))
    dispatcher.add_handler(CommandHandler('feedback', feedback_handler, run_async=True))
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
