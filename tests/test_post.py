from io import BytesIO

import pytest
from django import forms
from django.contrib.auth import get_user_model
from django.core.files.base import File
from django.db.models.query import QuerySet
from PIL import Image
from django.core.cache import cache

from posts.models import Post
from posts.forms import PostForm
from django.core.paginator import Page

from tests.utils import get_field_from_context


class TestPostView:

    @pytest.mark.django_db(transaction=True)
    def test_index_post_with_image(self, client, post):
        url_index = '/'
        cache.clear()
        response = client.get(url_index)

        page_context = get_field_from_context(response.context, Page)
        assert page_context is not None, (
            'Проверьте, что передали статьи автора в контекст главной страницы `/` типа `Page`'
        )
        assert len(page_context.object_list) == 1, (
            'Проверьте, что в контекст главной страницы переданы правильные статьи автора'
        )
        posts_list = page_context.object_list
        for post in posts_list:
            assert hasattr(post, 'image'), (
                'Убедитесь, что статья, передаваемая в контекст главной страницы `/`, имеет поле `image`'
            )
            assert getattr(post, 'image') is not None, (
                'Убедитесь, что статья, передаваемая в контекст главной страницы `/`, имеет поле `image`, '
                'и туда передается изображение'
            )

    @pytest.mark.django_db(transaction=True)
    def test_index_post_caching(self, client, post, post_with_group):
        url_index = '/'
        cache.clear()
        response = client.get(url_index)

        page_context = get_field_from_context(response.context, Page)
        assert page_context is not None, (
            'Проверьте, что передали статьи автора в контекст главной страницы `/` типа `Page`'
        )
        posts_cnt = Post.objects.count()
        post.delete()
        assert len(page_context.object_list) == posts_cnt is not None, (
            'Проверьте, что настроили кэширование для главной страницы `/` '
            'и посты на ней даже при удалении в базе, остаются до очистки кэша'
        )
        cache.clear()
        posts_cnt = Post.objects.count()
        response = client.get(url_index)
        page_context = get_field_from_context(response.context, Page)
        assert len(page_context.object_list) == posts_cnt is not None, (
            'Проверьте, что настроили кэширование для главной страницы `/` '
            'и при принудительной очистке кэша, удаленный в базе пост, '
            'пропадает из кэша'
        )

    @pytest.mark.django_db(transaction=True)
    def test_post_view_get(self, client, post_with_group):
        try:
            response = client.get(f'/posts/{post_with_group.id}')
        except Exception as e:
            assert False, f'''Страница `/posts/<post_id>/` работает неправильно. Ошибка: `{e}`'''
        if response.status_code in (301, 302):
            response = client.get(f'/posts/{post_with_group.id}/')
        assert response.status_code != 404, (
            'Страница `/posts/<post_id>/` не найдена, проверьте этот адрес в *urls.py*'
        )

        post_context = get_field_from_context(response.context, Post)
        assert post_context is not None, (
            'Проверьте, что передали статью в контекст страницы `/posts/<post_id>/` типа `Post`'
        )

        try:
            from posts.forms import CommentForm
        except ImportError:
            assert False, 'Не найдена форма CommentForm в posts.form'

        comment_form_context = get_field_from_context(response.context, CommentForm)
        assert comment_form_context is not None, (
            'Проверьте, что передали форму комментария в контекст страницы `/posts/<post_id>/` типа `CommentForm`'
        )
        assert len(comment_form_context.fields) == 1, (
            'Проверьте, что форма комментария в контексте страницы `/posts/<post_id>/` состоит из одного поля'
        )
        assert 'text' in comment_form_context.fields, (
            'Проверьте, что форма комментария в контексте страницы `/posts/<post_id>/` содержится поле `text`'
        )
        assert type(comment_form_context.fields['text']) == forms.fields.CharField, (
            'Проверьте, что форма комментария в контексте страницы `/posts/<post_id>/` '
            'содержится поле `text` типа `CharField`'
        )
        assert hasattr(post_context, 'image'), (
            'Убедитесь, что статья, передаваемая в контекст страницы `/posts/<post_id>/`, имеет поле `image`'
        )
        assert getattr(post_context, 'image') is not None, (
            'Убедитесь, что статья, передаваемая в контекст страницы `/posts/<post_id>/`, имеет поле `image`, '
            'и туда передается изображение'
        )


class TestPostEditView:

    @pytest.mark.django_db(transaction=True)
    def test_post_edit_view_get(self, client, post_with_group):
        try:
            response = client.get(f'/posts/{post_with_group.id}/edit')
        except Exception as e:
            assert False, f'''Страница `/posts/<post_id>/edit/` работает неправильно. Ошибка: `{e}`'''
        if (
                response.status_code in (301, 302)
                and not response.url.startswith(f'/posts/{post_with_group.id}')
        ):
            response = client.get(f'/posts/{post_with_group.id}/edit/')
        assert response.status_code != 404, (
            'Страница `/posts/<post_id>/edit/` не найдена, проверьте этот адрес в *urls.py*'
        )

        assert response.status_code in (301, 302), (
            'Проверьте, что вы переадресуете пользователя со страницы '
            '`/posts/<post_id>/edit/` на страницу поста, если он не автор'
        )

    @pytest.mark.django_db(transaction=True)
    def test_post_edit_view_author_get(self, user_client, post_with_group):
        try:
            response = user_client.get(f'/posts/{post_with_group.id}/edit')
        except Exception as e:
            assert False, f'''Страница `/posts/<post_id>/edit/` работает неправильно. Ошибка: `{e}`'''
        if response.status_code in (301, 302):
            response = user_client.get(f'/posts/{post_with_group.id}/edit/')
        assert response.status_code != 404, (
            'Страница `/posts/<post_id>/edit/` не найдена, проверьте этот адрес в *urls.py*'
        )

        post_context = get_field_from_context(response.context, Post)
        postform_context = get_field_from_context(response.context, PostForm)
        assert any([post_context, postform_context]) is not None, (
            'Проверьте, что передали статью в контекст страницы `/posts/<post_id>/edit/` типа `Post` или `PostForm`'
        )

        assert 'form' in response.context, (
            'Проверьте, что передали форму `form` в контекст страницы `/posts/<post_id>/edit/`'
        )
        fields_cnt = 3
        assert len(response.context['form'].fields) == fields_cnt, (
            f'Проверьте, что в форме `form` на страницу `/posts/<post_id>/edit/` {fields_cnt} поля'
        )
        assert 'group' in response.context['form'].fields, (
            'Проверьте, что в форме `form` на странице `/posts/<post_id>/edit/` есть поле `group`'
        )
        assert type(response.context['form'].fields['group']) == forms.models.ModelChoiceField, (
            'Проверьте, что в форме `form` на странице `/posts/<post_id>/edit/` поле `group` типа `ModelChoiceField`'
        )
        assert not response.context['form'].fields['group'].required, (
            'Проверьте, что в форме `form` на странице `/posts/<post_id>/edit/` поле `group` не обязательно'
        )

        assert 'text' in response.context['form'].fields, (
            'Проверьте, что в форме `form` на странице `/posts/<post_id>/edit/` есть поле `text`'
        )
        assert type(response.context['form'].fields['text']) == forms.fields.CharField, (
            'Проверьте, что в форме `form` на странице `/posts/<post_id>/edit/` поле `text` типа `CharField`'
        )
        assert response.context['form'].fields['text'].required, (
            'Проверьте, что в форме `form` на странице `/posts/<post_id>/edit/` поле `group` обязательно'
        )

        assert 'image' in response.context['form'].fields, (
            'Проверьте, что в форме `form` на странице `/posts/<post_id>/edit/` есть поле `image`'
        )
        assert type(response.context['form'].fields['image']) == forms.fields.ImageField, (
            'Проверьте, что в форме `form` на странице `/posts/<post_id>/edit/` поле `image` типа `ImageField`'
        )

    @staticmethod
    def get_image_file(name, ext='png', size=(50, 50), color=(256, 0, 0)):
        file_obj = BytesIO()
        image = Image.new("RGBA", size=size, color=color)
        image.save(file_obj, ext)
        file_obj.seek(0)
        return File(file_obj, name=name)

    @pytest.mark.django_db(transaction=True)
    def test_post_edit_view_author_post(self, mock_media, user_client, post_with_group):
        text = 'Проверка изменения поста!'
        try:
            response = user_client.get(f'/posts/{post_with_group.id}/edit')
        except Exception as e:
            assert False, f'''Страница `/posts/<post_id>/edit/` работает неправильно. Ошибка: `{e}`'''
        url = (
            f'/posts/{post_with_group.id}/edit/'
            if response.status_code in (301, 302)
            else f'/posts/{post_with_group.id}/edit'
        )

        image = self.get_image_file('image2.png')
        response = user_client.post(url, data={'text': text, 'group': post_with_group.group_id, 'image': image})

        assert response.status_code in (301, 302), (
            'Проверьте, что со страницы `/posts/<post_id>/edit/` '
            'после создания поста перенаправляете на страницу поста'
        )
        post = Post.objects.filter(author=post_with_group.author, text=text, group=post_with_group.group).first()
        assert post is not None, (
            'Проверьте, что вы изменили пост при отправки формы на странице `/posts/<post_id>/edit/`'
        )
        assert response.url.startswith(f'/posts/{post_with_group.id}'), (
            'Проверьте, что перенаправляете на страницу поста `/posts/<post_id>/`'
        )
