from pomozne_funkcije import Seznam
import baza
import sqlite3
from geslo import sifriraj_geslo, preveri_geslo

conn = sqlite3.connect('baza_zavetisce.db')
baza.ustvari_bazo_ce_ne_obstaja(conn)
conn.execute('PRAGMA foreign_keys = ON')

uporabnik, cepiva, prostor, zival, oseba, posvojitev, cepljenja, namestitev = baza.pripravi_tabele(conn)


class LoginError(Exception):
    """
    Napaka ob napačnem uporabniškem imenu ali geslu.
    """
    pass


class Uporabnik:
    """
    Razred za uporabnika.
    """

    insert = uporabnik.dodajanje(["ime", "zgostitev", "sol"])

    def __init__(self, ime, id=None):
        """
        Konstruktor uporabnika.
        """
        self.id = id
        self.ime = ime

    def __str__(self):
        """
        Znakovna predstavitev uporabnika.
        Vrne uporabniško ime.
        """
        return self.ime

    @staticmethod
    def prijava(ime, geslo):
        """
        Preveri, ali sta uporabniško ime geslo pravilna.
        """
        sql = """
            SELECT id, zgostitev, sol FROM uporabnik
            WHERE ime = ?
        """
        try:
            id, zgostitev, sol = conn.execute(sql, [ime]).fetchone()
            if preveri_geslo(geslo, zgostitev, sol):
                return Uporabnik(ime, id)
        except TypeError:
            pass
        raise LoginError(ime)

    def dodaj_v_bazo(self, geslo):
        """
        V bazo doda uporabnika s podanim geslom.
        """
        assert self.id is None
        zgostitev, sol = sifriraj_geslo(geslo)
        with conn:
            self.id = uporabnik.dodaj_vrstico(
                [self.ime, zgostitev, sol],
                self.insert
            )

class Zival:
    """
    Razred za zival.
    """

    insert = zival.dodajanje(["ime", "vrsta", "spol", "dat_roj", "dat_spr", "bolezni"])

    def __init__(self, ime, vrsta, spol, dat_roj, dat_spr, bolezni, id = None):
        """
        Konstruktor zivali.
        """
        self.id = id
        self.ime = ime
        self.vrsta = vrsta
        self.spol = spol
        self.dat_roj = dat_roj
        self.dat_spr = dat_spr
        self.bolezni = bolezni

    def __str__(self):
        """
        Znakovna predstavitev zivali.
        """
        return self.vrsta + "-" + self.ime

    @staticmethod
    def najmlajsi(vrsta):
        """
        Vrne najmlajsih 10 zivali.
        """
        sql = """ SELECT * FROM zival WHERE vrsta = ? ORDER BY dat_roj DESC LIMIT 10"""
        for id, ime, vrsta, spol, dat_roj, dat_spr, bolezni in conn.execute(sql, [vrsta]):
            yield Zival(id, ime, vrsta, spol, dat_roj, dat_spr, bolezni)
    def dodaj_v_bazo(self):
        """
        Doda osebo v bazo.
        """
        assert self.id is None
        with conn:
            self.id = zival.dodaj_vrstico([self.ime, self.vrsta, self.spol, self.dat_roj, self.dat_spr, self.bolezni], self.insert)
    @staticmethod
    def poisci(niz):
        """
        Vrne vse zivali, ki v imenu vsebujejo dani niz.
        """
        sql = "SELECT id, ime, vrsta, spol, dat_roj, dat_spr, bolezni from zival WHERE ime LIKE ? "
        for id, ime, vrsta, spol, dat_roj, dat_spr, bolezni in conn.execute(sql, ['%' + niz + '%']):
            yield Zival(id = id, ime=ime, vrsta=vrsta, spol=spol, dat_roj = dat_roj, dat_spr= dat_spr, bolezni=bolezni)

    @staticmethod
    def obst(niz):
        """
        Vrne zival z id niz.
        """
        sql = "SELECT * from zival WHERE id = ? "
        for id, ime, vrsta, spol, dat_roj, dat_spr, bolezni in conn.execute(sql, [niz]):
            yield Zival(id = id, ime=ime, vrsta=vrsta, spol=spol, dat_roj = dat_roj, dat_spr= dat_spr, bolezni=bolezni)
    @staticmethod
    def posvojena(niz):
        """
        Vrne zival ce je posvojena.
        """
        sql = "SELECT zival.id, ime, vrsta, spol, dat_roj, dat_spr, bolezni from posvojitev, zival  WHERE zival.id = id_z AND zival.id = ? "
        for id, ime, vrsta, spol, dat_roj, dat_spr, bolezni in conn.execute(sql, [niz]):
            yield Zival(id = id, ime=ime, vrsta=vrsta, spol=spol, dat_roj = dat_roj, dat_spr= dat_spr, bolezni=bolezni)
    @staticmethod
    def odstrani_nah(id):
        """
        Žival odstrani iz nahajalisca.
        """
        odstrani_nah = "DELETE from namestitev WHERE id_z = ? "
        conn.execute(odstrani_nah, [id])
    @staticmethod
    def nahajalisce(id):
        """
        Žival nahajališče.
        """
        sql = "SELECT id_p, zasedenost, oddelek, kapaciteta from namestitev JOIN prostor ON namestitev.id_p = prostor.id WHERE id_z = ? "
        for id_p, zasedenost, oddelek, kapaciteta in conn.execute(sql, [id]):
            yield Prostor(id=id_p, oddelek =oddelek, kapaciteta = kapaciteta, zasedenost = zasedenost)
    @staticmethod
    def namesti(id_z, id_p):
        """
        Žival namesti.
        """
        sql = "INSERT INTO namestitev (id_z, id_p) VALUES (?, ?)"
        conn.execute(sql, [id_z, id_p])
            
           

class Oseba:
    """
    Razred za osebo.
    """

    insert = oseba.dodajanje(["ime", "priimek", "mail"])
    def __init__(self, ime, priimek, mail, id=None):
        """
        Konstruktor osebe.
        """
        self.id = id
        self.ime = ime
        self.priimek = priimek
        self.mail = mail

    def __str__(self):
        """
        Znakovna predstavitev osebe.
        Vrne ime osebe.
        """
        return self.ime


    @staticmethod
    def poisci(niz):
        """
        Vrne vse osebe, ki v imenu vsebujejo dani niz.
        """
        sql = "SELECT id, ime, priimek, mail FROM oseba WHERE ime LIKE ? OR priimek LIKE ?"
        for id, ime, priimek, mail in conn.execute(sql, ['%' + niz + '%', '%' + niz + '%']):
            yield Oseba(ime=ime, id=id, priimek=priimek, mail=mail)
   
    def dodaj_v_bazo(self):
        """
        Doda osebo v bazo.
        """
        assert self.id is None
        with conn:
            self.id = oseba.dodaj_vrstico([self.ime, self.priimek, self.mail], self.insert)
    @staticmethod
    def obst(niz):
        """
        Vrne osebo z id niz.
        """
        sql = "SELECT * from oseba WHERE id = ? "
        for id, ime, priimek, mail in conn.execute(sql, [niz]):
            yield Oseba(id = id, ime=ime, priimek = priimek, mail = mail)


class Prostor:
    """
    Razred za prostor.
    """
    def __init__(self, id, oddelek, kapaciteta, zasedenost):
        """
        Konstruktor osebe.
        """
        self.id = id
        self.oddelek = oddelek
        self.kapaciteta = kapaciteta
        self.zasedenost = zasedenost

    def __str__(self):
        """
        Znakovna predstavitev osebe.
        Vrne ime osebe.
        """
        return self.id
    @staticmethod
    def aliJeProstor(vrsta):
        """
        Ali je prostor za vrsto živali vrsta.
        """
        sql = "SELECT * FROM prostor WHERE oddelek = ? AND kapaciteta > zasedenost"
        for id, oddelek, kapaciteta, zasedenost in conn.execute(sql, [vrsta]):
            yield Prostor(id=id, oddelek = oddelek, kapaciteta = kapaciteta, zasedenost = zasedenost)
    @staticmethod
    def napolni_izprazni(zasedenost, id):
        """
        Napolni prostor.
        """
        sql_update = "UPDATE prostor SET zasedenost = ?  WHERE id = ?"
        conn.execute(sql_update, [zasedenost, id])
    @staticmethod
    def vsi():
        """
        Vrne vse prostore
        """
        sql = "SELECT * FROM prostor"
        for id, oddelek, kapaciteta, zasedenost in conn.execute(sql, []):
            yield Prostor(id=id, oddelek = oddelek, kapaciteta = kapaciteta, zasedenost = zasedenost)
   
    
class Namestitev:
    """
    Razred za nam.
    """
    def __init__(self, id_z, id_p):
        """
        Konstruktor.
        """
        self.id_z = id_z
        self.id_p = id_p
    @staticmethod
    def vsi():
        """
        Vrne vse namestitve
        """
        sql = "SELECT * FROM namestitev"
        for id_z, id_p in conn.execute(sql, []):
            yield Namestitev(id_z=id_z, id_p = id_p)
        
#cepljenja
class Cepljenja:
    """
    Razred za cep.
    """

    insert = cepljenja.dodajanje(["id_z", "id_c"])
    def __init__(self, id_z, id_c, id=None):
        """
        Konstruktor cep.
        """
        self.id = id
        self.id_z = id_z
        self.id_c = id_c

    def __str__(self):
        """
        Znakovna predstavitev cep.
        """
        return self.id_z + "-" + self.id_c

    def dodaj_v_bazo(self):
        """
        Doda cep v bazo.
        """
        assert self.id is None
        with conn:
            self.id = cepljenja.dodaj_vrstico([self.id_z, self.id_c], self.insert)

    @staticmethod
    def vsa():
        """
        Vrne vsa cepljenja
        """
        sql = "SELECT * FROM cepljenja"
        for id, id_z, id_c in conn.execute(sql, []):
            yield Cepljenja(id=id, id_z = id_z, id_c = id_c)
    
    #posvojitev
class Posvojitev:
    """
    Razred za pos.
    """
    insert = posvojitev.dodajanje(["id_z", "id_o", "datum"])
    def __init__(self, id_z, id_o, datum, id=None):
        """
        Konstruktor pos.
        """
        self.id = id
        self.id_z = id_z
        self.id_o = id_o
        self.datum = datum

    def __str__(self):
        """
        Znakovna predstavitev pos.
        """
        return self.id_z + "-" + self.id_o

    def dodaj_v_bazo(self):
        """
        Doda cep v bazo.
        """
        assert self.id is None
        with conn:
            self.id = posvojitev.dodaj_vrstico([self.id_z, self.id_o, self.datum], self.insert)


