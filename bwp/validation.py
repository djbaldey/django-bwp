from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.forms.models import _get_foreign_key
from django.contrib.admin.options import flatten_fieldsets
from django.contrib.admin.validation import (check_isseq, check_isdict,
    get_field, check_formfield, fetch_attr, check_readonly_fields)

from bwp.models import BaseModel

__all__ = ['validate']

def validate(cls, model):
    """
    Does basic ModelAdmin option validation. Calls custom validation
    classmethod in the end if it is provided in cls. The signature of the
    custom validation classmethod should be: def validate(cls, model).
    """
    # Before we can introspect models, they need to be fully loaded so that
    # inter-relations are set up correctly. We force that here.
    models.get_apps()

    opts = model._meta
    validate_base(cls, model)

    # list_display
    if hasattr(cls, 'list_display'):
        check_isseq(cls, 'list_display', cls.list_display)
        for idx, field in enumerate(cls.list_display):
            if not callable(field):
                if not hasattr(cls, field):
                    if not hasattr(model, field):
                        try:
                            opts.get_field(field)
                        except models.FieldDoesNotExist:
                            raise ImproperlyConfigured("%s.list_display[%d], %r is not a callable or an attribute of %r or found in the model %r."
                                % (cls.__name__, idx, field, cls.__name__, model._meta.object_name))
                    else:
                        # getattr(model, field) could be an X_RelatedObjectsDescriptor
                        f = fetch_attr(cls, model, opts, "list_display[%d]" % idx, field)
                        if isinstance(f, models.ManyToManyField):
                            raise ImproperlyConfigured("'%s.list_display[%d]', '%s' is a ManyToManyField which is not supported."
                                % (cls.__name__, idx, field))

    # search_fields = ()
    if hasattr(cls, 'search_fields'):
        check_isseq(cls, 'search_fields', cls.search_fields)

    # ordering = None
    if cls.ordering:
        check_isseq(cls, 'ordering', cls.ordering)
        for idx, field in enumerate(cls.ordering):
            if field == '?' and len(cls.ordering) != 1:
                raise ImproperlyConfigured("'%s.ordering' has the random "
                        "ordering marker '?', but contains other fields as "
                        "well. Please either remove '?' or the other fields."
                        % cls.__name__)
            if field == '?':
                continue
            if field.startswith('-'):
                field = field[1:]
            # Skip ordering in the format field1__field2 (FIXME: checking
            # this format would be nice, but it's a little fiddly).
            if '__' in field:
                continue
            get_field(cls, model, opts, 'ordering[%d]' % idx, field)

    if hasattr(cls, "readonly_fields"):
        check_readonly_fields(cls, model, opts)

    # list_select_related = False
    # save_as = False
    # save_on_top = False
    for attr in ('list_select_related', 'save_as', 'save_on_top'):
        if not isinstance(getattr(cls, attr), bool):
            raise ImproperlyConfigured("'%s.%s' should be a boolean."
                    % (cls.__name__, attr))

    # compositions = []
    if hasattr(cls, 'inlines'):
        check_isseq(cls, 'compositions', cls.compositions)
        for idx, compose in enumerate(cls.compositions):
            if not issubclass(compose, BaseModel):
                raise ImproperlyConfigured("'%s.compositions[%d]' does not inherit "
                        "from BaseModel." % (cls.__name__, idx))
            if not inline.model:
                raise ImproperlyConfigured("'model' is a required attribute "
                        "of '%s.compositions[%d]'." % (cls.__name__, idx))
            if not issubclass(compose.model, models.Model):
                raise ImproperlyConfigured("'%s.compositions[%d].model' does not "
                        "inherit from models.Model." % (cls.__name__, idx))
            validate_base(compose, compose.model)
            validate_compose(compose, cls, model)

def validate_compose(cls, parent, parent_model):

    # model is already verified to exist and be a Model
    if cls.fk_name: # default value is None
        f = get_field(cls, cls.model, cls.model._meta, 'fk_name', cls.fk_name)
        if not isinstance(f, models.ForeignKey):
            raise ImproperlyConfigured("'%s.fk_name is not an instance of "
                    "models.ForeignKey." % cls.__name__)

    fk = _get_foreign_key(parent_model, cls.model, fk_name=cls.fk_name, can_fail=True)

def validate_base(cls, model):
    opts = model._meta

    # fields
    if cls.fields: # default value is None
        check_isseq(cls, 'fields', cls.fields)
        validate_fields_spec(cls, model, opts, cls.fields, 'fields')
        if cls.fieldsets:
            raise ImproperlyConfigured('Both fieldsets and fields are specified in %s.' % cls.__name__)
        if len(cls.fields) > len(set(cls.fields)):
            raise ImproperlyConfigured('There are duplicate field(s) in %s.fields' % cls.__name__)

    # fieldsets
    if cls.fieldsets: # default value is None
        check_isseq(cls, 'fieldsets', cls.fieldsets)
        for idx, fieldset in enumerate(cls.fieldsets):
            check_isseq(cls, 'fieldsets[%d]' % idx, fieldset)
            if len(fieldset) != 2:
                raise ImproperlyConfigured("'%s.fieldsets[%d]' does not "
                        "have exactly two elements." % (cls.__name__, idx))
            check_isdict(cls, 'fieldsets[%d][1]' % idx, fieldset[1])
            if 'fields' not in fieldset[1]:
                raise ImproperlyConfigured("'fields' key is required in "
                        "%s.fieldsets[%d][1] field options dict."
                        % (cls.__name__, idx))
            validate_fields_spec(cls, model, opts, fieldset[1]['fields'], "fieldsets[%d][1]['fields']" % idx)
        flattened_fieldsets = flatten_fieldsets(cls.fieldsets)
        if len(flattened_fieldsets) > len(set(flattened_fieldsets)):
            raise ImproperlyConfigured('There are duplicate field(s) in %s.fieldsets' % cls.__name__)

    # exclude
    if cls.exclude: # default value is None
        check_isseq(cls, 'exclude', cls.exclude)
        for field in cls.exclude:
            check_formfield(cls, model, opts, 'exclude', field)
            try:
                f = opts.get_field(field)
            except models.FieldDoesNotExist:
                # If we can't find a field on the model that matches,
                # it could be an extra field on the form.
                continue
        if len(cls.exclude) > len(set(cls.exclude)):
            raise ImproperlyConfigured('There are duplicate field(s) in %s.exclude' % cls.__name__)
