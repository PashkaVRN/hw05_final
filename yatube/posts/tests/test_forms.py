import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
        )
        cls.group_new = Group.objects.create(
            title='Тестовое название1',
            slug='slug2',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        """Валидная форма создает запись """
        image_name = 'small.gif'
        uploaded = SimpleUploadedFile(
            name=image_name,
            content=self.small_gif,
            content_type='image/gif'
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.pk,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', args=(self.user.username,),))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.first()
        check_post_fields = (
            (post.author, self.post.author),
            (post.text, self.post.text),
            (post.group, self.post.group),
            (post.image, f'posts/{uploaded}'),
        )
        for new_post, expected in check_post_fields:
            with self.subTest(new_post=expected):
                self.assertEqual(new_post, expected)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_edit_post(self):
        """Текст поста меняется при редактировании."""
        image_name = 'small_0.gif'
        uploaded = SimpleUploadedFile(
            name=image_name,
            content=self.small_gif,
            content_type='image/gif'
        )
        new_text = 'Самый новый пост'
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.pk,)),
            data={
                'text': new_text,
                'group': self.group_new.pk,
                'image': uploaded
            },
            follow=True,)
        post = Post.objects.first()
        self.assertEqual(new_text, post.text)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=(self.post.id,)),
            HTTPStatus.FOUND
        )
        self.assertTrue(
            Post.objects.filter(
                group=self.group_new.pk,
                author=self.user,
                text=new_text,
                image='posts/small_0.gif'
            ).exists()
        )
        response = self.authorized_client.get(reverse(
            'posts:group_list', args=(self.group.slug,)))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_anon_post(self):
        """Тест доступа анониму."""
        post_count = Post.objects.count()
        text = 'Тестовый текст'
        form_data = {
            'text': text,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        user_login = reverse('users:login')
        create = reverse('posts:post_create')
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response, f'{user_login}?next={create}')

    def test_comment(self):
        """Проверка создания пользователем комментария"""
        comments_count = Comment.objects.count()
        form_data = {
            'post': self.post,
            'author': self.user,
            'text': 'text',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=(self.post.id,)))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
