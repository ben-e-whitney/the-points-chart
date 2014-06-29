"""
Django settings for the_points_chart project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# TODO: supposed to remove reliance on actual name of project.
project_name = 'the_points_chart'
with open(os.path.join(BASE_DIR, project_name, 'SECRET_KEY.txt'), 'r') as f:
    SECRET_KEY = f.read().rstrip()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True
TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

ALLOWED_HOSTS = []

LOGIN_URL = '/login/'
# Maybe get rid of this so that there's the same setup with Coop and Cooper?
AUTH_PROFILE_MODULE = 'profiles.UserProfile'

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'localflavor',
    'timezone_field',
    'chores',
    'profiles',
    'stewardships',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # IMPORTANT TODO: re-enable this, maybe rewriting AJAX scripts with jQuery.
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'the_points_chart.urls'

WSGI_APPLICATION = 'the_points_chart.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
# TODO: eventually this is all supposed to be moved out of Django or something.
# See <https://docs.djangoproject.com/en/dev/howto/static-files/>.
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)

