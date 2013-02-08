from django.template import Library
from bwp.conf import settings
from django.utils.translation import ugettext_lazy as _

APP_LABELS = getattr(settings, 'APP_LABELS',
    {
        'admin':            _('administration'),
        'auth':             _('authentication'),
        'sites':            _('sites'),
    }
)

register = Library()

@register.simple_tag
#~ @register.filter
def app_label_locale(app_name):
    try:
        return APP_LABELS[app_name.lower()].title()
    except:
        pass
    for app in settings.INSTALLED_APPS:
        if app_name.lower() in app.lower():
            L = app.split('.')
            if len(L) == 1:
                try:
                    app = __import__(app, fromlist=[''])
                except Exception as e:
                    print e
            elif len(L) >= 2:
                try:
                    module = __import__('.'.join(L[:-1]), fromlist=[''])
                    app = getattr(module, L[-1])
                except Exception as e:
                    print e
            try:
                return app.__label__.title()
            except Exception as e:
                print app.__name__, e
                return app_name
    return app_name
