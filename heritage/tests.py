from datetime import timedelta
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .models import District, HeritageCategory, HeritageSite, PreservationTag, VisitationLog


class HeritageSiteRegistryTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_gov",
            email="admin@wanderinsight.ph",
            password="StrongPassword123!",
            role=User.Role.ADMIN,
        )
        self.curator_a = User.objects.create_user(
            username="curator_ana",
            email="ana@wanderinsight.ph",
            password="StrongPassword123!",
            role=User.Role.CURATOR,
            first_name="Ana",
            last_name="Reyes",
        )
        self.curator_b = User.objects.create_user(
            username="curator_ben",
            email="ben@wanderinsight.ph",
            password="StrongPassword123!",
            role=User.Role.CURATOR,
            first_name="Ben",
            last_name="Cruz",
        )
        self.viewer = User.objects.create_user(
            username="viewer_user",
            email="viewer@wanderinsight.ph",
            password="StrongPassword123!",
            role=User.Role.VIEWER,
        )

        self.district = District.objects.create(
            name="Old Downtown Cebu",
            zone=District.Zone.METRO_CEBU,
            description="Historic colonial core of Cebu City.",
        )
        self.category = HeritageCategory.objects.create(
            code="FORTIFICATION",
            name="Colonial Fortification",
            description="Spanish-era defensive structures and bastions.",
        )
        self.tag_nhcp = PreservationTag.objects.create(
            code="NHCP_LANDMARK",
            name="NHCP National Historical Landmark",
        )

        self.site_a = HeritageSite.objects.create(
            name="Fuerza de San Pedro",
            district=self.district,
            category=self.category,
            created_by=self.curator_a,
            municipality="Cebu City",
            established_year=1565,
            latitude=Decimal("10.29250"),
            longitude=Decimal("123.90580"),
            preservation_status=HeritageSite.PreservationStatus.WELL_PRESERVED,
            daily_capacity=800,
            entry_fee=Decimal("30.00"),
            custodian_organization="Cebu City Tourism Commission",
            historical_overview="Triangular bastion fort founded under Miguel Lopez de Legazpi overlooking Cebu harbor.",
            is_published=True,
        )
        self.site_a.preservation_tags.add(self.tag_nhcp)

    def test_anonymous_users_redirected_to_login(self):
        for url in [
            reverse("heritage:site_list"),
            reverse("heritage:site_create"),
            reverse("heritage:site_detail", args=[self.site_a.slug]),
        ]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            self.assertIn(reverse("accounts:login"), resp.url)

    def test_viewer_can_browse_published_sites_but_cannot_mutate(self):
        self.client.login(username="viewer_user", password="StrongPassword123!")
        list_resp = self.client.get(reverse("heritage:site_list"))
        self.assertEqual(list_resp.status_code, 200)
        self.assertContains(list_resp, "Fuerza de San Pedro")

        create_resp = self.client.get(reverse("heritage:site_create"))
        self.assertEqual(create_resp.status_code, 302)
        edit_resp = self.client.get(reverse("heritage:site_update", args=[self.site_a.slug]))
        self.assertEqual(edit_resp.status_code, 302)
        del_resp = self.client.post(reverse("heritage:site_delete", args=[self.site_a.slug]))
        self.assertEqual(del_resp.status_code, 302)
        self.assertTrue(HeritageSite.objects.filter(pk=self.site_a.pk).exists())

    def test_curator_can_create_edit_and_delete_own_site_with_m2m_tags(self):
        self.client.login(username="curator_ana", password="StrongPassword123!")
        resp = self.client.post(
            reverse("heritage:site_create"),
            {
                "name": "Casa Gorordo Museum",
                "district": self.district.id,
                "category": self.category.id,
                "municipality": "Cebu City",
                "established_year": 1850,
                "preservation_status": HeritageSite.PreservationStatus.WELL_PRESERVED,
                "latitude": "10.29830",
                "longitude": "123.90460",
                "daily_capacity": 250,
                "entry_fee": "120.00",
                "custodian_organization": "Ramon Aboitiz Foundation Inc.",
                "preservation_tags": [self.tag_nhcp.id],
                "historical_overview": "Mid-19th century balay na tisa lifestyle museum in the Parian district.",
                "is_published": "on",
            },
        )
        self.assertEqual(resp.status_code, 302)
        created = HeritageSite.objects.get(name="Casa Gorordo Museum")
        self.assertEqual(created.created_by, self.curator_a)
        self.assertIn(self.tag_nhcp, created.preservation_tags.all())

        # Update own site
        edit_resp = self.client.post(
            reverse("heritage:site_update", args=[created.slug]),
            {
                "name": "Casa Gorordo Museum",
                "district": self.district.id,
                "category": self.category.id,
                "municipality": "Cebu City",
                "established_year": 1850,
                "preservation_status": HeritageSite.PreservationStatus.RESTORATION_ONGOING,
                "latitude": "10.29830",
                "longitude": "123.90460",
                "daily_capacity": 300,
                "entry_fee": "120.00",
                "custodian_organization": "Ramon Aboitiz Foundation Inc.",
                "preservation_tags": [self.tag_nhcp.id],
                "historical_overview": "Mid-19th century balay na tisa lifestyle museum in the Parian district.",
                "is_published": "on",
            },
        )
        self.assertEqual(edit_resp.status_code, 302)
        created.refresh_from_db()
        self.assertEqual(created.daily_capacity, 300)

        # Delete own site
        del_resp = self.client.post(reverse("heritage:site_delete", args=[created.slug]))
        self.assertEqual(del_resp.status_code, 302)
        self.assertFalse(HeritageSite.objects.filter(pk=created.pk).exists())

    def test_curator_cannot_edit_or_delete_other_curators_site(self):
        self.client.login(username="curator_ben", password="StrongPassword123!")
        edit_resp = self.client.post(
            reverse("heritage:site_update", args=[self.site_a.slug]),
            {"name": "Tampered Name"},
        )
        self.assertRedirects(edit_resp, reverse("heritage:site_detail", args=[self.site_a.slug]))
        self.site_a.refresh_from_db()
        self.assertEqual(self.site_a.name, "Fuerza de San Pedro")

        del_resp = self.client.post(reverse("heritage:site_delete", args=[self.site_a.slug]))
        self.assertRedirects(del_resp, reverse("heritage:site_detail", args=[self.site_a.slug]))
        self.assertTrue(HeritageSite.objects.filter(pk=self.site_a.pk).exists())

    def test_unpublished_draft_hidden_from_other_curators_and_viewers(self):
        self.site_a.is_published = False
        self.site_a.save()

        self.client.login(username="curator_ben", password="StrongPassword123!")
        resp = self.client.get(reverse("heritage:site_detail", args=[self.site_a.slug]))
        self.assertRedirects(resp, reverse("heritage:site_list"))

        self.client.login(username="admin_gov", password="StrongPassword123!")
        admin_resp = self.client.get(reverse("heritage:site_detail", args=[self.site_a.slug]))
        self.assertEqual(admin_resp.status_code, 200)

    def test_site_validation_rejects_out_of_bounds_coordinates_and_duplicate_name(self):
        self.client.login(username="curator_ana", password="StrongPassword123!")
        resp = self.client.post(
            reverse("heritage:site_create"),
            {
                "name": "Fuerza de San Pedro",  # duplicate in same district
                "district": self.district.id,
                "category": self.category.id,
                "municipality": "Cebu City",
                "established_year": 1400,  # invalid (< 1500)
                "preservation_status": HeritageSite.PreservationStatus.WELL_PRESERVED,
                "latitude": "14.59950",  # Manila, outside Cebu bounds
                "longitude": "120.98420",
                "daily_capacity": 5,
                "entry_fee": "0.00",
                "historical_overview": "Too short",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "already registered")
        self.assertContains(resp, "Cebu province bounds")
        self.assertContains(resp, "at least 30 characters")



class VisitationLogVerticalSliceTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_gov",
            email="admin@wanderinsight.ph",
            password="StrongPassword123!",
            role=User.Role.ADMIN,
        )
        self.curator_a = User.objects.create_user(
            username="curator_ana",
            email="ana@wanderinsight.ph",
            password="StrongPassword123!",
            role=User.Role.CURATOR,
        )
        self.curator_b = User.objects.create_user(
            username="curator_ben",
            email="ben@wanderinsight.ph",
            password="StrongPassword123!",
            role=User.Role.CURATOR,
        )
        self.viewer = User.objects.create_user(
            username="viewer_user",
            email="viewer@wanderinsight.ph",
            password="StrongPassword123!",
            role=User.Role.VIEWER,
        )

        self.district = District.objects.create(
            name="Old Downtown Cebu",
            zone=District.Zone.METRO_CEBU,
        )
        self.category = HeritageCategory.objects.create(
            code="COLONIAL_CHURCH",
            name="Spanish Colonial Church",
        )
        self.site_a = HeritageSite.objects.create(
            name="Basilica Minore del Santo Niño",
            district=self.district,
            category=self.category,
            created_by=self.curator_a,
            municipality="Cebu City",
            established_year=1565,
            latitude=Decimal("10.29420"),
            longitude=Decimal("123.90210"),
            daily_capacity=3000,
            entry_fee=Decimal("0.00"),
            historical_overview="Oldest Roman Catholic church in the Philippines built with coral stone.",
        )
        self.site_b = HeritageSite.objects.create(
            name="Mactan Liberty Shrine",
            district=self.district,
            category=self.category,
            created_by=self.curator_b,
            municipality="Lapu-Lapu City",
            established_year=1969,
            latitude=Decimal("10.31110"),
            longitude=Decimal("124.01520"),
            daily_capacity=1200,
            entry_fee=Decimal("0.00"),
            historical_overview="Bayfront historical shrine commemorating the 1521 Battle of Mactan.",
        )
        self.today = timezone.localdate()

    def test_curator_full_visitation_log_crud_and_live_dashboard_metrics(self):
        self.client.login(username="curator_ana", password="StrongPassword123!")
        create_resp = self.client.post(
            reverse("heritage:site_log_create", args=[self.site_a.slug]),
            {
                "site": self.site_a.id,
                "visit_date": self.today.isoformat(),
                "local_visitors": 200,
                "domestic_visitors": 120,
                "foreign_visitors": 80,
                "total_visitors": 400,
                "weather_condition": VisitationLog.WeatherCondition.SUNNY,
                "special_event": "Heritage Guided Tour",
                "remarks": "Smooth visitor flow.",
            },
        )
        self.assertRedirects(create_resp, reverse("heritage:site_detail", args=[self.site_a.slug]))
        log = VisitationLog.objects.get(site=self.site_a, visit_date=self.today)
        self.assertEqual(log.recorded_by, self.curator_a)
        self.assertEqual(log.total_visitors, 400)

        # Dashboard reflects SQL SUM()
        dash_resp = self.client.get(reverse("accounts:curator_dashboard"))
        self.assertEqual(dash_resp.status_code, 200)
        self.assertEqual(dash_resp.context["analytics"]["total_visitors"], 400)

        # Update log
        upd_resp = self.client.post(
            reverse("heritage:log_update", args=[log.pk]),
            {
                "site": self.site_a.id,
                "visit_date": self.today.isoformat(),
                "local_visitors": 250,
                "domestic_visitors": 150,
                "foreign_visitors": 100,
                "total_visitors": 500,
                "weather_condition": VisitationLog.WeatherCondition.PARTLY_CLOUDY,
                "special_event": "Updated Tour",
                "remarks": "Afternoon surge.",
            },
        )
        self.assertRedirects(upd_resp, reverse("heritage:site_detail", args=[self.site_a.slug]))
        log.refresh_from_db()
        self.assertEqual(log.total_visitors, 500)

        # Delete log
        del_resp = self.client.post(reverse("heritage:log_delete", args=[log.pk]))
        self.assertRedirects(del_resp, reverse("heritage:site_detail", args=[self.site_a.slug]))
        self.assertFalse(VisitationLog.objects.filter(pk=log.pk).exists())

    def test_br01_demographic_sum_mismatch_and_future_date_rejected(self):
        self.client.login(username="curator_ana", password="StrongPassword123!")
        future_day = (self.today + timedelta(days=2)).isoformat()
        resp = self.client.post(
            reverse("heritage:log_create"),
            {
                "site": self.site_a.id,
                "visit_date": future_day,
                "local_visitors": 100,
                "domestic_visitors": 50,
                "foreign_visitors": 25,
                "total_visitors": 999,  # violates BR-01 (175 != 999)
                "weather_condition": VisitationLog.WeatherCondition.SUNNY,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Demographic sum mismatch (BR-01)")
        self.assertContains(resp, "cannot be in the future")
        self.assertEqual(VisitationLog.objects.count(), 0)

    def test_br04_duplicate_site_and_date_rejected(self):
        VisitationLog.objects.create(
            site=self.site_a,
            recorded_by=self.curator_a,
            visit_date=self.today,
            local_visitors=50,
            domestic_visitors=30,
            foreign_visitors=20,
            total_visitors=100,
        )
        self.client.login(username="curator_ana", password="StrongPassword123!")
        resp = self.client.post(
            reverse("heritage:log_create"),
            {
                "site": self.site_a.id,
                "visit_date": self.today.isoformat(),
                "local_visitors": 60,
                "domestic_visitors": 20,
                "foreign_visitors": 20,
                "total_visitors": 100,
                "weather_condition": VisitationLog.WeatherCondition.SUNNY,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "already exists (BR-04)")
        self.assertEqual(VisitationLog.objects.count(), 1)

    def test_curator_isolation_on_visitation_logs_and_admin_override(self):
        log_a = VisitationLog.objects.create(
            site=self.site_a,
            recorded_by=self.curator_a,
            visit_date=self.today,
            local_visitors=100,
            domestic_visitors=50,
            foreign_visitors=30,
            total_visitors=180,
        )
        self.client.login(username="curator_ben", password="StrongPassword123!")
        # Curator Ben does not see Curator Ana's log in his log_list
        list_resp = self.client.get(reverse("heritage:log_list"))
        self.assertNotContains(list_resp, "Basilica Minore del Santo Niño")

        # Curator Ben cannot edit or delete Curator Ana's log
        edit_resp = self.client.post(reverse("heritage:log_update", args=[log_a.pk]))
        self.assertRedirects(edit_resp, reverse("heritage:site_detail", args=[self.site_a.slug]))
        del_resp = self.client.post(reverse("heritage:log_delete", args=[log_a.pk]))
        self.assertRedirects(del_resp, reverse("heritage:site_detail", args=[self.site_a.slug]))
        self.assertTrue(VisitationLog.objects.filter(pk=log_a.pk).exists())

        # Viewer cannot open log_list or log_create
        self.client.login(username="viewer_user", password="StrongPassword123!")
        self.assertEqual(self.client.get(reverse("heritage:log_list")).status_code, 302)
        self.assertEqual(self.client.get(reverse("heritage:log_create")).status_code, 302)

        # Admin sees all logs across curators
        self.client.login(username="admin_gov", password="StrongPassword123!")
        admin_list = self.client.get(reverse("heritage:log_list"))
        self.assertContains(admin_list, "Basilica Minore del Santo Niño")

    def test_seed_heritage_data_command_is_idempotent(self):
        call_command("seed_heritage_data")
        call_command("seed_heritage_data")
        self.assertGreaterEqual(HeritageSite.objects.count(), 6)
        self.assertGreaterEqual(VisitationLog.objects.count(), 36)


    def test_log_list_handles_malformed_and_inverted_date_filters_gracefully(self):
        self.client.login(username="curator_ana", password="StrongPassword123!")
        resp_bad = self.client.get(reverse("heritage:log_list") + "?date_from=notadate&date_to=99-99-99")
        self.assertEqual(resp_bad.status_code, 200)
        self.assertContains(resp_bad, "Invalid")

        resp_inv = self.client.get(reverse("heritage:log_list") + "?date_from=2026-12-01&date_to=2026-01-01")
        self.assertEqual(resp_inv.status_code, 200)
        self.assertContains(resp_inv, "Start date cannot be later than end date")

    def test_visitation_log_rejects_unrealistically_old_visit_date(self):
        self.client.login(username="curator_ana", password="StrongPassword123!")
        resp = self.client.post(
            reverse("heritage:log_create"),
            {
                "site": self.site_a.id,
                "visit_date": "1800-01-01",
                "local_visitors": 10,
                "domestic_visitors": 0,
                "foreign_visitors": 0,
                "total_visitors": 10,
                "weather_condition": VisitationLog.WeatherCondition.SUNNY,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "cannot be earlier than")
        self.assertEqual(VisitationLog.objects.count(), 0)

    def test_log_update_emits_capacity_warning(self):
        log = VisitationLog.objects.create(
            site=self.site_a,
            recorded_by=self.curator_a,
            visit_date=self.today,
            local_visitors=100,
            domestic_visitors=0,
            foreign_visitors=0,
            total_visitors=100,
        )
        self.client.login(username="curator_ana", password="StrongPassword123!")
        resp = self.client.post(
            reverse("heritage:log_update", args=[log.pk]),
            {
                "site": self.site_a.id,
                "visit_date": self.today.isoformat(),
                "local_visitors": 4000,
                "domestic_visitors": 0,
                "foreign_visitors": 0,
                "total_visitors": 4000,
                "weather_condition": VisitationLog.WeatherCondition.SUNNY,
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "exceeding")

    def test_curator_dashboard_shows_empty_state_when_zero_logs(self):
        self.client.login(username="curator_ana", password="StrongPassword123!")
        resp = self.client.get(reverse("accounts:curator_dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No visitation logs recorded for your landmarks yet")
        self.assertNotContains(resp, "Sample Baseline")
