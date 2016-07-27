# -*- coding: utf-8 -*-

import sys

sys.path.append('../')

from coscupbot import db, model
import os
import pytest
import redis

should_skip = 'REDIS' not in os.environ

if not should_skip:
    REDIS_URL = os.environ['REDIS']


def get_dao():
    return db.Dao(REDIS_URL)


def gen_test_commands(num, language='zh_TW'):
    commands = []
    for i in range(0, num):
        response = ['resp%s-1' % i, 'resp%s-2' % i]
        cmd = model.Command(language, 'CMD%s' % i, response)
        commands.append(cmd)
    return commands


@pytest.mark.skipif(should_skip, reason="Redis connection url not configured")
class TestDb:

    def teardown_method(self, test_method):
        r = redis.from_url(REDIS_URL)
        r.flushall()

    def test_ping(self):
        get_dao().test_connection()

    def test_add_command_one_lang(self):
        get_dao().add_commands(gen_test_commands(10, 'zh_TW'))
        r = redis.from_url(REDIS_URL)
        assert 10 == len(r.keys('COMMAND::zh_TW::*'))

    def test_add_command_two_lang(self):
        get_dao().add_commands(gen_test_commands(10, 'zh_TW'))
        get_dao().add_commands(gen_test_commands(20, 'en'))
        r = redis.from_url(REDIS_URL)
        assert 10 == len(r.keys('COMMAND::zh_TW::*'))
        assert 20 == len(r.keys('COMMAND::en::*'))
        assert 30 == len(r.keys('COMMAND::*'))

    def test_delete_command(self):
        self.test_add_command_two_lang()
        get_dao().clear_all_command()
        r = redis.from_url(REDIS_URL)
        assert 0 == len(r.keys('COMMAND::*'))

    def test_get_command_response(self):
        cmd1 = model.Command('zh_TW', 'help', ['help', 'hi'])
        cmd2 = model.Command('zh_TW', 'hello', ['hello', 'world'])
        get_dao().add_commands([cmd1, cmd2])
        result = get_dao().get_command_responses('help', 'zh_TW')
        assert 'help' and 'hi' not in result

    def test_get_command_response_no_data(self):
        try:
            get_dao().get_command_responses('help', 'zh_TW')
        except db.CommandError as ce:
            assert True
        except Exception as ex:
            assert False

    def test_update_command(self):
        r = redis.from_url(REDIS_URL)
        get_dao().add_commands(gen_test_commands(10, 'zh_TW'))
        assert 10 == len(r.keys('COMMAND::zh_TW::*'))
        get_dao().update_commands(gen_test_commands(20, 'en'))
        assert 0 == len(r.keys('COMMAND::zh_TW::*'))
        assert 20 == len(r.keys('COMMAND::en::*'))
        assert 20 == len(r.keys('COMMAND::*'))
