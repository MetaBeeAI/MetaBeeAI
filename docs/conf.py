import os
import sys
from datetime import datetime

# Add project source to path
sys.path.insert(0, os.path.abspath("../src"))

project = "MetaBeeAI"
release = "0.1.0"
version = release
year = datetime.now().year
copyright = f"{year}, MetaBeeAI Contributors"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "sphinx_autodoc_typehints",
    "sphinx_automodapi.automodapi",
    # Gallery disabled due to zero examples; avoids needless processing and warnings
    # "sphinx_gallery.gen_gallery",
    "myst_parser",
]

autosummary_generate = True
autoclass_content = "both"
html_theme = "pydata_sphinx_theme"

exclude_patterns = [
    # Exclude stale autosummary files for non-existent API symbols
    "generated/api/metabeeai.metabeeai_llm.check_chunk_ids_in_pages_dir.rst",
]

# Preserve gallery config for future re-enable
sphinx_gallery_conf = {
    "examples_dirs": "../examples",
    "gallery_dirs": os.path.join("generated", "gallery"),
    "filename_pattern": "^((?!skip_).)*$",
    "default_thumb_file": "_static/gallery_default.png",
    "download_all_examples": True,
    "backreferences_dir": "gen_modules/backreferences",
    "doc_module": ("metabeeai",),
}


html_static_path = ["_static"]
html_css_files = ["bee.css"]
html_theme_options = {
    "logo": {
        "text": "MetaBeeAI",
        "image_light": "_static/metabeeai.png",
        "image_dark": "_static/metabeeai_dark.png",
    },
    "show_nav_level": 2,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/MetaBeeAI/MetaBeeAI",
            "icon": "fa-brands fa-github",
        },
    ],
}

automodapi_toctreedirnm = "generated/api"
