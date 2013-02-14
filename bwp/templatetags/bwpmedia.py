import warnings
from django.template import Library
from django.templatetags.static import PrefixNode

register = Library()

@register.simple_tag
def bwp_media_prefix():
    """
    Returns the string contained in the setting BWP_MEDIA_PREFIX.
    """
    warnings.warn(
        "The bwp_media_prefix template tag is deprecated. "
        "Use the static template tag instead.", PendingDeprecationWarning)
    return PrefixNode.handle_simple("BWP_MEDIA_PREFIX")
