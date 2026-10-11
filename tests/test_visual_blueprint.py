"""Tests for Visual Product Blueprint & Reverse-Engineering Engine."""

from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient

from ethical_crawler.api.app import app
from ethical_crawler.extractors.visual_blueprint_generator import (
    ProductBlueprintResult,
    ScreenDecomposition,
    VisualBlueprintGenerator,
)


def test_screen_decomposition_and_semantics(tmp_path):
    """Verify screen categorization across dashboard, admin, and settings views."""
    generator = VisualBlueprintGenerator(base_screenshots_dir=tmp_path)

    # 1. Dashboard
    dash_img = tmp_path / "app_01_dashboard_123.jpg"
    dash_img.write_text("fake image")
    s_dash = generator.decompose_screen(dash_img, "app.io")
    assert s_dash.view_type == "dashboard"
    assert "/dashboard" in s_dash.inferred_route
    assert len(s_dash.metrics) > 0

    # 2. Admin Users Table
    admin_img = tmp_path / "app_02_admin_users_456.jpg"
    admin_img.write_text("fake image")
    s_admin = generator.decompose_screen(admin_img, "app.io")
    assert s_admin.view_type == "admin_table"
    assert "/admin" in s_admin.inferred_route
    assert any("Invite" in a for a in s_admin.actions)

    # 3. Settings & Billing
    bill_img = tmp_path / "app_03_settings_billing_789.jpg"
    bill_img.write_text("fake image")
    s_bill = generator.decompose_screen(bill_img, "app.io")
    assert s_bill.view_type == "settings_form"
    assert "/billing" in s_bill.inferred_route


def test_mermaid_diagrams_generation():
    """Verify Navigation flowchart and Entity-Relationship Diagram (ERD) syntax."""
    generator = VisualBlueprintGenerator()
    screens = [
        ScreenDecomposition(
            filename="01_dash.jpg",
            filepath="fake.jpg",
            route_name="dash",
            view_type="dashboard",
            title="Main Dashboard",
            inferred_route="/dashboard",
        ),
        ScreenDecomposition(
            filename="02_users.jpg",
            filepath="fake.jpg",
            route_name="users",
            view_type="admin_table",
            title="User Management",
            inferred_route="/admin/users",
        ),
    ]

    nav_mermaid = generator.build_navigation_diagram(screens)
    assert "flowchart TD" in nav_mermaid
    assert "Main Dashboard" in nav_mermaid
    assert "User Management" in nav_mermaid
    assert "-->" in nav_mermaid

    erd_mermaid = generator.build_erd_diagram(screens)
    assert "erDiagram" in erd_mermaid
    assert "ORGANIZATION" in erd_mermaid
    assert "USER" in erd_mermaid
    assert "SUBSCRIPTION" in erd_mermaid


def test_api_contracts_and_components_generation():
    """Verify REST API specifications and Atomic Design components."""
    generator = VisualBlueprintGenerator()
    screens = [
        ScreenDecomposition(
            filename="01_dash.jpg",
            filepath="fake.jpg",
            route_name="dash",
            view_type="dashboard",
            title="Main Dashboard",
        )
    ]

    api_specs = generator.build_api_contracts(screens)
    assert len(api_specs) >= 4
    paths = [ep.path for ep in api_specs]
    assert "/api/v1/dashboard/metrics" in paths
    assert "/api/v1/users" in paths

    components, tokens = generator.build_frontend_components(screens)
    assert len(components) >= 3
    assert any(c.name == "AppShellLayout" for c in components)
    assert "colors" in tokens
    assert "primary" in tokens["colors"]


@pytest.mark.asyncio
async def test_full_blueprint_generation_and_pdf_export(tmp_path):
    """Verify complete blueprint generation and PDF export."""
    domain_dir = tmp_path / "mocksaas.com"
    domain_dir.mkdir(parents=True)
    (domain_dir / "01_dashboard.jpg").write_text("fake image")
    (domain_dir / "02_admin_users.jpg").write_text("fake image")

    generator = VisualBlueprintGenerator(base_screenshots_dir=tmp_path)
    res = await generator.generate_blueprint("mocksaas.com")

    assert isinstance(res, ProductBlueprintResult)
    assert res.domain == "mocksaas.com"
    assert res.screenshot_count == 2
    assert "# Full-Stack Product Blueprint" in res.full_markdown_dossier
    assert "flowchart TD" in res.navigation_mermaid
    assert "erDiagram" in res.erd_mermaid

    # Test PDF compilation
    pdf_bytes = VisualBlueprintGenerator.export_pdf(res)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


@pytest.mark.asyncio
async def test_blueprint_api_endpoints(monkeypatch, tmp_path):
    """Verify GET and POST /api/v1/blueprint/* endpoints."""
    domain_dir = tmp_path / "testportal.io"
    domain_dir.mkdir(parents=True)
    (domain_dir / "01_home.jpg").write_text("fake image")

    monkeypatch.setattr(
        "ethical_crawler.extractors.visual_blueprint_generator.VisualBlueprintGenerator.__init__",
        lambda self, base_screenshots_dir=None: setattr(self, "screenshots_root", tmp_path),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. List domains
        res_domains = await client.get("/api/v1/blueprint/domains")
        assert res_domains.status_code == 200
        domains_data = res_domains.json()
        assert any(d["domain"] == "testportal.io" for d in domains_data)

        # 2. Generate blueprint
        res_gen = await client.post(
            "/api/v1/blueprint/generate",
            json={"domain": "testportal.io", "custom_focus": "user flows"},
        )
        assert res_gen.status_code == 200
        blueprint_data = res_gen.json()
        assert blueprint_data["domain"] == "testportal.io"
        assert "flowchart TD" in blueprint_data["navigation_mermaid"]

        # 3. Export Markdown
        res_md = await client.post(
            "/api/v1/blueprint/export",
            json={"domain": "testportal.io", "format": "markdown"},
        )
        assert res_md.status_code == 200
        assert res_md.headers["content-type"].startswith("text/markdown")
        assert "Product Blueprint" in res_md.text

        # 4. Export PDF
        res_pdf = await client.post(
            "/api/v1/blueprint/export",
            json={"domain": "testportal.io", "format": "pdf"},
        )
        assert res_pdf.status_code == 200
        assert res_pdf.headers["content-type"] == "application/pdf"
        assert res_pdf.content.startswith(b"%PDF")

        # 5. Upload screenshots
        import base64
        fake_b64 = base64.b64encode(b"\x89PNG\r\n\x1a\nfakeimage").decode("utf-8")
        try:
            res_upload = await client.post(
                "/api/v1/blueprint/upload",
                json={
                    "domain": "testportal.io",
                    "files": [
                        {"filename": "02_admin.png", "data_base64": fake_b64}
                    ],
                },
            )
            assert res_upload.status_code == 200
            upload_data = res_upload.json()
            assert upload_data["status"] == "success"
            assert upload_data["saved_count"] == 1
            assert "02_admin.png" in upload_data["files"]
        finally:
            import shutil
            test_dir = Path("data/screenshots/testportal.io")
            if test_dir.exists():
                shutil.rmtree(test_dir, ignore_errors=True)

