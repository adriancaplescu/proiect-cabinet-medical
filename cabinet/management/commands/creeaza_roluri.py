from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from cabinet.models import Medic, Pacient
from cabinet.roluri import MEDIC, PACIENT, RECEPTIE


def cont(username, parola, prenume, nume, grup):
    user, creat = User.objects.get_or_create(username=username,
                                             defaults={'first_name': prenume, 'last_name': nume})
    if creat:
        user.set_password(parola)
        user.save()
    user.groups.add(grup)
    return user


class Command(BaseCommand):
    help = 'Creează grupurile Receptie, Medic, Pacient și conturi de test pentru fiecare.'

    def handle(self, *args, **opt):
        g_rec, _ = Group.objects.get_or_create(name=RECEPTIE)
        g_med, _ = Group.objects.get_or_create(name=MEDIC)
        g_pac, _ = Group.objects.get_or_create(name=PACIENT)

        cont('receptie', 'receptie123', 'Recepție', 'Cabinet', g_rec)
        self.stdout.write('  receptie / receptie123')

        for medic in Medic.objects.all():
            username = f'dr.{medic.nume.lower()}'
            medic.user = cont(username, 'medic123', medic.prenume, medic.nume, g_med)
            medic.save()
            self.stdout.write(f'  {username} / medic123  ->  {medic}')

        for pacient in Pacient.objects.order_by('nr_fisa')[:3]:
            username = pacient.nume.lower()
            pacient.user = cont(username, 'pacient123', pacient.prenume, pacient.nume, g_pac)
            pacient.save()
            self.stdout.write(f'  {username} / pacient123  ->  {pacient}')

        self.stdout.write(self.style.SUCCESS('Gata: grupuri și conturi create.'))
