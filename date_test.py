# Populează baza cu date de test.
# Rulare: python manage.py shell < date_test.py
import random
from datetime import date, time, timedelta
from decimal import Decimal

from cabinet.models import (Chitanta, Consultatie, Contract, DetaliuConsultatie, GrilaSpor,
                            Interventie, Medic, Pacient, ParametriSalarizare, Programare)

if Medic.objects.exists():
    print("Baza are deja date. Nu am adăugat nimic.")
else:
    random.seed(42)

    # --- Parametri salarizare și grilă sporuri ---
    ParametriSalarizare.objects.create(data_valabilitate=date(2026, 1, 1),
                                       cota_cas=Decimal("25"), cota_impozit=Decimal("10"))
    GrilaSpor.objects.create(nr_min_consultatii=11, procent_spor=Decimal("5"))
    GrilaSpor.objects.create(nr_min_consultatii=21, procent_spor=Decimal("10"))

    # --- Medici + contracte ---
    medici_date = [
        ("Popescu", "Andrei", "1800512350011", "TM", "123456", "Str. Republicii 10, Timișoara",
         "0721000001", "Medicină generală", date(2022, 3, 1), "6000"),
        ("Ionescu", "Maria", "2850923350022", "TM", "234567", "Bd. Revoluției 5, Timișoara",
         "0721000002", "Cardiologie", date(2023, 9, 15), "7500"),
        ("Stan", "Mihai", "1900115350033", "TM", "345678", "Str. Mărășești 3, Timișoara",
         "0721000003", "Dermatologie", date(2024, 2, 1), "6500"),
    ]
    medici = []
    for i, (nume, prenume, cnp, serie, nr, adresa, tel, spec, data_ang, sal) in enumerate(medici_date, 1):
        m = Medic.objects.create(nume=nume, prenume=prenume, cnp=cnp, serie_ci=serie, nr_ci=nr,
                                 adresa=adresa, telefon=tel, specializare=spec)
        Contract.objects.create(nr_contract=f"CIM-{i:03d}", medic=m,
                                data_angajarii=data_ang, salariu_incadrare=Decimal(sal))
        medici.append(m)

    # --- Pacienți ---
    pacienti_date = [
        ("Georgescu", "Ana", date(1985, 4, 12), "Str. Florilor 7, Timișoara", "0744000001"),
        ("Dumitru", "Vlad", date(1972, 11, 3), "Str. Lugojului 22, Timișoara", "0744000002"),
        ("Matei", "Elena", date(1990, 6, 25), "Calea Aradului 15, Timișoara", "0744000003"),
        ("Radu", "Cristian", date(1964, 1, 30), "Str. Gheorghe Lazăr 9, Timișoara", "0744000004"),
        ("Constantin", "Ioana", date(2001, 8, 17), "Str. Eroilor 4, Dumbrăvița", "0744000005"),
        ("Moldovan", "Paul", date(1958, 3, 8), "Str. Sagului 101, Timișoara", "0744000006"),
        ("Lupu", "Diana", date(1995, 12, 1), "Str. Ciprian Porumbescu 2, Timișoara", "0744000007"),
        ("Barbu", "Sorin", date(1980, 9, 19), "Str. Iosif Bulbuca 30, Timișoara", "0744000008"),
    ]
    pacienti = [Pacient.objects.create(nume=n, prenume=p, data_nasterii=dn, adresa=a, telefon=t,
                                       data_intocmirii=date(2026, 9, 1))
                for n, p, dn, a, t in pacienti_date]

    # --- Catalog intervenții ---
    interventii_date = [
        ("Consultație generală", "0", "150"),
        ("Electrocardiogramă (EKG)", "20", "130"),
        ("Ecografie abdominală", "30", "220"),
        ("Analize de sânge uzuale", "60", "40"),
        ("Injecție intramusculară", "15", "35"),
        ("Pansament", "25", "45"),
        ("Măsurare tensiune arterială", "0", "30"),
        ("Dermatoscopie", "10", "200"),
    ]
    interventii = [Interventie.objects.create(denumire=d, cost_materiale=Decimal(c), tarif_medic=Decimal(t))
                   for d, c, t in interventii_date]

    # --- Programări + consultații în noiembrie 2026 ---
    # Popescu: 12 consultații (peste 10 -> spor 5%), Ionescu: 7, Stan: 4
    nr_consultatii = {medici[0]: 12, medici[1]: 7, medici[2]: 4}
    ore = [time(h, m) for h in range(9, 16) for m in (0, 30)]
    zile_lucru = [date(2026, 11, d) for d in range(2, 20) if date(2026, 11, d).weekday() < 5]

    for medic, n in nr_consultatii.items():
        sloturi = random.sample([(z, o) for z in zile_lucru for o in ore], n)
        for zi, ora in sorted(sloturi):
            prog = Programare.objects.create(pacient=random.choice(pacienti), medic=medic,
                                             data=zi, ora=ora, status="efectuata")
            cons = Consultatie.objects.create(programare=prog, data_consultatie=zi,
                                              observatii=random.choice(["", "Revine la control peste o lună.",
                                                                        "Tratament recomandat.", "Stare bună."]))
            for interv in random.sample(interventii, random.randint(1, 3)):
                DetaliuConsultatie.objects.create(consultatie=cons, interventie=interv,
                                                  cantitate=random.choice([1, 1, 1, 2]))
            cost = cons.cost_total()
            # 70% plătesc integral, 20% parțial (în 1-2 rate), 10% nu au plătit încă
            r = random.random()
            if r < 0.7:
                Chitanta.objects.create(consultatie=cons, data_emiterii=zi, suma_achitata=cost)
            elif r < 0.9:
                prima = (cost / 2).quantize(Decimal("1"))
                Chitanta.objects.create(consultatie=cons, data_emiterii=zi, suma_achitata=prima)
                if random.random() < 0.5:
                    Chitanta.objects.create(consultatie=cons, data_emiterii=zi + timedelta(days=3),
                                            suma_achitata=(cost - prima) / 2)

    # --- Programări viitoare (fără consultație încă) ---
    for i in range(10):
        zi = date(2026, 11, 23) + timedelta(days=i % 5)
        Programare.objects.create(pacient=pacienti[i % len(pacienti)], medic=medici[i % 3],
                                  data=zi, ora=time(9 + i % 6, 0), status="programata")

    print("Gata!")
    print(f"  Medici: {Medic.objects.count()}, Pacienți: {Pacient.objects.count()}, "
          f"Intervenții: {Interventie.objects.count()}")
    print(f"  Programări: {Programare.objects.count()}, Consultații: {Consultatie.objects.count()}, "
          f"Chitanțe: {Chitanta.objects.count()}")
    restante = [c for c in Consultatie.objects.all() if c.rest_de_plata() > 0]
    print(f"  Consultații cu rest de plată: {len(restante)}")
