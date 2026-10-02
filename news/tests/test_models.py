from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from news.models import Article, Publisher, Role

User = get_user_model()


class UserRoleGroupTests(TestCase):
    def test_user_is_added_to_group_matching_role(self):
        user = User.objects.create_user(username='jo', password='pass12345', role=Role.JOURNALIST)
        self.assertTrue(user.groups.filter(name='Journalist').exists())

    def test_switching_role_moves_user_to_new_group(self):
        user = User.objects.create_user(username='sam', password='pass12345', role=Role.READER)
        self.assertTrue(user.groups.filter(name='Reader').exists())

        user.role = Role.EDITOR
        user.save()
        user.refresh_from_db()

        self.assertFalse(user.groups.filter(name='Reader').exists())
        self.assertTrue(user.groups.filter(name='Editor').exists())

    def test_non_reader_subscription_fields_are_cleared(self):
        reader = User.objects.create_user(username='reader1', password='pass12345', role=Role.READER)
        journalist = User.objects.create_user(username='jstar', password='pass12345', role=Role.JOURNALIST)
        publisher = Publisher.objects.create(name='Daily Times')

        reader.subscriptions_publishers.add(publisher)
        reader.subscriptions_journalists.add(journalist)
        self.assertEqual(reader.subscriptions_publishers.count(), 1)

        reader.role = Role.JOURNALIST
        reader.save()

        self.assertEqual(reader.subscriptions_publishers.count(), 0)
        self.assertEqual(reader.subscriptions_journalists.count(), 0)


class ArticleApprovalSignalTests(TestCase):
    def setUp(self):
        self.journalist = User.objects.create_user(
            username='writer', password='pass12345', role=Role.JOURNALIST, email='writer@example.com'
        )
        self.reader = User.objects.create_user(
            username='reader', password='pass12345', role=Role.READER, email='reader@example.com'
        )
        self.reader.subscriptions_journalists.add(self.journalist)

    @patch('news.signals.post_approved_article_to_api')
    @patch('news.signals.email_subscribers_about_article')
    def test_approval_triggers_email_and_api_post_exactly_once(self, mock_email, mock_api_post):
        article = Article.objects.create(
            title='Breaking news', content='Something happened.', author=self.journalist
        )
        mock_email.assert_not_called()
        mock_api_post.assert_not_called()

        article.approved = True
        article.save()

        mock_email.assert_called_once_with(article)
        mock_api_post.assert_called_once_with(article)

    @patch('news.signals.post_approved_article_to_api')
    @patch('news.signals.email_subscribers_about_article')
    def test_resaving_an_already_approved_article_does_not_refire(self, mock_email, mock_api_post):
        article = Article.objects.create(
            title='Old news', content='Already covered.', author=self.journalist, approved=True
        )
        mock_email.reset_mock()
        mock_api_post.reset_mock()

        article.title = 'Old news (updated headline)'
        article.save()

        mock_email.assert_not_called()
        mock_api_post.assert_not_called()
