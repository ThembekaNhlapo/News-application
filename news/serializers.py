from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Article, Newsletter, Publisher

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role',
            'subscriptions_publishers', 'subscriptions_journalists',
        ]
        read_only_fields = ['id']


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ['id', 'name', 'description', 'editors', 'journalists']


class ArticleSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source='author.username')
    publisher_name = serializers.ReadOnlyField(source='publisher.name')

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'content', 'author', 'author_username',
            'publisher', 'publisher_name', 'created_at', 'updated_at', 'approved',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'approved', 'author']

    def create(self, validated_data):
        # The author is always the requesting journalist, never client-supplied.
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class ArticleApproveSerializer(serializers.ModelSerializer):
    """Used only by the editor-only approval action."""

    class Meta:
        model = Article
        fields = ['id', 'approved']
        read_only_fields = ['id']


class NewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Newsletter
        fields = ['id', 'title', 'description', 'created_at', 'author', 'articles']
        read_only_fields = ['id', 'created_at', 'author']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)
