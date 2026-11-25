from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProgramarePacientForm
from .models import Chitanta, Programare
from .roluri import PACIENT, rol_necesar
from .views_incasari import context_chitanta
from .views_receptie import context_fisa


def _pacientul_meu(request):
    """Fișa legată de contul logat (sau None dacă nu e legat de niciun pacient)."""
    return getattr(request.user, 'pacient', None)


@rol_necesar(PACIENT)
def fisa_mea(request):
    pacient = _pacientul_meu(request)
    if pacient is None:
        return render(request, 'cabinet/fara_rol.html', {'mesaj': 'Contul nu este legat de o fișă de pacient.'})
    return render(request, 'cabinet/receptie/pacient_fisa.html', context_fisa(pacient))


@rol_necesar(PACIENT)
def chitanta_mea(request, nr):
    # filtrăm după pacient: dacă chitanța e a altcuiva, primește 404
    ch = get_object_or_404(Chitanta, nr_chitanta=nr, consultatie__programare__pacient__user=request.user)
    return render(request, 'cabinet/receptie/chitanta.html', context_chitanta(ch))


@rol_necesar(PACIENT)
def programare_mea_noua(request):
    pacient = _pacientul_meu(request)
    if pacient is None:
        return render(request, 'cabinet/fara_rol.html', {'mesaj': 'Contul nu este legat de o fișă de pacient.'})
    form = ProgramarePacientForm(request.POST or None, instance=Programare(pacient=pacient),
                                 initial={'data': date.today()})
    if request.method == 'POST' and form.is_valid():
        p = form.save()
        messages.success(request, f'Te-ai programat la {p.medic} pe {p.data:%d.%m.%Y}, ora {p.ora:%H:%M}.')
        return redirect('pacient_acasa')
    return render(request, 'cabinet/receptie/formular.html',
                  {'form': form, 'titlu': 'Programare nouă', 'inapoi': 'pacient_acasa'})


@require_POST
@rol_necesar(PACIENT)
def programare_mea_anuleaza(request, pk):
    p = get_object_or_404(Programare, pk=pk, pacient__user=request.user,
                          status='programata', data__gte=date.today())
    p.status = 'anulata'
    p.save()
    messages.info(request, f'Programarea din {p.data:%d.%m.%Y}, ora {p.ora:%H:%M} a fost anulată.')
    return redirect('pacient_acasa')
