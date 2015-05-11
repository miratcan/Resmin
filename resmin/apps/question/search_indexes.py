import datetime
from haystack import indexes
from apps.question.models import QuestionMeta


class QuestionIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(model_attr='text', document=True, use_template=True)
    owner = indexes.CharField(model_attr='owner')
    answer_count = indexes.IntegerField(model_attr='answer_count')

    def get_model(self):
        return QuestionMeta

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
