# ACTION_CHECKBOX_NAME is unused, but should stay since its import from here
# has been referenced in documentation.
from bwp.core.helpers import ACTION_CHECKBOX_NAME
from bwp.core.options import ModelBWP, HORIZONTAL, VERTICAL
from bwp.core.options import StackedInline, TabularInline
from bwp.core.sites import BWPSite, site
from bwp.core.filters import (ListFilter, SimpleListFilter,
    FieldListFilter, BooleanFieldListFilter, RelatedFieldListFilter,
    ChoicesFieldListFilter, DateFieldListFilter, AllValuesFieldListFilter)


def autodiscover():
    """
    Auto-discover INSTALLED_APPS bwp.py modules and fail silently when
    not present. This forces an import on them to register any bwp bits they
    may want.
    """

    import copy
    from bwp.conf import settings
    from django.utils.importlib import import_module
    from django.utils.module_loading import module_has_submodule

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        # Attempt to import the app's bwp module.
        try:
            before_import_registry = copy.copy(site._registry)
            import_module('%s.__bwp__' % app)
        except:
            # Reset the model registry to the state before the last import as
            # this import will have to reoccur on the next request and this
            # could raise NotRegistered and AlreadyRegistered exceptions
            # (see #8245).
            site._registry = before_import_registry

            # Decide whether to bubble up this error. If the app just
            # doesn't have an bwp module, we can ignore the error
            # attempting to import it, otherwise we want it to bubble up.
            if module_has_submodule(mod, '__bwp__'):
                raise
