import os
import sys
from datetime import datetime

# Add project source to path
sys.path.insert(0, os.path.abspath("../src"))

project = "MetaBeeAI"
release = "0.1.0"
year = datetime.now().year
copyright = f"{year}, MetaBeeAI Contributors"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "sphinx_autodoc_typehints",
    "sphinx_automodapi.automodapi",
    "sphinx_gallery.gen_gallery",
    "myst_parser",
]

autosummary_generate = True
autoclass_content = "both"
html_theme = "pydata_sphinx_theme"

sphinx_gallery_conf = {
    "examples_dirs": "../examples",       # path to example scripts
    'gallery_dirs': os.path.join('generated', 'gallery'), # where to save generated gallery
    'filename_pattern': '^((?!skip_).)*$',
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