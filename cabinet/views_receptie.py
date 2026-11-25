from datetime import date, timedelta

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import PacientForm, ProgramareForm
from .models import Consultatie, Medic, Pacient, Programare
from .roluri import RECEPTIE, rol_necesar


# ---------- Pacienți ----------

@rol_necesar(RECEPTIE)
def pacienti_lista(request):
    q = request.GET.get('q', '').strip()
    pacienti = Pacient.objects.all()
    if q:
        filtru = Q(nume__icontains=q) | Q(prenume__icontains=q) | Q(telefon__icontains=q)
        if q.isdigit():
            filtru |= Q(nr_fisa=int(q))
        pacienti = pacienti.filter(filtru)
    return render(request, 'cabinet/receptie/pacienti_lista.html', {'pacienti': pacienti, 'q': q})


@rol_necesar(RECEPTIE)
def pacient_editeaza(request, nr_fisa=None):
    pacient = get_object_or_404(Pacient, nr_fisa=nr_fisa) if nr_fisa else None
    form = PacientForm(request.POST or None, instance=pacient)
    if request.method == 'POST' and form.is_valid():
        pacient = form.save()
        messages.success(request, f'Fișa pacientului {pacient.nume} {pacient.prenume} a fost salvată.')
        return redirect('pacient_fisa', nr_fisa=pacient.nr_fisa)
    titlu = f'Editează fișa nr. {pacient.nr_fisa}' if pacient else 'Fișă pacient nouă'
    return render(request, 'cabinet/receptie/formular.html',
                  {'form': form, 'titlu': titlu, 'inapoi': 'pacienti_lista'})


def context_fisa(pacient):
    """Datele afișate pe fișa pacientului (folosite și de recepție, și de pacient)."""
    consultatii = (Consultatie.objects.filter(programare__pacient=pacient)
                   .select_related('programare__medic')
                   .prefetch_related('detalii__interventie', 'chitante'))
    return {
        'pacient': pacient,
        'consultatii': consultatii,
        'programari_viitoare': pacient.programari.filter(data__gte=date.today(), status='programata'),
        'total_rest': sum(c.rest_de_plata() for c in consultatii),
    }


@rol_necesar(RECEPTIE)
def pacient_fisa(request, nr_fisa):
    pacient = get_object_or_404(Pacient, nr_fisa=nr_fisa)
    return render(request, 'cabinet/receptie/pacient_fisa.html', context_fisa(pacient))


# ---------- Programări ----------

def _citeste_data(text):
    try:
        return date.fromisoformat(text)
    except (TypeError, ValueError):
        return date.today()


@rol_necesar(RECEPTIE)
def programari(request):
    zi = _citeste_data(request.GET.get('data'))
    perioada = request.GET.get('perioada', 'zi')
    medic_id = request.GET.get('medic', '')

    if perioada == 'saptamana':
        inceput = zi - timedelta(days=zi.weekday())          # luni
        sfarsit = inceput + timedelta(days=6)                # duminică
        pas = timedelta(days=7)
    else:
        perioada = 'zi'
        inceput = sfarsit = zi
        pas = timedelta(days=1)

    lista = (Programare.objects.filter(data__range=(inceput, sfarsit))
             .select_related('pacient', 'medic').order_by('data', 'ora'))
    if medic_id:
        lista = lista.filter(medic_id=medic_id)

    context = {
        'programari': lista,
        'perioada': perioada,
        'zi': zi,
        'inceput': inceput,
        'sfarsit': sfarsit,
        'anterior': (zi - pas).isoformat(),
        'urmator': (zi + pas).isoformat(),
        'azi': date.today().isoformat(),
        'medici': Medic.objects.all(),
        'medic_id': medic_id,
    }
    return render(request, 'cabinet/receptie/programari.html', context)


@rol_necesar(RECEPTIE)
def programare_noua(request):
    initial = {'data': request.GET.get('data') or date.today()}
    if request.GET.get('pacient'):
        initial['pacient'] = request.GET['pacient']
    form = ProgramareForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        p = form.save()
        messages.success(request, f'Programare salvată: {p.pacient.nume} la {p.medic}, '
                                  f'{p.data:%d.%m.%Y} ora {p.ora:%H:%M}.')
        return redirect(f"/receptie/programari/?data={p.data.isoformat()}")
    return render(request, 'cabinet/receptie/formular.html',
                  {'form': form, 'titlu': 'Programare nouă', 'inapoi': 'programari'})


@require_POST
@rol_necesar(RECEPTIE)
def programare_anuleaza(request, pk):
    p = get_object_or_404(Programare, pk=pk, status='programata')
    p.status = 'anulata'
    p.save()
    messages.info(request, f'Programarea lui {p.pacient.nume} din {p.data:%d.%m.%Y} a fost anulată.')
    return redirect(f"/receptie/programari/?data={p.data.isoformat()}")
