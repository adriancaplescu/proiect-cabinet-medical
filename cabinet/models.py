from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum


class Medic(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name="cont utilizator")
    nume = models.CharField(max_length=50)
    prenume = models.CharField(max_length=50)
    cnp = models.CharField("CNP", max_length=13, unique=True)
    serie_ci = models.CharField("serie CI", max_length=2)
    nr_ci = models.CharField("număr CI", max_length=6)
    adresa = models.CharField("adresă", max_length=200)
    telefon = models.CharField(max_length=15)
    specializare = models.CharField(max_length=100)

    class Meta:
        db_table = "medici"
        verbose_name = "medic"
        verbose_name_plural = "medici"
        ordering = ["nume", "prenume"]

    def __str__(self):
        return f"Dr. {self.nume} {self.prenume}"


class Contract(models.Model):
    nr_contract = models.CharField("număr contract", max_length=20, unique=True)
    medic = models.OneToOneField(Medic, on_delete=models.CASCADE, related_name="contract")
    data_angajarii = models.DateField("data angajării")
    salariu_incadrare = models.DecimalField("salariu de încadrare", max_digits=10, decimal_places=2)

    class Meta:
        db_table = "contracte"
        verbose_name = "contract"
        verbose_name_plural = "contracte"

    def __str__(self):
        return f"Contract {self.nr_contract} - {self.medic}"


class Pacient(models.Model):
    nr_fisa = models.AutoField("număr fișă", primary_key=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name="cont utilizator")
    data_intocmirii = models.DateField("data întocmirii", default=date.today)
    nume = models.CharField(max_length=50)
    prenume = models.CharField(max_length=50)
    data_nasterii = models.DateField("data nașterii")
    adresa = models.CharField("adresă", max_length=200)
    telefon = models.CharField(max_length=15)

    class Meta:
        db_table = "pacienti"
        verbose_name = "pacient"
        verbose_name_plural = "pacienți"
        ordering = ["nume", "prenume"]

    def __str__(self):
        return f"{self.nume} {self.prenume} (fișa {self.nr_fisa})"


class Programare(models.Model):
    STATUS = [
        ("programata", "Programată"),
        ("efectuata", "Efectuată"),
        ("anulata", "Anulată"),
    ]
    pacient = models.ForeignKey(Pacient, on_delete=models.PROTECT, related_name="programari")
    medic = models.ForeignKey(Medic, on_delete=models.PROTECT, related_name="programari")
    data = models.DateField()
    ora = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS, default="programata")

    class Meta:
        db_table = "programari"
        verbose_name = "programare"
        verbose_name_plural = "programări"
        ordering = ["data", "ora"]

    def clean(self):
        # La creare: nu se poate programa în trecut (programările existente rămân editabile)
        if self._state.adding and self.data and self.ora:
            if self.data < date.today():
                raise ValidationError({"data": "Nu se pot face programări la o dată din trecut."})
            if datetime.combine(self.data, self.ora) < datetime.now():
                raise ValidationError({"ora": "Ora aleasă a trecut deja."})

        # Un medic nu poate avea două programări active la aceeași dată și oră.
        # Programările anulate nu ocupă ora, deci locul se poate reprograma.
        if self.status == "anulata" or not (self.medic_id and self.data and self.ora):
            return
        ocupat = (Programare.objects.filter(medic_id=self.medic_id, data=self.data, ora=self.ora)
                  .exclude(status="anulata").exclude(pk=self.pk).exists())
        if ocupat:
            raise ValidationError("Medicul are deja o programare la această dată și oră.")

    def __str__(self):
        return f"{self.data} {self.ora:%H:%M} - {self.pacient.nume} la {self.medic}"


class Interventie(models.Model):
    denumire = models.CharField(max_length=100, unique=True)
    cost_materiale = models.DecimalField(max_digits=10, decimal_places=2)
    tarif_medic = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "interventii"
        verbose_name = "intervenție"
        verbose_name_plural = "catalog intervenții"
        ordering = ["denumire"]

    def __str__(self):
        return self.denumire

    @property
    def pret_total(self):
        return self.cost_materiale + self.tarif_medic


class Consultatie(models.Model):
    programare = models.OneToOneField(Programare, on_delete=models.PROTECT, related_name="consultatie")
    data_consultatie = models.DateField("data consultației", default=date.today)
    observatii = models.TextField("observații", blank=True)

    class Meta:
        db_table = "consultatii"
        verbose_name = "consultație"
        verbose_name_plural = "consultații"
        ordering = ["-data_consultatie"]

    def __str__(self):
        return f"Consultația {self.pk} - {self.programare.pacient.nume} ({self.data_consultatie})"

    @property
    def medic(self):
        return self.programare.medic

    @property
    def pacient(self):
        return self.programare.pacient

    def cost_total(self):
        return sum((d.valoare for d in self.detalii.all()), Decimal("0"))

    def total_achitat(self):
        return self.chitante.aggregate(t=Sum("suma_achitata"))["t"] or Decimal("0")

    def rest_de_plata(self):
        return self.cost_total() - self.total_achitat()


class DetaliuConsultatie(models.Model):
    consultatie = models.ForeignKey(Consultatie, on_delete=models.CASCADE, related_name="detalii")
    interventie = models.ForeignKey(Interventie, on_delete=models.PROTECT)
    cantitate = models.PositiveIntegerField(default=1)
    # Prețurile se copiază din catalog în momentul consultației
    cost_materiale_aplicat = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tarif_aplicat = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    observatii = models.CharField("observații", max_length=200, blank=True)

    class Meta:
        db_table = "detalii_consultatie"
        verbose_name = "intervenție efectuată"
        verbose_name_plural = "intervenții efectuate"
        constraints = [
            models.UniqueConstraint(fields=["consultatie", "interventie"], name="uq_consultatie_interventie"),
        ]

    def save(self, *args, **kwargs):
        if self.cost_materiale_aplicat is None:
            self.cost_materiale_aplicat = self.interventie.cost_materiale
        if self.tarif_aplicat is None:
            self.tarif_aplicat = self.interventie.tarif_medic
        super().save(*args, **kwargs)

    @property
    def valoare(self):
        materiale = self.cost_materiale_aplicat or Decimal("0")
        tarif = self.tarif_aplicat or Decimal("0")
        return self.cantitate * (materiale + tarif)

    def __str__(self):
        return f"{self.interventie} x{self.cantitate}"


class Chitanta(models.Model):
    nr_chitanta = models.AutoField("număr chitanță", primary_key=True)
    consultatie = models.ForeignKey(Consultatie, on_delete=models.PROTECT, related_name="chitante")
    data_emiterii = models.DateField("data emiterii", default=date.today)
    suma_achitata = models.DecimalField("suma achitată", max_digits=10, decimal_places=2)

    class Meta:
        db_table = "chitante"
        verbose_name = "chitanță"
        verbose_name_plural = "chitanțe"
        ordering = ["-data_emiterii"]

    def clean(self):
        if self.suma_achitata is None or not self.consultatie_id:
            return
        if self.suma_achitata <= 0:
            raise ValidationError("Suma achitată trebuie să fie mai mare decât 0.")
        rest = self.consultatie.rest_de_plata()
        if self.pk:  # la modificare, suma veche nu se pune la socoteală
            rest += Chitanta.objects.get(pk=self.pk).suma_achitata
        if self.suma_achitata > rest:
            raise ValidationError(f"Suma depășește restul de plată ({rest} lei).")

    def __str__(self):
        return f"Chitanța {self.nr_chitanta} - {self.suma_achitata} lei"


class GrilaSpor(models.Model):
    nr_min_consultatii = models.PositiveIntegerField("număr minim de consultații", unique=True)
    procent_spor = models.DecimalField("procent spor (%)", max_digits=5, decimal_places=2)

    class Meta:
        db_table = "grila_sporuri"
        verbose_name = "prag spor"
        verbose_name_plural = "grilă sporuri"
        ordering = ["nr_min_consultatii"]

    def __str__(self):
        return f"≥ {self.nr_min_consultatii} consultații → {self.procent_spor}%"


class ParametriSalarizare(models.Model):
    data_valabilitate = models.DateField("valabil de la", unique=True)
    cota_cas = models.DecimalField("cota CAS (%)", max_digits=5, decimal_places=2, default=Decimal("25"))
    cota_impozit = models.DecimalField("cota impozit (%)", max_digits=5, decimal_places=2, default=Decimal("10"))

    class Meta:
        db_table = "parametri_salarizare"
        verbose_name = "parametri salarizare"
        verbose_name_plural = "parametri salarizare"
        ordering = ["-data_valabilitate"]

    def __str__(self):
        return f"De la {self.data_valabilitate}: CAS {self.cota_cas}%, impozit {self.cota_impozit}%"


class StatPlata(models.Model):
    medic = models.ForeignKey(Medic, on_delete=models.PROTECT, related_name="state_plata")
    luna = models.PositiveSmallIntegerField("luna")
    an = models.PositiveSmallIntegerField("anul")
    nr_consultatii = models.PositiveIntegerField("număr consultații")
    salariu_incadrare = models.DecimalField(max_digits=10, decimal_places=2)
    procent_spor = models.DecimalField(max_digits=5, decimal_places=2)
    valoare_spor = models.DecimalField(max_digits=10, decimal_places=2)
    salariu_brut = models.DecimalField(max_digits=10, decimal_places=2)
    cas = models.DecimalField("CAS", max_digits=10, decimal_places=2)
    baza_impozabila = models.DecimalField(max_digits=10, decimal_places=2)
    impozit = models.DecimalField(max_digits=10, decimal_places=2)
    salariu_net = models.DecimalField(max_digits=10, decimal_places=2)
    data_generarii = models.DateField(default=date.today)

    class Meta:
        db_table = "stat_plata"
        verbose_name = "rând stat de plată"
        verbose_name_plural = "state de plată"
        ordering = ["-an", "-luna", "medic"]
        constraints = [
            models.UniqueConstraint(fields=["medic", "luna", "an"], name="uq_stat_medic_luna_an"),
        ]

    def __str__(self):
        return f"{self.medic} - {self.luna:02d}/{self.an}"
