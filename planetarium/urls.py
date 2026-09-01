from django.urls import path, include
from rest_framework import routers

from planetarium.views import (
    ShowThemeViewSet,
    AstronomyShowViewSet,
    PlanetariumDomeViewSet,
    ShowSessionViewSet,
    ReservationViewSet
)

app_name = "planetarium"

router = routers.DefaultRouter()
router.register("show_theme", ShowThemeViewSet)
router.register("astronomy_show", AstronomyShowViewSet)
router.register("planetarium_dome", PlanetariumDomeViewSet)
router.register("show_session", ShowSessionViewSet)
router.register("reservation", ReservationViewSet)

urlpatterns = [path("", include(router.urls))]
