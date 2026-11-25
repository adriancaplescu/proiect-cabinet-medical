from datetime import date, time

from django import forms

from .models import Chitanta, Consultatie, DetaliuConsultatie, Pacient, Programare


class BootstrapMixin:
    """Pune clasele Bootstrap pe toate câmpurile formularului."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css)


class PacientForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Pacient
        fields = ['nume', 'prenume', 'data_nasterii', 'adresa', 'telefon', 'data_intocmirii']
        widgets = {
            'data_nasterii': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'data_intocmirii': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }


# Orele de programare: din 30 în 30 de minute, între 08:00 și 19:30
ORE_PROGRAMARE = [(f'{h:02d}:{m:02d}', f'{h:02d}:{m:02d}') for h in range(8, 20) for m in (0, 30)]


class ProgramareForm(BootstrapMixin, forms.ModelForm):
    ora = forms.TypedChoiceField(choices=[('', '-- alege ora --')] + ORE_PROGRAMARE,
                                 coerce=time.fromisoformat, label='Ora')

    class Meta:
        model = Programare
        fields = ['pacient', 'medic', 'data', 'ora']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # calendarul din browser nu mai permite alegerea zilelor trecute
        # (regula propriu-zisă e în Programare.clean(), în models.py)
        self.fields['data'].widget.attrs['min'] = date.today().isoformat()



class ChitantaForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Chitanta
        fields = ['suma_achitata', 'data_emiterii']
        widgets = {
            'data_emiterii': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'suma_achitata': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
        }


class ProgramarePacientForm(ProgramareForm):
    """Pacientul se programează singur: alege doar medicul, data și ora."""
    class Meta(ProgramareForm.Meta):
        fields = ['medic', 'data', 'ora']


class ConsultatieForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Consultatie
        fields = ['data_consultatie', 'observatii']
        widgets = {
            'data_consultatie': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'observatii': forms.Textarea(attrs={'rows': 3}),
        }


class DetaliuForm(BootstrapMixin, forms.ModelForm):
    cantitate = forms.IntegerField(min_value=1, initial=1, label='Cantitate',
                                   widget=forms.NumberInput(attrs={'min': 1}))

    class Meta:
        model = DetaliuConsultatie
        fields = ['interventie', 'cantitate', 'observatii']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # în listă apare și prețul: „Pansament (70,00 lei)”
        self.fields['interventie'].label_from_instance = lambda i: f'{i.denumire} ({i.pret_total} lei)'
        self.fields['interventie'].empty_label = '-- alege intervenția --'


# Intervențiile unei consultații: mai multe rânduri pe aceeași pagină
DetaliiFormSet = forms.inlineformset_factory(
    Consultatie, DetaliuConsultatie, form=DetaliuForm,
    extra=3, can_delete=True, min_num=1, validate_min=True,
)
