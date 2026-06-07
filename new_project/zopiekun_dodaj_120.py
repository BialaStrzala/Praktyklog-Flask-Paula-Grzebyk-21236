from app import app, db
import models as models
from datetime import date, timedelta

with app.app_context():
    me_uzytkownik = models.Uzytkownik.query.filter_by(imie='Paula').first()
    me_profil_opiekuna = models.OpiekunProfil.query.filter_by(uzytkownik_id=me_uzytkownik.id).first()

    # nowy student
    student_uzytkownik = models.Uzytkownik(imie='Maria', nazwisko='Ładniak', email='student3@student.pl', rola='student')
    db.session.add(student_uzytkownik)
    db.session.commit()
    student_profil = models.StudentProfil(uzytkownik_id=student_uzytkownik.id, indeks='45678', kierunek='Informatyka', specjalnosc='Projektowanie baz danych i oprogramowanie uzytkowe', semestr=6, opiekun_uczelniany_id=1, opiekun_zakladowy_id=me_profil_opiekuna.id)
    db.session.add(student_profil)
    db.session.commit()

    # harmonogram
    harmonogram = models.HarmonogramPraktyk(
        student_id=student_profil.id,
        opiekun_zakladowy_id=me_profil_opiekuna.id,
        firma_id=1,
        planowana_liczba_dni=120,
        planowana_data_rozpoczecia=date.fromisoformat('2026-07-01'),
        planowana_data_zakonczenia=date.fromisoformat('2027-02-01'),
        status='zaakceptowany',
    )
    db.session.add(harmonogram)
    db.session.commit()

    formularz = models.FormularzPraktyk(
        student_id=student_profil.id, 
        opiekun_zakladowy_id=me_profil_opiekuna.id, 
        firma_id=harmonogram.firma_id, 
        harmonogram_praktyk_id=harmonogram.id, 
        data_rozpoczecia=harmonogram.planowana_data_rozpoczecia,
        data_zakonczenia=harmonogram.planowana_data_zakonczenia,
        status = 'w_trakcie',
        )
    models.db.session.add(formularz)
    models.db.session.commit()

    # Wpisy (120)

    for i in range(1, 121):
        wpis = models.DziennikWpis(
            student_id=student_profil.id,
            nr_dnia=i,
            data=date.fromisoformat('2026-07-01') + timedelta(days=i-1),
            liczba_godzin=8,
            opis=f"Dzień {i} praktyk. Opis dnia.",
            status = 'zatwierdzony'
        )
        db.session.add(wpis)
    db.session.commit()

    print('Dodano nowego studenta z 120 wpisami do dziennika praktyk.')