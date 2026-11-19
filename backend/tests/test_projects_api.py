import uuid
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user
from app.core.permissions import PERMISSIONS
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.access_control import MembershipRole, Permission, Role, RolePermission
from app.models.organization import Organization
from app.models.user import OrganizationMembership, User
from app.modules.projects.models import Project


class ProjectsApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(
            bind=self.engine,
            class_=Session,
            expire_on_commit=False,
        )
        self.organization_id = uuid.uuid4()
        self.user_id = uuid.uuid4()
        with self.session_factory() as db:
            db.add(
                Organization(
                    id=self.organization_id,
                    name="Test organization",
                    slug=f"test-{self.organization_id.hex}",
                )
            )
            self.user = User(
                id=self.user_id,
                email=f"{self.user_id.hex}@example.test",
                full_name="Test user",
                password_hash="not-used",
            )
            db.add(self.user)
            db.flush()
            membership = OrganizationMembership(
                organization_id=self.organization_id,
                user_id=self.user_id,
                status="active",
            )
            db.add(membership)
            permissions = [
                Permission(code=code, name=name, description=description)
                for code, (name, description) in PERMISSIONS.items()
            ]
            db.add_all(permissions)
            db.flush()
            admin_role = Role(
                organization_id=self.organization_id,
                code="test_admin",
                name="Test Admin",
                is_system=False,
            )
            db.add(admin_role)
            db.flush()
            db.add(MembershipRole(membership_id=membership.id, role_id=admin_role.id))
            db.add_all(
                RolePermission(role_id=admin_role.id, permission_id=permission.id)
                for permission in permissions
            )
            db.commit()

        def override_get_db():
            with self.session_factory() as db:
                yield db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: self.user
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_create_and_list_project_and_daily_report(self):
        create_response = self.client.post(
            "/api/v1/projects",
            json={
                "organization_id": str(self.organization_id),
                "code": "AURORA-01",
                "name": "Aurora Tower",
                "status": "active",
                "currency": "MMK",
                "start_date": "2026-01-01",
                "end_date": "2027-01-01",
            },
        )
        self.assertEqual(create_response.status_code, 201, create_response.text)
        project = create_response.json()

        report_response = self.client.post(
            f"/api/v1/projects/{project['id']}/daily-reports",
            json={
                "report_date": "2026-11-19",
                "shift": "day",
                "headcount": 42,
                "work_completed": "Level 4 slab formwork",
                "safety_incidents": 0,
            },
        )
        self.assertEqual(report_response.status_code, 201, report_response.text)
        self.assertEqual(report_response.json()["status"], "draft")

        project_list = self.client.get("/api/v1/projects")
        self.assertEqual(project_list.status_code, 200)
        self.assertEqual([item["id"] for item in project_list.json()], [project["id"]])

        report_list = self.client.get(
            f"/api/v1/projects/{project['id']}/daily-reports"
        )
        self.assertEqual(report_list.status_code, 200)
        self.assertEqual(len(report_list.json()), 1)

    def test_project_in_another_organization_is_not_disclosed(self):
        other_organization_id = uuid.uuid4()
        project_id = uuid.uuid4()
        with self.session_factory() as db:
            db.add(
                Organization(
                    id=other_organization_id,
                    name="Other organization",
                    slug=f"other-{other_organization_id.hex}",
                )
            )
            db.add(
                Project(
                    id=project_id,
                    organization_id=other_organization_id,
                    code="PRIVATE-01",
                    name="Private project",
                    created_by_id=self.user_id,
                )
            )
            db.commit()

        response = self.client.get(f"/api/v1/projects/{project_id}")
        self.assertEqual(response.status_code, 404)

    def test_duplicate_daily_report_returns_conflict(self):
        with self.session_factory() as db:
            project = Project(
                organization_id=self.organization_id,
                code="AURORA-02",
                name="Aurora Annex",
                created_by_id=self.user_id,
            )
            db.add(project)
            db.commit()
            project_id = project.id

        payload = {
            "report_date": "2026-11-19",
            "shift": "day",
            "work_completed": "Rebar inspection",
        }
        first = self.client.post(
            f"/api/v1/projects/{project_id}/daily-reports",
            json=payload,
        )
        second = self.client.post(
            f"/api/v1/projects/{project_id}/daily-reports",
            json=payload,
        )
        self.assertEqual(first.status_code, 201, first.text)
        self.assertEqual(second.status_code, 409, second.text)

    def test_duplicate_project_code_returns_conflict(self):
        payload = {
            "organization_id": str(self.organization_id),
            "code": "SHARED-CODE",
            "name": "First project",
        }
        first = self.client.post("/api/v1/projects", json=payload)
        second = self.client.post(
            "/api/v1/projects",
            json={**payload, "name": "Second project"},
        )
        self.assertEqual(first.status_code, 201, first.text)
        self.assertEqual(second.status_code, 409, second.text)

    def test_create_project_rejects_an_unrelated_organization(self):
        response = self.client.post(
            "/api/v1/projects",
            json={
                "organization_id": str(uuid.uuid4()),
                "code": "OUTSIDE-ORG",
                "name": "Not accessible",
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_project_update_cannot_invert_existing_dates(self):
        project = self.client.post(
            "/api/v1/projects",
            json={
                "organization_id": str(self.organization_id),
                "code": "DATE-CHECK",
                "name": "Date check",
                "start_date": "2026-01-01",
                "end_date": "2026-12-01",
            },
        ).json()
        response = self.client.patch(
            f"/api/v1/projects/{project['id']}",
            json={"end_date": "2025-12-31"},
        )
        self.assertEqual(response.status_code, 422)

    def test_project_dates_are_validated(self):
        response = self.client.post(
            "/api/v1/projects",
            json={
                "organization_id": str(self.organization_id),
                "code": "INVALID-DATES",
                "name": "Invalid dates",
                "start_date": "2026-12-01",
                "end_date": "2026-11-01",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_site_operations_records_are_persisted_and_listed(self):
        project = self.client.post(
            "/api/v1/projects",
            json={
                "organization_id": str(self.organization_id),
                "code": "SITE-OPS",
                "name": "Site operations project",
            },
        ).json()
        project_url = f"/api/v1/projects/{project['id']}"

        workforce = self.client.post(
            f"{project_url}/workforce",
            json={
                "work_date": "2026-11-19",
                "trade": "Concrete workers",
                "contractor": "Direct",
                "worker_count": 12,
                "hours_per_worker": "8.00",
            },
        )
        self.assertEqual(workforce.status_code, 201, workforce.text)
        self.assertEqual(workforce.json()["worker_count"], 12)

        equipment = self.client.post(
            f"{project_url}/equipment-usage",
            json={
                "work_date": "2026-11-19",
                "equipment_code": "CRANE-01",
                "name": "Tower crane 01",
                "category": "Crane",
                "status": "operating",
                "operating_hours": "6.50",
                "idle_hours": "1.50",
                "fuel_liters": "24.250",
            },
        )
        self.assertEqual(equipment.status_code, 201, equipment.text)
        self.assertEqual(equipment.json()["equipment_code"], "CRANE-01")

        material = self.client.post(
            f"{project_url}/material-usage",
            json={
                "work_date": "2026-11-19",
                "material_code": "C30",
                "name": "Ready-mix concrete",
                "unit": "m3",
                "quantity": "18.500",
                "location": "Level 4",
            },
        )
        self.assertEqual(material.status_code, 201, material.text)
        self.assertEqual(material.json()["quantity"], "18.500")

        self.assertEqual(
            len(self.client.get(f"{project_url}/workforce").json()),
            1,
        )
        self.assertEqual(
            len(self.client.get(f"{project_url}/equipment-usage").json()),
            1,
        )
        self.assertEqual(
            len(self.client.get(f"{project_url}/material-usage").json()),
            1,
        )

    def test_site_operation_inputs_enforce_domain_limits(self):
        project = self.client.post(
            "/api/v1/projects",
            json={
                "organization_id": str(self.organization_id),
                "code": "LIMITS",
                "name": "Domain limits",
            },
        ).json()
        project_url = f"/api/v1/projects/{project['id']}"

        equipment = self.client.post(
            f"{project_url}/equipment-usage",
            json={
                "work_date": "2026-11-19",
                "equipment_code": "CRANE-02",
                "name": "Tower crane 02",
                "category": "Crane",
                "status": "operating",
                "operating_hours": "16",
                "idle_hours": "9",
            },
        )
        self.assertEqual(equipment.status_code, 422)

        material = self.client.post(
            f"{project_url}/material-usage",
            json={
                "work_date": "2026-11-19",
                "material_code": "C30",
                "name": "Ready-mix concrete",
                "unit": "m3",
                "quantity": "0",
            },
        )
        self.assertEqual(material.status_code, 422)

    def test_member_without_project_permission_cannot_create_project(self):
        limited_user = User(
            id=uuid.uuid4(),
            email=f"{uuid.uuid4().hex}@example.test",
            full_name="Read-only user",
            password_hash="not-used",
        )
        with self.session_factory() as db:
            db.add(limited_user)
            db.flush()
            membership = OrganizationMembership(
                organization_id=self.organization_id,
                user_id=limited_user.id,
                status="active",
            )
            db.add(membership)
            db.flush()
            role = Role(
                organization_id=self.organization_id,
                code="read_only",
                name="Read only",
                is_system=False,
            )
            db.add(role)
            db.flush()
            read_permission = db.scalar(
                select(Permission).where(Permission.code == "projects.read")
            )
            db.add(
                MembershipRole(
                    membership_id=membership.id,
                    role_id=role.id,
                )
            )
            db.add(
                RolePermission(
                    role_id=role.id,
                    permission_id=read_permission.id,
                )
            )
            db.commit()

        app.dependency_overrides[get_current_user] = lambda: limited_user
        response = self.client.post(
            "/api/v1/projects",
            json={
                "organization_id": str(self.organization_id),
                "code": "DENIED",
                "name": "Should not be created",
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_role_management_bootstraps_and_assigns_access(self):
        superuser = User(
            id=uuid.uuid4(),
            email=f"{uuid.uuid4().hex}@example.test",
            full_name="System administrator",
            password_hash="not-used",
            is_superuser=True,
        )
        with self.session_factory() as db:
            db.add(superuser)
            db.commit()

        app.dependency_overrides[get_current_user] = lambda: superuser
        response = self.client.post(
            f"/api/v1/organizations/{self.organization_id}/access/bootstrap",
            json={"initial_admin_user_id": str(self.user_id)},
        )
        self.assertEqual(response.status_code, 200, response.text)
        roles = response.json()
        self.assertEqual(
            {role["code"] for role in roles},
            {"organization_admin", "project_manager", "site_manager", "viewer"},
        )

        app.dependency_overrides[get_current_user] = lambda: self.user
        role_response = self.client.post(
            f"/api/v1/organizations/{self.organization_id}/access/roles",
            json={
                "code": "site_reader",
                "name": "Site Reader",
                "permissions": ["projects.read", "site_reports.read"],
            },
        )
        self.assertEqual(role_response.status_code, 201, role_response.text)

        limited_user = User(
            id=uuid.uuid4(),
            email=f"{uuid.uuid4().hex}@example.test",
            full_name="Site reader",
            password_hash="not-used",
        )
        with self.session_factory() as db:
            db.add(limited_user)
            db.flush()
            db.add(
                OrganizationMembership(
                    organization_id=self.organization_id,
                    user_id=limited_user.id,
                    status="active",
                )
            )
            db.commit()

        assignment = self.client.put(
            f"/api/v1/organizations/{self.organization_id}/access/members/{limited_user.id}/roles",
            json={"role_codes": ["site_reader"]},
        )
        self.assertEqual(assignment.status_code, 200, assignment.text)
        self.assertEqual([role["code"] for role in assignment.json()], ["site_reader"])

        app.dependency_overrides[get_current_user] = lambda: limited_user
        denied = self.client.post(
            "/api/v1/projects",
            json={
                "organization_id": str(self.organization_id),
                "code": "ROLE-DENIED",
                "name": "No create permission",
            },
        )
        self.assertEqual(denied.status_code, 403)

    def test_last_access_manager_cannot_be_demoted(self):
        response = self.client.put(
            f"/api/v1/organizations/{self.organization_id}/access/members/{self.user_id}/roles",
            json={"role_codes": []},
        )
        self.assertEqual(response.status_code, 409)

    def test_equipment_asset_registry_create_filter_and_update(self):
        project = self.client.post(
            "/api/v1/projects",
            json={
                "organization_id": str(self.organization_id),
                "code": "ASSET-PROJECT",
                "name": "Asset project",
            },
        ).json()
        base_url = (
            f"/api/v1/organizations/{self.organization_id}/equipment-assets"
        )
        response = self.client.post(
            base_url,
            json={
                "asset_code": "CRANE-01",
                "name": "Tower crane 01",
                "category": "Crane",
                "serial_number": "SN-1001",
                "current_project_id": project["id"],
                "status": "in_use",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        asset = response.json()
        self.assertEqual(asset["current_project_id"], project["id"])

        filtered = self.client.get(f"{base_url}?status=in_use")
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual([item["id"] for item in filtered.json()], [asset["id"]])

        updated = self.client.patch(
            f"{base_url}/{asset['id']}",
            json={"status": "maintenance", "location": "Workshop"},
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["status"], "maintenance")
        self.assertEqual(updated.json()["location"], "Workshop")

    def test_equipment_asset_cannot_be_assigned_to_another_organization_project(self):
        other_org_id = uuid.uuid4()
        other_project_id = uuid.uuid4()
        with self.session_factory() as db:
            db.add(
                Organization(
                    id=other_org_id,
                    name="Other organization",
                    slug=f"asset-other-{other_org_id.hex}",
                )
            )
            db.add(
                Project(
                    id=other_project_id,
                    organization_id=other_org_id,
                    code="OTHER-PROJECT",
                    name="Other project",
                    created_by_id=self.user_id,
                )
            )
            db.commit()

        response = self.client.post(
            f"/api/v1/organizations/{self.organization_id}/equipment-assets",
            json={
                "asset_code": "CRANE-CROSS-ORG",
                "name": "Foreign project crane",
                "category": "Crane",
                "current_project_id": str(other_project_id),
            },
        )
        self.assertEqual(response.status_code, 404)

    def _create_inspection(self, code, result="pass"):
        project = self.client.post(
            "/api/v1/projects",
            json={
                "organization_id": str(self.organization_id),
                "code": f"QUALITY-{code}",
                "name": "Quality workflow project",
            },
        ).json()
        finding = {
            "finding_code": "ITEM-01",
            "description": "Verify installed work against the approved specification",
            "result": result,
        }
        if result == "fail":
            finding.update(
                {
                    "severity": "major",
                    "corrective_action": "Replace the nonconforming installed work",
                }
            )
        response = self.client.post(
            f"/api/v1/projects/{project['id']}/inspections",
            json={
                "inspection_code": code,
                "title": "Concrete placement check",
                "inspection_type": "Concrete",
                "location": "Level 4, Grid A",
                "scheduled_on": "2026-11-20",
                "findings": [finding],
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return project["id"], response.json()

    def _create_quality_reviewer(self):
        reviewer = User(
            id=uuid.uuid4(),
            email=f"{uuid.uuid4().hex}@example.test",
            full_name="Quality reviewer",
            password_hash="not-used",
        )
        with self.session_factory() as db:
            db.add(reviewer)
            db.flush()
            membership = OrganizationMembership(
                organization_id=self.organization_id,
                user_id=reviewer.id,
                status="active",
            )
            db.add(membership)
            role = db.scalar(
                select(Role).where(
                    Role.organization_id == self.organization_id,
                    Role.code == "test_admin",
                )
            )
            db.add(MembershipRole(membership_id=membership.id, role_id=role.id))
            db.commit()
        return reviewer

    def test_quality_inspection_requires_independent_approval_and_single_decision(self):
        project_id, inspection = self._create_inspection("QC-001")
        base_url = (
            f"/api/v1/projects/{project_id}/inspections/{inspection['id']}"
        )

        premature_review = self.client.post(
            f"{base_url}/decision",
            json={"decision": "approved"},
        )
        self.assertEqual(premature_review.status_code, 409)

        submitted = self.client.post(f"{base_url}/submit")
        self.assertEqual(submitted.status_code, 200, submitted.text)
        self.assertEqual(submitted.json()["status"], "submitted")
        repeated_submission = self.client.post(f"{base_url}/submit")
        self.assertEqual(repeated_submission.status_code, 409)

        self_review = self.client.post(
            f"{base_url}/decision",
            json={"decision": "approved"},
        )
        self.assertEqual(self_review.status_code, 403)

        reviewer = self._create_quality_reviewer()
        app.dependency_overrides[get_current_user] = lambda: reviewer
        approved = self.client.post(
            f"{base_url}/decision",
            json={"decision": "approved", "comments": "Verified against specification"},
        )
        self.assertEqual(approved.status_code, 200, approved.text)
        self.assertEqual(approved.json()["status"], "approved")
        self.assertEqual(approved.json()["decision"]["reviewer_id"], str(reviewer.id))

        duplicate_decision = self.client.post(
            f"{base_url}/decision",
            json={"decision": "rejected", "comments": "Second decision"},
        )
        self.assertEqual(duplicate_decision.status_code, 409)

        listed = self.client.get(
            f"/api/v1/projects/{project_id}/inspections?status=approved"
        )
        self.assertEqual(listed.status_code, 200)
        self.assertEqual([item["id"] for item in listed.json()], [inspection["id"]])

    def test_failed_quality_finding_cannot_be_approved_and_rejection_needs_reason(self):
        project_id, inspection = self._create_inspection("QC-002", result="fail")
        base_url = (
            f"/api/v1/projects/{project_id}/inspections/{inspection['id']}"
        )
        submitted = self.client.post(f"{base_url}/submit")
        self.assertEqual(submitted.status_code, 200, submitted.text)

        reviewer = self._create_quality_reviewer()
        app.dependency_overrides[get_current_user] = lambda: reviewer
        approval = self.client.post(
            f"{base_url}/decision",
            json={"decision": "approved"},
        )
        self.assertEqual(approval.status_code, 422)

        missing_reason = self.client.post(
            f"{base_url}/decision",
            json={"decision": "rejected"},
        )
        self.assertEqual(missing_reason.status_code, 422)

        rejection = self.client.post(
            f"{base_url}/decision",
            json={"decision": "rejected", "comments": "Rework is required"},
        )
        self.assertEqual(rejection.status_code, 200, rejection.text)
        self.assertEqual(rejection.json()["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
