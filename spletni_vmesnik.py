import json
import random
import bottle
from sqlite3 import IntegrityError
import sqlite3
from model import LoginError, Uporabnik, Zival, Oseba, Prostor, Cepljenja, Posvojitev, Namestitev #, Cepiva

NASTAVITVE = 'nastavitve.json'

try:
    with open(NASTAVITVE) as f:
        nastavitve = json.load(f)
        SKRIVNOST = nastavitve['skrivnost']
except FileNotFoundError:
    SKRIVNOST = "".join(chr(random.randrange(32, 128)) for _ in range(32))
    with open(NASTAVITVE, "w") as f:
        json.dump({'skrivnost': SKRIVNOST}, f)


def zahtevaj_prijavo():
    if bottle.request.get_cookie('uporabnik', secret=SKRIVNOST) != 'admin':
        bottle.abort(401, 'Nimate pravice za urejanje!')


def zahtevaj_odjavo():
    if bottle.request.get_cookie('uporabnik', secret=SKRIVNOST):
        bottle.redirect('/')


@bottle.get('/prijava/')
def prijava():
    zahtevaj_odjavo()
    return bottle.template(
        'prijava.html',
        napaka=None, ime=""
    )


@bottle.post('/prijava/')
def prijava_post():
    zahtevaj_odjavo()
    ime = bottle.request.forms['uporabnisko_ime']
    geslo = bottle.request.forms['geslo']
    try:
        uporabnik = Uporabnik.prijava(ime, geslo)
        bottle.response.set_cookie('uporabnik', ime, path='/', secret=SKRIVNOST)
        bottle.response.set_cookie('uid', uporabnik.id, path='/', secret=SKRIVNOST)
        bottle.redirect('/')
    except LoginError:
        return bottle.template(
            'prijava.html',
            napaka='Uporabniško ime in geslo se ne ujemata!',
            ime=ime
        )


@bottle.get('/vpis/')
def vpis():
    zahtevaj_odjavo()
    return bottle.template(
        'vpis.html',
        napaka=None, ime=""
    )


@bottle.post('/vpis/')
def vpis_post():
    zahtevaj_odjavo()
    ime = bottle.request.forms['uporabnisko_ime']
    geslo1 = bottle.request.forms['geslo1']
    geslo2 = bottle.request.forms['geslo2']
    if geslo1 != geslo2:
        return bottle.template(
            'vpis.html',
            napaka='Gesli se ne ujemata!',
            ime=ime
        )
    try:
        uporabnik = Uporabnik(ime)
        uporabnik.dodaj_v_bazo(geslo1)
        bottle.response.set_cookie('uporabnik', ime, path='/', secret=SKRIVNOST)
        bottle.response.set_cookie('uid', uporabnik.id, path='/', secret=SKRIVNOST)
        bottle.redirect('/')
    except IntegrityError:
        return bottle.template(
            'vpis.html',
            napaka='Uporabniško ime že obstaja!',
            ime=ime
        )


@bottle.get('/odjava/')
def odjava():
    bottle.response.delete_cookie('uporabnik', path='/')
    bottle.redirect('/')


@bottle.get('/')
def zacetna_stran():
    return bottle.template(
        'zacetna_stran.html',
        leta=range(1950, 2020),
        ime=bottle.request.get_cookie('uporabnik', secret=SKRIVNOST)
    )


@bottle.get('/dodaj-osebo/')
def dodaj_osebo():
    zahtevaj_prijavo()
    return bottle.template(
        'dodaj_osebo.html',
        napaka=None, ime="", priimek = "", mail = ""
    )


@bottle.post('/dodaj-osebo/')
def dodaj_osebo_post():
    zahtevaj_prijavo()
    ime = bottle.request.forms.getunicode('ime')
    priimek = bottle.request.forms.getunicode('priimek')
    mail = bottle.request.forms.getunicode('mail')
    
   
    oseba = Oseba(ime, priimek, mail)
    oseba.dodaj_v_bazo()
    bottle.redirect('/')
    
 #ZIVAL
@bottle.get('/dodaj-zival/')
def dodaj_zival():
    zahtevaj_prijavo()
    return bottle.template(
        'dodaj_zival.html',
         napaka=None, ime="", vrsta ="", spol="", dat_roj = "", dat_spr = "", bolezni =""
     )


@bottle.post('/dodaj-zival/') 
def dodaj_zival_post():
    zahtevaj_prijavo()
    ime = bottle.request.forms.getunicode('ime')
    vrsta = bottle.request.forms.getunicode('vrsta')
    spol = bottle.request.forms.getunicode('spol')
    dat_roj = bottle.request.forms.getunicode('dat_roj')
    dat_spr = bottle.request.forms.getunicode('dat_spr')
    bolezni = bottle.request.forms.getunicode('bolezni')
    prostor = list(Prostor.aliJeProstor(vrsta))
    if (len(prostor) != 0):
        zasedenost = prostor[0].zasedenost + 1
        id = prostor[0].id
        prostor[0].napolni_izprazni(zasedenost, id)
        zival = Zival(ime, vrsta, spol, dat_roj, dat_spr, bolezni)
        zival.dodaj_v_bazo()
        Zival.namesti(zival.id, id)
        bottle.redirect('/')
    else:
        return bottle.template(
            'dodaj_zival.html',
            napaka='V zavetišču za to vrsto živali žal ni več prostora.',
             ime="", vrsta ="", spol="", dat_roj = "", dat_spr = "", bolezni =""
            )

#cepljenje
@bottle.get('/dodaj-cepljenje/')
def dodaj_cepljenje():
    zahtevaj_prijavo()
    return bottle.template(
        'dodaj_cepljenje.html',
        napaka=None, id_z="", id_c =""
    )


@bottle.post('/dodaj-cepljenje/')
def dodaj_cepljenje_post():
    zahtevaj_prijavo()
    id_z = bottle.request.forms.getunicode('id_z')
    id_c = bottle.request.forms.getunicode('id_c')
    
    zival = list(Zival.obst(id_z))
    if (len(zival) != 0):
      cepljenje = Cepljenja(id_z, id_c)
      cepljenje.dodaj_v_bazo()
      bottle.redirect('/')
    else:
        return bottle.template(
            'dodaj_cepljenje.html',
            napaka='Žival s tem ID ne obstaja!',
             id_z="", 
             id_c =""
            )


#posvojitve
@bottle.get('/posvojitev/')
def dodaj_posvojitev():
    zahtevaj_prijavo()
    return bottle.template(
        'dodaj_posvojitev.html',
        napaka=None, id_z="", id_o ="", datum = ""
    )


@bottle.post('/posvojitev/')
def dodaj_posvojitev_post():
    zahtevaj_prijavo()
    id_z = bottle.request.forms.getunicode('id_z')
    id_o = bottle.request.forms.getunicode('id_o')
    datum = bottle.request.forms.getunicode('datum')
    
    zival = list(Zival.obst(id_z))
    oseba = list(Oseba.obst(id_o))
    pos = list(Zival.posvojena(id_z))
    if (len(zival) != 0 and len(oseba) != 0 and len(pos) == 0):
      posvojitev = Posvojitev(id_z, id_o, datum)
      posvojitev.dodaj_v_bazo()
      nah = list(Zival.nahajalisce(id_z))[0]
      id_nah = nah.id
      zas_nah = nah.zasedenost - 1
      Prostor.napolni_izprazni(zas_nah, id_nah)
      Zival.odstrani_nah(id_z)
      bottle.redirect('/')
    else:
        return bottle.template(
            'dodaj_posvojitev.html',
            napaka='Žival ali oseba s tem ID ne obstaja ali je že posvojena!',
             id_z="", 
             id_o ="",
             datum = ""
            )



@bottle.get('/isci-o/')
def isci():
    iskalni_niz = bottle.request.query.getunicode('iskalni_niz')
    osebe = Oseba.poisci(iskalni_niz)
    return bottle.template(
        'rezultati_iskanja.html',
        iskalni_niz=iskalni_niz,
        osebe=osebe
    )
@bottle.get('/isci-z/')
def isci():
    iskalni_niz = bottle.request.query.getunicode('iskalni_niz')
    zivali = Zival.poisci(iskalni_niz)
    return bottle.template(
        'rezultati_iskanja_z.html',
        iskalni_niz=iskalni_niz,
        zivali=zivali
    )


@bottle.get('/prostori/')
def isci():
    prostori = Prostor.vsi()
    namestitve = Namestitev.vsi()
    return bottle.template(
        'prostori.html',
        prostori = prostori,
        namestitve = namestitve
    )

@bottle.get('/precepljenost/')
def isci():
    precepljenost = Cepljenja.vsa()
    return bottle.template(
        'precepljenost.html',
        precepljenost = precepljenost
       
    )


bottle.run(debug=True, reloader=True)