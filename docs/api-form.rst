Ptah form  API
--------------

.. automodule:: ptah.form

  .. py:data:: null

  .. py:data:: required

  .. autoclass:: Invalid

Form
~~~~

  .. autoclass:: Form
     :members:

  .. autoclass:: DisplayForm

  .. autoclass:: FormWidgets

  .. autofunction:: set_csrf_utility


Field
~~~~~

  .. autoclass:: Field

  .. autoclass:: FieldFactory

  .. autoclass:: Fieldset

  .. autoclass:: FieldsetErrors

  .. autofunction:: field

  .. autofunction:: fieldpreview

  .. autofunction:: get_field_factory

  .. autofunction:: get_field_preview

  .. autofunction:: register_field_factory


Vocabulary
~~~~~~~~~~

  .. autoclass:: SimpleTerm

  .. autoclass:: SimpleVocabulary


Validators
~~~~~~~~~~

  .. autoclass:: All

  .. autoclass:: Function

  .. autoclass:: Regex

  .. autoclass:: Email

  .. autoclass:: Range

  .. autoclass:: Length

  .. autoclass:: OneOf


Predefined fields
~~~~~~~~~~~~~~~~~

  .. autoclass:: TextField

  .. autoclass:: IntegerField

  .. autoclass:: FloatField

  .. autoclass:: DecimalField

  .. autoclass:: TextAreaField

  .. autoclass:: FileField

  .. autoclass:: LinesField

  .. autoclass:: PasswordField

  .. autoclass:: DateField

  .. autoclass:: DateTimeField

  .. autoclass:: RadioField

  .. autoclass:: BoolField

  .. autoclass:: ChoiceField

  .. autoclass:: MultiChoiceField

  .. autoclass:: MultiSelectField

  .. autoclass:: JSDateField

  .. autoclass:: JSDateTimeField

  .. autoclass:: TinymceField


Button
~~~~~~

  .. autofunction:: button

  .. autoclass:: Button

  .. autoclass:: Buttons

  .. py:data:: AC_DEFAULT

  .. py:data:: AC_PRIMARY

  .. py:data:: AC_DANGER

  .. py:data:: AC_SUCCESS

  .. py:data:: AC_INFO


Form snippets
~~~~~~~~~~~~~

  .. py:data:: FORM_VIEW

  .. py:data:: FORM_ACTIONS

  .. py:data:: FORM_WIDGET

  .. py:data:: FORM_DISPLAY_WIDGET
