from django import template

register = template.Library()


@register.filter
def get_turkish_name(class_name):
    """Convert class name to Turkish equivalent"""
    turkish_names = {
        "person": "İnsan",
        "car": "Araç",
        "truck": "Kamyon",
        "bicycle": "Bisiklet",
        "motorcycle": "Motosiklet",
        "bus": "Otobüs",
        "dog": "Köpek",
        "cat": "Kedi",
        "waste": "Çöp",
        "garbage": "Çöp",
        "construction": "İnşaat",
        "debris": "Moloz",
        "graffiti": "Grafiti",
        "pothole": "Çukur",
    }
    return turkish_names.get(class_name.lower(), class_name)


@register.filter
def has_class_name(notification_types, class_name):
    """Check if notification types contain a specific class name"""
    if not notification_types:
        return False
    return any(nt.class_name == class_name for nt in notification_types)


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary safely"""
    if not dictionary:
        return None
    return dictionary.get(key)
