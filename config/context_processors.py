from django.conf import settings


def my_setting(request):
    return {"MY_SETTING": settings}


def language_code(request):
    """
    Return language code that will be used as template context.
    """
    return {
        "LANGUAGE_CODE": getattr(request, "LANGUAGE_CODE", "tr")  # Default to Turkish if not set
    }


def get_cookie(request):
    return {"COOKIES": request.COOKIES}


# Add the 'ENVIRONMENT' setting to the template context
def environment(request):
    return {"ENVIRONMENT": settings.ENVIRONMENT}
