from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from planetarium.models import (
    ShowSession,
    ShowTheme
)

from planetarium.serializers import (
    ShowSessionRetrieveSerializer,
    ShowSessionListSerializer
)

from planetarium.tests.tests_planetarium_dome_api import (
    sample_planetarium_dome)
from planetarium.tests.tests_astronomy_show_api import (
    sample_astronomy_show)


SHOW_SESSION_URL = reverse("planetarium:showsession-list")


def detail_url(show_session_id):
    return reverse("planetarium:showsession-detail", args=(show_session_id,))


def sample_show_session(**params):
    if "astronomy_show" not in params:
        params["astronomy_show"] = sample_astronomy_show()

    if "planetarium_dome" not in params:
        params["planetarium_dome"] = sample_planetarium_dome()

    if "show_time" not in params:
        params["show_time"] = timezone.now()

    return ShowSession.objects.create(**params)


class UnauthenticatedShowSessionApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_show_session_list(self):
        response = self.client.get(SHOW_SESSION_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_show_session_detail(self):

        show_session = sample_show_session(
            astronomy_show=sample_astronomy_show(
                title="not_default_title",
                description="not_default_description"
            ),
            planetarium_dome=sample_planetarium_dome(
                name="not_default_name",
                rows=20,
                seats_in_row=20,
            ),
        )
        url = detail_url(show_session.id)

        response = self.client.get(url)
        serializer = ShowSessionRetrieveSerializer(show_session)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_show_session(self):
        payload = {
            "astronomy_show": sample_astronomy_show(
                title="not_default_title",
                description="not_default_description"
            ),
            "planetarium_dome": sample_planetarium_dome(
                name="not_default_name",
                rows=20,
                seats_in_row=20,
            ),
        }
        response = self.client.post(SHOW_SESSION_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_show_session(self):
        show_session = sample_show_session()
        url = detail_url(show_session.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(
            ShowSession.objects
            .filter(id=show_session.id)
            .exists()
        )

    def test_filter_by_theme_title_date_planetarium_dome(self):
        show_without_theme = sample_astronomy_show()
        show_with_theme_1 = sample_astronomy_show(title="AAA")
        show_with_theme_2 = sample_astronomy_show(title="BBB")

        theme_1 = ShowTheme.objects.create(name="test_theme_1")
        theme_2 = ShowTheme.objects.create(name="test_theme_2")

        show_with_theme_1.theme.add(theme_1)
        show_with_theme_2.theme.add(theme_2)

        planetarium_dome = sample_planetarium_dome()
        planetarium_dome_aaa = sample_planetarium_dome(name="AAA")
        planetarium_dome_bbb = sample_planetarium_dome(name="BBB")

        show_session_without_theme_title_01_09_26 = sample_show_session(
            astronomy_show=show_without_theme,
            planetarium_dome=planetarium_dome,
            show_time=datetime(2026, 9, 1, 1, 0,)
        )
        show_session_with_theme_1_aaa_01_10_26 = sample_show_session(
            astronomy_show=show_with_theme_1,
            planetarium_dome=planetarium_dome_aaa,
            show_time=datetime(2026, 10, 1, 1, 0,)
        )
        show_session_with_theme_2_bbb_01_11_26 = sample_show_session(
            astronomy_show=show_with_theme_2,
            planetarium_dome=planetarium_dome_bbb,
            show_time=datetime(2026, 11, 1, 1, 0,)
        )

        response = self.client.get(
            SHOW_SESSION_URL,
            {
                "theme": f"{theme_1.id},{theme_2.id}",
            }
        )

        for result in response.data["results"]:
            result.pop("tickets_available", None)

        response_2 = self.client.get(
            SHOW_SESSION_URL,
            {
                "title": "AAA",
            }
        )

        for result in response_2.data["results"]:
            result.pop("tickets_available", None)

        response_3 = self.client.get(
            SHOW_SESSION_URL,
            {
                "date": "2026-11-01",
            }
        )

        for result in response_3.data["results"]:
            result.pop("tickets_available", None)

        response_4 = self.client.get(
            SHOW_SESSION_URL,
            {
                "planetarium_dome": "AAA",
            }
        )

        for result in response_4.data["results"]:
            result.pop("tickets_available", None)

        serializer_without_theme_title_01_09_26 = ShowSessionListSerializer(
            show_session_without_theme_title_01_09_26
        )
        serializer_with_theme_1_aaa_01_10_26 = ShowSessionListSerializer(
            show_session_with_theme_1_aaa_01_10_26
        )
        serializer_with_theme_2_bbb_01_11_26 = ShowSessionListSerializer(
            show_session_with_theme_2_bbb_01_11_26
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertNotIn(
            serializer_without_theme_title_01_09_26.data,
            response.data["results"]
        )
        self.assertIn(
            serializer_with_theme_1_aaa_01_10_26.data,
            response.data["results"]
        )
        self.assertIn(
            serializer_with_theme_2_bbb_01_11_26.data,
            response.data["results"]
        )

        self.assertNotIn(
            serializer_without_theme_title_01_09_26.data,
            response_2.data["results"]
        )
        self.assertIn(
            serializer_with_theme_1_aaa_01_10_26.data,
            response_2.data["results"]
        )
        self.assertNotIn(
            serializer_with_theme_2_bbb_01_11_26.data,
            response_2.data["results"]
        )

        self.assertNotIn(
            serializer_without_theme_title_01_09_26.data,
            response_3.data["results"]
        )
        self.assertNotIn(
            serializer_with_theme_1_aaa_01_10_26.data,
            response_3.data["results"]
        )
        self.assertIn(
            serializer_with_theme_2_bbb_01_11_26.data,
            response_3.data["results"]
        )

        self.assertNotIn(
            serializer_without_theme_title_01_09_26.data,
            response_2.data["results"]
        )
        self.assertIn(
            serializer_with_theme_1_aaa_01_10_26.data,
            response_2.data["results"]
        )
        self.assertNotIn(
            serializer_with_theme_2_bbb_01_11_26.data,
            response_2.data["results"]
        )


class AuthenticatedShowSssionApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test_password"
        )
        self.client.force_authenticate(self.user)

    def test_create_show_session(self):
        payload = {
            "astronomy_show": sample_astronomy_show(
                title="not_default_title",
                description="not_default_description"
            ),
            "planetarium_dome": sample_planetarium_dome(
                name="not_default_name",
                rows=20,
                seats_in_row=20,
            ),
        }
        response = self.client.post(SHOW_SESSION_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_show_session(self):
        show_session = sample_show_session()
        url = detail_url(show_session.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            ShowSession.objects
            .filter(id=show_session.id)
            .exists()
        )


class AdminShowSessionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@admin.com",
            password="admin_password",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_show_session(self):
        astronomy_show = sample_astronomy_show()
        planetarium_dome = sample_planetarium_dome()
        payload = {
            "astronomy_show": astronomy_show.id,
            "planetarium_dome": planetarium_dome.id,
            "show_time": "2026-09-01T18:00:00Z",
        }
        response = self.client.post(SHOW_SESSION_URL, payload)
        show_session = ShowSession.objects.get(id=response.data["id"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(astronomy_show.id, show_session.astronomy_show_id)
        self.assertEqual(planetarium_dome.id, show_session.planetarium_dome_id)

    def test_delete_show_session(self):
        show_session = sample_show_session()
        url = detail_url(show_session.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            ShowSession.objects
            .filter(id=show_session.id)
            .exists()
        )
