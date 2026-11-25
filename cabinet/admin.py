from django.contrib import admin

from .models import (Chitanta, Consultatie, Contract, DetaliuConsultatie, GrilaSpor,
                     Interventie, Medic, Pacient, ParametriSalarizare, Programare, StatPlata)


class ContractInline(admin.StackedInline):
    model = Contract
    can_delete = False


@admin.register(Medic)
class MedicAdmin(admin.ModelAdmin):
    list_display = ["nume", "prenume", "specializare", "telefon"]
    search_fields = ["nume", "prenume", "cnp"]
    inlines = [ContractInline]


@admin.register(Pacient)
class PacientAdmin(admin.ModelAdmin):
    list_display = ["nr_fisa", "nume", "prenume", "data_nasterii", "telefon", "data_intocmirii"]
    search_fields = ["nume", "prenume", "telefon", "nr_fisa"]


@admin.register(Programare)
class ProgramareAdmin(admin.ModelAdmin):
    list_display = ["data", "ora", "pacient", "medic", "status"]
    list_filter = ["status", "medic", "data"]
    search_fields = ["pacient__nume", "pacient__prenume"]
    date_hierarchy = "data"


@admin.register(Interventie)
class InterventieAdmin(admin.ModelAdmin):
    list_display = ["denumire", "cost_materiale", "tarif_medic", "pret_total"]
    search_fields = ["denumire"]


class DetaliuInline(admin.TabularInline):
    model = DetaliuConsultatie
    extra = 1
    fields = ["interventie", "cantitate", "cost_materiale_aplicat", "tarif_aplicat", "observatii"]


class ChitantaInline(admin.TabularInline):
    model = Chitanta
    extra = 0


@admin.register(Consultatie)
class ConsultatieAdmin(admin.ModelAdmin):
    list_display = ["id", "data_consultatie", "pacient", "medic", "cost", "achitat", "rest"]
    list_filter = ["data_consultatie", "programare__medic"]
    search_fields = ["programare__pacient__nume", "programare__pacient__prenume"]
    readonly_fields = ["cost", "achitat", "rest"]
    inlines = [DetaliuInline, ChitantaInline]

    @admin.display(description="cost total")
    def cost(self, obj):
        return obj.cost_total()

    @admin.display(description="achitat")
    def achitat(self, obj):
        return obj.total_achitat()

    @admin.display(description="rest de plată")
    def rest(self, obj):
        return obj.rest_de_plata()


@admin.register(Chitanta)
class ChitantaAdmin(admin.ModelAdmin):
    list_display = ["nr_chitanta", "data_emiterii", "consultatie", "suma_achitata"]
    list_filter = ["data_emiterii"]
    date_hierarchy = "data_emiterii"


admin.site.register(GrilaSpor)
admin.site.register(ParametriSalarizare)


@admin.register(StatPlata)
class StatPlataAdmin(admin.ModelAdmin):
    list_display = ["medic", "luna", "an", "nr_consultatii", "salariu_brut", "cas", "impozit", "salariu_net"]
    list_filter = ["an", "luna", "medic"]