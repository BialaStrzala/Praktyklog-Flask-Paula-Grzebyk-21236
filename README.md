# System Obsługi Praktyk Zawodowych

Aplikacja internetowa wspomagająca cyfrowy obieg dokumentacji praktyk zawodowych. System zastępuje tradycyjny, papierowy obieg dokumentów (dziennik praktyk, arkusz efektów uczenia się, opinie opiekunów) procesem cyfrowym z możliwością generowania plików PDF.

---

## Wymagania funkcjonalne

| ID | Aktor | Nazwa | Opis | Priorytet |
|----|-------|-------|------|-----------|
| 1 | Student | Zarządzanie dziennikiem praktyk | Student może przeglądać własny dziennik, dodawać, edytować i usuwać wpisy w formie tabeli | M |
| 2 | Student | Przegląd efektów nauki | Student może przeglądać efekty swojej nauki w formie tabeli | M |
| 3 | Opiekun Zakładowy | Dodawanie uwag i zatwierdzanie wpisów w dzienniku | Opiekun może zatwierdzić wpisy w dzienniku praktyk studenta lub dodawać uwagi | M |
| 4 | Opiekun Zakładowy | Potwierdzanie efektów nauki | Opiekun może zatwierdzić efekty uczenia się studenta | M |
| 5 | Opiekun Uczelniany | Wystawianie opinii dotyczącej efektów nauki studentów | Opiekun może zatwierdzić efekty uczenia się studenta oraz dodać swoją opinię | M |
| 6 | Opiekun Uczelniany | Wystawienie oceny końcowej | Po zatwierdzeniu wszystkich dokumentów studenta, opiekun może wystawić ocenę końcową. System blokuje możliwość edytowania dokumentów związanych z danym studentem | S |
| 7 | Student | Sprawozdanie z praktyki zawodowej | Po zakończeniu praktyk, student może wypełnić sprawozdanie z praktyki zawodowej | C |
| 8 | Student | Ankieta oceniająca przebieg praktyk | Po zakończeniu praktyk, student może wypełnić ankietę oceniającą przebieg swoich praktyk zawodowych | C |
| 9 | Dziekanat | Wgląd do dokumentów studentów | Dziekanat może przeglądać dokumenty wszystkich studentów | S |
| 10 | Dziekanat | Przegląd ankiet oceniających przebieg praktyk | Dziekanat może przeglądać wypełnione ankiety dotyczące oceny przebiegu praktyk przez studentów | C |
| 11 | Dziekanat, Administrator | Przydzielanie studentów do opiekunów | Dziekanat oraz administracja mogą przydzielać opiekunów zakładowych i uczelnianych do studentów | M |
| 12 | Administrator | Zarządzanie użytkownikami | Administrator może przydzielać role oraz zarządzać użytkownikami | M |
| 13 | Wszystkie jednostki | Generowanie raportów PDF | Wszyscy użytkownicy mają możliwość generowania raportów PDF na podstawie przechowywanych dokumentów | S |

Priorytety: **M** – must have, **S** – should have, **C** – could have

---

## User Stories

1. Jako **student**, chcę prowadzić dziennik praktyk gdzie mogę przeglądać swoją historię praktyk oraz efekty mojej nauki.
2. Jako **opiekun zakładowy**, chcę mieć wgląd do dzienników moich praktykantów, potwierdzać efekty ich pracy, dodawać uwagi do ich wpisów, oraz zatwierdzić końcową ocenę i dodać swoją opinię.
3. Jako **opiekun uczelniany**, chcę mieć wgląd do dzienników moich studentów, przeglądać efekty ich pracy, oraz zatwierdzić końcową ocenę i dodać swoją opinię.
4. Jako **dziekanat**, chcę mieć wgląd do dokumentów wszystkich studentów, móc przydzielać studentów do opiekunów, oraz generować raporty PDF.

---

## Wymagania niefunkcjonalne

**Bezpieczeństwo:**
- System wykorzystuje uwierzytelnianie
- Dostęp do danych tylko dla uprawnionych użytkowników
- Opiekunowie mogą przeglądać tylko dane dotyczące przydzielonych im studentów
- Hasła użytkowników są szyfrowane

**Użyteczność:**
- Aplikacja jest przystosowana do urządzeń mobilnych
- Formularze zachowują wpisane do nich dane w sytuacji odświeżenia strony lub wystąpienia błędu
- Intuicyjny interfejs
- Walidacja formularzy w czasie rzeczywistym
- Czytelne komunikaty błędów

**Wydajność:**
- Raporty PDF są generowane w <= 5 sekund
- Czas odpowiedzi systemu <= 2 sekundy
- Obsługa wielu użytkowników jednocześnie

**Archiwizacja:**
- Dane są zapisywane w bazie danych
- Prowadzone są kopie zapasowe

---

## Diagram ERD bazy danych

TBA

---

## Diagramy przepływu danych

TBA

---

## Opis wyboru narzędzi

### Baza danych – SQLite

SQLite to wbudowana, bezserwerowa baza danych, w której całość danych przechowywana jest w jednym pliku. Wybrano ją z następujących powodów:
- Nie wymaga instalacji ani konfiguracji serwera bazy danych.
- Natywna integracja z Pythonem przez moduł `sqlite3` oraz z Flask-SQLAlchemy.
- Wystarczająca wydajność dla aplikacji uczelnianych z ograniczoną liczbą jednoczesnych użytkowników.
- Uproszczone wdrożenie i przenoszenie aplikacji – baza danych to pojedynczy plik `.db`.

### Narzędzie do zarządzania bazą danych – DBeaver Community

DBeaver Community to darmowe, wieloplatformowe narzędzie graficzne do zarządzania bazami danych. W projekcie służy do:
- Przeglądania struktury tabel i relacji bez pisania zapytań SQL.
- Ręcznej inspekcji i edycji danych podczas developmentu i testowania.
- Eksportowania danych do formatów CSV lub SQL.
- Wizualizacji diagramu ERD na podstawie istniejącej bazy danych.

DBeaver obsługuje SQLite, MySQL, PostgreSQL i wiele innych silników, co umożliwia używanie tego samego narzędzia po ewentualnej migracji bazy danych.

### Narzędzie do tworzenia diagramów przepływu - Mermaid

TBA