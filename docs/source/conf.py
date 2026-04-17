# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from __future__ import annotations

from pathlib import Path

# -- Path setup --------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "oas2mcp"
copyright = "2026, pr1m8"
author = "pr1m8"
release = "0.1.7"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.linkcode",
    "sphinx.ext.graphviz",
    "sphinx.ext.githubpages",
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_togglebutton",
    "sphinx_inline_tabs",
    "sphinxcontrib.mermaid",
    "autoapi.extension",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

root_doc = "index"
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
language = "en"

# -- Extension configuration -------------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = False

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
]

copybutton_prompt_text = r">>> |\.\.\. |\$ |# "
copybutton_prompt_is_regexp = True
copybutton_remove_prompts = True

autoapi_type = "python"
autoapi_dirs = [str(SRC / "oas2mcp")]
autoapi_root = "autoapi"
autoapi_keep_files = False
autoapi_add_toctree_entry = False
autoapi_member_order = "groupwise"
autoapi_python_class_content = "class"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
]
autoapi_ignore = [
    "*migrations*",
    "*tests*",
    "*/conftest.py",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_title = "oas2mcp"
html_static_path = ["_static"]
html_css_files = ["custom_css.css"]

html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "light_css_variables": {
        "color-brand-primary": "#2563eb",
        "color-brand-content": "#2563eb",
        "color-api-name": "#2563eb",
        "color-api-pre-name": "#1d4ed8",
        "color-admonition-title--note": "#2563eb",
        "color-admonition-title-background--note": "#dbeafe",
    },
    "dark_css_variables": {
        "color-brand-primary": "#60a5fa",
        "color-brand-content": "#60a5fa",
        "color-api-name": "#93c5fd",
        "color-api-pre-name": "#60a5fa",
        "color-admonition-title--note": "#93c5fd",
        "color-admonition-title-background--note": "#1e3a8a",
    },
}

html_sidebars = {
    "**": [
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/scroll-start.html",
        "sidebar/navigation.html",
        "sidebar/ethical-ads.html",
        "sidebar/scroll-end.html",
        "sidebar/variant-selector.html",
    ]
}


def linkcode_resolve(domain: str, info: dict[str, str]) -> str | None:
    """Resolve GitHub source links for documented Python objects."""
    if domain != "py":
        return None

    module_name = info.get("module")
    if not module_name:
        return None

    module_path = module_name.replace(".", "/")
    return f"https://github.com/pr1m8/oas2mcp/blob/main/src/{module_path}.py"
