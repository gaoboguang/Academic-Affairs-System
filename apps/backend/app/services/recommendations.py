from __future__ import annotations

from ._recommendations_catalog import (
    create_college,
    create_major,
    import_admissions,
    list_admission_records,
    list_colleges,
    list_majors,
    update_college,
    update_major,
)
from ._recommendations_drafts import (
    create_volunteer_draft,
    delete_volunteer_draft,
    get_volunteer_draft_detail,
    list_volunteer_drafts,
    update_volunteer_draft,
)
from ._recommendations_employment import (
    create_employment_direction,
    create_major_employment_mapping,
    list_employment_directions,
    list_major_employment_mappings,
    update_employment_direction,
    update_major_employment_mapping,
)
from ._recommendations_generation import (
    batch_generate_recommendations,
    generate_recommendations,
)
from ._recommendations_history import (
    list_recommendation_history,
    list_scheme_results,
)
from ._recommendations_plans import (
    import_enrollment_plans,
    list_enrollment_plans,
)
from ._recommendations_rules import (
    bootstrap_province_volunteer_rules,
    create_province_volunteer_rule,
    list_province_volunteer_rules,
    update_province_volunteer_rule,
)
from ._recommendations_settings import (
    create_recommendation_strategy_preset,
    delete_recommendation_strategy_preset,
    get_recommendation_settings,
    update_recommendation_settings,
)
from ._recommendations_shared import _load_recommendation_thresholds
from ._recommendations_workbench import preview_volunteer_workbench


__all__ = [
    "batch_generate_recommendations",
    "bootstrap_province_volunteer_rules",
    "create_college",
    "create_employment_direction",
    "create_major",
    "create_major_employment_mapping",
    "create_recommendation_strategy_preset",
    "delete_recommendation_strategy_preset",
    "delete_volunteer_draft",
    "generate_recommendations",
    "get_recommendation_settings",
    "get_volunteer_draft_detail",
    "import_admissions",
    "import_enrollment_plans",
    "list_admission_records",
    "list_colleges",
    "list_employment_directions",
    "list_enrollment_plans",
    "list_major_employment_mappings",
    "list_majors",
    "preview_volunteer_workbench",
    "list_province_volunteer_rules",
    "list_recommendation_history",
    "list_scheme_results",
    "list_volunteer_drafts",
    "create_volunteer_draft",
    "create_province_volunteer_rule",
    "update_volunteer_draft",
    "update_college",
    "update_employment_direction",
    "update_major",
    "update_major_employment_mapping",
    "update_province_volunteer_rule",
    "update_recommendation_settings",
    "_load_recommendation_thresholds",
]
