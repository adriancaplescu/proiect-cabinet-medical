from datetime import date

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Max, Min
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ConsultatieForm, DetaliiFormSet
from .models import Consultatie, Medic, Pacient, Programare, StatPlata
from .roluri import MEDIC, RECEPTIE, rol_necesar
from .views_incasari import LUNI


def _medicul_meu(request):
    return getattr(request.user, 'medic', None)


def _fara_medic(request):
    return render(request, 'cabinet/fara_rol.html', {'mesaj': 'Contul nu este legat de un medic.'})


@rol_necesar(MEDIC)
def consulta(request, programare_id):
    """Foaia de consultație: se completează la prezentarea pacientului."""
    medic = _medicul_meu(request)
    if medic is None:
        return _fara_medic(request)
    prog = get_object_or_404(Programare.objects.select_related('pacient'), pk=programare_id, medic=medic)

    if hasattr(prog, 'consultatie'):
        return redirect('consultatie', pk=prog.consultatie.pk)
    if prog.status != 'programata':
        messages.error(request, 'Programarea a fost anulată.')
        return redirect('medic_acasa')
    if prog.data > date.today():
        messages.error(request, 'Consultația se poate completa doar în ziua programării sau după.')
        return redirect('medic_acasa')

    cons = Consultatie(programare=prog, data_consultatie=date.today())
    return _foaie_consultatie(request, cons, nou=True)


@rol_necesar(MEDIC)
def consultatie(request, pk):
    """Vizualizare / modificare consultație existentă (doar ale medicului logat)."""
    medic = _medicul_meu(request)
    if medic is None:
        return _fara_medic(request)
    cons = get_object_or_404(Consultatie.objects.select_related('programare__pacient'),
                             pk=pk, programare__medic=medic)
    return _foaie_consultatie(request, cons, nou=False)


def _foaie_consultatie(request, cons, nou):
    # după ce s-a emis o chitanță, consultația nu se mai modifică (ar schimba suma datorată)
    blocata = not nou and cons.chitante.exists()

    if request.method == 'POST' and not blocata:
        form = ConsultatieForm(request.POST, instance=cons)
        formset = DetaliiFormSet(request.POST, instance=cons)
        if form.is_valid() and formset.is_valid():
            if not nou and not form.has_changed() and not formset.has_changed():
                messages.info(request, 'Nu ai modificat nimic.')
                return redirect('consultatie', pk=cons.pk)
            with transaction.atomic():           # totul se salvează împreună, sau nimic
                cons = form.save()
                for f in formset.forms:
                    # dacă s-a schimbat intervenția, prețurile se recopiază din catalog
                    if f.instance.pk and 'interventie' in f.changed_data:
                        f.instance.cost_materiale_aplicat = None
                        f.instance.tarif_aplicat = None
                formset.instance = cons
                formset.save()
                prog = cons.programare
                prog.status = 'efectuata'
                prog.save(update_fields=['status'])
            if nou:
                messages.success(request, f'Consultația a fost salvată. Cost total: {cons.cost_total()} lei.')
            else:
                messages.success(request, f'Modificările au fost salvate. Cost total nou: {cons.cost_total()} lei.')
            return redirect('consultatie', pk=cons.pk)
        else:
            messages.error(request, 'Consultația nu a fost salvată. Verifică erorile marcate cu roșu.')
    else:
        form = ConsultatieForm(instance=cons)
        formset = DetaliiFormSet(instance=cons)

    return render(request, 'cabinet/medic/consultatie.html', {
        'cons': cons, 'prog': cons.programare, 'pacient': cons.programare.pacient,
        'form': form, 'formset': formset, 'nou': nou, 'blocata': blocata,
    })


def context_pacienti_medic(request, medic):
    """Pacienții consultați de un medic într-o lună sau într-un an (folosit de medic și de recepție)."""
    azi = date.today()
    tip = request.GET.get('tip', 'luna')
    try:
        an = int(request.GET.get('an', azi.year))
        luna = int(request.GET.get('luna', azi.month))
    except ValueError:
        an, luna = azi.year, azi.month

    consultatii = Consultatie.objects.filter(programare__medic=medic, data_consultatie__year=an)
    if tip == 'luna':
        consultatii = consultatii.filter(data_consultatie__month=luna)
        titlu = f'Pacienți consultați — {LUNI[luna]} {an}'
    else:
        tip = 'an'
        titlu = f'Pacienți consultați — anul {an}'

    pacienti = (Pacient.objects.filter(programari__consultatie__in=consultatii)
                .annotate(nr=Count('programari__consultatie'),
                          prima=Min('programari__consultatie__data_consultatie'),
                          ultima=Max('programari__consultatie__data_consultatie'))
                .order_by('nume', 'prenume'))
    return {
        'medic': medic, 'pacienti': pacienti, 'tip': tip, 'an': an, 'luna': luna, 'titlu': titlu,
        'nr_consultatii': consultatii.count(),
        'consultatii': consultatii.select_related('programare__pacient').order_by('data_consultatie'),
        'luni': list(enumerate(LUNI))[1:], 'ani': range(azi.year - 3, azi.year + 1),
    }


@rol_necesar(MEDIC)
def pacientii_mei(request):
    medic = _medicul_meu(request)
    if medic is None:
        return _fara_medic(request)
    return render(request, 'cabinet/medic/pacienti.html', context_pacienti_medic(request, medic))


@rol_necesar(RECEPTIE)
def pacienti_pe_medic(request):
    """Recepția alege medicul din listă și vede pacienții lui pe lună sau pe an."""
    medici = Medic.objects.all()
    medic = medici.filter(pk=request.GET.get('medic') or 0).first() or medici.first()
    if medic is None:
        return render(request, 'cabinet/fara_rol.html', {'mesaj': 'Nu există niciun medic în baza de date.'})
    context = context_pacienti_medic(request, medic)
    context.update(medici=medici, receptie=True)
    return render(request, 'cabinet/medic/pacienti.html', context)


@rol_necesar(MEDIC)
def fluturasii_mei(request):
    medic = _medicul_meu(request)
    if medic is None:
        return _fara_medic(request)
    state = [(s, LUNI[s.luna]) for s in StatPlata.objects.filter(medic=medic)]
    return render(request, 'cabinet/medic/fluturasi.html', {'medic': medic, 'state': state})
