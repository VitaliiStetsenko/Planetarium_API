from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from planetarium.models import ShowTheme
from planetarium.serializers import ShowThemeSerializer


SHOW_THEME_URL = reverse("planetarium:showtheme-list")


def detail_url(theme_id):
    return reverse("planetarium:showtheme-detail", args=(theme_id,))


def sample_show_theme(**params):
    defaults = {
        "name": "test_theme",
    }
    defaults.update(params)
    return ShowTheme.objects.create(**defaults)


class UnauthenticatedShowThemeApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_show_theme_list(self):
        response = self.client.get(SHOW_THEME_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_show_theme_detail(self):

        theme = sample_show_theme(name="not_default_test_name")
        url = detail_url(theme.id)

        response = self.client.get(url)
        serializer = ShowThemeSerializer(theme)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_theme(self):
        payload = {
            "name": "test_theme",
        }
        response = self.client.post(SHOW_THEME_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_theme(self):
        theme = sample_show_theme()
        url = detail_url(theme.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(ShowTheme.objects.filter(id=theme.id).exists())


class AuthenticatedShowThemeApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test_password"
        )
        self.client.force_authenticate(self.user)

    def test_create_theme(self):
        payload = {
            "name": "test_theme",
        }
        response = self.client.post(SHOW_THEME_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_theme(self):
        theme = sample_show_theme()
        url = detail_url(theme.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(ShowTheme.objects.filter(id=theme.id).exists())


class AdminShowThemeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@admin.com",
            password="admin_password",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_theme(self):
        payload = {
            "name": "test_theme",
        }
        response = self.client.post(SHOW_THEME_URL, payload)
        show_theme = ShowTheme.objects.get(id=response.data["id"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key in payload:
            self.assertEqual(payload[key], getattr(show_theme, key))

    def test_delete_theme(self):
        theme = sample_show_theme()
        url = detail_url(theme.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ShowTheme.objects.filter(id=theme.id).exists())
