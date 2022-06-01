import pytest


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username='TestUser', password='1234567')


@pytest.fixture
def user_client(user, client):
    client.force_login(user)
    return client


@pytest.fixture
def another_user(mixer):
    from django.contrib.auth.models import User
    return mixer.blend(User, username='AnotherUser')
