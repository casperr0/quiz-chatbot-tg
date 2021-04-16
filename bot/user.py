from bot.request_type import AnswerReq, RegisterReq
from dataclasses import dataclass
from typing import List, Union
from random import shuffle

from . import backend

@dataclass
class Problem:
    quiz_uuid: str
    category: str
    question: str
    options: List[str]
    hint: Union[str, None] = None

    def text(self):
        quest = f'<b>[{self.category}]</b>\n{self.question.ljust(25, " ")}\n'

        for i in range(len(self.options)):
            opchar = chr(ord('A') + i)
            quest += f'({opchar}) {self.options[i]}\n'

        return quest

@dataclass
class User:
    username: str
    userid: str
    uuid: str = ''
    company: str = ''
    title: str = ''
    prob: Union[Problem, None] = None
    finished: bool = False

    def get_company(self, update, bot, chat_id):

        #print("trying to update")
        message_text = update.message.text
        print(message_text)
        if message_text is not None:
            self.company = message_text

    def get_problem(self) -> Union[Problem, None]:
        if not self.finished:
            feed = backend.get_feed(self.uuid)
        else:
            feed = backend.get_rand_feed()

        if not feed:
            self.finished = True
            return

        self.prob = Problem(
            feed['quiz_uuid'],
            feed['domain'],
            feed['description'],
            feed['options'],
            None
        )
        return self.prob

    def check_answer(self, ans: str) -> bool:
        payload: AnswerReq = {
            'player_uuid': self.uuid,
            'quiz_uuid': self.prob.quiz_uuid,
            'answer': self.prob.options[int(ans)]
        }
        res = backend.post_answer(payload)
        return res['correct']

    def get_status(self):
        return backend.get_status(self.uuid)

    def register(self, bot, chat_id, update) -> bool:

        res = backend.search(self.userid)
        if res:
            self.uuid = res['player_uuid']
            return True
        self.get_company( update, bot, chat_id=chat_id)

        payload: RegisterReq = {
            'name': self.username,
            'platform': 'telegram',
            'platform_userid': self.userid,
            'company': self.company,
        }

        res = backend.register(payload)
        if res:
            self.uuid = res['player_uuid']
            return True

        return False
