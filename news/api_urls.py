from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .api_views import ApprovedArticleLogView, ArticleViewSet, NewsletterViewSet, PublisherViewSet

router = DefaultRouter()
router.register('articles', ArticleViewSet, basename='api-article')
router.register('newsletters', NewsletterViewSet, basename='api-newsletter')
router.register('publishers', PublisherViewSet, basename='api-publisher')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', obtain_auth_token, name='api_token_auth'),
    path('approved/', ApprovedArticleLogView.as_view(), name='api_approved_log'),
]
