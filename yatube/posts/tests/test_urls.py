from http import HTTPStatus

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
        cls.user_1 = User.objects.create_user(username='auth_1')
        cls.group = Group.objects.create(
            title='Текстовый заголовок',
            description='Тестовое описание группы',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            pub_date='Тестовая дата',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client_no_author = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_no_author.force_login(self.user_1)
        self.url_templates_names = (
            ('posts:posts_index', None, 'posts/index.html', '/'),
            ('posts:group_list', (self.group.slug,), 'posts/group_list.html',
             f'/group/{self.group.slug}/'),
            ('posts:profile', (self.user.username,), 'posts/profile.html',
             f'/profile/{self.user.username}/'),
            ('posts:post_edit', (self.post.pk,), 'posts/create_post.html',
             f'/posts/{self.post.pk}/edit/'),
            ('posts:post_detail', (self.post.pk,), 'posts/post_detail.html',
             f'/posts/{self.post.pk}/'),
            ('posts:post_create', None, 'posts/create_post.html', '/create/'),
        )

    def test_revers(self):
        """Проверка реверсов."""
        for url, args, _, hard_link in self.url_templates_names:
            reverse_name = reverse(url, args=args)
            with self.subTest(reverse_name=hard_link):
                self.assertEqual(reverse_name, hard_link)

    def test_urls_uses_correct_template(self):
        """Проверяем, что URL-адрес использует соответствующий шаблон."""
        for address, args, template, _ in self.url_templates_names:
            reverse_name = reverse(address, args=args)
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_author_page(self):
        """Тесты доступности автору."""
        for address, args, _, _ in self.url_templates_names:
            reverse_name = reverse(address, args=args)
            with self.subTest(address=address):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_users_page(self):
        """Тестируем доступность страниц неавторизованными пользователями."""
        three_hundred_two_found_address = (
            'posts:post_edit',
            'posts:post_create',
        )
        for address, args, _, _ in self.url_templates_names:
            reverse_name = reverse(address, args=args)
            with self.subTest(reverse_name=reverse_name):
                if address in three_hundred_two_found_address:
                    response = self.client.get(
                        reverse_name, args=args, follow=True)
                    user_login = reverse('users:login')
                    self.assertRedirects(
                        response, f'{user_login}?next={reverse_name}',
                        HTTPStatus.FOUND
                    )
                else:
                    response = self.client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_for_user(self):
        """Тестируем доступность страниц для автора."""
        three_hundred_two_found_address = ('posts:post_edit',)
        for address, args, _, _ in self.url_templates_names:
            reverse_name = reverse(address, args=args)
            with self.subTest(reverse_name=reverse_name):
                if address in three_hundred_two_found_address:
                    response = self.authorized_client_no_author.get(
                        reverse_name, follow=True)
                    redirect_name = reverse('posts:post_detail', args=args)
                    self.assertRedirects(
                        response, redirect_name, HTTPStatus.FOUND)
                else:
                    response = self.authorized_client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404_page(self):
        """Проверка 404 для несуществующих страниц."""
        url = '/unexisting_page/'
        clients = (
            self.authorized_client,
            self.authorized_client_no_author,
            self.client,
        )
        for role in clients:
            with self.subTest(url=url):
                response = role.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
                self.assertTemplateUsed(response, 'core/404.html')
