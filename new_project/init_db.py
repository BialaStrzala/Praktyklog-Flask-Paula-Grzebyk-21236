from app import app, db
import models as models

with app.app_context():
    db.drop_all()
    db.create_all()

    # Firma XYZ
    firma = models.Firma(nazwa='Firma XYZ')
    db.session.add(firma)
    db.session.commit()

    # Firma ABC123
    firma = models.Firma(nazwa='Firma ABC123')
    db.session.add(firma)
    db.session.commit()

    # Opiekun Zakladowy
    opiekun_z_uzytkownik = models.Uzytkownik(imie='Anna', nazwisko='Nowak', email='opiekunz@opiekunz.pl', rola='opiekun')
    db.session.add(opiekun_z_uzytkownik)
    db.session.commit()
    opiekun_z_profil = models.OpiekunProfil(uzytkownik_id=opiekun_z_uzytkownik.id, firma_id=firma.id, typ_opiekuna='zakladowy')
    db.session.add(opiekun_z_profil)
    db.session.commit()

    # Opiekun Uczelniany
    opiekun_z_uzytkownik = models.Uzytkownik(imie='Jan', nazwisko='Kowalski', email='opiekunu@opiekunu.pl', rola='opiekun')
    db.session.add(opiekun_z_uzytkownik)
    db.session.commit()
    opiekun_z_profil = models.OpiekunProfil(uzytkownik_id=opiekun_z_uzytkownik.id, firma_id=firma.id, typ_opiekuna='uczelniany')
    db.session.add(opiekun_z_profil)
    db.session.commit()

    # efekty uczenia
    e1 = models.EfektUczenia(kod='01', opis='Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących informatyki z zachowaniem standardów i norm technicznych')
    e2 = models.EfektUczenia(kod='02', opis='Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce')
    e3 = models.EfektUczenia(kod='03', opis='Zna ekonomiczne, prawne skutki własnych działań podejmowanych w ramach praktyki oraz  ograniczenia wynikające z prawa autorskiego i kodeksu pracy')
    e4 = models.EfektUczenia(kod='04', opis='Zna zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka')
    e5 = models.EfektUczenia(kod='05', opis='Pozyskuje informacje odnośnie technologii, metod, technik, sprzętu wymaganego do realizacji powierzonego zadania, posługując się rozmaitymi źródłami literaturowymi i zasobami publikowanymi w języku polskim  jak i angielskim')
    e6 = models.EfektUczenia(kod='06', opis='W oparciu o kontakty ze środowiskiem inżynierskim zakładu, potrafi podnieść swoje kompetencje, wiedzę i umiejętności, co najmniej z dwóch zakresów: zadania dotyczące  sprzętu i oprogramowania: np.: programowania, administrowanie siecią komputerową, konserwacja sprzętu i oprogramowania, bieżące usuwanie usterek , administrowanie zasobami informatycznymi, zakładu pracy / instytucji, (e)-usługami.')
    e7 = models.EfektUczenia(kod='07', opis='Opracowuje dokumentację dotyczącą realizacji podejmowanych zadań w ramach praktyki, a także referuje ustnie prezentowane w niej zagadnienia')
    e8 = models.EfektUczenia(kod='08', opis='Potrafi zidentyfikować problem informatyczny występujący w zakładzie pracy / instytucji, opisać go, przedstawić koncepcję rozwiązania i ją zrealizować.')
    e9 = models.EfektUczenia(kod='09', opis='Potrafi rozwiązać rzeczywiste zadanie inżynierskie z zakresu działalności  informatycznej zakładu pracy/instytucji stosując normy i standardy stosowane w informatyce oraz biorąc pod uwagę aspekty środowiskowe i etyczne.')
    e10 = models.EfektUczenia(kod='10', opis='Pracuje w zespole zajmującym się zawodowo branżą IT')
    e11 = models.EfektUczenia(kod='11', opis='Przestrzega zasad etyki zawodowej i zgodnie z tymi zasadami korzysta z wiedzy i pomocy doświadczonych kolegów')
    e12 = models.EfektUczenia(kod='12', opis='Kontaktując  się z osobami spoza branży potrafi zarówno pozyskać od nich niezbędne informacje do realizacji planowanego zadania,  jak i przekazać im w sposób zrozumiały informacje i opinie z zakresu informatyki')
    e13 = models.EfektUczenia(kod='13', opis='Dostrzega w praktyce tempo deaktualizacji  wiedzy informatycznej  oraz skutki działalności informatyków w szczególności ekonomiczne i społeczne')
    db.session.add(e1)
    db.session.add(e2)
    db.session.add(e3)
    db.session.add(e4)
    db.session.add(e5)
    db.session.add(e6)
    db.session.add(e7)
    db.session.add(e8)
    db.session.add(e9)
    db.session.add(e10)
    db.session.add(e11)
    db.session.add(e12)
    db.session.add(e13)
    db.session.commit()

    print("DB initialized")
    print(models.Uzytkownik.query.all())

