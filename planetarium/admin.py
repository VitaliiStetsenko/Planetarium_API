from django.contrib import admin

from planetarium.models import (
    Ticket,
    ShowTheme,
    AstronomyShow,
    ShowSession,
    PlanetariumDome,
    Reservation
)

admin.site.register(ShowTheme)
admin.site.register(AstronomyShow)
admin.site.register(ShowSession)
admin.site.register(PlanetariumDome)
admin.site.register(Ticket)
admin.site.register(Reservation)
