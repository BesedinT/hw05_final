from http import HTTPStatus

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
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

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)
        self.authorized_client_user = Client()
        self.authorized_client_user.force_login(self.user_2)
        self.url_names = (
            ('posts:index', None, '/'),
            ('posts:group_list', (self.post.group.slug,),
             f'/group/{self.post.group.slug}/'),
            ('posts:profile', (self.post.author,),
             f'/profile/{self.post.author}/'),
            ('posts:post_detail', (self.post.id,), f'/posts/{self.post.id}/'),
            ('posts:post_create', None, '/create/'),
            ('posts:post_edit', (self.post.id,),
             f'/posts/{self.post.id}/edit/'),
            ('posts:add_comment', (self.post.id,),
             f'/posts/{self.post.id}/comment/'),
            ('posts:follow_index', None, '/follow/'),
            ('posts:profile_follow', (self.post.author,),
             f'/profile/{self.post.author}/follow/'),
            ('posts:profile_unfollow', (self.post.author,),
             f'/profile/{self.post.author}/unfollow/'),
        )

    def test_namespace_name_vs_urls(self):
        """Ошибка соответствия namespaсe и name прямым URL ссылкам"""
        for name, args, url in self.url_names:
            with self.subTest(name=name):
                self.assertEqual(reverse(name, args=args), url)

    def test_author_page(self):
        """Ошибка доступности страниц для автора"""
        for name, args, _ in self.url_names:
            with self.subTest(name=name):
                response = self.authorized_client.get(reverse(name, args=args))
                if name in [
                    'posts:add_comment',
                ]:
                    self.assertRedirects(response,
                                         f'/posts/{self.post.id}/')
                elif name in [
                    'posts:profile_follow',
                ]:
                    self.assertRedirects(response,
                                         f'/profile/{self.post.author}/')
                elif name in [
                    'posts:profile_unfollow'
                ]:
                    self.assertEqual(response.status_code,
                                     HTTPStatus.NOT_FOUND)
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_user_page(self):
        """Ошибка доступности страниц для авторизрванного пользователя"""
        for name, args, _ in self.url_names:
            with self.subTest(name=name):
                response = self.authorized_client_user.get(reverse(name,
                                                                   args=args))
                if name == 'posts:post_edit':
                    self.assertRedirects(response, reverse('posts:post_detail',
                                                           args=args))
                elif name in [
                    'posts:add_comment',
                ]:
                    self.assertRedirects(response,
                                         f'/posts/{self.post.id}/')
                elif name in [
                    'posts:profile_follow',
                    'posts:profile_unfollow'
                ]:
                    self.assertRedirects(response,
                                         f'/profile/{self.post.author}/')
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_page(self):
        """Ошибка доступности страниц для гостя"""
        for name, args, _ in self.url_names:
            with self.subTest(name=name):
                login = reverse('users:login')
                reverse_name = reverse(name, args=args)
                response = self.client.get(reverse_name)
                if name in [
                    'posts:post_edit',
                    'posts:post_create',
                    'posts:add_comment',
                    'posts:follow_index',
                    'posts:profile_follow',
                    'posts:profile_unfollow'
                ]:
                    self.assertRedirects(response,
                                         f'{login}?next={reverse_name}')
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting(self):
        """Несуществующая страница выдаёт код 404"""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """Ошибка использования соответсвующего шаблона"""
        templates_url_names = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:group_list', (self.post.group.slug,),
             'posts/group_list.html'),
            ('posts:profile', (self.post.author,), 'posts/profile.html'),
            ('posts:post_detail', (self.post.id,), 'posts/post_detail.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
            ('posts:post_edit', (self.post.id,), 'posts/create_post.html'),
            ('posts:follow_index', None, 'posts/follow.html'),
        )
        for name, args, template in templates_url_names:
            with self.subTest(name=name):
                response = self.authorized_client.get(reverse(name, args=args))
                self.assertTemplateUsed(response, template)
