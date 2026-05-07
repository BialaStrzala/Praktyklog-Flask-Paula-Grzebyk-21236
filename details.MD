# 📘 System Obsługi Praktyk – Postęp Projektu

## 📌 Cel dokumentu

Dokument określa aktualny stan realizacji projektu oraz wymagania dotyczące elementów, które powinny być już zaimplementowane i dostępne w repozytorium GitHub.

---

## 🧱 1. Podstawy aplikacji Flask

Na tym etapie powinna istnieć działająca aplikacja Flask:

* plik `app.py`
* zdefiniowane trasy:

  * `/`
  * podstrony (np. `/kontakt`, `/hobby`)
* wykorzystanie `render_template`
* folder `templates/` z plikami HTML
* podstawowa nawigacja między stronami
* środowisko wirtualne (`venv`)

---

## 📝 2. Obsługa formularzy i JSON

Aplikacja powinna umożliwiać:

* obsługę formularzy (`method="POST"`)
* odbieranie danych przez `request.form`
* rozróżnienie metod `GET` / `POST`
* zwracanie danych w formacie JSON (`jsonify`)
* zapis danych do pliku `.json`
* wykorzystanie klas Python do przetwarzania danych
* podstawową walidację danych (np. email)

---

## 💾 3. Trwałość danych i operacje na listach

W projekcie powinny być zaimplementowane:

* funkcje do obsługi danych:

  * `load_data()`
  * `save_data()`
* przetwarzanie danych listowych (`request.form.getlist`)
* dynamiczne formularze (np. tabela)
* integracja z JavaScript:

  * dodawanie/usuwanie wierszy
* synchronizacja frontend ↔ backend
* zapis danych formularzy praktyk (np. dziennik)

---

## 📊 4. Analiza systemu i wymagania

Dokumentacja powinna zawierać:

* listę aktorów systemu:

  * student
  * opiekun uczelniany
  * opiekun zakładowy
  * dziekanat
* minimum 8 wymagań funkcjonalnych
* minimum 3 user stories
* wymagania niefunkcjonalne:

  * bezpieczeństwo
  * wydajność
  * użyteczność
  * archiwizacja
* opis workflow dokumentów

---

## 🔄 5. Modelowanie systemu (diagramy)

W repozytorium powinny znajdować się:

* diagram sekwencji (proces weryfikacji)
* diagram stanów:

  * `Draft → Submitted → Under Review → Approved/Rejected`
* diagram przepływu (flowchart):

  * logika uprawnień
* diagramy wykonane w Mermaid
* eksport diagramów (PNG/SVG)
* kod źródłowy diagramów

---

## 🗄️ 6. Projekt bazy danych

Projekt bazy danych powinien zawierać:

* diagram ERD:

  * encje
  * relacje
  * klucze główne i obce
* plik `.sql`:

  * `CREATE TABLE`
  * `PRIMARY KEY`, `FOREIGN KEY`
  * `NOT NULL`, `UNIQUE`
* wybór bazy danych:

  * SQLite (prototyp)
  * propozycja docelowa (np. MariaDB)
* opis narzędzi:

  * DBeaver
  * Mermaid

---

## 🧠 7. Model danych i walidacja (SQL)

Powinny być przygotowane:

* rozszerzony model ERD (pełny system)
* podział na tabele:

  * studenci
  * formularze
  * firmy
  * opiekunowie
  * efekty kształcenia
  * harmonogram
* normalizacja danych
* zapytania SQL do walidacji:

  * kompletność danych
  * liczba dni (120)
  * poprawność dat
  * liczba efektów (13)
* przypadki brzegowe (błędy danych)
* walidacja między formularzami

---

## 🔐 8. System logowania

System powinien zawierać:

* logowanie przez Microsoft (OAuth2)
* obsługę callback
* pobieranie danych użytkownika
* model `User` w bazie danych
* integrację z Flask-Login:

  * `login_user`
  * `logout_user`
  * `@login_required`
* system ról:

  * student
  * opiekun
  * administrator
* logikę pierwszego logowania
* plik `.env` z konfiguracją
* przygotowanie pod integrację Google (opcjonalnie)

---

## 📁 9. Wymagania dotyczące repozytorium

Repozytorium GitHub musi zawierać:

* kod źródłowy aplikacji
* dokumentację (`README.md` + pliki dodatkowe)
* diagramy (Mermaid + eksport)
* pliki SQL
* pliki JSON (przykładowe dane)
* instrukcję uruchomienia projektu

---

## ✅ 10. Stan oczekiwany projektu

Na tym etapie projekt powinien:

* działać jako aplikacja Flask
* obsługiwać formularze
* zapisywać dane (JSON lub baza danych)
* posiadać model danych
* zawierać dokumentację projektową
* posiadać podstawowy system logowania

❗ Brak któregokolwiek z powyższych elementów oznacza niepełną realizację projektu.

---

## 📌 Uwagi końcowe

Projekt powinien być rozwijany w sposób uporządkowany, z czytelną strukturą katalogów oraz systematycznym commitowaniem zmian do repozytorium GitHub.




# 🚀 Kolejne etapy projektu – System Obsługi Praktyk

---

## 🔷 ETAP 9: API aplikacji (REST API)

### 🎯 Cel

Rozdzielenie warstwy backendowej od frontendowej poprzez stworzenie API.

### 📌 Zadania

* zaprojektowanie endpointów API:

  * `/api/students`
  * `/api/internships`
  * `/api/documents`
* obsługa metod:

  * GET (pobieranie danych)
  * POST (tworzenie)
  * PUT/PATCH (edycja)
  * DELETE (usuwanie)
* zwracanie danych w formacie JSON
* walidacja danych wejściowych
* obsługa błędów (statusy HTTP: 200, 400, 404, 500)

### 🧩 Rozszerzenia

* filtrowanie danych (np. po studencie)
* paginacja wyników

### 📦 Efekt końcowy (repo)

* pliki z API (np. `api/routes.py`)
* dokumentacja endpointów (README lub Swagger)
* przykłady zapytań (Postman / curl)

---

## 🔷 ETAP 10: Frontend (interfejs użytkownika)

### 🎯 Cel

Oddzielenie logiki backendu od warstwy prezentacji.

### 📌 Zadania

* stworzenie interfejsu użytkownika:

  * dashboard użytkownika
  * formularze (praktyki, dziennik, efekty)
* komunikacja z API (fetch / axios)
* dynamiczne ładowanie danych
* obsługa błędów i komunikatów
* poprawa UX:

  * walidacja po stronie klienta
  * komunikaty użytkownika

### 🧩 Technologie (do wyboru)

* czysty JS + HTML


### 📦 Efekt końcowy (repo)

* katalog `frontend/` lub `static/js`
* działający interfejs komunikujący się z API

---

## 🔷 ETAP 11: Generowanie dokumentów (PDF)

### 🎯 Cel

Automatyzacja generowania dokumentacji praktyk.

### 📌 Zadania

* generowanie PDF na podstawie danych:

  * dziennik praktyk
  * potwierdzenie efektów
  * raport końcowy
* wykorzystanie bibliotek:

  * reportlab lub
  * weasyprint / html2pdf
* tworzenie szablonów dokumentów
* możliwość pobrania pliku przez użytkownika

### 🧩 Rozszerzenia

* podpisy (np. imię i nazwisko zamiast podpisu)
* eksport wielu dokumentów naraz

### 📦 Efekt końcowy (repo)

* moduł generowania PDF
* przykładowe wygenerowane pliki
* endpoint np. `/generate-pdf/<id>`

---

## 🔷 ETAP 12: Bezpieczeństwo i wdrożenie

### 🎯 Cel

Przygotowanie aplikacji do działania w środowisku produkcyjnym.

### 📌 Zadania

#### 🔐 Bezpieczeństwo

* ochrona endpointów API
* walidacja danych wejściowych
* zabezpieczenie przed:

  * SQL Injection
  * XSS
  * CSRF
* konfiguracja sesji i tokenów

#### ⚙️ Konfiguracja

* konfiguracja środowisk:

  * development
  * production
* użycie `.env`

#### ☁️ Wdrożenie

* deployment aplikacji:
  * Docker

### 🧩 Rozszerzenia

* logowanie błędów
* monitoring aplikacji

### 📦 Efekt końcowy (repo)

* działająca aplikacja online
* instrukcja wdrożenia (README)
* konfiguracja środowiska produkcyjnego

---

# ✅ Podsumowanie kolejnych etapów

Po realizacji etapów 9–12 projekt powinien być:

* kompletną aplikacją webową (backend + frontend)
* posiadać API
* umożliwiać generowanie dokumentów
* być zabezpieczony i gotowy do wdrożenia
* dostępny online

---

# 📌 Finalny efekt projektu

System powinien umożliwiać:

* zarządzanie praktykami studentów
* obsługę dokumentów
* pracę wielu ról użytkowników
* generowanie raportów
* dostęp przez przeglądarkę (online)

---

