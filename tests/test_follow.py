import re
import tempfile

from django.contrib.auth import get_user_model
from django.db.models.fields.related import ForeignKey
from django.core.paginator import Page

import pytest


try:
    from posts.models import Post
except ImportError:
    assert False, 'Не найдена модель Post'

try:
    from posts.models import Follow
except ImportError:
    assert False, 'Не найдена модель Follow'


def search_field(model_fields, searching_field_name):
    for field in model_fields:
        if field.name == searching_field_name:
            return field
    return None


def search_refind(execution, user_code):
    """Поиск запуска"""
    for temp_line in user_code.split('\n'):
        if re.search(execution, temp_line):
            return True
    return False


class TestFollow:

    @pytest.mark.parametrize('field_name', ['author', 'user'])
    def test_follow(self, field_name):
        model_name = 'Follow'
        related_name = 'follower' if field_name == 'user' else 'following'
        checking_field = search_field(Follow._meta.fields, field_name)
        field_in_model_text = (f'Поле `{field_name}` в модели `{model_name}`')
        assert checking_field is not None, (
            f'{field_in_model_text} отсутствует в модели или переименовано. '
        )
        assert isinstance(checking_field, ForeignKey), (
            f'{field_in_model_text} '
            'должно быть связано через отношение многие-к-одному '
            'с моделью пользователей. Проверьте класс поля.'
        )
        assert checking_field.related_model == get_user_model(), (
            f'{field_in_model_text} должно быть связано с моделью '
            f'`{get_user_model().__name__}`'
        )
        assert checking_field.remote_field.related_name == related_name, (
            f'{field_in_model_text} должно при объявлении содержать '
            f'`related_name=\'{related_name}\'`'
        )
        assert not checking_field.unique, (
            f'{field_in_model_text} '
            'не следует ограничивать уникальными значениями. '
            'На одного и того же автора может быть подписано несколько '
            'читателей. Один и тот же читатель может быть подписан на '
            'несколько авторов. '
        )
        assert checking_field.remote_field.on_delete.__name__ == 'CASCADE', (
            f'{field_in_model_text} должно предусматривать '
            '`on_delete=models.CASCADE`.'
        )

    def check_url(self, client, url, str_url):
        try:
            response = client.get(f'{url}')
        except Exception as e:
            assert False, f'''Страница `{str_url}` работает неправильно. Ошибка: `{e}`'''
        if response.status_code in (301, 302) and response.url == f'{url}/':
            response = client.get(f'{url}/')
        assert response.status_code != 404, f'Страница `{str_url}` не найдена, проверьте этот адрес в *urls.py*'
        return response

    @pytest.mark.django_db(transaction=True)
    def test_follow_not_auth(self, client, user):
        response = self.check_url(client, '/follow', '/follow/')
        if not(response.status_code in (301, 302) and response.url.startswith('/auth/login')):
            assert False, (
                'Проверьте, что не авторизованного пользователя `/follow/` отправляет на страницу авторизации'
            )

        response = self.check_url(client, f'/profile/{user.username}/follow', '/profile/<username>/follow/')
        if not(response.status_code in (301, 302) and response.url.startswith('/auth/login')):
            assert False, (
                'Проверьте, что не авторизованного пользователя `profile/<username>/follow/` '
                'отправляете на страницу авторизации'
            )

        response = self.check_url(client, f'/profile/{user.username}/unfollow', '/profile/<username>/unfollow/')
        if not(response.status_code in (301, 302) and response.url.startswith('/auth/login')):
            assert False, (
                'Проверьте, что не авторизованного пользователя `profile/<username>/unfollow/` '
                'отправляете на страницу авторизации'
            )

    @pytest.mark.django_db(transaction=True)
    def test_follow_auth(self, user_client, user, post):
        assert hasattr(user, 'follower'), (
            'Поле `user` в модели `Follow` должно при объявлении содержать '
            '`related_name="follower"'
        )
        assert user.follower.count() == 0, 'Проверьте, что правильно считается подписки'
        self.check_url(user_client, f'/profile/{post.author.username}/follow', '/profile/<username>/follow/')
        assert user.follower.count() == 0, 'Проверьте, что нельзя подписаться на самого себя'

        user_1 = get_user_model().objects.create_user(username='TestUser_2344')
        user_2 = get_user_model().objects.create_user(username='TestUser_73485')

        self.check_url(user_client, f'/profile/{user_1.username}/follow', '/profile/<username>/follow/')
        assert user.follower.count() == 1, 'Проверьте, что вы можете подписаться на пользователя'
        self.check_url(user_client, f'/profile/{user_1.username}/follow', '/profile/<username>/follow/')
        assert user.follower.count() == 1, 'Проверьте, что вы можете подписаться на пользователя только один раз'

        image = tempfile.NamedTemporaryFile(suffix=".jpg").name
        Post.objects.create(text='Тестовый пост 4564534', author=user_1, image=image)
        Post.objects.create(text='Тестовый пост 354745', author=user_1, image=image)

        Post.objects.create(text='Тестовый пост 245456', author=user_2, image=image)
        Post.objects.create(text='Тестовый пост 9789', author=user_2, image=image)
        Post.objects.create(text='Тестовый пост 4574', author=user_2, image=image)

        response = self.check_url(user_client, '/follow', '/follow/')
        assert 'page_obj' in response.context, (
            'Проверьте, что передали переменную `page_obj` в контекст страницы `/follow/`'
        )
        assert type(response.context['page_obj']) == Page, (
            'Проверьте, что переменная `page_obj` на странице `/follow/` типа `Page`'
        )
        assert len(response.context['page_obj']) == 2, (
            'Проверьте, что на странице `/follow/` список статей авторов на которых подписаны'
        )

        self.check_url(user_client, f'/profile/{user_2.username}/follow', '/profile/<username>/follow/')
        assert user.follower.count() == 2, 'Проверьте, что вы можете подписаться на пользователя'
        response = self.check_url(user_client, '/follow', '/follow/')
        assert len(response.context['page_obj']) == 5, (
            'Проверьте, что на странице `/follow/` список статей авторов на которых подписаны'
        )

        self.check_url(user_client, f'/profile/{user_1.username}/unfollow', '/profile/<username>/unfollow/')
        assert user.follower.count() == 1, 'Проверьте, что вы можете отписаться от пользователя'
        response = self.check_url(user_client, '/follow', '/follow/')
        assert len(response.context['page_obj']) == 3, (
            'Проверьте, что на странице `/follow/` список статей авторов на которых подписаны'
        )

        self.check_url(user_client, f'/profile/{user_2.username}/unfollow', '/profile/<username>/unfollow/')
        assert user.follower.count() == 0, 'Проверьте, что вы можете отписаться от пользователя'
        response = self.check_url(user_client, '/follow', '/follow/')
        assert len(response.context['page_obj']) == 0, (
            'Проверьте, что на странице `/follow/` список статей авторов на которых подписаны'
        )
