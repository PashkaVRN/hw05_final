import re
import tempfile

import pytest
from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.db.models import fields
from django.template.loader import select_template
from django.core.paginator import Page

from tests.utils import get_field_from_context

try:
    from posts.models import Post
except ImportError:
    assert False, 'Не найдена модель Post'

try:
    from posts.models import Group
except ImportError:
    assert False, 'Не найдена модель Group'


def search_field(fields, attname):
    for field in fields:
        if attname == field.attname:
            return field
    return None


def search_refind(execution, user_code):
    """Поиск запуска"""
    for temp_line in user_code.split('\n'):
        if re.search(execution, temp_line):
            return True
    return False


class TestPost:

    def test_post_model(self):
        model_fields = Post._meta.fields
        text_field = search_field(model_fields, 'text')
        assert text_field is not None, 'Добавьте название события `text` модели `Post`'
        assert type(text_field) == fields.TextField, (
            'Свойство `text` модели `Post` должно быть текстовым `TextField`'
        )

        pub_date_field_name = 'created'
        pub_date_field = search_field(model_fields, 'pub_date')
        if pub_date_field is not None:
            pub_date_field_name = 'pub_date'
        else:
            pub_date_field = search_field(model_fields, 'created')
            if pub_date_field is not None:
                pub_date_field_name = 'created'

        assert pub_date_field is not None, (
            f'Добавьте дату и время проведения события в `{pub_date_field_name}` модели `Post`'
        )
        assert type(pub_date_field) == fields.DateTimeField, (
            f'Свойство `{pub_date_field_name}` модели `Post` должно быть датой и временем `DateTimeField`'
        )
        assert pub_date_field.auto_now_add, (
            f'Свойство `pub_date` или `created` модели `Post` должно быть `auto_now_add`'
        )

        author_field = search_field(model_fields, 'author_id')
        assert author_field is not None, 'Добавьте пользователя, автор который создал событие `author` модели `Post`'
        assert type(author_field) == fields.related.ForeignKey, (
            'Свойство `author` модели `Post` должно быть ссылкой на другую модель `ForeignKey`'
        )
        assert author_field.related_model == get_user_model(), (
            'Свойство `author` модели `Post` должно быть ссылкой на модель пользователя `User`'
        )

        group_field = search_field(model_fields, 'group_id')
        assert group_field is not None, 'Добавьте свойство `group` в модель `Post`'
        assert type(group_field) == fields.related.ForeignKey, (
            'Свойство `group` модели `Post` должно быть ссылкой на другую модель `ForeignKey`'
        )
        assert group_field.related_model == Group, (
            'Свойство `group` модели `Post` должно быть ссылкой на модель `Group`'
        )
        assert group_field.blank, (
            'Свойство `group` модели `Post` должно быть с атрибутом `blank=True`'
        )
        assert group_field.null, (
            'Свойство `group` модели `Post` должно быть с атрибутом `null=True`'
        )

        image_field = search_field(model_fields, 'image')
        assert image_field is not None, 'Добавьте свойство `image` в модель `Post`'
        assert type(image_field) == fields.files.ImageField, (
            'Свойство `image` модели `Post` должно быть `ImageField`'
        )
        assert image_field.upload_to == 'posts/', (
            "Свойство `image` модели `Post` должно быть с атрибутом `upload_to='posts/'`"
        )

    @pytest.mark.django_db(transaction=True)
    def test_post_create(self, user):
        text = 'Тестовый пост'
        author = user

        assert Post.objects.count() == 0

        image = tempfile.NamedTemporaryFile(suffix=".jpg").name
        post = Post.objects.create(text=text, author=author, image=image)
        assert Post.objects.count() == 1
        assert Post.objects.get(text=text, author=author).pk == post.pk

    def test_post_admin(self):
        admin_site = site

        assert Post in admin_site._registry, 'Зарегистрируйте модель `Post` в админской панели'

        admin_model = admin_site._registry[Post]

        assert 'text' in admin_model.list_display, (
            'Добавьте `text` для отображения в списке модели административного сайта'
        )

        assert 'pub_date' in admin_model.list_display or 'created' in admin_model.list_display, (
            f'Добавьте `pub_date` или `created` для отображения в списке модели административного сайта'
        )
        assert 'author' in admin_model.list_display, (
            'Добавьте `author` для отображения в списке модели административного сайта'
        )

        assert 'text' in admin_model.search_fields, (
            'Добавьте `text` для поиска модели административного сайта'
        )

        assert 'pub_date' in admin_model.list_filter or 'created' in admin_model.list_filter, (
            f'Добавьте `pub_date` или `created` для фильтрации модели административного сайта'
        )

        assert hasattr(admin_model, 'empty_value_display'), (
            'Добавьте дефолтное значение `-пусто-` для пустого поля'
        )
        assert admin_model.empty_value_display == '-пусто-', (
            'Добавьте дефолтное значение `-пусто-` для пустого поля'
        )


class TestGroup:

    def test_group_model(self):
        model_fields = Group._meta.fields
        title_field = search_field(model_fields, 'title')
        assert title_field is not None, 'Добавьте название события `title` модели `Group`'
        assert type(title_field) == fields.CharField, (
            'Свойство `title` модели `Group` должно быть символьным `CharField`'
        )
        assert title_field.max_length == 200, 'Задайте максимальную длину `title` модели `Group` 200'

        slug_field = search_field(model_fields, 'slug')
        assert slug_field is not None, 'Добавьте уникальный адрес группы `slug` модели `Group`'
        assert type(slug_field) == fields.SlugField, (
            'Свойство `slug` модели `Group` должно быть `SlugField`'
        )
        assert slug_field.unique, 'Свойство `slug` модели `Group` должно быть уникальным'

        description_field = search_field(model_fields, 'description')
        assert description_field is not None, 'Добавьте описание `description` модели `Group`'
        assert type(description_field) == fields.TextField, (
            'Свойство `description` модели `Group` должно быть текстовым `TextField`'
        )

    @pytest.mark.django_db(transaction=True)
    def test_group_create(self, user):
        text = 'Тестовый пост'
        author = user

        assert Post.objects.count() == 0

        post = Post.objects.create(text=text, author=author)
        assert Post.objects.count() == 1
        assert Post.objects.get(text=text, author=author).pk == post.pk

        title = 'Тестовая группа'
        slug = 'test-link'
        description = 'Тестовое описание группы'

        assert Group.objects.count() == 0
        group = Group.objects.create(title=title, slug=slug, description=description)
        assert Group.objects.count() == 1
        assert Group.objects.get(slug=slug).pk == group.pk

        post.group = group
        post.save()
        assert Post.objects.get(text=text, author=author).group == group


class TestGroupView:

    @pytest.mark.django_db(transaction=True)
    def test_group_view(self, client, post_with_group):
        url = f'/group/{post_with_group.group.slug}'
        url_templ = '/group/<slug>/'
        try:
            response = client.get(url)
        except Exception as e:
            assert False, f'''Страница `{url_templ}` работает неправильно. Ошибка: `{e}`'''
        if response.status_code in (301, 302):
            response = client.get(f'{url}/')
        if response.status_code == 404:
            assert False, f'Страница `{url_templ}` не найдена, проверьте этот адрес в *urls.py*'

        if response.status_code != 200:
            assert False, f'Страница `{url_templ}` работает неправильно.'

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

        group = post_with_group.group
        html = response.content.decode()

        templates_list = ['group_list.html', 'posts/group_list.html']
        html_template = select_template(templates_list).template.source

        assert search_refind(r'{%\s*for\s+.+in.*%}', html_template), (
            'Отредактируйте HTML-шаблон, используйте тег цикла'
        )
        assert search_refind(r'{%\s*endfor\s*%}', html_template), (
            'Отредактируйте HTML-шаблон, не найден тег закрытия цикла'
        )

        assert re.search(
            group.title,
            html
        ), (
            'Отредактируйте HTML-шаблон, не найден заголовок группы '
            '`{% block header %}{{ название_группы }}{% endblock %}`'
        )
        assert re.search(
            r'<\s*p\s*>\s*' + group.description + r'\s*<\s*\/p\s*>',
            html
        ), 'Отредактируйте HTML-шаблон, не найдено описание группы `<p>{{ описание_группы }}</p>`'


class TestCustomErrorPages:

    @pytest.mark.django_db(transaction=True)
    def test_custom_404(self, client):
        url_invalid = '/some_invalid_url_404/'
        code = 404
        response = client.get(url_invalid)

        assert response.status_code == code, (
            f'Убедитесь, что для несуществующих адресов страниц, сервер возвращает код {code}'
        )

        try:
            from yatube.urls import handler404 as handler404_student
        except ImportError:
            assert False, (
                f'Убедитесь, что для страниц, возвращающих код {code}, '
                'настроен кастомный шаблон'
            )

    @pytest.mark.django_db(transaction=True)
    def test_custom_500(self):
        code = 500

        try:
            from yatube.urls import handler500
        except ImportError:
            assert False, (
                f'Убедитесь, что для страниц, возвращающих код {code}, '
                'настроен кастомный шаблон'
            )

    @pytest.mark.django_db(transaction=True)
    def test_custom_403(self):
        code = 403

        try:
            from yatube.urls import handler403
        except ImportError:
            assert False, (
                f'Убедитесь, что для страниц, возвращающих код {code}, '
                'настроен кастомный шаблон'
            )
