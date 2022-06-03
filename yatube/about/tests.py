from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class StaticPagesURLTests(TestCase):
    def setUp(self):
        super().setUp()
        self.guest_client = Client()

    def test_urls_uses_correct_name(self):
        """URL-адрес соответствует их именам."""
        url_names = {
            reverse('about:author'): '/about/author/',
            reverse('about:tech'): '/about/tech/',

        }
        for reverse_name, urls in url_names.items():
            with self.subTest(urls=urls):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.request['PATH_INFO'], urls)

    def test_static_url_exists_at_desired_location(self):
        """Страницы доступные любому пользователю."""
        url_path = (
            reverse('about:author'),
            reverse('about:tech'),
        )

        for adress in url_path:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }

        for reverse_name, template in templates_url_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
