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
            ('posts:posts_index', None, '/'),
            ('posts:group_list', (self.group.slug,),
             f'/group/{self.group.slug}/'),
            ('posts:profile', (self.user.username,),
             f'/profile/{self.user.username}/'),
            ('posts:post_edit', (self.post.pk,),
             f'/posts/{self.post.pk}/edit/'),
            ('posts:post_detail', (self.post.pk,),
             f'/posts/{self.post.pk}/'),
            ('posts:post_create', None, '/create/'),
            ('posts:follow_index', None, '/follow/'),
            ('posts:profile_unfollow', (self.user.username,),
             f'/profile/{self.user.username}/unfollow/'),
            ('posts:add_comment', (self.post.pk,),
             f'/posts/{self.post.pk}/comment/'),
            ('posts:profile_follow', (self.user.username,),
             f'/profile/{self.user.username}/follow/'),
            ('posts:post_delete', (self.post.pk,),
             f'/posts/{self.post.pk}/delete/')
        )

    def test_revers(self):
        """Проверка реверсов."""
        for url, args, hard_link in self.url_templates_names:
            reverse_name = reverse(url, args=args)
            with self.subTest(reverse_name=hard_link):
                self.assertEqual(reverse_name, hard_link)

    def test_urls_uses_correct_template(self):
        """Проверяем, что URL-адрес использует соответствующий шаблон."""
        test_template = (
            ('posts:posts_index', None, 'posts/index.html'),
            ('posts:group_list', (self.group.slug,), 'posts/group_list.html'),
            ('posts:profile', (self.user.username,), 'posts/profile.html'),
            ('posts:post_edit', (self.post.pk,), 'posts/create_post.html'),
            ('posts:post_detail', (self.post.pk,), 'posts/post_detail.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
            ('posts:follow_index', None, 'posts/follow.html'),
        )
        for address, args, template in test_template:
            reverse_name = reverse(address, args=args)
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_author_page(self):
        """Тесты доступности автору."""
        redirect_profile = (
            'posts:post_delete',
            'posts:profile_follow',
            'posts:profile_unfollow',
        )
        redirect_detail = (
            'posts:add_comment',
        )
        for address, args, _ in self.url_templates_names:
            reverse_name = reverse(address, args=args)
            with self.subTest(address=address):
                if address in redirect_profile:
                    response = self.authorized_client.get(
                        reverse_name, follow=True
                    )
                    rederict = reverse('posts:profile', args=(self.user,))
                    self.assertRedirects(response, rederict, HTTPStatus.FOUND)
                elif address in redirect_detail:
                    response = self.authorized_client.get(
                        reverse_name, follow=True
                    )
                    rederict = reverse('posts:post_detail', args=args)
                    self.assertRedirects(response, rederict, HTTPStatus.FOUND)
                else:
                    response = self.authorized_client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_users_page(self):
        """Тестируем доступность страниц неавторизованными пользователями."""
        three_hundred_two_found_address = (
            'posts:post_edit',
            'posts:post_create',
            'posts:follow_index',
            'posts:add_comment',
            'posts:profile_follow',
            'posts:profile_unfollow',
            'posts:post_delete',
        )
        for address, args, _ in self.url_templates_names:
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

    def test_authorized_no_author(self):
        """Тесты авторизованного не автора."""
        redirect_profile = (
            'posts:profile_follow',
            'posts:profile_unfollow',
        )
        redirect_detail = (
            'posts:add_comment',
            'posts:post_edit',
            'posts:post_delete',
        )
        for address, args, _ in self.url_templates_names:
            reverse_name = reverse(address, args=args)
            with self.subTest(address=address):
                if address in redirect_profile:
                    response = self.authorized_client_no_author.get(
                        reverse_name, follow=True
                    )
                    rederict = reverse('posts:profile', args=(self.user,))
                    self.assertRedirects(response, rederict, HTTPStatus.FOUND)
                elif address in redirect_detail:
                    response = self.authorized_client_no_author.get(
                        reverse_name, follow=True
                    )
                    rederict = reverse('posts:post_detail', args=args)
                    self.assertRedirects(response, rederict, HTTPStatus.FOUND)
                else:
                    response = self.authorized_client_no_author.get(
                        reverse_name)
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
