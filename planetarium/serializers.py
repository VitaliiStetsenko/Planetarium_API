from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from planetarium.models import (
    ShowTheme,
    AstronomyShow,
    PlanetariumDome,
    ShowSession,
    Ticket,
    Reservation
)


class ShowThemeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShowTheme
        fields = ["id", "name"]


class AstronomyShowSerializer(serializers.ModelSerializer):

    class Meta:
        model = AstronomyShow
        fields = ["id", "title", "description", "theme"]


class AstronomyShowImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AstronomyShow
        fields = ["id", "image"]


class AstronomyShowListRetrieveSerializer(AstronomyShowSerializer):
    theme = serializers.SlugRelatedField(
        many=True,
        slug_field="name",
        read_only=True,
    )

    class Meta:
        model = AstronomyShow
        fields = ["id", "title", "description", "theme", "image"]


class PlanetariumDomeSerializer(serializers.ModelSerializer):

    class Meta:
        model = PlanetariumDome
        fields = ["id", "name", "rows", "seats_in_row", "capacity", "image"]


class ShowSessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShowSession
        fields = ["id", "astronomy_show", "planetarium_dome", "show_time"]


class ShowSessionListSerializer(ShowSessionSerializer):
    astronomy_show_title = serializers.CharField(
        source="astronomy_show.title",
        read_only=True
    )
    astronomy_show_description = serializers.CharField(
        source="astronomy_show.description",
        read_only=True
    )
    astronomy_show_theme = serializers.SlugRelatedField(
        source="astronomy_show.theme",
        many=True,
        slug_field="name",
        read_only=True
    )
    planetarium_dome_name = serializers.CharField(
        source="planetarium_dome.name",
        read_only=True
    )
    tickets_available = serializers.IntegerField(
        read_only=True,
    )

    class Meta:
        model = ShowSession
        fields = [
            "id",
            "astronomy_show_title",
            "astronomy_show_description",
            "astronomy_show_theme",
            "planetarium_dome_name",
            "show_time",
            "tickets_available",
        ]


class TicketSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = ["id", "seat", "row", "show_session"]
        validators = [
            UniqueTogetherValidator(
                queryset=Ticket.objects.all(),
                fields=["seat", "row", "show_session"],
            )
        ]

    def validate(self, attrs):
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            attrs["show_session"].planetarium_dome,
            serializers.ValidationError,
        )
        return attrs


class TakenSeatsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = ["seat", "row"]


class ShowSessionRetrieveSerializer(ShowSessionSerializer):
    astronomy_show = AstronomyShowListRetrieveSerializer()
    planetarium_dome = PlanetariumDomeSerializer()
    tickets = TakenSeatsSerializer(many=True, read_only=False)

    class Meta:
        model = ShowSession
        fields = [
            "id",
            "astronomy_show",
            "planetarium_dome",
            "show_time",
            "tickets"
        ]


class ReservationSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Reservation
        fields = ["id", "created_at", "tickets"]

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            reservation = Reservation.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(reservation=reservation, **ticket_data)
            return reservation


class ShowSessionListReservationSerializer(ShowSessionListSerializer):

    class Meta:
        model = ShowSession
        fields = [
            "astronomy_show_title",
            "planetarium_dome_name",
            "show_time",
        ]


class ShowSessionRetrieveReservationSerializer(ShowSessionListSerializer):

    class Meta:
        model = ShowSession
        fields = [
            "id",
            "astronomy_show_title",
            "astronomy_show_description",
            "astronomy_show_theme",
            "planetarium_dome_name",
            "show_time",
        ]


class TicketListSerializer(TicketSerializer):
    show_session = ShowSessionListReservationSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ["seat", "row", "show_session"]


class ReservationListSerializer(ReservationSerializer):
    tickets = TicketListSerializer(many=True, read_only=True,)


class TicketRetrieveSerializer(TicketSerializer):
    show_session = ShowSessionRetrieveReservationSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ["id", "seat", "row", "show_session"]


class ReservationRetrieveSerializer(ReservationSerializer):
    tickets = TicketRetrieveSerializer(many=True, read_only=True,)
