-- =========================================================================================================
-- === SCHEMA BAZY DANYCH – System Obsługi Praktyk Zawodowych ===
-- =========================================================================================================

PRAGMA foreign_keys = OFF;

-- =========================================================================================================
-- === DROP TABLES ===
-- =========================================================================================================

DROP TABLE IF EXISTS efekt_uczenia_harmonogram;
DROP TABLE IF EXISTS efekt_uczenia_formularz;
DROP TABLE IF EXISTS dziennik_wpis;
DROP TABLE IF EXISTS harmonogram_praktyk;
DROP TABLE IF EXISTS formularz_praktyk;
DROP TABLE IF EXISTS efekt_uczenia;
DROP TABLE IF EXISTS student_profil;
DROP TABLE IF EXISTS opiekun_profil;
DROP TABLE IF EXISTS firma;
DROP TABLE IF EXISTS uzytkownik;

PRAGMA foreign_keys = ON;

-- =========================================================================================================
-- === CREATE TABLES ===
-- =========================================================================================================

-- === UZYTKOWNIK ===
CREATE TABLE uzytkownik (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    imie        TEXT    NOT NULL CHECK (LENGTH(TRIM(imie)) > 0),
    nazwisko    TEXT    NOT NULL CHECK (LENGTH(TRIM(nazwisko)) > 0),
    email       TEXT    NOT NULL UNIQUE CHECK (email LIKE '%_@_%._%'),
    rola        TEXT    NOT NULL CHECK (rola IN ('student', 'opiekun_zakladowy', 'opiekun_uczelniany', 'dziekanat', 'admin')),
    konto_aktywne INTEGER NOT NULL DEFAULT 1 CHECK (konto_aktywne IN (0, 1)),
    telefon     TEXT    CHECK (telefon IS NULL OR LENGTH(TRIM(telefon)) >= 7),
    utworzono   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    auth_provider TEXT  NOT NULL DEFAULT 'microsoft' CHECK (auth_provider IN ('microsoft', 'local')),
    external_id TEXT    UNIQUE
);

-- === FIRMA ===
CREATE TABLE firma (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nazwa   TEXT    NOT NULL CHECK (LENGTH(TRIM(nazwa)) > 0),
    adres   TEXT
);

-- === OPIEKUN PROFIL ===
CREATE TABLE opiekun_profil (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    uzytkownik_id   INTEGER NOT NULL UNIQUE REFERENCES uzytkownik(id) ON DELETE CASCADE,
    firma_id        INTEGER REFERENCES firma(id) ON DELETE SET NULL,
    typ_opiekuna    TEXT    NOT NULL CHECK (typ_opiekuna IN ('uczelniany', 'zakladowy')),

    -- Opiekun zakładowy musi mieć przypisaną firmę
    CHECK (
        (typ_opiekuna = 'zakladowy' AND firma_id IS NOT NULL) OR
        (typ_opiekuna = 'uczelniany')
    )
);

-- === STUDENT PROFIL ===
CREATE TABLE student_profil (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    uzytkownik_id           INTEGER NOT NULL UNIQUE REFERENCES uzytkownik(id) ON DELETE CASCADE,
    indeks                  TEXT    UNIQUE CHECK (indeks IS NULL OR LENGTH(TRIM(indeks)) > 0),
    rok_akademicki          TEXT    CHECK (rok_akademicki IS NULL OR rok_akademicki GLOB '[0-9][0-9][0-9][0-9]/[0-9][0-9][0-9][0-9]'),
    semestr                 INTEGER CHECK (semestr IS NULL OR (semestr >= 1 AND semestr <= 14)),
    kierunek                TEXT,
    specjalnosc             TEXT,
    czy_stacjonarne         INTEGER NOT NULL DEFAULT 1 CHECK (czy_stacjonarne IN (0, 1)),
    opiekun_zakladowy_id    INTEGER REFERENCES opiekun_profil(id) ON DELETE SET NULL,
    opiekun_uczelniany_id   INTEGER REFERENCES opiekun_profil(id) ON DELETE SET NULL,

    -- Opiekunowie nie mogą być tą samą osobą
    CHECK (opiekun_zakladowy_id IS NULL OR opiekun_uczelniany_id IS NULL OR opiekun_zakladowy_id != opiekun_uczelniany_id)
);

-- === EFEKTY UCZENIA ===
CREATE TABLE efekt_uczenia (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    kod     TEXT    NOT NULL UNIQUE CHECK (LENGTH(TRIM(kod)) > 0),
    opis    TEXT    NOT NULL CHECK (LENGTH(TRIM(opis)) > 0)
);

-- === HARMONOGRAM PRAKTYK ===
CREATE TABLE harmonogram_praktyk (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id              INTEGER NOT NULL REFERENCES student_profil(id) ON DELETE CASCADE,
    opiekun_zakladowy_id    INTEGER NOT NULL REFERENCES opiekun_profil(id) ON DELETE RESTRICT,
    firma_id                INTEGER REFERENCES firma(id) ON DELETE SET NULL,
    planowana_liczba_dni    INTEGER NOT NULL CHECK (planowana_liczba_dni > 0),
    status                  TEXT    NOT NULL DEFAULT 'oczekuje' CHECK (status IN ('oczekuje', 'zaakceptowany', 'odrzucony'))
);

-- === FORMULARZ PRAKTYK ===
CREATE TABLE formularz_praktyk (
    id                              INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id                      INTEGER NOT NULL REFERENCES student_profil(id) ON DELETE CASCADE,
    opiekun_uczelniany_id           INTEGER REFERENCES opiekun_profil(id) ON DELETE SET NULL,
    opiekun_zakladowy_id            INTEGER REFERENCES opiekun_profil(id) ON DELETE SET NULL,
    harmonogram_praktyk_id          INTEGER REFERENCES harmonogram_praktyk(id) ON DELETE SET NULL,

    data_rozpoczecia                TEXT CHECK (data_rozpoczecia IS NULL OR date(data_rozpoczecia) IS NOT NULL),
    data_zakonczenia                TEXT CHECK (data_zakonczenia IS NULL OR date(data_zakonczenia) IS NOT NULL),

    status                          TEXT NOT NULL DEFAULT 'w_trakcie'
                                        CHECK (status IN ('w_trakcie', 'zakonczone', 'porzucone')),

    opinia_opiekuna_zakladowego     TEXT,
    opinia_opiekuna_uczelnianego    TEXT,

    ocena_opiekuna_zakladowego      REAL CHECK (ocena_opiekuna_zakladowego IS NULL OR
                                        (ocena_opiekuna_zakladowego >= 2.0 AND ocena_opiekuna_zakladowego <= 5.0)),
    ocena_opiekuna_uczelnianego     REAL CHECK (ocena_opiekuna_uczelnianego IS NULL OR
                                        (ocena_opiekuna_uczelnianego >= 2.0 AND ocena_opiekuna_uczelnianego <= 5.0)),
    ocena_sprawozdanie              REAL CHECK (ocena_sprawozdanie IS NULL OR
                                        (ocena_sprawozdanie >= 2.0 AND ocena_sprawozdanie <= 5.0)),
    ocena_egzamin                   REAL CHECK (ocena_egzamin IS NULL OR
                                        (ocena_egzamin >= 2.0 AND ocena_egzamin <= 5.0)),
    ocena_koncowa                   REAL CHECK (ocena_koncowa IS NULL OR
                                        (ocena_koncowa >= 2.0 AND ocena_koncowa <= 5.0)),

    utworzono                       TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    zaktualizowano                  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),

    -- Data zakończenia musi być późniejsza niż data rozpoczęcia
    CHECK (data_rozpoczecia IS NULL OR data_zakonczenia IS NULL OR data_zakonczenia > data_rozpoczecia),

    -- Opiekunowie w formularzu nie mogą być tą samą osobą
    CHECK (opiekun_zakladowy_id IS NULL OR opiekun_uczelniany_id IS NULL OR opiekun_zakladowy_id != opiekun_uczelniany_id),

    -- Oceny cząstkowe mogą być wystawione tylko gdy formularz jest zakończony
    CHECK (status = 'zakonczone' OR (
        ocena_opiekuna_zakladowego IS NULL AND
        ocena_opiekuna_uczelnianego IS NULL AND
        ocena_sprawozdanie IS NULL AND
        ocena_egzamin IS NULL AND
        ocena_koncowa IS NULL
    ))
);

-- === EFEKTY UCZENIA – POWIĄZANIE Z FORMULARZEM ===
CREATE TABLE efekt_uczenia_formularz (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    formularz_praktyk_id    INTEGER NOT NULL REFERENCES formularz_praktyk(id) ON DELETE CASCADE,
    efekt_uczenia_id        INTEGER NOT NULL REFERENCES efekt_uczenia(id) ON DELETE CASCADE,
    czy_potwierdzony_zakladowy  INTEGER NOT NULL DEFAULT 0 CHECK (czy_potwierdzony_zakladowy IN (0, 1)),
    czy_potwierdzony_uczelniany INTEGER NOT NULL DEFAULT 0 CHECK (czy_potwierdzony_uczelniany IN (0, 1)),
    uwagi                   TEXT,

    -- Ten sam efekt nie może być przypisany do tego samego formularza dwa razy
    UNIQUE (formularz_praktyk_id, efekt_uczenia_id),

    -- Opiekun uczelniany może potwierdzić tylko jeśli zakładowy już potwierdził
    CHECK (
        czy_potwierdzony_uczelniany = 0 OR czy_potwierdzony_zakladowy = 1
    )
);

-- === EFEKTY UCZENIA – POWIĄZANIE Z HARMONOGRAMEM ===
CREATE TABLE efekt_uczenia_harmonogram (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    harmonogram_praktyk_id  INTEGER NOT NULL REFERENCES harmonogram_praktyk(id) ON DELETE CASCADE,
    efekt_uczenia_id        INTEGER NOT NULL REFERENCES efekt_uczenia(id) ON DELETE CASCADE,
    opis                    TEXT,

    -- Ten sam efekt nie może być przypisany do tego samego harmonogramu dwa razy
    UNIQUE (harmonogram_praktyk_id, efekt_uczenia_id)
);

-- === DZIENNIK PRAKTYK – WPIS ===
CREATE TABLE dziennik_wpis (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id          INTEGER NOT NULL REFERENCES student_profil(id) ON DELETE CASCADE,
    nr_dnia             INTEGER NOT NULL CHECK (nr_dnia > 0),
    data                TEXT    NOT NULL CHECK (date(data) IS NOT NULL),
    liczba_godzin       REAL    NOT NULL CHECK (liczba_godzin > 0 AND liczba_godzin <= 24),
    opis                TEXT    NOT NULL CHECK (LENGTH(TRIM(opis)) > 0),
    czy_zatwierdzony    INTEGER         DEFAULT 0 CHECK (czy_zatwierdzony IN (0, 1, NULL)),
    powod_odrzucenia    TEXT    CHECK (powod_odrzucenia IS NULL OR LENGTH(TRIM(powod_odrzucenia)) > 0),
    utworzono           TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    zaktualizowano      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),

    -- Powód odrzucenia ma sens tylko gdy wpis nie jest zatwierdzony
    CHECK (czy_zatwierdzony != 0 OR powod_odrzucenia IS NULL OR czy_zatwierdzony IS NULL),

    -- Jeden student nie może mieć dwóch wpisów z tym samym numerem dnia
    UNIQUE (student_id, nr_dnia),

    -- Jeden student nie może mieć dwóch wpisów z tą samą datą
    UNIQUE (student_id, data)
);

-- =========================================================================================================
-- === TRIGGERS – automatyczna aktualizacja pola zaktualizowano ===
-- =========================================================================================================

CREATE TRIGGER trg_formularz_zaktualizowano
AFTER UPDATE ON formularz_praktyk
FOR EACH ROW
BEGIN
    UPDATE formularz_praktyk SET zaktualizowano = datetime('now', 'localtime') WHERE id = OLD.id;
END;

CREATE TRIGGER trg_dziennik_zaktualizowano
AFTER UPDATE ON dziennik_wpis
FOR EACH ROW
BEGIN
    UPDATE dziennik_wpis SET zaktualizowano = datetime('now', 'localtime') WHERE id = OLD.id;
END;