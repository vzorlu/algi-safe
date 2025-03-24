from django import template

register = template.Library()


@register.filter
def has_class_name(notification_types, class_name):
    """
    Check if a class_name exists in notification_types
    """
    return notification_types.filter(class_name=class_name).exists()
