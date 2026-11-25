from datetime import date

from django.contrib import messages
from django.db.models import Sum
from django.db.models.functions import ExtractDay, ExtractMonth
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ChitantaForm
from .models import Chitanta, Consultatie
from .roluri import RECEPTIE, rol_necesar

LUNI = ['', 'Ianuarie', 'Februarie', 'Martie', 'Aprilie', 'Mai', 'Iunie', 'Iulie',
        'August', 'Septembrie', 'Octombrie', 'Noiembrie', 'Decembrie']


@rol_necesar(RECEPTIE)
def incaseaza(request, consultatie_id):
    """Emite o chitanță (integrală sau parțială) pentru o consultație."""
    cons = get_object_or_404(Consultatie.objects.select_related('programare__pacient', 'programare__medic'),
                             pk=consultatie_id)
    rest = cons.rest_de_plata()
    if rest <= 0:
        messages.info(request, 'Consultația este achitată integral.')
        return redirect('pacient_fisa', nr_fisa=cons.pacient.nr_fisa)

    chitanta = Chitanta(consultatie=cons)
    form = ChitantaForm(request.POST or None, instance=chitanta,
                        initial={'suma_achitata': rest, 'data_emiterii': date.today()})
    if request.method == 'POST' and form.is_valid():
        ch = form.save()
        messages.success(request, f'Chitanța nr. {ch.nr_chitanta} a fost emisă ({ch.suma_achitata} lei).')
        return redirect('chitanta', nr=ch.nr_chitanta)
    return render(request, 'cabinet/receptie/incaseaza.html', {'form': form, 'cons': cons, 'rest': rest})


def context_chitanta(ch):
    """Datele afișate pe chitanță (folosite și de recepție, și de pacient)."""
    cons = ch.consultatie
    # cât s-a plătit pe consultație până la această chitanță inclusiv
    platit_pana_acum = (cons.chitante.filter(nr_chitanta__lte=ch.nr_chitanta)
                        .aggregate(t=Sum('suma_achitata'))['t'])
    return {
        'ch': ch,
        'cons': cons,
        'pacient': cons.pacient,
        'cost_total': cons.cost_total(),
        'rest_dupa': cons.cost_total() - platit_pana_acum,
    }


@rol_necesar(RECEPTIE)
def chitanta(request, nr):
    ch = get_object_or_404(Chitanta.objects.select_related('consultatie__programare__pacient',
                                                           'consultatie__programare__medic'),
                           nr_chitanta=nr)
    return render(request, 'cabinet/receptie/chitanta.html', context_chitanta(ch))


@rol_necesar(RECEPTIE)
def restante(request):
    """Pacienții care mai au de achitat sume în contul consultațiilor."""
    consultatii = (Consultatie.objects.select_related('programare__pacient', 'programare__medic')
                   .prefetch_related('detalii', 'chitante').order_by('programare__pacient__nume', 'data_consultatie'))
    pe_pacient = {}
    for c in consultatii:
        rest = c.rest_de_plata()
        if rest > 0:
            rand = pe_pacient.setdefault(c.pacient.nr_fisa, {'pacient': c.pacient, 'consultatii': [], 'total': 0})
            rand['consultatii'].append({'c': c, 'cost': c.cost_total(), 'achitat': c.total_achitat(), 'rest': rest})
            rand['total'] += rest
    randuri = list(pe_pacient.values())
    context = {
        'randuri': randuri,
        'total_general': sum(r['total'] for r in randuri),
        'azi': date.today(),
    }
    return render(request, 'cabinet/receptie/restante.html', context)


@rol_necesar(RECEPTIE)
def incasari(request):
    """Situația încasărilor: pe o zi (chitanțele), pe o lună (pe zile) sau pe un an (pe luni)."""
    azi = date.today()
    tip = request.GET.get('tip', 'zi')
    context = {'tip': tip, 'luni': list(enumerate(LUNI))[1:], 'ani': range(azi.year - 3, azi.year + 1)}

    if tip == 'luna':
        luna = int(request.GET.get('luna', azi.month))
        an = int(request.GET.get('an', azi.year))
        chitante = Chitanta.objects.filter(data_emiterii__year=an, data_emiterii__month=luna)
        randuri = (chitante.annotate(zi=ExtractDay('data_emiterii')).values('zi')
                   .annotate(total=Sum('suma_achitata')).order_by('zi'))
        randuri = [{'eticheta': date(an, luna, r['zi']).strftime('%d.%m.%Y'), 'total': r['total'],
                    'link': f"?tip=zi&data={date(an, luna, r['zi']).isoformat()}"} for r in randuri]
        context.update(titlu=f'Încasări lunare — {LUNI[luna]} {an}', luna=luna, an=an, randuri=randuri)
    elif tip == 'an':
        an = int(request.GET.get('an', azi.year))
        chitante = Chitanta.objects.filter(data_emiterii__year=an)
        randuri = (chitante.annotate(l=ExtractMonth('data_emiterii')).values('l')
                   .annotate(total=Sum('suma_achitata')).order_by('l'))
        randuri = [{'eticheta': LUNI[r['l']], 'total': r['total'],
                    'link': f"?tip=luna&luna={r['l']}&an={an}"} for r in randuri]
        context.update(titlu=f'Încasări pe anul {an}', an=an, randuri=randuri)
    else:
        tip = context['tip'] = 'zi'
        try:
            zi = date.fromisoformat(request.GET.get('data', ''))
        except ValueError:
            zi = azi
        chitante = (Chitanta.objects.filter(data_emiterii=zi)
                    .select_related('consultatie__programare__pacient').order_by('nr_chitanta'))
        context.update(titlu=f'Încasări zilnice — {zi:%d.%m.%Y}', zi=zi, chitante=chitante)

    context['total'] = chitante.aggregate(t=Sum('suma_achitata'))['t'] or 0
    context['nr_chitante'] = chitante.count()
    return render(request, 'cabinet/receptie/incasari.html', context)
