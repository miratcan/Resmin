# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class QuestionConfig(AppConfig):
    name = 'question'

    def ready():
        Question = self.get_model('Question')

    # registering signals with the model's string label
    pre_save.connect(receiver, sender='app_label.MyModel')
