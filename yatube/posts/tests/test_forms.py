import shutil
import tempfile
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Post, Group


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='testslug1',
            description='Тестовое описание',
        )

        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='testslug2',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group_1,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)

    def test_create_post(self):
        """Ошибка формы create post"""
        Post.objects.all().delete()
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group_1.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data, follow=True)
        self.assertRedirects(response, reverse('posts:profile',
                                               args=(self.user.username,)))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.image, 'posts/small.gif')

    def test_post_edit(self):
        """Ошибка формы post edit"""
        posts_count = Post.objects.count()
        self.assertEqual(posts_count, 1)
        small_edit_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small_edit.gif',
            content=small_edit_gif,
            content_type='image_edit/gif'
        )
        form_data = {
            'text': 'Тестовый пост +',
            'group': self.group_2.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(reverse('posts:post_edit',
                                                       kwargs={'post_id':
                                                               self.post.id}),
                                               data=form_data, follow=True)
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id':
                                                       self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.image, 'posts/small_edit.gif')
        response = self.client.get(reverse('posts:group_list',
                                   args=(self.group_1.slug,)))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_create_post_no_login(self):
        """Ошибка запрета создания постов без авторизации"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group_1.id
        }
        response = self.client.post(reverse('posts:post_create'),
                                    data=form_data, follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), posts_count)

    def test_create_comment_no_login(self):
        """Ошибка запрета создания комментариев без авторизации"""
        Comment.objects.all().delete()
        posts_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.client.post(reverse('posts:add_comment',
                                            args=(self.post.id,)),
                                    data=form_data,
                                    follow=True)
        self.assertRedirects(response, (f'/auth/login/?next=/posts/'
                                        f'{self.post.id}/comment/'))
        self.assertEqual(Comment.objects.count(), posts_count)
