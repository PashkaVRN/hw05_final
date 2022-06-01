import pytest
from django.contrib.auth import get_user_model
from django.core.paginator import Page

from tests.utils import get_field_from_context


class TestProfileView:

    @pytest.mark.django_db(transaction=True)
    def test_profile_view_get(self, client, post_with_group):
        url = f'/profile/{post_with_group.author.username}'
        url_templ = '/profile/<username>/'
        try:
            response = client.get(url)
        except Exception as e:
            assert False, f'''Страница `{url_templ}` работает неправильно. Ошибка: `{e}`'''
        if response.status_code in (301, 302):
            response = client.get(f'{url}/')
        assert response.status_code != 404, (
            f'Страница `{url_templ}` не найдена, проверьте этот адрес в *urls.py*'
        )

        profile_context = get_field_from_context(response.context, get_user_model())
        assert profile_context is not None, f'Проверьте, что передали автора в контекст страницы `{url_templ}`'

        page_context = get_field_from_context(response.context, Page)
        assert page_context is not None, (
            f'Проверьте, что передали статьи автора в контекст страницы `{url_templ}` типа `Page`'
        )
        assert len(page_context.object_list) == 1, (
            f'Проверьте, что в контекст страницы переданы правильные статьи автора `{url_templ}`'
        )
        posts_list = page_context.object_list
        for post in posts_list:
            assert hasattr(post, 'image'), (
                f'Убедитесь, что статья, передаваемая в контекст страницы `{url_templ}`, имеет поле `image`'
            )
            assert getattr(post, 'image') is not None, (
                f'Убедитесь, что статья, передаваемая в контекст страницы `{url_templ}`, имеет поле `image`, '
                'и туда передается изображение'
            )

        new_user = get_user_model()(username='new_user_87123478')
        new_user.save()
        url = f'/profile/{new_user.username}'
        try:
            new_response = client.get(url)
        except Exception as e:
            assert False, f'''Страница `{url_templ}` работает неправильно. Ошибка: `{e}`'''
        if new_response.status_code in (301, 302):
            new_response = client.get(f'{url}/')

        page_context = get_field_from_context(new_response.context, Page)
        assert page_context is not None, (
            f'Проверьте, что передали статьи автора в контекст страницы `{url_templ}` типа `Page`'
        )
        assert len(page_context.object_list) == 0, (
            f'Проверьте, что правильные статьи автора в контекст страницы `{url_templ}`'
        )
