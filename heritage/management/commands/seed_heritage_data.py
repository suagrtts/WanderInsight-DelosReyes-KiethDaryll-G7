from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from heritage.models import (
    District,
    HeritageCategory,
    HeritageSite,
    PreservationTag,
    VisitationLog,
)


class Command(BaseCommand):
    help = "Idempotently seed WanderInsight PD2 test accounts, Cebu heritage sites, and daily visitation logs."

    @transaction.atomic
    def handle(self, *args, **options):
        # 1. Seed PD2 Test Accounts (one per role + secondary curator for ownership isolation)
        accounts_spec = [
            {
                "username": "admin_pd2",
                "email": "admin.pd2@wanderinsight.ph",
                "password": "WanderAdmin#2026",
                "role": User.Role.ADMIN,
                "first_name": "Kieth Daryll",
                "last_name": "Delos Reyes",
                "organization": "WanderInsight System Governance",
                "contact_number": "+63 917 800 1001",
                "bio": "Platform administrator overseeing Cebu cultural heritage registries and RBAC governance.",
                "is_superuser": True,
                "is_staff": True,
            },
            {
                "username": "curator_pd2",
                "email": "curator.pd2@wanderinsight.ph",
                "password": "WanderCurator#2026",
                "role": User.Role.CURATOR,
                "first_name": "Maria Clara",
                "last_name": "Santos",
                "organization": "Cebu City Cultural & Historical Affairs Office",
                "contact_number": "+63 917 800 2002",
                "bio": "Lead heritage curator managing downtown and Parian colonial landmarks.",
                "is_superuser": False,
                "is_staff": False,
            },
            {
                "username": "curator_south",
                "email": "south.pd2@wanderinsight.ph",
                "password": "WanderCurator#2026",
                "role": User.Role.CURATOR,
                "first_name": "Carlos",
                "last_name": "Mendoza",
                "organization": "Southern Cebu & Mactan Heritage Council",
                "contact_number": "+63 917 800 2003",
                "bio": "Regional curator assigned to Southern Cebu coastal churches and Mactan shrines.",
                "is_superuser": False,
                "is_staff": False,
            },
            {
                "username": "viewer_pd2",
                "email": "viewer.pd2@wanderinsight.ph",
                "password": "WanderViewer#2026",
                "role": User.Role.VIEWER,
                "first_name": "Elena",
                "last_name": "Villanueva",
                "organization": "CIT-U Cultural Research Fellowship",
                "contact_number": "+63 917 800 3003",
                "bio": "Cultural tourism researcher analyzing Cebu landmark foot traffic and visitor demographics.",
                "is_superuser": False,
                "is_staff": False,
            },
        ]

        users = {}
        for spec in accounts_spec:
            pwd = spec.pop("password")
            user, _ = User.objects.update_or_create(username=spec["username"], defaults=spec)
            user.set_password(pwd)
            user.save()
            users[user.username] = user

        # 2. Seed Districts
        districts_spec = [
            (
                "Old Downtown Cebu",
                District.Zone.METRO_CEBU,
                "Historic Spanish colonial port core surrounding Plaza Independencia and Basilica Santo Niño.",
            ),
            (
                "Parian & Uptown Heritage District",
                District.Zone.METRO_CEBU,
                "19th-century ancestral residences, provincial museums, and civic heritage avenues.",
            ),
            (
                "Mactan Historic Island",
                District.Zone.MACTAN_ISLANDS,
                "Coastal shrines and commemorative sites in Lapu-Lapu City.",
            ),
            (
                "Southern Cebu Coastal Corridor",
                District.Zone.SOUTH_CEBU,
                "Coral-stone colonial churches, watchtowers, and coastal heritage towns along southeastern Cebu.",
            ),
        ]
        districts = {}
        for name, zone, desc in districts_spec:
            dist, _ = District.objects.update_or_create(
                name=name,
                defaults={"zone": zone, "description": desc},
            )
            districts[name] = dist

        # 3. Seed Categories
        categories_spec = [
            ("COLONIAL_CHURCH", "Spanish Colonial Church", "Historic churches, basilicas, and convents."),
            ("FORTIFICATION", "Colonial Fortification", "Defensive bastions, forts, and coastal watchtowers."),
            ("ANCESTRAL_MUSEUM", "Ancestral House & Museum", "Preserved residential heritage houses and galleries."),
            ("SHRINE_MONUMENT", "Historical Shrine & Monument", "National shrines and commemorative plazas."),
            ("CIVIC_ARCHIVE", "Civic & Provincial Landmark", "Historic public institutions converted into archives."),
        ]
        categories = {}
        for code, name, desc in categories_spec:
            cat, _ = HeritageCategory.objects.update_or_create(
                code=code,
                defaults={"name": name, "description": desc},
            )
            categories[code] = cat

        # 4. Seed Preservation Tags (ManyToMany)
        tags_spec = [
            ("NHCP_LANDMARK", "NHCP National Historical Landmark"),
            ("NATIONAL_TREASURE", "National Cultural Treasure"),
            ("GUIDED_ARCHIVE", "Curated Audio & Archival Guide"),
            ("STRUCTURAL_RETROFIT", "Post-Earthquake Structural Retrofit"),
            ("WHEELCHAIR_ACCESS", "Barrier-Free Visitor Access"),
            ("CROWD_MONITORED", "Daily Conservation Capacity Monitored"),
        ]
        tags = {}
        for code, name in tags_spec:
            tag, _ = PreservationTag.objects.update_or_create(code=code, defaults={"name": name})
            tags[code] = tag

        # 5. Seed Heritage Sites
        sites_spec = [
            {
                "name": "Basilica Minore del Santo Niño de Cebu",
                "district": districts["Old Downtown Cebu"],
                "category": categories["COLONIAL_CHURCH"],
                "created_by": users["curator_pd2"],
                "municipality": "Cebu City",
                "established_year": 1565,
                "latitude": Decimal("10.29420"),
                "longitude": Decimal("123.90210"),
                "preservation_status": HeritageSite.PreservationStatus.WELL_PRESERVED,
                "daily_capacity": 3500,
                "entry_fee": Decimal("0.00"),
                "custodian_organization": "Order of Saint Augustine – Province of Santo Niño de Cebu",
                "historical_overview": (
                    "Founded in 1565, the Basilica Minore del Santo Niño is the oldest Roman Catholic church "
                    "in the Philippines. Built with hewn coral stone, its pilgrim courtyard and museum preserve "
                    "four centuries of religious artistry and Sinulog liturgical heritage."
                ),
                "tags": ["NATIONAL_TREASURE", "NHCP_LANDMARK", "STRUCTURAL_RETROFIT", "CROWD_MONITORED"],
                "base_counts": (620, 390, 175),
            },
            {
                "name": "Fuerza de San Pedro",
                "district": districts["Old Downtown Cebu"],
                "category": categories["FORTIFICATION"],
                "created_by": users["curator_pd2"],
                "municipality": "Cebu City",
                "established_year": 1565,
                "latitude": Decimal("10.29250"),
                "longitude": Decimal("123.90580"),
                "preservation_status": HeritageSite.PreservationStatus.WELL_PRESERVED,
                "daily_capacity": 900,
                "entry_fee": Decimal("30.00"),
                "custodian_organization": "Cebu City Tourism & Heritage Office",
                "historical_overview": (
                    "A triangular coral-stone military defence structure facing Cebu Harbor, featuring three "
                    "bastions—La Concepcion, Ignacio de Loyola, and San Miguel—and archival galleries of Spanish "
                    "maritime cartography."
                ),
                "tags": ["NHCP_LANDMARK", "GUIDED_ARCHIVE", "WHEELCHAIR_ACCESS"],
                "base_counts": (280, 210, 145),
            },
            {
                "name": "Casa Gorordo Museum",
                "district": districts["Parian & Uptown Heritage District"],
                "category": categories["ANCESTRAL_MUSEUM"],
                "created_by": users["curator_pd2"],
                "municipality": "Cebu City",
                "established_year": 1850,
                "latitude": Decimal("10.29830"),
                "longitude": Decimal("123.90460"),
                "preservation_status": HeritageSite.PreservationStatus.WELL_PRESERVED,
                "daily_capacity": 280,
                "entry_fee": Decimal("120.00"),
                "custodian_organization": "Ramon Aboitiz Foundation Inc. (RAFI)",
                "historical_overview": (
                    "Mid-19th-century balay na tisa residence in historic Parian showcasing molave joinery, "
                    "capiz shell windows, period decorative arts, and interactive digital heritage interpretation."
                ),
                "tags": ["NHCP_LANDMARK", "GUIDED_ARCHIVE", "CROWD_MONITORED"],
                "base_counts": (95, 78, 62),
            },
            {
                "name": "Museo Sugbo",
                "district": districts["Parian & Uptown Heritage District"],
                "category": categories["CIVIC_ARCHIVE"],
                "created_by": users["curator_pd2"],
                "municipality": "Cebu City",
                "established_year": 1871,
                "latitude": Decimal("10.30370"),
                "longitude": Decimal("123.90650"),
                "preservation_status": HeritageSite.PreservationStatus.RESTORATION_ONGOING,
                "daily_capacity": 450,
                "entry_fee": Decimal("75.00"),
                "custodian_organization": "Cebu Provincial Government Museum Division",
                "historical_overview": (
                    "Designed in 1869 by Domingo de Escondrillas as the Carcel de Cebu using coral blocks, "
                    "now serving as the Cebu Provincial Museum housing pre-colonial gold, trade ceramics, and press archives."
                ),
                "tags": ["NHCP_LANDMARK", "STRUCTURAL_RETROFIT", "GUIDED_ARCHIVE"],
                "base_counts": (150, 105, 58),
            },
            {
                "name": "Mactan Liberty Shrine",
                "district": districts["Mactan Historic Island"],
                "category": categories["SHRINE_MONUMENT"],
                "created_by": users["curator_south"],
                "municipality": "Lapu-Lapu City",
                "established_year": 1969,
                "latitude": Decimal("10.31110"),
                "longitude": Decimal("124.01520"),
                "preservation_status": HeritageSite.PreservationStatus.WELL_PRESERVED,
                "daily_capacity": 1200,
                "entry_fee": Decimal("0.00"),
                "custodian_organization": "Lapu-Lapu City Cultural & Tourism Council",
                "historical_overview": (
                    "Bayfront national shrine commemorating the 1521 Battle of Mactan and Datu Lapulapu's "
                    "resistance, overlooking Magellan Bay with open civic grounds and interpretive plaques."
                ),
                "tags": ["NHCP_LANDMARK", "WHEELCHAIR_ACCESS", "CROWD_MONITORED"],
                "base_counts": (310, 265, 190),
            },
            {
                "name": "Patrocinio de Maria Parish Church of Boljoon",
                "district": districts["Southern Cebu Coastal Corridor"],
                "category": categories["COLONIAL_CHURCH"],
                "created_by": users["curator_south"],
                "municipality": "Boljoon",
                "established_year": 1783,
                "latitude": Decimal("9.63310"),
                "longitude": Decimal("123.48320"),
                "preservation_status": HeritageSite.PreservationStatus.RESTORATION_ONGOING,
                "daily_capacity": 600,
                "entry_fee": Decimal("0.00"),
                "custodian_organization": "Archdiocese of Cebu Commission on Cultural Heritage",
                "historical_overview": (
                    "Fortress-like seaside Rococo coral-stone church complex complete with an intact convent, "
                    "stone blockhouse watchtower, cemetery gates, and polychrome retablos."
                ),
                "tags": ["NATIONAL_TREASURE", "NHCP_LANDMARK", "STRUCTURAL_RETROFIT"],
                "base_counts": (140, 118, 54),
            },
        ]

        today = timezone.localdate()
        weathers = [
            VisitationLog.WeatherCondition.SUNNY,
            VisitationLog.WeatherCondition.PARTLY_CLOUDY,
            VisitationLog.WeatherCondition.SUNNY,
            VisitationLog.WeatherCondition.OVERCAST,
            VisitationLog.WeatherCondition.RAINY,
            VisitationLog.WeatherCondition.PARTLY_CLOUDY,
        ]
        month_multipliers = [0.82, 0.88, 0.94, 1.02, 1.09, 1.16]
        day_offsets = [155, 124, 93, 62, 32, 4]

        log_total_created = 0
        for idx, spec in enumerate(sites_spec):
            tag_codes = spec.pop("tags")
            base_local, base_dom, base_for = spec.pop("base_counts")
            site, _ = HeritageSite.objects.update_or_create(
                name=spec["name"],
                district=spec["district"],
                defaults={**spec, "is_published": True},
            )
            site.preservation_tags.set([tags[c] for c in tag_codes])

            for m_idx, days_back in enumerate(day_offsets):
                visit_dt = today - timedelta(days=days_back + idx)
                mult = month_multipliers[m_idx]
                loc = max(12, int(round(base_local * mult)))
                dom = max(8, int(round(base_dom * mult)))
                frn = max(5, int(round(base_for * mult)))
                tot = loc + dom + frn
                weather = weathers[(m_idx + idx) % len(weathers)]
                VisitationLog.objects.update_or_create(
                    site=site,
                    visit_date=visit_dt,
                    defaults={
                        "recorded_by": site.created_by,
                        "local_visitors": loc,
                        "domestic_visitors": dom,
                        "foreign_visitors": frn,
                        "total_visitors": tot,
                        "weather_condition": weather,
                        "special_event": "Weekend Heritage Guided Walk" if m_idx % 2 == 1 else "",
                        "remarks": "Verified gate counter tally aligned with BR-01 demographic audit.",
                    },
                )
                log_total_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(users)} users, {len(districts)} districts, {len(categories)} categories, "
                f"{len(tags)} tags, {len(sites_spec)} heritage sites, and {log_total_created} visitation logs."
            )
        )
