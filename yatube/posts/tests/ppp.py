import shutil 
import tempfile 
 
from django.conf import settings 
from django.contrib.auth import get_user_model 
from django.core.files.uploadedfile import SimpleUploadedFile 
from django.test import Client, TestCase, override_settings 
from django.urls import reverse 
from posts.forms import CommentForm, PostForm 
from posts.models import Comment, Group, Post, User 
 
User = get_user_model() 
 
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR) 
 
 
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT) 
class PostCreateFormTests(TestCase): 
    @classmethod 
    def setUpClass(cls): 
        super().setUpClass() 
        cls.user = User.objects.create_user(username='test_user') 
        cls.group = Group.objects.create( 
            title='Тестовая группа', 
            slug='test-slug', 
            description='Тестовое описание', 
        ) 
        cls.post = Post.objects.create( 
            author=cls.user, 
            text='Тестовый пост', 
        ) 
        cls.form = PostForm() 
        cls.small_gif = ( 
            b'\x47\x49\x46\x38\x39\x61\x02\x00' 
            b'\x01\x00\x80\x00\x00\x00\x00\x00' 
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00' 
            b'\x00\x00\x00\x2C\x00\x00\x00\x00' 
            b'\x02\x00\x01\x00\x00\x02\x02\x0C' 
            b'\x0A\x00\x3B' 
        ) 
 
    @classmethod 
    def tearDownClass(cls): 
        super().tearDownClass() 
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True) 
 
    def setUp(self): 
        self.authorized_client = Client() 
        self.authorized_client.force_login(PostCreateFormTests.user) 
 
    def test_form_create_post(self): 
        """Валидная форма создает запись.""" 
        uploaded = SimpleUploadedFile( 
            name='small.gif', 
            content=PostCreateFormTests.small_gif, 
            content_type='image/gif' 
        ) 
        posts_count = Post.objects.count() 
        form_data = { 
            'text': 'Тестовая запись 1', 
            'group': PostCreateFormTests.group.pk, 
            'image': uploaded, 
        } 
        response = self.authorized_client.post( 
            reverse('posts:post_create'), 
            data=form_data, 
            follow=True 
        ) 
        self.assertRedirects( 
            response, reverse( 
                'posts:profile', 
                kwargs={'username': PostCreateFormTests.user} 
            ) 
        ) 
        self.assertEqual( 
            Post.objects.count(), 
            posts_count + 1 
        ) 
        self.assertTrue( 
            Post.objects.filter( 
                group=PostCreateFormTests.group.pk, 
                text='Тестовая запись 1', 
                author=PostCreateFormTests.user, 
                image='posts/small.gif' 
            ).exists() 
        ) 
 
    def test_post_edit(self): 
        """Валидная форма редактирует запись.""" 
        uploaded = SimpleUploadedFile( 
            name='small_0.gif', 
            content=PostCreateFormTests.small_gif, 
            content_type='image/gif' 
        ) 
        posts_count = Post.objects.count() 
        self.authorized_client.get( 
            reverse( 
                'posts:post_edit', 
                kwargs={'pk': PostCreateFormTests.post.pk} 
            ) 
        ) 
        form_data = { 
            'text': 'Отредактированная запись 1', 
            'group': PostCreateFormTests.group.pk, 
            'image': uploaded, 
        } 
        response = self.authorized_client.post( 
            reverse( 
                'posts:post_edit', 
                kwargs={'pk': PostCreateFormTests.post.pk} 
            ), 
            data=form_data, 
            follow=True 
        ) 
        self.assertRedirects( 
            response, reverse( 
                'posts:post_detail', 
                kwargs={'pk': PostCreateFormTests.post.pk} 
            ) 
        ) 
        self.assertTrue( 
            Post.objects.filter( 
                text='Отредактированная запись 1', 
                group=PostCreateFormTests.group.pk, 
                author=PostCreateFormTests.user,
                image='posts/small_0.gif' 
            ).exists() 
        ) 
        self.assertEqual( 
            Post.objects.count(), 
            posts_count 
        ) 
 
 
class CommentCreateFormTests(TestCase): 
    @classmethod 
    def setUpClass(cls): 
        super().setUpClass() 
        cls.user = User.objects.create_user(username='test_user') 
        cls.post = Post.objects.create( 
            author=cls.user, 
            text='Тестовый пост', 
        ) 
        cls.form = CommentForm() 
 
    def setUp(self): 
        self.authorized_client = Client() 
        self.authorized_client.force_login(CommentCreateFormTests.user) 
 
    def test_add_comment_form(self): 
        """Валидная форма создаёт комментарий.""" 
        comments_count = CommentCreateFormTests.post.comments.count() 
        form_data = { 
            'text': 'Test comment', 
        } 
        response = self.authorized_client.post( 
            reverse( 
                'posts:add_comment', 
                kwargs={'pk': CommentCreateFormTests.post.pk} 
            ), 
            data=form_data, 
            follow=True 
        ) 
        self.assertRedirects( 
            response, reverse( 
                'posts:post_detail', 
                kwargs={'pk': CommentCreateFormTests.post.pk} 
            ) 
        ) 
        self.assertEqual( 
            CommentCreateFormTests.post.comments.count(), 
            comments_count + 1 
        ) 
        self.assertTrue( 
            Comment.objects.filter( 
                text='Test comment', 
                author=CommentCreateFormTests.user 
            ).exists() 
        )