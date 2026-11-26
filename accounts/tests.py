from django.test import TestCase
from django.urls import reverse

from .models import User

PASSWORD = "Heritage#2026pass"


def make_user(username, role, **extra):
    return User.objects.create_user(
        username=username, email=f"{username}@example.com", password=PASSWORD, role=role, **extra
    )


class RegistrationTests(TestCase):
    def payload(self, **overrides):
        data = {
            "username": "newcurator",
            "first_name": "Juan",
            "last_name": "Dela Cruz",
            "email": "juan@example.com",
            "role": User.Role.CURATOR,
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        data.update(overrides)
        return data

    def test_register_success_hashes_password(self):
        resp = self.client.post(reverse("accounts:register"), self.payload(), follow=True)
        self.assertRedirects(resp, reverse("accounts:login"))
        self.assertContains(resp, "Account created successfully")
        user = User.objects.get(username="newcurator")
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(user.role, User.Role.CURATOR)

    def test_password_mismatch(self):
        resp = self.client.post(reverse("accounts:register"), self.payload(password2="different#2026"))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username="newcurator").exists())
        self.assertContains(resp, "didn")  # "The two password fields didn't match."

    def test_invalid_email(self):
        resp = self.client.post(reverse("accounts:register"), self.payload(email="not-an-email"))
        self.assertContains(resp, "Enter a valid email address")

    def test_duplicate_username_and_email(self):
        make_user("taken", User.Role.VIEWER)
        resp = self.client.post(
            reverse("accounts:register"), self.payload(username="taken", email="TAKEN@example.com")
        )
        self.assertContains(resp, "A user with that username already exists")
        self.assertContains(resp, "An account with this email already exists")

    def test_required_fields(self):
        resp = self.client.post(reverse("accounts:register"), {})
        self.assertContains(resp, "This field is required")
        self.assertEqual(User.objects.count(), 0)

    def test_cannot_self_register_as_admin(self):
        self.client.post(reverse("accounts:register"), self.payload(role=User.Role.ADMIN))
        self.assertFalse(User.objects.filter(username="newcurator").exists())


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = make_user("viewer1", User.Role.VIEWER)

    def test_invalid_credentials_show_error(self):
        resp = self.client.post(reverse("accounts:login"), {"username": "viewer1", "password": "wrong"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Invalid username or password")

    def test_login_redirects_to_role_dashboard(self):
        resp = self.client.post(reverse("accounts:login"), {"username": "viewer1", "password": PASSWORD}, follow=True)
        self.assertRedirects(resp, reverse("accounts:viewer_dashboard"))

    def test_logout_ends_session(self):
        self.client.login(username="viewer1", password=PASSWORD)
        self.client.post(reverse("accounts:logout"))
        resp = self.client.get(reverse("accounts:profile"))
        self.assertRedirects(resp, f"{reverse('accounts:login')}?next={reverse('accounts:profile')}")


class RoleAccessTests(TestCase):
    def setUp(self):
        self.admin = make_user("admin1", User.Role.ADMIN)
        self.curator = make_user("curator1", User.Role.CURATOR)
        self.viewer = make_user("viewer1", User.Role.VIEWER)
        self.urls = {
            User.Role.ADMIN: reverse("accounts:admin_dashboard"),
            User.Role.CURATOR: reverse("accounts:curator_dashboard"),
            User.Role.VIEWER: reverse("accounts:viewer_dashboard"),
        }

    def test_anonymous_redirected_to_login(self):
        for url in list(self.urls.values()) + [reverse("accounts:profile"), reverse("accounts:profile_edit")]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            self.assertTrue(resp.url.startswith(reverse("accounts:login")))

    def test_each_role_only_opens_own_dashboard(self):
        for user in (self.admin, self.curator, self.viewer):
            self.client.force_login(user)
            for role, url in self.urls.items():
                resp = self.client.get(url)
                if role == user.role:
                    self.assertEqual(resp.status_code, 200, f"{user} -> {url}")
                else:
                    self.assertRedirects(resp, reverse("accounts:dashboard"), fetch_redirect_response=False)
            self.client.logout()

    def test_admin_role_is_staff(self):
        self.assertTrue(self.admin.is_staff)
        self.assertFalse(self.curator.is_staff)


class ProfileTests(TestCase):
    def setUp(self):
        self.user = make_user("curator1", User.Role.CURATOR)
        self.other = make_user("curator2", User.Role.CURATOR)
        self.client.force_login(self.user)

    def test_view_own_profile(self):
        resp = self.client.get(reverse("accounts:profile"))
        self.assertContains(resp, "curator1@example.com")
        self.assertNotContains(resp, "curator2@example.com")

    def test_update_profile(self):
        resp = self.client.post(
            reverse("accounts:profile_edit"),
            {"first_name": "Maria", "last_name": "Santos", "email": "maria@example.com",
             "contact_number": "+63 912 345 6789", "organization": "Magellan's Cross", "bio": "Curator"},
            follow=True,
        )
        self.assertContains(resp, "Your profile has been updated")
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Maria")
        self.assertEqual(self.user.contact_number, "+63 912 345 6789")
        self.other.refresh_from_db()
        self.assertEqual(self.other.email, "curator2@example.com")

    def test_profile_email_must_be_unique(self):
        resp = self.client.post(
            reverse("accounts:profile_edit"),
            {"first_name": "A", "last_name": "B", "email": "curator2@example.com"},
        )
        self.assertContains(resp, "An account with this email already exists")


class AdminPortalStylingTests(TestCase):
    def setUp(self):
        self.admin = make_user("admin_portal", User.Role.ADMIN, is_superuser=True)
        self.curator = make_user("curator_portal", User.Role.CURATOR)
        self.viewer = make_user("viewer_portal", User.Role.VIEWER)

    def test_admin_login_renders_heritage_theme_and_3d_globe(self):
        resp = self.client.get(reverse("admin:login"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "admin-heritage.css")
        self.assertContains(resp, 'id="wi-three-canvas"')
        self.assertContains(resp, 'id="wi-bg-canvas"')
        self.assertContains(resp, 'data-ua="shield"')

    def test_admin_index_renders_kpis_charts_and_3d_globe(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("admin:index"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Cultural Heritage Governance Console")
        self.assertContains(resp, 'id="wi-three-canvas"')
        self.assertContains(resp, 'id="wi-visitation-chart"')
        self.assertContains(resp, 'id="wi-admin-role-chart"')
        self.assertEqual(resp.context["wi_admin_stats"]["total_users"], 3)
        self.assertEqual(resp.context["wi_admin_stats"]["admin_count"], 1)
        self.assertEqual(resp.context["wi_admin_stats"]["curator_count"], 1)
        self.assertEqual(resp.context["wi_admin_stats"]["viewer_count"], 1)

    def test_admin_user_changelist_renders_role_badges(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("admin:accounts_user_changelist"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "role-badge role-admin")
        self.assertContains(resp, "role-badge role-curator")
        self.assertContains(resp, "role-badge role-viewer")



class AuditHardeningTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        self.user = make_user("throttle_user", User.Role.VIEWER)

    def test_login_rate_limits_after_repeated_failures(self):
        url = reverse("accounts:login")
        for _ in range(10):
            resp = self.client.post(url, {"username": "throttle_user", "password": "wrong"})
            self.assertEqual(resp.status_code, 200)
        blocked = self.client.post(url, {"username": "throttle_user", "password": "wrong"})
        self.assertEqual(blocked.status_code, 429)
        self.assertContains(blocked, "Too many failed login attempts", status_code=429)

    def test_profile_photo_rejects_oversized_upload(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.force_login(self.user)
        big_file = SimpleUploadedFile(
            "huge.jpg",
            b"x" * (2 * 1024 * 1024 + 10),
            content_type="image/jpeg",
        )
        resp = self.client.post(
            reverse("accounts:profile_edit"),
            {
                "first_name": "Elena",
                "last_name": "V",
                "email": "throttle_user@example.com",
                "profile_photo": big_file,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["form"].errors.get("profile_photo"))
