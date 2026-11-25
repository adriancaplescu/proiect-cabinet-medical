from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

RECEPTIE = 'Receptie'
MEDIC = 'Medic'
PACIENT = 'Pacient'


def are_rol(user, *roluri):
    """Superuserul are acces peste tot; ceilalți doar dacă sunt într-unul din grupuri."""
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name__in=roluri).exists()


def rol_necesar(*roluri):
    """Decorator pentru pagini: cere login și unul dintre rolurile date."""
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not are_rol(request.user, *roluri):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


def roluri_utilizator(request):
    """Context processor: în orice template avem acces la `rol_receptie`, `rol_medic`, `rol_pacient`."""
    u = request.user
    return {
        'rol_receptie': are_rol(u, RECEPTIE),
        'rol_medic': u.is_authenticated and u.groups.filter(name=MEDIC).exists(),
        'rol_pacient': u.is_authenticated and u.groups.filter(name=PACIENT).exists(),
    }
