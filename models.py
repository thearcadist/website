from django import forms
from django.db import models
from django.utils.timezone import now
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.models import ClusterableModel
from taggit.models import TaggedItemBase, Tag

from wagtail.snippets.models import register_snippet
from wagtail.core.models import Page, Orderable
from wagtail.core import blocks
from wagtail.core.blocks import StructBlock, CharBlock, ChoiceBlock, BlockQuoteBlock
from wagtail.core.fields import RichTextField, StreamField
from wagtail.embeds.blocks import EmbedBlock
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, StreamFieldPanel, MultiFieldPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index
from wagtail.images.blocks import ImageChooserBlock  

@register_snippet
class ArticleCategory(models.Model):
    name = models.CharField(max_length=255)

    panels = [
        FieldPanel('name'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'article categories'

@register_snippet
class ArticleAuthor(models.Model):
    name = models.CharField(max_length=255, blank=True)
    bio = models.CharField(max_length=255, blank=True)
    twitch_name = models.CharField(max_length=255, blank=True)
    email = models.CharField(max_length=255, blank=True)
    avatar = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )  

    panels = [
        FieldPanel('name'),
        FieldPanel('bio'),
        FieldPanel('email'),
        FieldPanel('twitch_name'),
        ImageChooserPanel('avatar'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'authors'        

class ArticlesIndexPage(Page):

    def get_context(self, request):
        context = super().get_context(request)
        articles = self.get_children().live().order_by('-first_published_at')

        paginator = Paginator(articles, 10)
        page = request.GET.get('page')
        try:
            articles = paginator.page(page)
        except PageNotAnInteger:
            articles = paginator.page(1)
        except EmptyPage:
            articles = paginator.page(paginator.num_pages)        

        context['articles'] = articles
        return context  

    subpage_types = [
        'articles.ArticlesPage',  # appname.ModelName
    ]
    
    parent_page_type = [
        'wagtailcore.Page'  # appname.ModelName
    ]    

class ArticlePageTag(TaggedItemBase):
    content_object = ParentalKey(
        'ArticlesPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )

class ArticlesPage(Page): 

    date = models.DateField("Post date")
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    published_at = models.DateTimeField(auto_now_add=False, blank=True, null=True, help_text=u"Needs to be converted to PST plz and ty")
    tags = ClusterTaggableManager(through=ArticlePageTag, blank=True)
    authors = ParentalManyToManyField('articles.ArticleAuthor', blank=True)
    categories = ParentalManyToManyField('articles.ArticleCategory', blank=True)
    cover_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )  
    intro = models.CharField(max_length=250)
    body = StreamField([
        ('heading', blocks.CharBlock(classname="full title")),
        ('image', ImageChooserBlock()),
        ('blockquote', BlockQuoteBlock()),
        ('paragraph', blocks.RichTextBlock()),
        ('embed', EmbedBlock()),
    ])

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('authors', widget=forms.SelectMultiple),
            FieldPanel('date'),
            FieldPanel('tags'),
            FieldPanel('categories', widget=forms.SelectMultiple),
        ], heading="Article information"),        
        ImageChooserPanel('cover_image'),
        FieldPanel('intro'),
        StreamFieldPanel('body'),
        FieldPanel('published_at'),
    ]

    def articles(self):
        articles = ArticlesPage.objects.sibling_of(self,inclusive=False).order_by('-first_published_at')
        return articles    

    def related(self):
        return ArticlesPage.objects.sibling_of(self,inclusive=False).filter(tags__in=self.tags.all()).order_by('-first_published_at').distinct()

class ArticleTagIndexPage(Page):

    def get_context(self, request):

        # Filter by tag
        tag = request.GET.get('tag')
        articlepages = ArticlesPage.objects.live().filter(tags__slug=tag).order_by('-first_published_at')

        # Update template context
        context = super().get_context(request)
        context['articlepages'] = articlepages
        return context    

class NewsIndexPage(Page):

    def get_context(self, request):
        context = super().get_context(request)
        news = self.get_children().live().order_by('-first_published_at')

        paginator = Paginator(news, 10)
        page = request.GET.get('page')
        try:
            news = paginator.page(page)
        except PageNotAnInteger:
            news = paginator.page(1)
        except EmptyPage:
            news = paginator.page(paginator.num_pages)        

        context['news'] = news
        return context  

    subpage_types = [
        'articles.ArticlesPage',  # appname.ModelName
    ]
    
    parent_page_type = [
        'wagtailcore.Page'  # appname.ModelName
    ]   