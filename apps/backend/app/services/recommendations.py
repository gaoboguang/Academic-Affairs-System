from __future__ import annotations

from ._recommendations_catalog import (
    create_college,
    create_major,
    import_admissions,
    list_admission_records,
    list_admission_records_page,
    list_colleges,
    list_colleges_page,
    list_majors,
    list_majors_page,
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
from ._recommendations_details import (
    get_college_admission_history,
    get_college_detail,
    get_major_admission_history,
    get_major_detail,
)
from ._recommendations_employment import (
    bootstrap_employment_directions,
    bootstrap_major_employment_mappings,
    create_employment_direction,
    create_major_employment_mapping,
    list_employment_directions,
    list_major_employment_mappings,
    list_major_employment_mappings_page,
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
    list_enrollment_plans_page,
)
from ._recommendations_rules import (
    bootstrap_province_score_transform_rules,
    bootstrap_province_volunteer_rules,
    bootstrap_special_type_rules,
    bootstrap_subject_requirement_dicts,
    create_province_score_transform_rule,
    create_province_volunteer_rule,
    create_special_type_rule,
    create_subject_requirement_dict,
    list_province_score_transform_rules,
    list_province_volunteer_rules,
    list_special_type_rules,
    list_subject_requirement_dicts,
    update_province_score_transform_rule,
    update_province_volunteer_rule,
    update_special_type_rule,
    update_subject_requirement_dict,
)
from ._recommendations_score_projection import (
    calculate_gaokao_score_projection,
    create_gaokao_score_projection,
    get_gaokao_score_projection,
    list_gaokao_score_projections,
)
from ._recommendations_settings import (
    create_recommendation_strategy_preset,
    delete_recommendation_strategy_preset,
    get_recommendation_settings,
    update_recommendation_settings,
)
from ._recommendations_shared import _load_recommendation_thresholds
from ._recommendations_shandong_rush_stable_safe import preview_shandong_rush_stable_safe_recommendations
from ._recommendations_volunteer_guide import preview_volunteer_guide
from ._recommendations_volunteer_options import get_volunteer_guide_options
from ._recommendations_workbench import preview_volunteer_workbench


__all__ = [
    "batch_generate_recommendations",
    "bootstrap_employment_directions",
    "bootstrap_major_employment_mappings",
    "bootstrap_province_score_transform_rules",
    "bootstrap_province_volunteer_rules",
    "bootstrap_special_type_rules",
    "bootstrap_subject_requirement_dicts",
    "calculate_gaokao_score_projection",
    "create_college",
    "create_employment_direction",
    "create_major",
    "create_major_employment_mapping",
    "create_province_score_transform_rule",
    "create_recommendation_strategy_preset",
    "create_gaokao_score_projection",
    "create_special_type_rule",
    "create_subject_requirement_dict",
    "delete_recommendation_strategy_preset",
    "delete_volunteer_draft",
    "generate_recommendations",
    "get_gaokao_score_projection",
    "get_college_admission_history",
    "get_college_detail",
    "get_major_admission_history",
    "get_major_detail",
    "get_recommendation_settings",
    "get_volunteer_draft_detail",
    "get_volunteer_guide_options",
    "import_admissions",
    "import_enrollment_plans",
    "list_admission_records",
    "list_admission_records_page",
    "list_colleges",
    "list_colleges_page",
    "list_employment_directions",
    "list_enrollment_plans",
    "list_enrollment_plans_page",
    "list_gaokao_score_projections",
    "list_major_employment_mappings",
    "list_major_employment_mappings_page",
    "list_majors",
    "list_majors_page",
    "list_province_score_transform_rules",
    "list_special_type_rules",
    "preview_volunteer_workbench",
    "preview_shandong_rush_stable_safe_recommendations",
    "preview_volunteer_guide",
    "list_province_volunteer_rules",
    "list_recommendation_history",
    "list_subject_requirement_dicts",
    "list_scheme_results",
    "list_volunteer_drafts",
    "create_volunteer_draft",
    "update_province_score_transform_rule",
    "create_province_volunteer_rule",
    "update_special_type_rule",
    "update_subject_requirement_dict",
    "update_volunteer_draft",
    "update_college",
    "update_employment_direction",
    "update_major",
    "update_major_employment_mapping",
    "update_province_volunteer_rule",
    "update_recommendation_settings",
    "_load_recommendation_thresholds",
]
