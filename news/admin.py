from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ApprovedArticleLog, Article, CustomUser, Newsletter, Publisher


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    '''
    Custom User admin interface allowing managemnet of custom
    fields such as
    role subscriptions, and associated group permissions.
    '''
    model = CustomUser
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')

    fieldsets = UserAdmin.fieldsets + (
        ('Custom Role & Subscriptions', {
            'fields': ('role', 'subscriptions_publishers',
                       'subscriptions_journalists')
        })
    )

@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    '''
    Admin interface for Publisher instances. Uses
    filter_horizontal for clean
    ManyToMany selection of associated editors and journalists.
    '''
    list_display = ('name', 'website')
    search_fields = ('name',)
    filter_horizontal = ('editors', 'journalists')

    fieldsets = (
        (None, {
            'fields': ('name', 'website')
        }),
        ('Associated Personnel', {
            'fields': ('editors', 'journalists')
        }),
    )

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    '''
    Admin interface for managing Article submissions and approval
    status
    '''
    list_display = ('title', 'author', 'publisher', 'approved', 
                    'created_at')
    list_filter = ('approved','created_at', 'publisher')
    search_fields = ('title', 'content', 'author__username') 

@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    '''
    Admin interface for Newsletter currated collections.
    '''
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'description', 'author__username')
    filter_horizontal = ('articles',)


@admin.register(ApprovedArticleLog)
class ApprovedArticleLogAdmin(admin.ModelAdmin):
    '''
    Read-only admin interface for monitoring internal syndication
    logs.
    '''
    list_display = ('article', 'approved_at')
    readonly_fields = ('article', 'approved_at')
