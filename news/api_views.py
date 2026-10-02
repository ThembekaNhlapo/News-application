from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .api_permissions import ArticlePermission, IsEditorForApproval
from .models import Article, ApprovedArticleLog, Newsletter, Publisher, Role
from .serializers import (
    ArticleApproveSerializer,
    ArticleSerializer,
    NewsletterSerializer,
    PublisherSerializer,
)


class ArticleViewSet(viewsets.ModelViewSet):
    """
    GET    /api/articles/              -> all approved articles
    GET    /api/articles/subscribed/   -> approved articles from the reader's subscriptions
    GET    /api/articles/<id>/         -> a single article (subject to visibility rules)
    POST   /api/articles/              -> create (journalists only)
    PUT    /api/articles/<id>/         -> update (author-journalist or any editor)
    DELETE /api/articles/<id>/         -> delete (author-journalist or any editor)
    PATCH  /api/articles/<id>/approve/ -> approve (editors only)
    """

    serializer_class = ArticleSerializer
    permission_classes = [ArticlePermission]

    def get_queryset(self):
        user = self.request.user
        if self.action == 'list':
            return Article.objects.filter(approved=True)
        if self.action in ('retrieve', 'update', 'partial_update', 'destroy', 'approve'):
            # Let object-level permissions decide visibility of unapproved items.
            return Article.objects.all()
        return Article.objects.filter(approved=True)

    @action(detail=False, methods=['get'], url_path='subscribed')
    def subscribed(self, request):
        user = request.user
        if user.role != Role.READER:
            return Response(
                {'detail': 'Only readers have subscriptions.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        queryset = Article.objects.filter(approved=True).filter(
            Q(author__in=user.subscriptions_journalists.all())
            | Q(publisher__in=user.subscriptions_publishers.all())
        ).distinct()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['patch'],
        url_path='approve',
        permission_classes=[IsEditorForApproval],
    )
    def approve(self, request, pk=None):
        article = self.get_object()
        serializer = ArticleApproveSerializer(article, data={'approved': True}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # approved=True save() triggers the approval signal
        return Response(ArticleSerializer(article).data)


class NewsletterViewSet(viewsets.ModelViewSet):
    """
    Newsletters can be viewed by anyone authenticated, and created/edited
    by journalists and editors.
    """

    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), _JournalistOrEditor()]


class _JournalistOrEditor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in (Role.JOURNALIST, Role.EDITOR)


class PublisherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [permissions.IsAuthenticated]


class ApprovedArticleLogView(APIView):
    """
    Internal 'external syndication' endpoint referenced throughout the
    brief as /api/approved/. The approval signal POSTs here whenever an
    editor approves an article; GET returns the log for verification.
    """

    def get_permissions(self):
        # POST is called server-to-server by the approval signal itself, so
        # it isn't gated behind a user's auth token. GET (viewing the log)
        # still requires an authenticated user.
        if self.request.method == 'POST':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def post(self, request):
        article_id = request.data.get('id')
        try:
            article = Article.objects.get(pk=article_id)
        except (Article.DoesNotExist, TypeError, ValueError):
            return Response({'detail': 'Unknown article id.'}, status=status.HTTP_400_BAD_REQUEST)

        log = ApprovedArticleLog.objects.create(article=article, payload=request.data)
        return Response(
            {'id': log.id, 'article': article.id, 'logged_at': log.logged_at},
            status=status.HTTP_201_CREATED,
        )

    def get(self, request):
        logs = ApprovedArticleLog.objects.select_related('article').all()
        data = [
            {
                'id': log.id,
                'article_id': log.article_id,
                'article_title': log.article.title,
                'logged_at': log.logged_at,
            }
            for log in logs
        ]
        return Response(data)
