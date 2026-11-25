from django.urls import path

from . import views, views_incasari as inc, views_medic as med, views_pacient as pac, views_receptie as rec, views_salarizare as sal

urlpatterns = [
    path('', views.acasa, name='acasa'),
    path('receptie/', views.receptie_acasa, name='receptie_acasa'),
    path('medic/', views.medic_acasa, name='medic_acasa'),
    path('pacient/', views.pacient_acasa, name='pacient_acasa'),

    # Recepție - pacienți
    path('receptie/pacienti/', rec.pacienti_lista, name='pacienti_lista'),
    path('receptie/pacienti/nou/', rec.pacient_editeaza, name='pacient_nou'),
    path('receptie/pacienti/pe-medic/', med.pacienti_pe_medic, name='pacienti_pe_medic'),
    path('receptie/pacienti/<int:nr_fisa>/', rec.pacient_fisa, name='pacient_fisa'),
    path('receptie/pacienti/<int:nr_fisa>/editeaza/', rec.pacient_editeaza, name='pacient_editeaza'),

    # Recepție - programări
    path('receptie/programari/', rec.programari, name='programari'),
    path('receptie/programari/noua/', rec.programare_noua, name='programare_noua'),
    path('receptie/programari/<int:pk>/anuleaza/', rec.programare_anuleaza, name='programare_anuleaza'),

    # Recepție - încasări
    path('receptie/incaseaza/<int:consultatie_id>/', inc.incaseaza, name='incaseaza'),
    path('receptie/chitante/<int:nr>/', inc.chitanta, name='chitanta'),
    path('receptie/restante/', inc.restante, name='restante'),
    path('receptie/incasari/', inc.incasari, name='incasari'),

    # Salarizare
    path('receptie/salarizare/', sal.stat_plata, name='stat_plata'),
    path('fluturas/<int:pk>/', sal.fluturas, name='fluturas'),

    # Medic
    path('medic/consulta/<int:programare_id>/', med.consulta, name='consulta'),
    path('medic/consultatii/<int:pk>/', med.consultatie, name='consultatie'),
    path('medic/pacienti/', med.pacientii_mei, name='pacientii_mei'),
    path('medic/fluturasi/', med.fluturasii_mei, name='fluturasii_mei'),

    # Pacient
    path('pacient/fisa/', pac.fisa_mea, name='fisa_mea'),
    path('pacient/chitante/<int:nr>/', pac.chitanta_mea, name='chitanta_mea'),
    path('pacient/programare/', pac.programare_mea_noua, name='programare_mea_noua'),
    path('pacient/programare/<int:pk>/anuleaza/', pac.programare_mea_anuleaza, name='programare_mea_anuleaza'),
]
