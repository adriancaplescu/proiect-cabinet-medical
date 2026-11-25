from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from .models import Consultatie, GrilaSpor, Medic, ParametriSalarizare, StatPlata


def rotunjeste(valoare):
    return valoare.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def procent_spor(nr_consultatii):
    """Cel mai mare procent din grilă pentru care medicul atinge pragul."""
    prag = (GrilaSpor.objects.filter(nr_min_consultatii__lte=nr_consultatii)
            .order_by("-nr_min_consultatii").first())
    return prag.procent_spor if prag else Decimal("0")


def genereaza_stat_plata(luna, an):
    """Calculează (sau recalculează) statul de plată pentru toți medicii, pe o lună."""
    parametri = (ParametriSalarizare.objects.filter(data_valabilitate__lte=date(an, luna, 1))
                 .order_by("-data_valabilitate").first())
    if parametri is None:
        raise ValueError("Nu există parametri de salarizare valabili pentru luna aleasă.")

    rezultate = []
    for medic in Medic.objects.filter(contract__isnull=False):
        nr = Consultatie.objects.filter(programare__medic=medic,
                                        data_consultatie__month=luna,
                                        data_consultatie__year=an).count()
        salariu = medic.contract.salariu_incadrare
        procent = procent_spor(nr)
        spor = rotunjeste(salariu * procent / 100)
        brut = salariu + spor
        cas = rotunjeste(brut * parametri.cota_cas / 100)
        baza = brut - cas
        impozit = rotunjeste(baza * parametri.cota_impozit / 100)
        net = brut - cas - impozit

        stat, _ = StatPlata.objects.update_or_create(
            medic=medic, luna=luna, an=an,
            defaults=dict(nr_consultatii=nr, salariu_incadrare=salariu, procent_spor=procent,
                          valoare_spor=spor, salariu_brut=brut, cas=cas, baza_impozabila=baza,
                          impozit=impozit, salariu_net=net, data_generarii=date.today()),
        )
        rezultate.append(stat)
    return rezultate