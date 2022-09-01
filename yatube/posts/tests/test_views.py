from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.forms import PostForm
from posts.models import Comment, Follow, Post, Group


User = get_user_model()

POSTS_OF_PAGE = settings.POSTS_OF_PAGE
POST_COUNT_TEST = 13


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Тестовый комментарий',
            author=cls.user
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)
        self.authorized_client_user = Client()
        self.authorized_client_user.force_login(self.user_2)

    def context_post_in_page(self, response, post=False):
        """Контекст поста на странице."""
        if post:
            post = response.context['post']
        else:
            post = response.context['page_obj'][0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.image, self.post.image)

    def test_index_forms(self):
        """Шаблон Index, ошибка context"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.context_post_in_page(response)

    def test_group_forms(self):
        """Шаблон Group, ошибка context"""
        response = self.authorized_client.get(reverse('posts:group_list',
                                                      args=(self.group.slug,)))
        self.context_post_in_page(response)
        self.assertEqual(response.context['group'], self.post.group)

    def test_profile_forms(self):
        """Шаблон Profile, ошибка context"""
        response = self.authorized_client.get(reverse
                                              ('posts:profile',
                                               args=(self.user.username,)))
        self.context_post_in_page(response)
        self.assertEqual(response.context['author'], self.post.author)

    def test_detail_forms(self):
        """Шаблон post_detail, ошибка context"""
        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      args=(self.post.id,)))
        self.context_post_in_page(response, True)

    def test_create_and_edit_forms(self):
        """Шаблон create/edit, ошибка context"""
        urls = {
            'posts:post_create': None,
            'posts:post_edit': (self.post.id,)
        }
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for name, args in urls.items():
            with self.subTest(name=name):
                response = self.authorized_client.get(reverse(name, args=args))
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)
                for value, expencted in form_fields.items():
                    with self.subTest(value=value):
                        form_field = (response.context.get('form').
                                      fields.get(value))
                        self.assertIsInstance(form_field, expencted)

    def test_correct_group(self):
        """Ошибка выбора группы"""
        group_test = Group.objects.create(
            title='Тестовая группа 2',
            slug='testslug2',
            description='Тестовое описание',
        )
        response = self.client.get(reverse('posts:group_list',
                                   args=(group_test.slug,)))
        self.assertEqual(len(response.context['page_obj']), 0)
        self.assertTrue(self.post.group)
        response = self.client.get(reverse('posts:group_list',
                                   args=(self.group.slug,)))
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_comment_view_on_post_detail(self):
        """Ошибка отображения комментария на странице поста"""
        response = self.client.get(reverse('posts:post_detail',
                                   args=(self.comment.post.id,)))
        self.assertEqual(response.context['comments'][0].text,
                         self.comment.text)

    def test_index_cache(self):
        """Ошибка кэша главной страницы"""
        Post.objects.create(
            author=self.user,
            text='Кэш',
            group=self.group,
        )
        response_1 = self.client.get(reverse('posts:index'))
        Post.objects.filter(text='Кэш').delete()
        response_2 = self.client.get(reverse('posts:index'))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.client.get(reverse('posts:index'))
        self.assertNotEqual(response_1.content, response_3.content)

    def test_follow(self):
        """Ошибка создания подписки"""
        Follow.objects.all().delete()
        self.assertEqual(Follow.objects.count(), 0)
        self.authorized_client.get(reverse('posts:profile_follow',
                                           args=(self.user_2,)))
        self.assertEqual(Follow.objects.count(), 1)
        follow = Follow.objects.first()
        self.assertEqual(follow.user, self.user)
        self.assertEqual(follow.author, self.user_2)

    def test_unfollow(self):
        """Ошибка удаления подписки"""
        Follow.objects.all().delete()
        Follow.objects.create(user=self.user, author=self.user_2)
        self.assertEqual(Follow.objects.count(), 1)
        self.authorized_client.get(reverse('posts:profile_unfollow',
                                           args=(self.user_2,)))
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_index(self):
        """Ошибка отображения новой записи в ленте"""
        Follow.objects.all().delete()
        response = self.authorized_client.get(reverse
                                              ('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
        response = self.authorized_client_user.get(reverse
                                                   ('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
        Follow.objects.create(user=self.user, author=self.user_2)
        Post.objects.create(
            author=self.user_2,
            text='Тестовый пост_user_2',
        )
        Post.objects.create(
            author=self.user,
            text='Тестовый пост_user',
        )
        response = self.authorized_client.get(reverse
                                              ('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 1)
        response = self.authorized_client_user.get(reverse
                                                   ('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание',
        )

        posts = [
            Post(
                author=cls.user,
                text=f'Тестовый пост {post_id}',
                group=cls.group
            ) for post_id in range(POST_COUNT_TEST)
        ]
        Post.objects.bulk_create(posts)

    def setUp(self):
        self.authorized_client_user = Client()
        self.authorized_client_user.force_login(self.user_2)
        Follow.objects.create(user=self.user_2, author=self.user)

    def test_page_paginator(self):
        """Ошибка Paginator"""
        urls = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.user,)),
            ('posts:follow_index', None)
        )
        pages = (
            ('?page=1', POSTS_OF_PAGE),
            ('?page=2', POST_COUNT_TEST - POSTS_OF_PAGE),
        )
        for name, args in urls:
            with self.subTest(name=name):
                for page, posts_in_page in pages:
                    with self.subTest(page=page):
                        response = (self.authorized_client_user.get
                                    (reverse(name, args=args) + page))
                        self.assertEqual(len(response.context['page_obj']),
                                         posts_in_page)
