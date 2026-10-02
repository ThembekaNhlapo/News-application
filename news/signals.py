"""
Signal handlers.

1. CustomUser post_save:
   - Adds the user to the Django Group matching their role (creating the
     groups/permissions the first time they're needed).
   - Clears reader-only subscription fields for non-reader users.

2. Article approval workflow (Option 1 - Django Signals, per the brief):
   - A pre_save handler records whether the article was already approved.
   - A post_save handler fires only on the transition to approved=True and:
       a) emails the approved article to subscribers of the journalist
          and/or publisher, and
       b) POSTs the approved article to our own /api/approved/ endpoint
          using the `requests` library, simulating external syndication.
"""

import logging

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver

from .models import Article, CustomUser, Role
from .permissions_utils import get_or_create_role_groups

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# User <-> Group / role field enforcement
# ---------------------------------------------------------------------------
@receiver(post_save, sender=CustomUser)
def assign_user_group_and_enforce_fields(sender, instance, created, **kwargs):
    groups = get_or_create_role_groups()
    target_group = groups.get(instance.role)

    # Make sure the user belongs only to the group matching their role.
    instance.groups.remove(*[g for g in groups.values() if g != target_group])
    if target_group:
        instance.groups.add(target_group)

    # Enforce: Journalist/Editor => reader subscription fields are cleared.
    instance.clear_role_inappropriate_fields()


# ---------------------------------------------------------------------------
# Article approval -> email subscribers + log to internal REST API
# ---------------------------------------------------------------------------
@receiver(pre_save, sender=Article)
def stash_previous_approval_state(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._was_approved = Article.objects.get(pk=instance.pk).approved
        except Article.DoesNotExist:
            instance._was_approved = False
    else:
        instance._was_approved = False


@receiver(post_save, sender=Article)
def notify_on_article_approval(sender, instance, created, **kwargs):
    was_approved = getattr(instance, '_was_approved', False)
    if instance.approved and not was_approved:
        handle_article_approved(instance)


def handle_article_approved(article):
    """Email subscribers and log the approval to our internal REST API."""
    email_subscribers_about_article(article)
    post_approved_article_to_api(article)


def email_subscribers_about_article(article):
    subscriber_emails = set()

    # Subscribers of the journalist who wrote it.
    subscriber_emails.update(
        CustomUser.objects.filter(
            role=Role.READER, subscriptions_journalists=article.author
        ).values_list('email', flat=True)
    )

    # Subscribers of the publisher, if any.
    if article.publisher_id:
        subscriber_emails.update(
            CustomUser.objects.filter(
                role=Role.READER, subscriptions_publishers=article.publisher
            ).values_list('email', flat=True)
        )

    subscriber_emails.discard('')
    if not subscriber_emails:
        return

    try:
        send_mail(
            subject=f'New article published: {article.title}',
            message=(
                f'{article.title}\n\n{article.content}\n\n'
                f'-- {getattr(article.author, "get_full_name", lambda: "")() or article.author.username}'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=list(subscriber_emails),
            fail_silently=True,
        )
    except Exception:  # pragma: no cover - defensive; never break approval flow
        logger.exception('Failed to email subscribers for article %s', article.pk)


def post_approved_article_to_api(article):
    url = f'{settings.INTERNAL_API_BASE_URL}/api/approved/'
    payload = {
        'id': article.pk,
        'title': article.title,
        'author': article.author.username,
        'publisher': article.publisher.name if article.publisher_id else None,
        'created_at': article.created_at.isoformat() if article.created_at else None,
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except requests.RequestException:
        # In a dev/test environment the server may not be reachable from
        # inside a signal handler; log it rather than breaking approval.
        logger.warning('Could not reach internal API at %s to log article %s', url, article.pk)
