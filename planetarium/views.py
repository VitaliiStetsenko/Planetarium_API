from django.db.models import Count, F
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from planetarium.models import (
    ShowTheme,
    AstronomyShow,
    PlanetariumDome,
    ShowSession,
    Reservation
)
from planetarium.permissions import AdminAllAuthenticatedReadPostDelete
from planetarium.serializers import (
    ShowThemeSerializer,
    AstronomyShowSerializer,
    PlanetariumDomeSerializer,
    ShowSessionSerializer,
    AstronomyShowListRetrieveSerializer,
    ShowSessionListSerializer,
    ShowSessionRetrieveSerializer,
    ReservationSerializer,
    ReservationListSerializer,
    ReservationRetrieveSerializer,
    AstronomyShowImageSerializer,
)


class DefaultPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 20


class ShowThemeViewSet(viewsets.ModelViewSet):
    queryset = ShowTheme.objects.all().order_by("name")
    serializer_class = ShowThemeSerializer
    pagination_class = DefaultPagination


class AstronomyShowViewSet(viewsets.ModelViewSet):
    queryset = AstronomyShow.objects.all()
    pagination_class = DefaultPagination

    @staticmethod
    def _params_to_ints(query_string):
        """Converts a string of '1,2,3' to a list of integers [1, 2, 3]."""
        return [int(str_id) for str_id in query_string.split(",")]

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return AstronomyShowListRetrieveSerializer
        elif self.action == "upload_image":
            return AstronomyShowImageSerializer
        return AstronomyShowSerializer

    def get_queryset(self):

        queryset = self.queryset

        """
        Searching by fields:
        theme (theme of the astronomy show),
        title (title of the astronomy show)
        """

        theme = self.request.query_params.get("theme", None)
        title = self.request.query_params.get("title", None)

        if theme:
            theme = self._params_to_ints(theme)
            queryset = queryset.filter(theme__id__in=theme).distinct()
        if title:
            queryset = queryset.filter(title__icontains=title).distinct()

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("theme")

        return queryset.order_by("title")

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload_image",
    )
    def upload_image(self, request, pk=None):
        astronomy_show = self.get_object()
        serializer = self.get_serializer(astronomy_show, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PlanetariumDomeViewSet(viewsets.ModelViewSet):
    queryset = PlanetariumDome.objects.all().order_by("name")
    serializer_class = PlanetariumDomeSerializer
    pagination_class = DefaultPagination


class ShowSessionViewSet(viewsets.ModelViewSet):
    queryset = ShowSession.objects.all()
    pagination_class = DefaultPagination

    @staticmethod
    def _params_to_ints(query_string):
        """Converts a string of '1,2,3' to a list of integers [1, 2, 3]."""
        return [int(str_id) for str_id in query_string.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return ShowSessionListSerializer
        elif self.action == "retrieve":
            return ShowSessionRetrieveSerializer
        return ShowSessionSerializer

    def get_queryset(self):
        queryset = self.queryset

        """
        Searching by fields:
        theme (theme of the astronomy show),
        title (title of the astronomy show),
        planetarium_dome (name of the planetarium dome),
        date (date of the astronomy show),
        """

        theme = self.request.query_params.get("theme", None)
        title = self.request.query_params.get("title", None)
        planetarium_dome = self.request.query_params.get(
            "planetarium_dome",
            None
        )
        date = self.request.query_params.get("date", None)

        if theme:
            theme = self._params_to_ints(theme)
            queryset = queryset.filter(
                astronomy_show__theme__id__in=theme
            ).distinct()

        if title:
            queryset = queryset.filter(
                astronomy_show__title__icontains=title
            ).distinct()

        if planetarium_dome:
            queryset = queryset.filter(
                planetarium_dome__name__icontains=planetarium_dome
            ).distinct()

        if date:
            queryset = queryset.filter(show_time__date=date).distinct()

        if self.action == "list":
            return queryset.select_related(
                "astronomy_show",
                "planetarium_dome",
            ).prefetch_related(
                "astronomy_show__theme",
            ).annotate(
                tickets_available=F(
                    "planetarium_dome__rows"
                ) * F(
                    "planetarium_dome__seats_in_row"
                ) - Count(
                    "tickets"
                )
            ).order_by("show_time")
        elif self.action == "retrieve":
            return queryset.select_related(
                "astronomy_show",
                "planetarium_dome",
            ).prefetch_related(
                "astronomy_show__theme",
            )
        return queryset


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (AdminAllAuthenticatedReadPostDelete,)

    def get_queryset(self):
        queryset = Reservation.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related(
                "tickets__show_session__astronomy_show__theme",
                "tickets__show_session__planetarium_dome",
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer
        elif self.action == "retrieve":
            return ReservationRetrieveSerializer
        return ReservationSerializer
