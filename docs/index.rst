Frame Stamp
-----------

Библиотека для добавления информации на кадры используя шаблон и контекст с переменными.

Установка
=========

Добавление в проект с помощью `poetry` или `uv`

.. code-block:: bash

   poetry add https://github.com/paulwinex/frame-stamp.git#version
   uv add https://github.com/paulwinex/frame-stamp.git#version

Локальная разработка и запуск

.. code-block:: bash

   git clone https://github.com/paulwinex/frame-stamp.git
   cd frame-stamp
   make install

Запуск диалога разработки шаблона

.. code-block:: bash

   make run

Сборка документации

.. code-block:: bash

   make docs


Разделы
=======

.. toctree::
   :maxdepth: 1

   make_template
   viewer
   shapes/index
   expressions
   environment_variables
   development
   debug
   tricks
   faq


TODO
---

- alignment for grid
- add templates in yaml and py format
- limit column with
- fit ceil content
- Gradient fill
- Template Designer UI