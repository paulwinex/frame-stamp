Frame Stamp
-----------

Библиотека для добавления информации на кадры используя шаблон и контекст с переменными.

Установка
=========

Добавление в проект с помощью `poetry`

.. code-block:: bash

   poetry add https://github.com/paulwinex/frame-stamp.git#version

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
