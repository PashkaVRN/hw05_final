from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст нового поста',
            'group': 'Группа',
        }
        help_texts = {
            'group': 'Выберите группу для новой записи',
            'text': 'Добавьте текст для новой записи',
        }


class CommentForm(forms.ModelForm):
    class Meta():
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст комментария',
        }
        help_texts = {
            'text': 'Напишите ваш комментарий',
        }
