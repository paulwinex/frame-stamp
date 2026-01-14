import os, sys, json, codecs
# import mock
from unittest.mock import Mock
from sphinx.builders.html import StandaloneHTMLBuilder

CWD = os.path.dirname(os.path.dirname(__file__))
sys.path.append(CWD)

# add Qt names as mock
autodoc_mock_imports = [
    'sip', 'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets',
    'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui',
    'shiboken6', 'PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
    'Qt', 'Qt.QtCore', 'Qt.QtGui', 'Qt.QtWidgets']

# MOCK_MODULES = []
# MOCK_MODULES_ENV = BUILD_ENV.get('MOCK_MODULES', '').strip()
# if MOCK_MODULES_ENV:
#     MOCK_MODULES.extend(MOCK_MODULES_ENV.split(os.pathsep))
# for mod_name in MOCK_MODULES:
#     sys.modules[mod_name] = Mock()

project = 'Frame Stamp'
copyright = '2024'
author = 'paulwinex'

version = '0.1.0'


StandaloneHTMLBuilder.supported_image_types = [
    'image/svg+xml',
    'image/gif',
    'image/png',
    'image/jpeg'
]
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinx.ext.imgmath',
    'recommonmark',
    # 'numpydoc',
    # 'sphinxcontrib.youtube',
    # 'extensions.video'
]
numpydoc_show_class_members = False
templates_path = ['_templates']
source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'markdown',
    '.md': 'markdown',
}
# The master toctree document.
master_doc = 'index'
language = 'ru'
exclude_patterns = []
pygments_style = None
html_theme = "sphinx_rtd_theme"

html_theme_path = ["_themes", ]
# html_theme_options = {}
html_static_path = ['.']
# html_sidebars = {}
htmlhelp_basename = 'FrameStampDocs'

latex_elements = {}
latex_documents = [
    (master_doc, 'documents.tex', 'documents', 'manual'),
]

man_pages = [
    (master_doc, 'documentation', 'Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'Documentation',
     author, 'CGF Documentation.',
     'Miscellaneous'),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']


# -- Extension configuration -------------------------------------------------

# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True
html_show_sourcelink = False

html_context = {
    'show_sphinx': False,
}
# html_context.update(BUILD_ENV)

autodoc_member_order = 'bysource'

# Список файлов CSS, которые должны быть включены в HTML-вывод
html_css_files = [
    # 'css/custom.css',  # Путь относительно html_static_path
    # Добавьте любые другие CSS-файлы, которые вы хотите включить
]

# def setup(app):
#     app.add_directive('video', Video)
#     app.add_directive('img2', Image)
    # app.add_stylesheet('css/custom.css')
