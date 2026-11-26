from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import District, HeritageCategory, HeritageSite, PreservationTag


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
