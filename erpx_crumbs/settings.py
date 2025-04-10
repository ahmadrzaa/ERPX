from erpx.settings import TEMPLATES

TEMPLATES[0]["OPTIONS"]["context_processors"].append(
    "erpx_crumbs.context_processors.breadcrumbs",
)
