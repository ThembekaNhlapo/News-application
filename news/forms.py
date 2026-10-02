'''
Form defintions for the News Application.

Provides Modelforms for creating and editing Articles.
Newsletters, and Publishers
with field-level validation and widget styling.
'''
from django import forms
from .models import Article, CustomUser, Newsletter, Publisher


class ArticleForm(forms.ModelForm):
    '''
    Form for creating and updating Article instances.
    '''
    class Meta:
        model = Article
        fields = ['title', 'content', 'publisher']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'publisher': forms.Select(attrs={'class': 'form-control'}),
        }


class NewsletterForm(forms.ModelForm):
    '''
    Form for creating and updating Newsletter collections.
    '''
    class Meta:
        model = Newsletter
        fields = ['title', 'description', 'articles']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'articles': forms.CheckboxSelectMultiple(),
        }

class PublisherForm(forms.ModelForm):
    '''
    Form for managing Publishers and linking associated Editors
    and Journalists.
    '''
    class Meta:
        model = Publisher
        fields = ['name', 'website','editors', 'journalists']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'editors': forms.CheckboxSelectMultiple(),
            'journalists': forms.CheckboxSelectMultiple(),
        }

        def __init__(self, *args, **kwargs):
            '''
            Filters querysets for editors and journalists to display
            appropriate user roles.
            '''
            super().__init__(*args, **kwargs)
            self.fields['editors'].queryset = CustomUser.objects.filter(role='editor')
            self.fields['journalists'].queryset= CustomUser.objects.filter(role='journalist')


