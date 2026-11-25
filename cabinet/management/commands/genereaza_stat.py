from django.core.management.base import BaseCommand

from cabinet.salarizare import genereaza_stat_plata


class Command(BaseCommand):
    help = "Generează statul de plată pentru o lună. Exemplu: python manage.py genereaza_stat 11 2026"

    def add_arguments(self, parser):
        parser.add_argument("luna", type=int)
        parser.add_argument("an", type=int)

    def handle(self, *args, **opt):
        state = genereaza_stat_plata(opt["luna"], opt["an"])
        self.stdout.write(f"Stat de plată {opt['luna']:02d}/{opt['an']}")
        self.stdout.write(f"{'Medic':<22}{'Cons.':>6}{'Spor%':>7}{'Brut':>10}{'CAS':>10}{'Impozit':>10}{'Net':>10}")
        for s in state:
            self.stdout.write(f"{str(s.medic):<22}{s.nr_consultatii:>6}{s.procent_spor:>7}"
                              f"{s.salariu_brut:>10}{s.cas:>10}{s.impozit:>10}{s.salariu_net:>10}")
        self.stdout.write(self.style.SUCCESS(f"Gata: {len(state)} rânduri salvate."))
