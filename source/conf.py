# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'HPE KAUST'
copyright = '2022-2023, Hewlett Packard Enterprise.'
author = 'Mohammed Al Farhan'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["myst_parser"]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_material'

# import sphinx_rtd_theme

# html_theme = "sphinx_rtd_theme"
# html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# html_theme = 'sphinx_rtd_theme'
# html_theme = 'python_docs_theme'
# html_theme = 'classic'

# html_theme_options = { "logo_only": True }

# html_favicon = ""

html_static_path = []
# html_static_path = ['_static']

html_last_updated_fmt = "%b %d, %Y"
