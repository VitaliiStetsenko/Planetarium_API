from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from planetarium.models import Reservation
from planetarium.tests.tests_astronomy_show_api import sample_astronomy_show
from planetarium.tests.tests_planetarium_dome_api import (
    sample_planetarium_dome)
from planetarium.tests.tests_show_session_api import sample_show_session

RESERVATION_URL = reverse("planetarium:reservation-list")


def detail_url(reservation_id):
    return reverse("planetarium:reservation-detail", args=(reservation_id,))


class UnauthenticatedReservationApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_reservation_list(self):
        response = self.client.get(RESERVATION_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reservation_detail(self):
        user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test_password"
        )

        reservation = Reservation.objects.create(
            user=user,
        )

        url = detail_url(reservation.id)

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_create_reservation(self):
        user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test_password"
        )

        payload = {
            "user": user,
        }

        response = self.client.post(RESERVATION_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_reservation(self):
        user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test_password"
        )

        reservation = Reservation.objects.create(
            user=user,
        )
        url = detail_url(reservation.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Reservation.objects.filter(id=reservation.id).exists())


class AuthenticatedReservationApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test_password"
        )
        self.client.force_authenticate(self.user)

    def test_create_delete_reservation(self):
        astronomy_show = sample_astronomy_show()
        planetarium_dome = sample_planetarium_dome(
            rows=10,
            seats_in_row=10,
        )

        show_session = sample_show_session(
            astronomy_show=astronomy_show,
            planetarium_dome=planetarium_dome,
        )
        payload = {
            "user": self.user.id,
            "tickets": [
                {
                    "row": 1,
                    "seat": 1,
                    "show_session": show_session.id,
                }
            ]
        }

        response = self.client.post(
            RESERVATION_URL,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        reservation_id = response.data["id"]
        url = detail_url(reservation_id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Reservation.objects
            .filter(id=reservation_id)
            .exists()
        )
