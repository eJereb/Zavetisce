import csv
from geslo import sifriraj_geslo

class Tabela:
    """
    Razred, ki predstavlja tabelo v bazi.

    Polja razreda:
    - ime: ime tabele
    - podatki: datoteka s podatki ali None
    """
    ime = None
    podatki = None

    def __init__(self, conn):
        """
        Konstruktor razreda.
        """
        self.conn = conn

    def ustvari(self):
        """
        Metoda za ustvarjanje tabele.
        Podrazredi morajo povoziti to metodo.
        """
        raise NotImplementedError

    def izbrisi(self):
        """
        Metoda za brisanje tabele.
        """
        self.conn.execute("DROP TABLE IF EXISTS {};".format(self.ime))



    def uvozi(self, encoding="UTF-8", **kwargs):
        """
        Metoda za uvoz podatkov.
        Argumenti:
        - encoding: kodiranje znakov
        - ostali poimenovani argumenti: za metodo dodaj_vrstico
        """
        if self.podatki is None:
            return
        with open(self.podatki, encoding=encoding) as datoteka:
            podatki = csv.reader(datoteka)
            stolpci = self.pretvori(next(podatki), kwargs)
            poizvedba = self.dodajanje(stolpci)
            for vrstica in podatki:
                vrstica = [None if x == "" else x for x in vrstica]
                self.dodaj_vrstico(vrstica, poizvedba, **kwargs)

    def izprazni(self):
        """
        Metodo za praznjenje tabele.
        """
        self.conn.execute("DELETE FROM {};".format(self.ime))

    @staticmethod
    def pretvori(stolpci, kwargs):
        """
        Prilagodi imena stolpcev
        in poskrbi za ustrezne argumente za dodaj_vrstico.

        Privzeto vrne podane stolpce.
        """
        return stolpci

    def dodajanje(self, stolpci=None, stevilo=None):
        """
        Metoda za gradnjo poizvedbe.

        Arugmenti uporabimo enega od njiju):
        - stolpci: seznam stolpcev
        - stevilo: število stolpcev
        """
        if stolpci is None:
            assert stevilo is not None
            st = ""
        else:
            st = " ({})".format(", ".join(stolpci))
            stevilo = len(stolpci)
        return "INSERT INTO {}{} VALUES ({})". \
            format(self.ime, st, ", ".join(["?"] * stevilo))

    def dodaj_vrstico(self, podatki, poizvedba=None, **kwargs):
        """
        Metoda za dodajanje vrstice.

        Argumenti:
        - podatki: seznam s podatki v vrstici
        - poizvedba: poizvedba, ki naj se zažene
        - poljubni poimenovani parametri: privzeto se ignorirajo
        """
        if poizvedba is None:
            poizvedba = self.dodajanje(stevilo=len(podatki))
        cur = self.conn.execute(poizvedba, podatki)
        return cur.lastrowid


class Uporabnik(Tabela):
    """
    Tabela za uporabnike.
    """
    ime = "uporabnik"
    podatki = "podatki/uporabnik.csv"

    def ustvari(self):
        """
        Ustvari tabelo uporabnik.
        """
        self.conn.execute("""
            CREATE TABLE uporabnik (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ime       TEXT NOT NULL UNIQUE,
                zgostitev TEXT NOT NULL,
                sol       TEXT NOT NULL
            )
        """)

    @staticmethod
    def pretvori(stolpci, kwargs):
        """
        Zapomni si indeksa stolpcev za zgostitev in sol.
        """
        kwargs["zgostitev"] = stolpci.index("zgostitev")
        kwargs["sol"] = stolpci.index("sol")
        return stolpci

    def dodaj_vrstico(self, podatki, poizvedba=None, zgostitev=None, sol=None):
        """
        Dodaj uporabnika.
        Če sol ni podana, zašifrira podano geslo.
        """
        if sol is not None and zgostitev is not None and podatki[sol] is None:
            podatki[zgostitev], podatki[sol] = sifriraj_geslo(podatki[zgostitev])
        return super().dodaj_vrstico(podatki, poizvedba)


class Cepiva(Tabela):
    """
    Tabela za cepiva.
    """
    ime = "cepiva"
    podatki = "podatki/cepiva.csv"

    def ustvari(self):
        """
        Ustvari tabelo cepiva.
        """
        self.conn.execute("""
            CREATE TABLE cepiva (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                naziv TEXT UNIQUE
            );
        """)


class Prostor(Tabela):
    """
    Tabela za prostor.
    """
    ime = "prostor"
    podatki = "podatki/prostor.csv"

    def ustvari(self):
        """
        Ustvari tabelo prostor.
        """
        self.conn.execute("""
            CREATE TABLE prostor (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                oddelek      CHARACTER CHECK (oddelek IN ('M','P')),
                kapaciteta   INTEGER,
                zasedenost   INTEGER
            );
        """)


class Zival(Tabela):
    """
    Tabela za zivali.
    """
    ime = "zival"
    podatki = "podatki/zival.csv"


    def __init__(self, conn):
        """
        Konstruktor tabele.

        Argumenti:
        - conn: povezava na bazo
        """
        super().__init__(conn)
        #self.oznaka = oznaka

    def ustvari(self):
        """
        Ustavari tabelo zival.
        """
        self.conn.execute("""
            CREATE TABLE zival (
                id         INTEGER PRIMARY KEY,
                ime        TEXT,
                spol       CHARACTER CHECK (spol IN ('M','Z')),
                vrsta      CHARACTER CHECK (vrsta IN ('M','P')),
                dat_roj    DATE,
                dat_spr    DATE,
                bolezni    TEXT
            );
        """)


    def dodaj_vrstico(self, podatki, poizvedba=None):
        """
        Dodaj ZIVAL.

        Argumenti:
        - podatki: seznam s podatki o zivali
        - poizvedba: poizvedba za dodajanje zivali
        """
        return super().dodaj_vrstico(podatki, poizvedba)


class Oseba(Tabela):
    """
    Tabela za osebe.
    """
    ime = "oseba"
    podatki = "podatki/oseba.csv"
   

    def ustvari(self):
        """
        Ustvari tabelo oseba.
        """
        self.conn.execute("""
            CREATE TABLE oseba (
                id       INTEGER PRIMARY KEY,
                ime      TEXT,
                priimek  TEXT,
                mail     TEXT
            );
        """)
   
    def dodaj_vrstico(self, podatki, poizvedba=None):
        """
        Dodaj OSEBO.

        Argumenti:
        - podatki: seznam s podatki o osebi
        - poizvedba: poizvedba za dodajanje osebe
        """
        return super().dodaj_vrstico(podatki, poizvedba)


class Posvojitev(Tabela):
    """
    Tabela za posvojitve.
    """
    ime = "posvojitev"
   

    def ustvari(self):
        """
        Ustvari tabelo pos.
        """
        self.conn.execute("""
            CREATE TABLE posvojitev (
                id        INTEGER PRIMARY KEY,
                id_z      INTEGER,
                id_o      INTEGER,
                datum     DATE
            );
        """)
   
    def dodaj_vrstico(self, podatki, poizvedba=None):
        """
        Dodaj POS.
        """
        return super().dodaj_vrstico(podatki, poizvedba)


class Cepljenja(Tabela):
    """
    Tabela za cep.
    """
    ime = "cepljenja"


    def ustvari(self):
        """
        Ustvari tabelo cep.
        """
        self.conn.execute("""
            CREATE TABLE cepljenja (
                id       INTEGER PRIMARY KEY,
                id_z     INTEGER,
                id_c     INTEGER
            );
        """)
   
    def dodaj_vrstico(self, podatki, poizvedba=None):
        """
        Dodaj Cepljenje.

       """
        return super().dodaj_vrstico(podatki, poizvedba)

class Namestitev(Tabela):
    """
    Tabela za namestitev
    """
    ime = "namestitev"
    podatki = "podatki/namestitev.csv"


    def ustvari(self):
        """
        Ustvari tabelo namestitev.
        """
        self.conn.execute("""
            CREATE TABLE namestitev (
                id_z INTEGER REFERENCES zival (id),
                id_p INTEGER REFERENCES prostor (id)
            );
        """)

    def dodaj_vrstico(self, podatki, poizvedba=None):
    
        return super().dodaj_vrstico(podatki, poizvedba)

def ustvari_tabele(tabele):
    """
    Ustvari podane tabele.
    """
    for t in tabele:
        t.ustvari()


def izbrisi_tabele(tabele):
    """
    Izbriši podane tabele.
    """
    for t in tabele:
        t.izbrisi()

def izprazni_tabele(tabele):
    """
    Izprazni podane tabele.
    """
    for t in tabele:
        t.izprazni()

def uvozi_podatke(tabele):
    """
    Uvozi podatke v podane tabele.
    """
    for t in tabele:
        t.uvozi()


def ustvari_bazo(conn):
    """
    Izvede ustvarjanje baze.
    """
    tabele = pripravi_tabele(conn)
    izbrisi_tabele(tabele)
    ustvari_tabele(tabele)
    uvozi_podatke(tabele)
    
def pripravi_tabele(conn):
    """
    Pripravi objekte za tabele.
    """
    uporabnik = Uporabnik(conn)
    cepiva = Cepiva(conn)
    prostor = Prostor(conn)
    zival = Zival(conn)
    oseba = Oseba(conn)
    posvojitev = Posvojitev(conn)
    cepljenja = Cepljenja(conn)
    namestitev = Namestitev(conn)
    return [uporabnik, cepiva, prostor, zival, oseba, posvojitev, cepljenja, namestitev]


def ustvari_bazo_ce_ne_obstaja(conn):
    """
    Ustvari bazo, če ta še ne obstaja.
    """
    with conn:
        cur = conn.execute("SELECT COUNT(*) FROM sqlite_master")
        if cur.fetchone() == (0, ):
            ustvari_bazo(conn)