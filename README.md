# Cabinet medical – evidența pacienților, încasărilor și angajaților

Proiect sincretic: aplicație web Django + MySQL pentru un cabinet medical privat
(programări, foi de consultație, chitanțe, restanțe, state de plată și fluturași).

Proiect Sincretic II A – Utilizarea și proiectarea bazelor de date (BD + PBD), UPT.

**Echipa:** Căplescu Adrian-Grigore, Secetă Alexandru-Adrian, Terec Darius-Mihai

Documentația completă: [`documentatie/Documentatie_cabinet_medical.pdf`](documentatie/Documentatie_cabinet_medical.pdf)

## Ce trebuie instalat

- **Python 3.12 sau mai nou**
- **MySQL 8 sau mai nou**, pornit pe calculatorul local
- pentru `mysqlclient`:
  - macOS: `brew install mysql pkg-config`
  - Linux (Ubuntu/Debian): `sudo apt install python3-dev default-libmysqlclient-dev build-essential pkg-config`
  - Windows: nu e nevoie de nimic în plus (pachetul vine gata compilat)

## Pornire, pas cu pas

**1. Descarcă proiectul**

```bash
git clone https://github.com/adriancaplescu/proiect-cabinet-medical.git
cd proiect-cabinet-medical
```

**2. Creează baza de date** (în `mysql -u root`). Numele, utilizatorul și parola trebuie
să fie cele din `config/settings.py`:

```sql
CREATE DATABASE cabinet_medical CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'cabinet_user'@'localhost' IDENTIFIED BY 'cabinet123';
GRANT ALL PRIVILEGES ON cabinet_medical.* TO 'cabinet_user'@'localhost';
```

**3. Instalează dependențele într-un mediu virtual**

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**4. Creează tabelele, datele de test și conturile**

```bash
python manage.py migrate
python manage.py shell < date_test.py
python manage.py creeaza_roluri
python manage.py genereaza_stat 11 2026
python manage.py createsuperuser
```

**5. Pornește aplicația**

```bash
python manage.py runserver
```

Deschide http://127.0.0.1:8000 în browser. Panoul de administrare este la http://127.0.0.1:8000/admin.

## Conturi de test

| Rol | Utilizator | Parolă |
|---|---|---|
| Recepție | `receptie` | `receptie123` |
| Medic | `dr.popescu`, `dr.ionescu`, `dr.stan` | `medic123` |
| Pacient | `georgescu`, `dumitru`, `matei` | `pacient123` |
| Administrator | cel creat cu `createsuperuser` | aleasă la creare |

Datele de test sunt din noiembrie 2026. Parolele sunt doar pentru demonstrație.

## Structura proiectului

| Folder / fișier | Rol |
|---|---|
| `config/` | setările proiectului (conexiunea MySQL, limba, adresele) |
| `cabinet/models.py` | cele 11 tabele și validările |
| `cabinet/views_*.py` | paginile pe roluri: recepție, încasări, salarizare, medic, pacient |
| `cabinet/templates/` | paginile HTML |
| `cabinet/salarizare.py` | calculul statului de plată |
| `cabinet/management/commands/` | comenzile `genereaza_stat` și `creeaza_roluri` |
| `date_test.py` | datele de test |
