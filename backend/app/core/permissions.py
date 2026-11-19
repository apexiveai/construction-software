PERMISSIONS: dict[str, tuple[str, str]] = {
    "projects.read": ("Read projects", "View projects in an organization."),
    "projects.create": ("Create projects", "Create projects in an organization."),
    "projects.update": ("Update projects", "Edit projects in an organization."),
    "site_reports.read": (
        "Read site reports",
        "View daily site reports.",
    ),
    "site_reports.create": (
        "Create site reports",
        "Create daily site reports.",
    ),
    "workforce.read": ("Read workforce", "View workforce records."),
    "workforce.create": ("Create workforce", "Create workforce records."),
    "equipment_usage.read": (
        "Read equipment usage",
        "View daily equipment usage.",
    ),
    "equipment_usage.create": (
        "Create equipment usage",
        "Create daily equipment usage.",
    ),
    "equipment_assets.read": (
        "Read equipment assets",
        "View the organization's equipment asset register.",
    ),
    "equipment_assets.create": (
        "Create equipment assets",
        "Register equipment assets for the organization.",
    ),
    "equipment_assets.update": (
        "Update equipment assets",
        "Update equipment asset details and status.",
    ),
    "material_usage.read": ("Read material usage", "View material usage records."),
    "material_usage.create": (
        "Create material usage",
        "Create material usage records.",
    ),
    "quality_inspections.read": (
        "Read quality inspections",
        "View inspection records and decisions.",
    ),
    "quality_inspections.create": (
        "Create quality inspections",
        "Create inspection records and findings.",
    ),
    "quality_inspections.submit": (
        "Submit quality inspections",
        "Submit inspections for independent review.",
    ),
    "quality_inspections.review": (
        "Review quality inspections",
        "Approve or reject submitted inspections.",
    ),
    "access_control.manage": (
        "Manage organization access",
        "Create roles and assign them to organization members.",
    ),
}

ROLE_TEMPLATES: dict[str, tuple[str, tuple[str, ...]]] = {
    "organization_admin": (
        "Organization Admin",
        tuple(PERMISSIONS),
    ),
    "project_manager": (
        "Project Manager",
        (
            "projects.read",
            "projects.create",
            "projects.update",
            "site_reports.read",
            "site_reports.create",
            "workforce.read",
            "workforce.create",
            "equipment_usage.read",
            "equipment_usage.create",
            "equipment_assets.read",
            "equipment_assets.create",
            "equipment_assets.update",
            "material_usage.read",
            "material_usage.create",
            "quality_inspections.read",
            "quality_inspections.create",
            "quality_inspections.submit",
            "quality_inspections.review",
        ),
    ),
    "site_manager": (
        "Site Manager",
        (
            "projects.read",
            "site_reports.read",
            "site_reports.create",
            "workforce.read",
            "workforce.create",
            "equipment_usage.read",
            "equipment_usage.create",
            "equipment_assets.read",
            "equipment_assets.create",
            "equipment_assets.update",
            "material_usage.read",
            "material_usage.create",
            "quality_inspections.read",
            "quality_inspections.create",
            "quality_inspections.submit",
        ),
    ),
    "viewer": (
        "Viewer",
        (
            "projects.read",
            "site_reports.read",
            "workforce.read",
            "equipment_usage.read",
            "equipment_assets.read",
            "material_usage.read",
            "quality_inspections.read",
        ),
    ),
}
