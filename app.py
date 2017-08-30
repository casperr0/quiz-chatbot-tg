# app.py
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from random import randrange
import requests
from reply import Reply, Judge

url = ""
entry = {}
option_mapping = {}


def Reply_markup():
    keyboard = [[InlineKeyboardButton("A", callback_data='0'),
                 InlineKeyboardButton("B", callback_data='1')],
                [InlineKeyboardButton("C", callback_data='2'),
                 InlineKeyboardButton("D", callback_data='3')]]
    return InlineKeyboardMarkup(keyboard)


def Randomize_option(username):
    global option_mapping
    om = option_mapping[username] = []
    op = entry[username]['option']
    while(len(om) != len(op)):
        num = randrange(len(op))
        if num not in om: om.append(num)


def Generate_problem(username):
    global entry
    entry[username] = requests.get(url+'/question?user='+username).json()
    Randomize_option(username)
    pb = entry[username]['question']
    op = entry[username]['option']
    om = option_mapping[username]
    for i in range(len(op)):
        pb = pb + '\n(' + chr(ord('A')+i) + ') ' + op[om[i]]

    return pb


def Start(bot, update):
    username = update.message.from_user.username

    requests.post(url+'/user', json={"user": username})
    bot.send_message(chat_id=update.message.chat_id, text=Reply('welcome'))
    bot.send_message(chat_id=update.message.chat_id, text=Generate_problem(username), reply_markup=Reply_markup())


def Receive_and_reply(bot, update):
    rcv = update.callback_query
    username = rcv.message.chat.username
    id = entry[username]['id']
    op = entry[username]['option']
    om = option_mapping[username]

    result = requests.post(url+'/answer', json={'user': username, 'id': id, 'answer': om[int(rcv.data)]}).json()
    bot.send_message(chat_id=rcv.message.chat.id, text=op[om[int(rcv.data)]])
    bot.send_message(chat_id=rcv.message.chat.id, text=Judge(result))
    bot.send_message(chat_id=rcv.message.chat.id, text=Generate_problem(username), reply_markup=Reply_markup())


def Status(bot, update):
    username = update.message.from_user.username
    stat = requests.get(url+'/user?user='+username).json()
    reply = 'Score: ' + str(stat['point']) + '\nRank: ' + str(stat['order']) + '\nRemainders: ' + str(stat['questionStatus'].count(0))

    bot.send_message(chat_id=update.message.chat_id, text=reply)


def Statistic(bot, update):
    stat = requests.get(url+'/user-database.json').json()
    reply = 'Total players: ' + str(len(stat))
    for name in stat:
        reply = reply + '\n' + name + ', score: ' + str(stat[name]['point'])

    bot.send_message(chat_id=update.message.chat_id, text=reply)


def Feedback(bot, update):
    reply = 'Submit a new issue:\nhttps://github.com/ccns/quiz-chatbot-tg/issues\nor contact us:\nhttps://www.facebook.com/ncku.ccns'
    bot.send_message(chat_id=update.message.chat_id, text=reply)


def main():
    global url
    url = '<url>'
    updater = Updater(token='<token>')
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CallbackQueryHandler(Receive_and_reply))
    dispatcher.add_handler(CommandHandler('start', Start))
    dispatcher.add_handler(CommandHandler('status', Status))
    dispatcher.add_handler(CommandHandler('statistic', Statistic))
    dispatcher.add_handler(CommandHandler('feedback', Feedback))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
