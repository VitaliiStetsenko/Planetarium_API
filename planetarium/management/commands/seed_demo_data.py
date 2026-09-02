"""
Management command that populates the database with a couple of sample
records for every endpoint of the Planetarium API.

Usage (locally):
    python manage.py seed_demo_data

Usage (via docker-compose, matching this project's setup):
    docker-compose exec planetarium python manage.py seed_demo_data

The command is safe to run more than once:
- ShowTheme / AstronomyShow / PlanetariumDome are looked up by their
  unique field first (get_or_create), so re-running won't create
  duplicates or crash on the unique constraints.
- ShowSession is looked up by (astronomy_show, planetarium_dome,
  show_time) for the same reason.
- Reservations/Tickets are only created once per user: if the target
  user already has at least one reservation, that step is skipped so
  you don't get a growing pile of demo bookings every time you run it.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from planetarium.models import (
    AstronomyShow,
    PlanetariumDome,
    Reservation,
    ShowSession,
    ShowTheme,
    Ticket,
)

User = get_user_model()

TARGET_USER_ID = 2
TARGET_USER_EMAIL = "user1111@gmail.com"


class Command(BaseCommand):
    help = "Seeds the database with demo data for every planetarium endpoint."

    def handle(self, *args, **options):
        user = self._get_target_user()
        themes = self._seed_show_themes()
        shows = self._seed_astronomy_shows(themes)
        domes = self._seed_planetarium_domes()
        sessions = self._seed_show_sessions(shows, domes)
        self._seed_reservations(user, sessions)

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))

    # ------------------------------------------------------------------
    # User
    # ------------------------------------------------------------------
    def _get_target_user(self):
        try:
            user = User.objects.get(pk=TARGET_USER_ID)
            if user.email != TARGET_USER_EMAIL:
                self.stdout.write(
                    self.style.WARNING(
                        f"User id={TARGET_USER_ID} exists but has email "
                        f"'{user.email}', not '{TARGET_USER_EMAIL}'. "
                        "Using this user anyway since the id matched."
                    )
                )
            else:
                self.stdout.write(
                    f"Using existing user id={user.id} ({user.email})."
                )
            return user
        except User.DoesNotExist:
            pass

        # Fallback for a fresh/empty database (e.g. this sandbox check):
        # the id is not guaranteed to be 2 here, since it's assigned by
        # the database - only use this path if id=2 truly doesn't exist.
        user, created = User.objects.get_or_create(
            email=TARGET_USER_EMAIL,
            defaults={"first_name": "Demo", "last_name": "User"},
        )
        if created:
            user.set_password("testpass123")
            user.save()
        self.stdout.write(
            self.style.WARNING(
                f"No user with id={TARGET_USER_ID} was found, so a user "
                f"with email '{TARGET_USER_EMAIL}' was "
                f"{'created' if created else 'reused'} instead "
                f"(actual id={user.id}, password: testpass123 if newly "
                "created). Create/import the real user first if you need "
                "the id to match exactly."
            )
        )
        return user

    # ------------------------------------------------------------------
    # ShowTheme
    # ------------------------------------------------------------------
    def _seed_show_themes(self):
        names = ["Stars & Constellations", "Planets of the Solar System"]
        themes = []
        for name in names:
            theme, created = ShowTheme.objects.get_or_create(name=name)
            self._log(ShowTheme, theme, created)
            themes.append(theme)
        return themes

    # ------------------------------------------------------------------
    # AstronomyShow
    # ------------------------------------------------------------------
    def _seed_astronomy_shows(self, themes):
        data = [
            {
                "title": "Journey Through the Milky Way",
                "description": (
                    "A guided tour across our home galaxy, from the "
                    "core to the outer spiral arms."
                ),
                "themes": [themes[0]],
            },
            {
                "title": "Wonders of the Solar System",
                "description": (
                    "An up-close look at the planets, moons, and "
                    "asteroids that share our sun."
                ),
                "themes": [themes[1]],
            },
        ]
        shows = []
        for item in data:
            show, created = AstronomyShow.objects.get_or_create(
                title=item["title"],
                defaults={"description": item["description"]},
            )
            if created:
                show.theme.set(item["themes"])
            self._log(AstronomyShow, show, created)
            shows.append(show)
        return shows

    # ------------------------------------------------------------------
    # PlanetariumDome
    # ------------------------------------------------------------------
    def _seed_planetarium_domes(self):
        data = [
            {"name": "Main Dome", "rows": 10, "seats_in_row": 15},
            {"name": "Small Dome", "rows": 5, "seats_in_row": 8},
        ]
        domes = []
        for item in data:
            dome, created = PlanetariumDome.objects.get_or_create(
                name=item["name"],
                defaults={
                    "rows": item["rows"],
                    "seats_in_row": item["seats_in_row"],
                },
            )
            self._log(PlanetariumDome, dome, created)
            domes.append(dome)
        return domes

    # ------------------------------------------------------------------
    # ShowSession
    # ------------------------------------------------------------------
    def _seed_show_sessions(self, shows, domes):
        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        data = [
            {
                "astronomy_show": shows[0],
                "planetarium_dome": domes[0],
                "show_time": now + timedelta(days=3, hours=2),
            },
            {
                "astronomy_show": shows[1],
                "planetarium_dome": domes[1],
                "show_time": now + timedelta(days=5, hours=5),
            },
        ]
        sessions = []
        for item in data:
            session, created = ShowSession.objects.get_or_create(
                astronomy_show=item["astronomy_show"],
                planetarium_dome=item["planetarium_dome"],
                show_time=item["show_time"],
            )
            self._log(ShowSession, session, created)
            sessions.append(session)
        return sessions

    # ------------------------------------------------------------------
    # Reservation + Ticket
    # ------------------------------------------------------------------
    def _seed_reservations(self, user, sessions):
        if Reservation.objects.filter(user=user).exists():
            self.stdout.write(
                f"User id={user.id} already has reservations - "
                "skipping reservation/ticket seeding."
            )
            return

        seat_pairs = [(1, 1), (1, 2)]
        for session in sessions:
            reservation = Reservation.objects.create(user=user)
            self._log(Reservation, reservation, True)
            for row, seat in seat_pairs:
                ticket = Ticket.objects.create(
                    row=row,
                    seat=seat,
                    show_session=session,
                    reservation=reservation,
                )
                self._log(Ticket, ticket, True)

    # ------------------------------------------------------------------
    def _log(self, model, instance, created):
        verb = "Created" if created else "Reused"
        self.stdout.write(f"  {verb} {model.__name__}: {instance}")
