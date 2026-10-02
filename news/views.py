'''
Web views for News Application.
Provides user interface endpoints for viewing, creating,
updating, deleting, and
approving Articles and Newsletters, as well as managing Publisher
entities.
'''
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect

from .forms import ArticleForm, PublisherForm, NewsletterForm
from .models import Article, Newsletter, Publisher


def is_editor(user):
    '''
    Checks whether the authenticated user has an Editor role or
    superuser status.
    
    :param user: CustomUser instance to check.
    :return: True if the user is and Editor or speruser, False
    otherwise.
    '''
    return user.is_authenticated and (user.role == 'editor' or
                                      user.is_superuser)


def is_journalist(user):
    '''
    Checks whether the authenticated user has a Journalist role or
    superuser status.
    
    :param user: CustomUser instance to check.
    :return: True if the user is a Journalist or superuser, False
    otherwise.
    '''
    return user.is_authenticated and (user.role == 'journalist' or
                                      user.is_superuser)

#--- ARTICLE VIEWS ---

def article_list(request):
    '''
    Displays published articles. Aprroved articles are visible to
    all readers,
    while unapproved articles are visible only to editors or
    their author.
    Show all approved articles to the reader.
    '''
    if is_editor(request.user):
        articles = Article.objects.all().order_by('-created_at')
    elif is_journalist(request.user):
        articles = Article.objects.filter(approved=True)|Article.objects.filter(author=request.user)
        articles = articles.distinct().order_by('-created_at')
    else:
        articles = Article.objects.filter(approved=True).order_by
        ('-created_at')
        return render(request, 'news/article_list.html', 
                      {'articles': articles})

def article_detail(request, pk):
    '''
    Displays detailed content of a single article.
    '''
    article = get_object_or_404(Article, pk=pk)
    if not article.approved and not (is_editor(request.user) or
        article.author == request.user):
            raise PermissionDenied('You do not have permission to view'
            'unapproved articles.')
    return render(request, 'news/article_detail.html', 
                  {'article': article})

@login_required
def article_create(request):
    '''
    Allows journalists to create new articles.
    '''
    if not is_journalist(request.user) and not is_editor(request.user):
        raise PermissionDenied('Only journalists and editors' \
        ' can create articles.')
        
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.approved = False # Requires approval
            article.save()
            messages.success(
                request,
                'Article submitted successfully for editor approval.'
            )
            return redirect('article_detail', pk=article.pk)
        else:
            form = ArticleForm()
        return render(request, 'news/article_form.html', {'form': form, 
                                                          'title': 'Create Article'})
    
@login_required
def article_update(request, pk):
    '''
    Updates an existing article. Editors can update any article;
    journalists can only update their own.
    '''
    article = get_object_or_404(Article, pk=pk)
    if not is_editor(request.user) and article.author != request.user:
        raise PermissionDenied('You do not have permission to edit this article.')
    
    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Article updated successfully.'
            )
            return redirect('article_detail', pk=article.pk)
    else:
        form = ArticleForm(instance=article)
    return render(request, 'news/article_form.html', {'form': form, 
                                                      'title': 'Edit Article', 
                                                      'article': article})

@login_required
def article_delete(request, pk):
    '''
    Deletes an existing article. Editors can delete any article;
    journalists can only delete their own.
    '''
    article = get_object_or_404(Article, pk=pk)
    if not is_editor(request.user) and article.author != request.user:
        raise PermissionDenied('You do not have permission to delete this ' \
        'article.')
    
    if request.method == 'POST':
        article.delete()
        messages.success(
            request,
            'Article deleted successfully.'
        )
        return redirect('article_list')
    return render(request, 'news/article_confirm_delete.html', 
                  {'article': article})

@login_required
def approve_article(request, pk):
    '''
    Allows editors to approve articles, triggering notifictation
    emails and internal API logging signals.
    '''
    if not is_editor(request.user):
        raise PermissionDenied('Only editors can approve articles.')
    
    article = get_object_or_404(Article, pk=pk)
    article.approved = True
    article.save() # Triggers post_save approval signal
    messages.success(
        request,
        f"Article '{article.title}' has been approved and published.")
    return redirect('article_detail', pk=article.pk)

#--- NEWSLETTER VIEWS ---

def newsletter_list(request):
    '''
    Displays a list of all published newsletters.
    '''
    newsletters = Newsletter.objects.all().order_by('-created_at')
    return render(request, 'news/newsletter_list.html', 
                  {'newsletters': newsletters})

def newsletter_detail(request, pk):
    '''
    Displays details and articles included within a specific
    newsletter.
    '''
    newsletter = get_object_or_404(Newsletter, pk=pk)
    return render(request, 'news/newsletter_detail.html', 
                  {'newsletter': newsletter})

def newsletter_detail(request, pk):
    '''Displays details and articles included within a specific
    newsletter.
    '''
    newsletter = get_object_or_404(Newsletter, pk=pk)
    return render(request, 'news/newsletter_detail.html', 
                  {'newsletter': newsletter})

@login_required
def newsletter_create(request):
    '''
    Allows Journalists andeditors to curate create new newsletters.
    '''
    if not is_journalist(request.user) and not is_editor(request.user):
        raise PermissionDenied('Only journalistseditors can' \
        ' create newsletters.')
    
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.save()
            form.save_m2m() # Save many-to-many relationships
            messages.success(
                request,
                'Newsletter created successfully.'
            )
            return redirect('newsletter_detail', pk=newsletter.pk)
    else:
        form = NewsletterForm()
    return render(request, 'news/newsletter_form.html', {'form': form, 
                                                          'title': 'Create Newsletter'})

@login_required
def newsletter_update(request, pk):
    '''
    Updates an existing newsletter. Editors can edit any
    newsletter; journalists can only edit their own.
    '''
    newsletter = get_object_or_404(Newsletter, pk=pk)
    if not is_editor(request.user) and newsletter.author != request.user:
        raise PermissionDenied('You do not have permission to edit this '
        'newsletter.')

    if request.method == 'POST':
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Newsletter updated successfully.'
            )
            return redirect('newsletter_detail', pk=newsletter.pk)
    else:
        form = NewsletterForm(instance=newsletter)
    return render(request, 'news/newsletter_form.html', {'form': form,
                                                          'title': 'Edit Newsletter',
                                                          'newsletter': newsletter})

@login_required
def newsletter_delete(request, pk):
    '''
    Deletes an existing newsletter. Editors can delete any
    newsletter; journalists can only delete their own.
    '''
    newsletter = get_object_or_404(Newsletter, pk=pk)
    if not is_editor(request.user) and newsletter.author != request.user:
        raise PermissionDenied('You do not have permission to delete this '
        'newsletter.')

    if request.method == 'POST':
        newsletter.delete()
        messages.success(
            request,
            'Newsletter deleted successfully.'
        )
        return redirect('newsletter_list')
    return render(request, 'news/newsletter_confirm_delete.html', 
                  {'newsletter': newsletter})

#--- PUBLISHER VIEWS ---

@login_required
def publisher_manage(request, pk=None):
    '''
    Dedicated web dashboard allowing Editors to view, create,
    edit and link.
    Journalists and Editors to Publisher entities.
    '''
    if not is_editor(request.user):
        raise PermissionDenied('Only editors can manage publications and'
        'staff associations.')

    publisher = get_object_or_404(Publisher, pk=pk) if pk else None
    publishers = Publisher.objects.all().prefetch_related('editors', 
                                                          'journalists')
    
    if request.method == 'POST':
        form = PublisherForm(request.POST, instance=publisher)
        if form.is_valid():
            form.save()
            action = 'updated' if publisher else 'created'
            messages.success(
                request,
                f'Publisher {action} successfully.'
            )
            return redirect('publisher_manage')
        else:
            form = PublisherForm(instance=publisher)

    return render(request, 'news/publisher_manage.html', 
                  {'form': form, 
                   'publishers': publishers,
                   'selected_publisher': publisher,
                   })

@login_required
def publisher_delete(request, pk):
    '''
    Deletes a publisher record. Restricted to editors.
    '''
    if not is_editor(request.user):
        raise PermissionDenied('Only editors can delete publications.')

    publisher = get_object_or_404(Publisher, pk=pk)
    
    if request.method == 'POST':
        publisher.delete()
        messages.success(
            request,
            'Publisher deleted successfully.'
        )
        return redirect('publisher_manage')
    return render(request, 'news/publisher_confirm_delete.html', 
                  {'publisher': publisher})