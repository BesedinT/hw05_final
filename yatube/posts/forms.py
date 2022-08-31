from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Пост',
            'group': 'Группа',
        }
        help_texts = {
            'text': 'Чем хотите поделиться?',
            'group': 'В какой группе разместим запись?',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Комментарий',
        }
        help_texts = {
            'text': 'Напишите ваш комментарий',
        }
