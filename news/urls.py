'''
URL Routing configuration for the News Application.

Maps web view functions and REST API endpoints to defend
URL paths.
'''
from django.urls import path
from . import views

urlpatterns = [
    # Article Web Routes
    path('', views.article_list, name='article_list'),
    path('articles/new/', views.article_create, name='article_create'),
    path('articles/<int:pk>/', views.article_detail, name='article_detail'),
    path('articles/<int:pk>/edit/', views.article_update, name='article_edit'),
    path('articles/<int:pk>/delete/', views.article_delete, name='article_delete'),
    path('articles/<int:pk>/approve/', views.approve_article, name='approve_article'),  

    # Newsletter Web Routes
    path('newsletters/', views.newsletter_list, name='newsletter_list'),
    path('newsletters/new/', views.newsletter_create, name='newsletter_create'),
    path('newsletters/<int:pk>/', views.newsletter_detail, name='newsletter_detail'),
    path('newsletters/<int:pk>/edit/', views.newsletter_update, name='newsletter_edit'),
    path('newsletters/<int:pk>/delete/', views.newsletter_delete, name='newsletter_delete'),

    # Publisher Web Routes
    path('publishers/manage/', views.publisher_manage, name='publisher_manage'),
    path('publishers/manage/<int:pk>/', views.publisher_manage, name='publisher_edit'), 
    path('publishers/<int:pk>/delete/', views.publisher_delete, name='publisher_delete'),
]