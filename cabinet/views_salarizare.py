from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from .models import StatPlata
from .roluri import RECEPTIE, are_rol, rol_necesar
from .salarizare import genereaza_stat_plata
from .views_incasari import LUNI


def _luna_an(request):
    azi = date.today()
    try:
        luna = int(request.GET.get('luna') or request.POST.get('luna') or azi.month)
        an = int(request.GET.get('an') or request.POST.get('an') or azi.year)
    except ValueError:
        luna, an = azi.month, azi.year
    return luna, an


@rol_necesar(RECEPTIE)
def stat_plata(request):
    """Statul de plată lunar: se generează (sau recalculează) cu un buton și se poate tipări."""
    luna, an = _luna_an(request)

    if request.method == 'POST':
        try:
            state = genereaza_stat_plata(luna, an)
            messages.success(request, f'Statul de plată pe {LUNI[luna]} {an} a fost generat '
                                      f'({len(state)} medici).')
        except ValueError as e:
            messages.error(request, str(e))
        return redirect(f'/receptie/salarizare/?luna={luna}&an={an}')

    randuri = StatPlata.objects.filter(luna=luna, an=an).select_related('medic')
    totaluri = randuri.aggregate(brut=Sum('salariu_brut'), spor=Sum('valoare_spor'), cas=Sum('cas'),
                                 impozit=Sum('impozit'), net=Sum('salariu_net'))
    azi = date.today()
    context = {
        'randuri': randuri,
        'totaluri': totaluri,
        'luna': luna,
        'an': an,
        'nume_luna': LUNI[luna],
        'luni': list(enumerate(LUNI))[1:],
        'ani': range(azi.year - 3, azi.year + 1),
    }
    return render(request, 'cabinet/receptie/stat_plata.html', context)


@login_required
def fluturas(request, pk):
    """Fluturașul de salariu: îl vede recepția sau medicul căruia îi aparține."""
    stat = get_object_or_404(StatPlata.objects.select_related('medic__contract'), pk=pk)
    if not (are_rol(request.user, RECEPTIE) or stat.medic.user_id == request.user.id):
        raise PermissionDenied
    return render(request, 'cabinet/fluturas.html', {'s': stat, 'nume_luna': LUNI[stat.luna]})
