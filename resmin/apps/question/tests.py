from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from apps.question.models import Question, Answer
from apps.follow.models import UserFollow
from django.conf import settings
from os.path import join

cl = Client()

LOGIN_PASSWORD = "123456"
TEST_IMG_PATH = join(settings.PROJECT_ROOT, 'static', 'logo.png')

def _create_user(username, password):
    return User.objects.create_user(username, username, password)

def _login(username, password=LOGIN_PASSWORD):
    response = cl.post(
        '/login/',
        {'username': username,
         'password': LOGIN_PASSWORD})
    return response

def _logout():
    return cl.get('/logout/')

def _create_question(text, is_anonymouse=False, is_nsfw=False):
    response = cl.post(
        '/q/',
        {'text': text,
         'is_anonymouse': is_anonymouse,
         'is_nsfw': is_nsfw})
    return response

def _delete_question(text):
    question = Question.objects.get(text=text)
    return cl.post(question.get_absolute_url(), {'delete': 'delete'})

def _answer_question(
    qid, visible_for, img_path=TEST_IMG_PATH,
        visible_for_users=[], is_anonymouse=False, is_nsfw=False):
    question = Question.objects.get(id=qid)
    response = cl.post(
        question.get_absolute_url(),
        {'visible_for': visible_for,
         'visible_for_users': visible_for_users,
         'is_anonymouse': is_anonymouse,
         'is_nsfw': is_nsfw,
         'answer': 'answer',
         'image': open(img_path, 'r')})
    return response

def _delete_answer(answer):
    return cl.post(
        answer.get_absolute_url(),
        {'delete': 'delete'})

class QuestionAnswerTest(TestCase):
    def setUp(self):
        self.user1 = _create_user("user1", "123456")
        self.user2 = _create_user("user2", "123456")

    def testSubmitQuestion(self):
        # Login with user1
        _login("user1")

        # Create a question with test1
        response = _create_question("test1")

        # If successfully created it must be redirected to /q/B/
        self.assertEqual(
            response._headers['location'][1],
            'http://testserver/q/B/')

    def testDeleteQuestion(self):
        # Login with user1
        _login("user1")

        # Create a question with test1
        _create_question("test1")

        # Delete question
        _delete_question("test1")

    def testAnswerQuestion(self):
        # Login with user1
        _login("user1")

        # Create a question with test1
        _create_question("test1")

        # Get question with text test1
        question = Question.objects.get(text="test1")

        # Get response from posting answer
        response = _answer_question(question.id, visible_for=0)

        # If successfully created it must be redirected to /a/B/
        self.assertEqual(
            response._headers['location'][1],
            'http://testserver/a/B/')

        # Get answer
        answer = Answer.objects.all()[0]

        # Delete answer
        response = _delete_answer(answer)

        # If successfully deleted, must be redirected to /
        self.assertEqual(
            response._headers['location'][1],
            'http://testserver/')

        # There must be 1 answer marked as deleted
        self.assertEqual(Answer.objects.filter(status=1).count(), 1)

    def testAnswerVisibilityPublicWhenListing(self):
        # Login with user1
        _login("user1")

        # Create a question with test1
        _create_question("test1")

        # Get question with text test1
        question = Question.objects.get(text="test1")

        # Get response from posting answer
        response = _answer_question(question.id, visible_for=0)

        # If successfully created it must be redirected to /a/B/
        self.assertEqual(
            response._headers['location'][1],
            'http://testserver/a/B/')

        # Get homepage
        response = cl.get('/')

        # There must be 1 answer at homepage
        self.assertEqual(len(response.context['answers']), 1)

        _logout()

        # Get homepage
        response = cl.get('/')

        # There must be 1 answer at homepage
        self.assertEqual(len(response.context['answers']), 1)

    def testAnswerVisibilityForFollowingsWhenListing(self):

        # Login with user1
        _login("user1")

        # Create a question with test1
        _create_question("test1")

        # Get question with text test1
        question = Question.objects.get(text="test1")

        # Post an answer to that question
        _answer_question(question.id, visible_for=1)

        # Get homepage
        response = cl.get('/')

        # There must be no answers at homepage
        self.assertEqual(len(response.context['answers']), 0)

        # Logout from user1
        _logout()

        _login("user2", "123456")

        # Follow user2 with user1
        UserFollow.objects.create(
            follower=self.user2, target=self.user1, status=1)

        # Get answers from followings
        response = cl.get('/f/')

        # There must be 1 answer at homepage
        self.assertEqual(len(response.context['answers']), 1)
 
    
    def testAnswerVisibilityForDirectWhenListing(self):
        from apps.follow.models import UserFollow

        # Login with user1
        _login("user1")

        # Create a question with test1
        _create_question("test1")

        # Get question with text test1
        question = Question.objects.get(text="test1")

        # Follow user2 with user1
        UserFollow.objects.create(
            follower=self.user2, target=self.user1, status=1)

        # Post an answer to that question
        response = _answer_question(
            question.id, visible_for=2, visible_for_users=[self.user2.id])

        # If successfully created it must be redirected to /a/B/
        self.assertEqual(
            response._headers['location'][1],
            'http://testserver/a/B/')

        # Get answer at database
        answer = Answer.objects.all()[0]

        # Story should have 1 visible_for_user
        self.assertEqual(len(answer.visible_for_users.all()), 1)

        # There must be no answers at homepage
        response = cl.get('/')
        self.assertEqual(len(response.context['answers']), 0)

        # Logout from user1
        _logout()

        # Login with user2 and make user2 following user1
        _login("user2", "123456")

        # There must be no answers at homepage
        response = cl.get('/')
        self.assertEqual(len(response.context['answers']), 0)

        # There must be no answers at from followings page
        response = cl.get('/f/')
        self.assertEqual(len(response.context['answers']), 0)

        # There must be 1 answer at direct answers page
        response = cl.get('/d/')
        self.assertEqual(len(response.context['answers']), 1)

    def testAnswerVisibilityAtQuestionPage(self):
        # Login with user1
        _login("user1")

        # Create a question called test1
        _create_question("test1")

        # Create a public answer for question
        _answer_question(1, 0)

        # Create an answer which is for followers
        _answer_question(1, 1)

        # Logout
        _logout()

        # Shortcut for posted questions url
        qurl = Question.objects.all()[0].get_absolute_url()

        # Get question root
        response = cl.get(qurl)

        # Response should have 1 answers
        self.assertEqual(len(response.context['answers']), 1)

        # Get question with from followings
        response = cl.get(qurl + 'f/')

        # Response should have 0 answers
        self.assertEqual(len(response.context['answers']), 0)

        # Get question with from direct
        response = cl.get(qurl + 'd/')

        # Response should have 0 answers
        self.assertEqual('answers' in response.context, False)

        # Follow user2 with user1
        UserFollow.objects.create(
            follower=self.user2, target=self.user1, status=1)

        # Login with user 2
        _login("user2")

        # Get question root
        response = cl.get(qurl)

        # Response should have 1 answers
        self.assertEqual(len(response.context['answers']), 1)

        # Get question with from followings
        response = cl.get(qurl + 'f/')

        # Response should have 1 answers
        self.assertEqual(len(response.context['answers']), 1)

    def testAnswerVisibilityAtAnswerDetailPage(self):
        pass