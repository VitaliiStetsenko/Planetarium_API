from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from planetarium.models import AstronomyShow, ShowTheme
from planetarium.serializers import AstronomyShowListRetrieveSerializer


ASTRONOMY_SHOW_URL = reverse("planetarium:astronomyshow-list")


def detail_url(astronomy_show_id):
    return reverse(
        "planetarium:astronomyshow-detail",
        args=(astronomy_show_id,),
    )


def sample_astronomy_show(**params):
    defaults = {
        "title": "test_title",
        "description": "test_description",
    }
    defaults.update(params)
    return AstronomyShow.objects.create(**defaults)


class UnauthenticatedAstronomyShowApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_astronomy_show_list(self):
        response = self.client.get(ASTRONOMY_SHOW_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_astronomy_show_detail(self):
        astronomy_show = sample_astronomy_show(
            title="not_default_title",
            description="not_default_description",
        )
        url = detail_url(astronomy_show.id)

        response = self.client.get(url)
        serializer = AstronomyShowListRetrieveSerializer(astronomy_show)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_astronomy_show(self):
        payload = {
            "title": "test_title",
            "description": "test_description",
        }
        response = self.client.post(ASTRONOMY_SHOW_URL, payload)
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_delete_astronomy_show(self):
        astronomy_show = sample_astronomy_show()
        url = detail_url(astronomy_show.id)

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertTrue(
            AstronomyShow.objects.filter(id=astronomy_show.id).exists()
        )

    def test_filter_by_theme(self):
        show_without_theme = sample_astronomy_show()
        show_with_theme_1 = sample_astronomy_show(title="show_with_theme_1")
        show_with_theme_2 = sample_astronomy_show(title="show_with_theme_2")

        theme_1 = ShowTheme.objects.create(name="test_theme_1")
        theme_2 = ShowTheme.objects.create(name="test_theme_2")

        show_with_theme_1.theme.add(theme_1)
        show_with_theme_2.theme.add(theme_2)

        response = self.client.get(
            ASTRONOMY_SHOW_URL,
            {"theme": f"{theme_1.id},{theme_2.id}"},
        )

        serializer_without_theme = AstronomyShowListRetrieveSerializer(
            show_without_theme
        )
        serializer_with_theme_1 = AstronomyShowListRetrieveSerializer(
            show_with_theme_1
        )
        serializer_with_theme_2 = AstronomyShowListRetrieveSerializer(
            show_with_theme_2
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertNotIn(
            serializer_without_theme.data,
            response.data["results"],
        )
        self.assertIn(
            serializer_with_theme_1.data,
            response.data["results"],
        )
        self.assertIn(
            serializer_with_theme_2.data,
            response.data["results"],
        )

    def test_filter_by_title(self):
        show_with_title_1 = sample_astronomy_show(title="AAAAAA")
        show_with_title_2 = sample_astronomy_show(title="BBBBBB")
        show_with_title_3 = sample_astronomy_show(title="CCCCCC")

        response = self.client.get(
            ASTRONOMY_SHOW_URL,
            {"title": "A"},
        )
        response_2 = self.client.get(
            ASTRONOMY_SHOW_URL,
            {"title": "B"},
        )

        serializer_with_title_1 = AstronomyShowListRetrieveSerializer(
            show_with_title_1
        )
        serializer_with_title_2 = AstronomyShowListRetrieveSerializer(
            show_with_title_2
        )
        serializer_with_title_3 = AstronomyShowListRetrieveSerializer(
            show_with_title_3
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn(
            serializer_with_title_1.data,
            response.data["results"],
        )
        self.assertNotIn(
            serializer_with_title_1.data,
            response_2.data["results"],
        )

        self.assertIn(
            serializer_with_title_2.data,
            response_2.data["results"],
        )
        self.assertNotIn(
            serializer_with_title_2.data,
            response.data["results"],
        )

        self.assertNotIn(
            serializer_with_title_3.data,
            response.data["results"],
        )
        self.assertNotIn(
            serializer_with_title_3.data,
            response_2.data["results"],
        )


class AuthenticatedAstronomyShowApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test_password",
        )
        self.client.force_authenticate(self.user)

    def test_create_astronomy_show(self):
        payload = {
            "title": "test_title",
            "description": "test_description",
        }
        response = self.client.post(ASTRONOMY_SHOW_URL, payload)
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_delete_astronomy_show(self):
        astronomy_show = sample_astronomy_show()
        url = detail_url(astronomy_show.id)

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertTrue(
            AstronomyShow.objects.filter(id=astronomy_show.id).exists()
        )


class AdminAstronomyShowApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@admin.com",
            password="admin_password",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_astronomy_show(self):
        payload = {
            "title": "test_title",
            "description": "test_description",
        }
        response = self.client.post(ASTRONOMY_SHOW_URL, payload)
        astronomy_show = AstronomyShow.objects.get(id=response.data["id"])
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        for key in payload:
            self.assertEqual(
                payload[key],
                getattr(astronomy_show, key),
            )

    def test_delete_astronomy_show(self):
        astronomy_show = sample_astronomy_show()
        url = detail_url(astronomy_show.id)

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(
            AstronomyShow.objects.filter(id=astronomy_show.id).exists()
        )
