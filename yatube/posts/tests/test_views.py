from django import forms
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
import shutil

from posts.forms import PostForm
from posts.models import Group, Post, Follow
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовое название',
            description='Тестовое описание группы',
            slug='test-slug',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image_name = 'small.gif'
        cls.uploaded = SimpleUploadedFile(
            name=cls.image_name,
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def chek_contex(self, response, bool=False):
        """Проверка контекста. Общая функция для тестов страниц."""
        if bool:
            post = response.context.get('post')
        else:
            post = response.context['page_obj'][0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image.name, f'posts/{self.uploaded}')
        self.assertContains(response, '<img', count=2)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:posts_index'))
        self.chek_contex(response)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', args=(self.group.slug,)))
        self.chek_contex(response)
        self.assertEqual(
            response.context.get('group'), self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', args=(self.user.username,)))
        self.assertEqual(
            response.context.get('author'), self.post.author)
        self.chek_contex(response)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=(self.post.id,))
        )
        self.chek_contex(response, True)

    def test_post_edit_and_create_show_correct_context(self):
        """Шаблон edit и create сформирован с правильным контекстом."""
        urls = (
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.pk,)),
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ChoiceField,
        }
        for url, slug in urls:
            reverse_name = reverse(url, args=slug)
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIsInstance(response.context['form'], PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form').fields.get(value)
                        self.assertIsInstance(form_field, expected)

    def test_no_in_wrong_group(self):
        """Пост не появляется в не своей группе."""
        wrong_group = Group.objects.create(
            title='Тестовое название группы 2',
            slug='test-slug2',
            description='Тестовое описание группы 2'
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={
                'slug': wrong_group.slug}))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_cache(self):
        """Тест кэша."""
        post = Post.objects.create(
            text='text',
            author=self.user,
            group=self.group
        )
        response = self.authorized_client.get(reverse('posts:posts_index'))
        response_post = response.context['page_obj'][0]
        self.assertEqual(post, response_post)
        post.delete()
        response_2 = self.authorized_client.get(reverse('posts:posts_index'))
        self.assertEqual(response.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(reverse('posts:posts_index'))
        self.assertNotEqual(response.content, response_3.content)


class PaginatorViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.count_post = 13
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test-slug'
        )
        for page_object in range(cls.count_post):
            Post.objects.create(
                text=f'Тестовый текст{page_object}',
                author=cls.user,
                group=cls.group
            )

    # def test_firs_page_paginators(self):
    #     """Корректная работа паджинатора на первой странице."""
    #     paginators_list = (
    #         ('posts:posts_index', None),
    #         ('posts:group_list', (self.group.slug,)),
    #         ('posts:profile', (self.user.username,)),
    #     )
    #     for reverse_name, arg in paginators_list:
    #         with self.subTest(reverse_name=reverse_name):
    #             response = self.client.get(reverse(reverse_name, args=arg))
    #             self.assertEqual(
    #                 len(response.context['page_obj']), settings.COUNT_POST)

    # def test_second_page_paginators(self):
    #     """Корректная работа паджинатора на второй странице."""
    #     paginators_list = (
    #         ('posts:posts_index', None),
    #         ('posts:group_list', (self.group.slug,)),
    #         ('posts:profile', (self.user.username,)),
    #     )
    #     for reverse_name, arg in paginators_list:
    #         with self.subTest(reverse_name=reverse_name):
    #             response = self.client.get(
    #                 reverse(reverse_name, args=arg) + '?page=2')
    #             self.assertEqual(
    #                 len(response.context['page_obj']
    #                     ), self.count_post - settings.COUNT_POST)

    def test_two_page_paginators(self):
        """Корректная работа паджинатора на двух страницах."""
        paginators_list = (
            ('posts:posts_index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.user.username,)),
        )
        for reverse_name, arg in paginators_list:
            with self.subTest(reverse_name=reverse_name):
                response_firs = self.client.get(
                    reverse(reverse_name, args=arg))
                response_second = self.client.get(
                    reverse(reverse_name, args=arg) + '?page=2')
                self.assertEqual(
                    len(response_firs.context['page_obj']
                        ), settings.COUNT_POST)
                self.assertEqual(
                    len(response_second.context['page_obj']
                        ), self.count_post - settings.COUNT_POST)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='user')
        cls.user_following = User.objects.create_user(username='user_1')
        cls.post = Post.objects.create(
            author=cls.user_following,
            text='Тестовый текст',
        )

    def setUp(self):
        self.following_client = Client()
        self.follower_client = Client()
        self.following_client.force_login(self.user_following)
        self.follower_client.force_login(self.user_follower)

    def test_follow(self):
        """Зарегистрированный пользователь может подписываться."""
        follower_count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_follow',
            args=(self.user_following.username,)))
        self.assertEqual(Follow.objects.count(), follower_count + 1)

    def test_unfollow(self):
        """Зарегистрированный пользователь может отписаться."""
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        follower_count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_unfollow',
            args=(self.user_following.username,)))
        self.assertEqual(Follow.objects.count(), follower_count - 1)

    def test_new_post_see_follower(self):
        """Пост появляется в ленте подписавшихся."""
        posts = Post.objects.create(
            text=self.post.text,
            author=self.user_following,
        )
        follow = Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post, posts)
        follow.delete()
        response_2 = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response_2.context['page_obj']), 0)
