from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render

from .models import Chitanta, Consultatie, Programare
from .roluri import MEDIC, PACIENT, RECEPTIE, are_rol, rol_necesar


@login_required
def acasa(request):
    """După login, fiecare utilizator ajunge pe pagina rolului său."""
    u = request.user
    if are_rol(u, RECEPTIE):
        return redirect('receptie_acasa')
    if u.groups.filter(name=MEDIC).exists():
        return redirect('medic_acasa')
    if u.groups.filter(name=PACIENT).exists():
        return redirect('pacient_acasa')
    return render(request, 'cabinet/fara_rol.html')


@rol_necesar(RECEPTIE)
def receptie_acasa(request):
    azi = date.today()
    restante = [c for c in Consultatie.objects.all() if c.rest_de_plata() > 0]
    context = {
        'azi': azi,
        'programari_azi': Programare.objects.filter(data=azi).select_related('pacient', 'medic'),
        'incasat_azi': Chitanta.objects.filter(data_emiterii=azi)
                                       .aggregate(t=Sum('suma_achitata'))['t'] or 0,
        'incasat_luna': Chitanta.objects.filter(data_emiterii__year=azi.year,
                                                data_emiterii__month=azi.month)
                                        .aggregate(t=Sum('suma_achitata'))['t'] or 0,
        'nr_restante': len(restante),
        'total_restante': sum(c.rest_de_plata() for c in restante),
    }
    return render(request, 'cabinet/receptie_acasa.html', context)


@rol_necesar(MEDIC)
def medic_acasa(request):
    medic = getattr(request.user, 'medic', None)
    if medic is None:
        return render(request, 'cabinet/fara_rol.html', {'mesaj': 'Contul nu este legat de un medic.'})
    azi = date.today()
    context = {
        'medic': medic,
        'azi': azi,
        'programari_azi': medic.programari.filter(data=azi).select_related('pacient'),
        'programari_viitoare': medic.programari.filter(data__gt=azi, status='programata')
                                               .select_related('pacient')[:10],
        'consultatii_luna': Consultatie.objects.filter(programare__medic=medic,
                                                       data_consultatie__year=azi.year,
                                                       data_consultatie__month=azi.month).count(),
        'de_completat': medic.programari.filter(data__lt=azi, status='programata',
                                                consultatie__isnull=True).select_related('pacient'),
        'recente': Consultatie.objects.filter(programare__medic=medic)
                                      .select_related('programare__pacient')
                                      .prefetch_related('detalii')[:8],
    }
    return render(request, 'cabinet/medic_acasa.html', context)


@rol_necesar(PACIENT)
def pacient_acasa(request):
    pacient = getattr(request.user, 'pacient', None)
    if pacient is None:
        return render(request, 'cabinet/fara_rol.html', {'mesaj': 'Contul nu este legat de o fișă de pacient.'})
    azi = date.today()
    consultatii = (Consultatie.objects.filter(programare__pacient=pacient)
                   .select_related('programare__medic').prefetch_related('chitante', 'detalii'))
    context = {
        'pacient': pacient,
        'programari_viitoare': pacient.programari.filter(data__gte=azi, status='programata')
                                                 .select_related('medic'),
        'consultatii': consultatii,
        'total_rest': sum(c.rest_de_plata() for c in consultatii),
    }
    return render(request, 'cabinet/pacient_acasa.html', context)
