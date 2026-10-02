"""
Models for the News Application capstone project.

Roles
-----
Every user has exactly one role: reader, editor, or journalist. The role
drives both the Django group/permission a user is placed in (see
news/signals.py) and which custom fields on CustomUser are meaningful for
that user (reader-only subscription fields are cleared for
editors/journalists).

Design notes
------------
- Publisher can have many editors and many journalists (both M2M).
- Article belongs to exactly one author (a journalist) and, optionally, to
  a Publisher. An article with no publisher is an independent article by
  that journalist; an article with a publisher is "publisher content".
- Newsletter is a curated collection of articles (M2M) written by a
  journalist or editor.
- Reader subscriptions can target a Publisher and/or individual
  journalists (both M2M), matching the brief's "subscription can pertain
  to either a publication or an individual journalist".
"""

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class Role(models.TextChoices):
    READER = 'reader', 'Reader'
    EDITOR = 'editor', 'Editor'
    JOURNALIST = 'journalist', 'Journalist'


class CustomUser(AbstractUser):
    """Custom user model with a role and role-specific relationships."""

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.READER,
        help_text='Determines which group/permissions this user receives.',
    )

    # --- Reader-only fields -------------------------------------------------
    subscriptions_publishers = models.ManyToManyField(
        'Publisher',
        blank=True,
        related_name='subscribers',
        help_text='Publishers this reader is subscribed to (reader role only).',
    )
    subscriptions_journalists = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='subscribed_by',
        help_text='Independent journalists this reader is subscribed to (reader role only).',
    )

    # Journalist "articles published independently" and "newsletters
    # published independently" are exposed as reverse relations from
    # Article.author (related_name='articles') and Newsletter.author
    # (related_name='newsletters') below - no extra field is needed here.

    def is_reader(self):
        return self.role == Role.READER

    def is_editor(self):
        return self.role == Role.EDITOR

    def is_journalist(self):
        return self.role == Role.JOURNALIST

    def clear_role_inappropriate_fields(self):
        """
        Enforce the brief's rule: a Journalist's reader-only subscription
        fields must be 'None' (empty), and vice versa. Only meaningful once
        the user has a primary key, since these are M2M fields.
        """
        if not self.pk:
            return
        if self.role != Role.READER:
            self.subscriptions_publishers.clear()
            self.subscriptions_journalists.clear()

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'


class Publisher(models.Model):
    """A curated publication that can have many editors and journalists."""

    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='editor_publishers'
    )
    journalists = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='journalist_publishers'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Article(models.Model):
    """A news article, written by a journalist, optionally under a Publisher."""

    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='articles',
        limit_choices_to={'role': Role.JOURNALIST},
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        related_name='articles',
        null=True,
        blank=True,
        help_text='Leave blank for an independent article by the journalist.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved = models.BooleanField(
        default=False, help_text='Set to True once an editor approves the article.'
    )

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.author_id and getattr(self.author, 'role', None) != Role.JOURNALIST:
            raise ValidationError('Only users with the Journalist role may author articles.')

    def __str__(self):
        return self.title


class ApprovedArticleLog(models.Model):
    """
    Records each POST received by /api/approved/. Acts as the "external"
    log that simulates syndicating an approved article outside the project,
    while keeping the whole integration inside it.
    """

    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name='approval_logs'
    )
    logged_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-logged_at']

    def __str__(self):
        return f'Approved log for "{self.article.title}" at {self.logged_at:%Y-%m-%d %H:%M}'


class Newsletter(models.Model):
    """A curated collection of articles, created by a journalist or editor."""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='newsletters',
    )
    articles = models.ManyToManyField(Article, blank=True, related_name='newsletters')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
