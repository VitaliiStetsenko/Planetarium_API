from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from planetarium.models import PlanetariumDome
from planetarium.serializers import PlanetariumDomeSerializer


PLANETARIUM_DOME_URL = reverse("planetarium:planetariumdome-list")


def detail_url(planetarium_dome_id):
    return reverse(
        "planetarium:planetariumdome-detail",
        args=(planetarium_dome_id,)
    )


def sample_planetarium_dome(**params):
    defaults = {
        "name": "test_name",
        "rows": 10,
        "seats_in_row": 10,
    }
    defaults.update(params)
    return PlanetariumDome.objects.create(**defaults)


class UnauthenticatedPlanetariumDomeApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_planetarium_dome_list(self):
        response = self.client.get(PLANETARIUM_DOME_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_planetarium_dome_detail(self):

        planetarium_dome = sample_planetarium_dome(
            name="not_default_name",
            rows=20,
            seats_in_row=20,
        )
        url = detail_url(planetarium_dome.id)

        response = self.client.get(url)
        serializer = PlanetariumDomeSerializer(planetarium_dome)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_planetarium_dome(self):
        payload = {
            "name": "not_default_name",
            "rows": 20,
            "seats_in_row": 20,
        }
        response = self.client.post(PLANETARIUM_DOME_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_planetarium_dome(self):
        planetarium_dome = sample_planetarium_dome()
        url = detail_url(planetarium_dome.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(
            PlanetariumDome.objects
            .filter(id=planetarium_dome.id)
            .exists()
        )


class AuthenticatedPlanetariumDomeApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test_password"
        )
        self.client.force_authenticate(self.user)

    def test_create_planetarium_dome(self):
        payload = {
            "name": "not_default_name",
            "rows": 20,
            "seats_in_row": 20,
        }
        response = self.client.post(PLANETARIUM_DOME_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_planetarium_dome(self):
        planetarium_dome = sample_planetarium_dome()
        url = detail_url(planetarium_dome.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            PlanetariumDome.objects.
            filter(id=planetarium_dome.id)
            .exists()
        )


class AdminPlanetariumDomeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@admin.com",
            password="admin_password",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_planetarium_dome(self):
        payload = {
            "name": "not_default_name",
            "rows": 20,
            "seats_in_row": 20,
        }
        response = self.client.post(PLANETARIUM_DOME_URL, payload)
        planetarium_dome = PlanetariumDome.objects.get(id=response.data["id"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key in payload:
            self.assertEqual(payload[key], getattr(planetarium_dome, key))

    def test_delete_planetarium_dome(self):
        planetarium_dome = sample_planetarium_dome()
        url = detail_url(planetarium_dome.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            PlanetariumDome.objects
            .filter(id=planetarium_dome.id)
            .exists()
        )
