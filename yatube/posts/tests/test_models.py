from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост больше 15 символов',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у модели Group, Post корректно работает __str__."""
        field_str = {
            PostModelTest.group: PostModelTest.group.title,
            PostModelTest.post: PostModelTest.post.text[:15],
        }
        for field, expected_value in field_str.items():
            with self.subTest(field=field):
                self.assertEqual(expected_value, str(field))

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        task = PostModelTest.post
        field_verboses = {
            'text': 'Пост',
            'pub_date': 'Дата',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Картинка',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    task._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        task = PostModelTest.post
        field_help_texts = {
            'text': 'Чем хотите поделиться?',
            'group': 'В какой группе разместим запись?',
            'image': 'Можете добавить изображение к посту',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    task._meta.get_field(field).help_text, expected_value)
