import os
import uuid
from functools import partial

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import UniqueConstraint
from django.utils.text import slugify

from django.conf import settings


def custom_name(instance, filename, path):
    _, extension = os.path.splitext(filename)
    return os.path.join(
        path,
        f"{slugify(instance.id)}-{uuid.uuid4()}{extension}"
    )


class ShowTheme(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class AstronomyShow(models.Model):
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    theme = models.ManyToManyField(
        ShowTheme,
        blank=True,
        related_name="astronomy_shows"
    )
    image = models.ImageField(
        upload_to=partial(custom_name, path="uploads/astronomy_shows/"),
        null=True,
    )

    def __str__(self):
        return self.title


class PlanetariumDome(models.Model):
    name = models.CharField(max_length=100, unique=True)
    rows = models.PositiveIntegerField()
    seats_in_row = models.PositiveIntegerField()
    image = models.ImageField(
        upload_to=partial(custom_name, path="uploads/planetarium_domes/"),
        null=True,
    )

    def __str__(self):
        return self.name

    @property
    def capacity(self):
        return self.rows * self.seats_in_row


class ShowSession(models.Model):
    astronomy_show = models.ForeignKey(
        AstronomyShow,
        on_delete=models.CASCADE,
        related_name="show_sessions"
    )
    planetarium_dome = models.ForeignKey(
        PlanetariumDome,
        on_delete=models.CASCADE,
        related_name="show_sessions"
    )
    show_time = models.DateTimeField()

    def __str__(self):
        return f"{self.astronomy_show}"


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservations"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.id}"


class Ticket(models.Model):
    row = models.PositiveIntegerField()
    seat = models.PositiveIntegerField()
    show_session = models.ForeignKey(
        ShowSession,
        on_delete=models.CASCADE,
        related_name="tickets",
    )
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="tickets",
    )

    class Meta:
        ordering = ["row", "seat"]
        constraints = [
            UniqueConstraint(
                fields=["row", "seat", "show_session"],
                name="unique_tickets_row_seat_show_session"
            )
        ]

    @staticmethod
    def validate_ticket(row, seat, planetarium_dome, error_to_raise):
        for ticket_value, ticket_name, dome_attr in [
            (row, "row", "rows"),
            (seat, "seat", "seats_in_row"),
        ]:
            max_value = getattr(planetarium_dome, dome_attr)

            if not (1 <= ticket_value <= max_value):
                raise error_to_raise(
                    {
                        ticket_name: (
                            f"{ticket_name} must be in range "
                            f"(1, {max_value})"
                        )
                    }
                )

    def clean(self):
        Ticket.validate_ticket(
            self.row,
            self.seat,
            self.show_session.planetarium_dome,
            ValidationError,
        )

    def save(
            self,
            *args,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None,
    ):
        self.full_clean()
        return super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    def __str__(self):
        return f"{self.show_session} | Row {self.row} Seat {self.seat}"
