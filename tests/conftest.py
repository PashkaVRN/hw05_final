import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_dir_content = os.listdir(BASE_DIR)
PROJECT_DIR_NAME = 'yatube'
MANAGE_PATH = os.path.join(BASE_DIR, PROJECT_DIR_NAME)
# проверяем, что в корне репозитория лежит папка с проектом
if (
        PROJECT_DIR_NAME not in root_dir_content
        or not os.path.isdir(MANAGE_PATH)
):
    assert False, (
        f'В директории `{BASE_DIR}` не найдена папка c проектом `{PROJECT_DIR_NAME}`. '
        f'Убедитесь, что у вас верная структура проекта.'
    )

project_dir_content = os.listdir(MANAGE_PATH)
FILENAME = 'manage.py'
# проверяем, что структура проекта верная, и manage.py на месте
if FILENAME not in project_dir_content:
    assert False, (
        f'В директории `{MANAGE_PATH}` не найден файл `{FILENAME}`. '
        f'Убедитесь, что у вас верная структура проекта.'
    )

from django.utils.version import get_version

assert get_version() < '3.0.0', 'Пожалуйста, используйте версию Django < 3.0.0'

from yatube.settings import INSTALLED_APPS

assert any(app in INSTALLED_APPS for app in ['posts.apps.PostsConfig', 'posts']), (
    'Пожалуйста зарегистрируйте приложение в `settings.INSTALLED_APPS`'
)

pytest_plugins = [
    'tests.fixtures.fixture_user',
    'tests.fixtures.fixture_data',
]
