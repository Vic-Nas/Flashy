"""Template rendering utilities."""
from django.template import loader
from django.http import HttpResponse
from config import SHOW_COFFEE, COFFEE_USERNAME


def render_template(template_name, context):
    """Simple template rendering."""
    template = loader.get_template(template_name)
    return template.render(context)


def service_not_found(service, reason=None):
    """Show friendly 404 page when service doesn't exist."""
    html = render_template('404.html', {
        'service': service,
        'reason': reason,
        'show_coffee': SHOW_COFFEE,
        'coffee_username': COFFEE_USERNAME,
    })
    return HttpResponse(html, status=404)


def path_not_found(service, path, target_domain):
    """Show 404 page when service exists but path doesn't."""
    html = render_template('error.html', {
        'title': '404 - Path Not Found',
        'message': f'The service "{service}" exists, but this path was not found on the backend.',
        'error_type': 'HTTP 404 Not Found',
        'service': service,
        'target': target_domain,
        'show_coffee': SHOW_COFFEE,
        'coffee_username': COFFEE_USERNAME,
    })
    return HttpResponse(html, status=404)


def error_page(title, message, error_type, service=None, target=None, status=502):
    """Show error page for backend issues."""
    html = render_template('error.html', {
        'title': title,
        'message': message,
        'error_type': error_type,
        'service': service,
        'target': target,
        'show_coffee': SHOW_COFFEE,
        'coffee_username': COFFEE_USERNAME,
    })
    return HttpResponse(html, status=status)
