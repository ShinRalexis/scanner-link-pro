# Scanner Link Pro

*SCSI/USB to Scanner.* Programma per usare l'Epson GT-10000+ (SCSI, 1997 circa) sul PC moderno tramite
l'adattatore **Logitec LUB-MSC** (USB 1.1 verso SCSI). Le scansioni finiscono in
`Documenti\Scansioni GT-10000`.

## Uso

1. Accendi lo scanner (spie READY e OPERATE verdi) con l'adattatore collegato al PC.
2. Avvia **Scanner Link Pro** dal Desktop o dal menu Start, oppure con doppio clic su
   `Avvia Scanner Link Pro.bat` nella cartella del programma.
3. Aspetta il pallino verde "EPSON GT-10000 pronto".
4. **Anteprima**: scansione veloce di tutto il vetro (circa 10 secondi).
5. Scegli l'area: dal menu "Area" (A4, A5, A3, foto) oppure trascinando sull'anteprima.
   Gli angoli si trascinano per ridimensionare, l'interno per spostare.
6. **Scelta rapida** (in cima al pannello) imposta tutto con un clic, oppure con Ctrl+1, Ctrl+2, Ctrl+3:

   | Profilo | Impostazioni | Per cosa |
   | --- | --- | --- |
   | Documento | colore, 200 dpi, PDF compatto | pagine leggere e leggibili, circa 200-300 KB per A4 |
   | Media | colore, 300 dpi, JPEG equilibrato | foto e stampe di tutti i giorni |
   | Illustrazione | colore, 600 dpi, TIFF senza perdita | illustrazioni e archivio |

   Oppure scegli a mano modalità, risoluzione e formato (JPEG, PNG, TIFF, PDF), poi **Scansiona**.
   Per JPEG e PDF c'è **Compressione**: Massima (qualità 95, colore pieno), Equilibrata (82),
   Compatta (65). PNG e TIFF sono senza perdita; il PDF in bianco e nero usa la compressione dei fax
   (CCITT G4), circa 50 KB per pagina A4 a 300 dpi.
   Il cursore **Gamma** schiarisce o scurisce i toni medi (al centro c'è la curva standard dello
   scanner, circa 2,2); in bianco e nero lo stesso posto diventa **Soglia**. Luminosità, nitidezza e
   gamma valgono anche per l'anteprima, così si vede subito l'effetto.
7. Il file viene salvato con data e ora nel nome; la miniatura in alto a destra lo apre.
8. **Pagine: Sequenza** serve per più pagine di seguito: con JPEG, PNG o TIFF i file prendono
   numeri progressivi (`Scansione_001.jpg`, `_002`...), con PDF le scansioni diventano pagine dello
   stesso documento. "Termina sequenza" chiude la serie.
9. **Pulsante blu dello scanner** (accanto al coperchio): a programma aperto e scanner fermo avvia
   **Scansiona** con le impostazioni correnti. In Sequenza basta girare la pagina e premerlo.
   Durante una scansione il pulsante non viene letto, quindi una pressione in più non fa danni.
10. **Regolazioni** e **Correzione righe** sono sezioni a tendina, chiuse all'avvio: un clic sul titolo
    le apre. Da chiuse mostrano a destra lo stato ("Modificate" se un cursore non è a zero, "Attiva" o
    "Spenta" per la correzione).
11. **Correzione righe** (il pulsante tondo **i** accanto al titolo apre una spiegazione
    illustrata): toglie le righe verticali che lo scanner lascia per la
    polvere nell'ottica (spesso sottili e colorate, per esempio ciano). La prima volta serve una calibrazione
    ("Calibra...", circa due minuti): **vetro vuoto e coperchio chiuso**, lo scanner legge il
    coperchio bianco a colori e in grigi, poi un quadratino attorno alla riga più evidente a ogni
    risoluzione, per misurare l'allineamento. Poi basta lasciarla su **Attiva**: vale per anteprima,
    colore e grigi (il bianco e nero non ne ha bisogno). Se compaiono righe nuove (polvere che si
    sposta), si rifà la calibrazione.

Tempi indicativi. Il limite è l'USB 1.1 dell'adattatore, circa 650 KB/s nelle scansioni grandi;
le righe "misurato" sono state cronometrate, le altre sono stime ricavate da quella velocità:

| Documento | Modalità | Risoluzione | Tempo |
| --- | --- | --- | --- |
| A4 | grigi | 150 dpi | 12 s (misurato) |
| A4 | colore | 150 dpi | circa 15 s |
| A4 | colore | 300 dpi | circa 45 s |
| A4 | colore | 600 dpi | circa 2,5 min |
| A3 | colore | 600 dpi | 5 min, 199 MB di dati, JPEG da 17 MB (misurato) |

Risoluzione ottica misurata sul nostro esemplare: **600 dpi**. Oltre quel valore il sensore non
aggiunge dettaglio in orizzontale e a 1200 dpi ne aggiunge poco in verticale: per le illustrazioni
600 dpi è il valore consigliato (un A3 a colori: circa 209 MB, 6-7 minuti). Il programma avvisa
sopra i 600 dpi, mostra sempre la stima di dimensioni, peso e tempo, e durante la scansione scrive i
dati su disco (cartella temporanea), così anche un A3 a 1200 dpi non riempie la memoria.

## Come funziona

```text
Interfaccia Windows (Python + Tkinter)          app\scanner_app.pyw, app\bridge.py
        |  pipe stdin/stdout (JSON + dati immagine)
Linux interno: distribuzione WSL "GT10000"      Debian 13 minimale, solo Python 3 + pyusb
        |  driver in spazio utente              gt10000\ (copiato in /opt/gt10000)
usbipd-win passa l'adattatore USB a Linux
        |
Logitec LUB-MSC  --SCSI-->  Epson GT-10000+ (ID SCSI 2)
```

Nessun sistema operativo ha un driver per questo adattatore: non è un dispositivo
"USB Mass Storage" standard ma usa un protocollo proprietario Logitec. Il protocollo è
stato ricostruito dal driver originale per Windows 2000/XP (`riferimenti\LUBSC_XPD340.EXE`,
file `LUBSC2K.SYS`) ed è implementato in `gt10000\lubsc.py`. Sopra c'è il protocollo Epson
ESC/I livello B7 (`gt10000\esci.py`), ricavato dal backend SANE `epson2`.

Dato che il driver lavora in spazio utente, al Linux interno non serve nessun modulo del
kernel: basta che veda il dispositivo USB.

**Perché un motore Linux dentro il programma e non un driver Windows.** Per la compatibilità nel
tempo. Un driver Windows per l'adattatore sarebbe legato alla versione del sistema: ogni nuovo
Windows (modello dei driver, firma obbligatoria, cambi del kernel, processori ARM) chiederebbe di
rimetterci mano, ed è proprio quello che ha fermato il driver originale Logitec a Windows XP. Il
motore Linux invece lavora in spazio utente su strati stabili (libusb, Python, il protocollo USB
dell'adattatore, che non cambierà più), e per Windows è solo un programma dentro WSL: con un Windows
nuovo non c'è niente da riscrivere, al massimo da reinstallare WSL e usbipd-win, mantenuti da
Microsoft e dal progetto usbipd. Lo stesso motore gira anche su un Linux vero (un PC o un Raspberry
Pi) senza modifiche.

## Compatibilità

**Scanner.** Verificato solo sull'Epson GT-10000+ (firmware 2.83, protocollo ESC/I livello B7). Il
programma però non è legato a quel modello: cerca qualunque scanner Epson sul bus SCSI e gli chiede
area del vetro, risoluzioni, livello del protocollo e (sui livelli B7 e B8) risoluzione ottica, poi
si adatta. Cosa funziona secondo il livello, dalla tabella dei comandi del backend SANE epson2:

| Livello ESC/I | Cosa funziona |
| --- | --- |
| B7, B8 | tutto |
| B5, B6 | tutto tranne il pulsante sullo scanner; luminosità da -3 invece che da -4 |
| B4 | grigi e bianco e nero; a colori no (lo scanner manda le righe dei tre colori separate, formato non gestito) |
| A, B1-B3, D, F | non supportati: il programma lo dice all'apertura |

Modelli Epson SCSI che dovrebbero funzionare, **da provare** (fonte: elenco dei modelli del backend
SANE epson2; i nomi tra parentesi sono le versioni per altri mercati):

| Modelli | Livello | Aspettativa |
| --- | --- | --- |
| GT-10000+ (ES-6000H, ES-6000HS) | B7 | verificato |
| GT-10000 (ES-6000) | probabilmente B7 | molto alta: stessa famiglia |
| GT-30000 (ES-9000H) | B7 (manuale di servizio) | molto alta; l'alimentatore di fogli non è gestito |
| Expression 1600 (ES-2000), Expression 1640XL (ES-8500), Expression 1680 (ES-2200), GT-15000 (ES-7000H), Perfection 1200S (GT-7600S), Perfection 1640SU (GT-8700) | B7 o B8, probabile | alta |
| GT-9600, GT-12000 (Expression 836XL, ES-8000), Expression 800, GT-9500 (Expression 636), Perfection 636S (GT-7000S) | anni '90, da B4 a B6 | media |
| GT-8000 (ES-800C), GT-5500, ES-300GS e precedenti | B3 o inferiore | non supportati |

La **correzione righe** misura tutto sullo scanner collegato (sensibilità delle colonne e
allineamento a ogni risoluzione). Solo la curva standard che serve a tornare in lineare è quella
misurata sul GT-10000+: su un altro modello, per la correzione più precisa conviene spostare il
cursore Gamma su un valore (es. 2,2) invece di lasciarlo su Standard.

**Adattatore.** Serve un **Logitec LUB-SC o LUB-MSC** (USB 0789:00C0, anche 0789:0004). Quello
provato dall'inizio alla fine è il **LUB-MSC** (0789:00C0): chi compra un adattatore apposta prenda
quello, è verificato al 100% con questo programma; il LUB-SC usa lo stesso protocollo ma non è stato
provato. Non sono più in produzione: si trovano usati su eBay, Yahoo! Aste Giappone, Mercari e simili.
Il produttore è **Logitec Corporation**, azienda giapponese (gruppo ELECOM), **non Logitech**, la marca
nota di mouse e tastiere. Altri
adattatori USB-SCSI non funzionano: quelli con protocollo proprietario per gli scanner (Adaptec
USB2-Xchange, Ratoc U2SCX in modalità SCSI) richiederebbero lo stesso lavoro di ricostruzione fatto
per il Logitec; quelli che Linux vede come normali dischi USB (Microtech USB-SCSI, Castlewood ORB,
chip Shuttle eUSCSI) potrebbero funzionare con un trasporto "SCSI generico" di Linux, non ancora
scritto perché nessuno ha potuto provarlo con uno scanner.

**Per aiutare:** se hai uno di questi scanner o adattatori, prova il programma e manda il contenuto
di "Mostra registro": c'è il modello, il livello del protocollo, l'area del vetro e ogni errore.

## Installazione

**Con l'installatore** (consigliato): scarica `ScannerLinkPro-Setup-<versione>.exe` dalla pagina delle
release su GitHub e avvialo. Chiede la lingua (9 lingue), installa il programma in Programmi con il
collegamento nel menu Start (e, se vuoi, sul Desktop) e la voce in "App installate" per disinstallarlo.
Se mancano, installa anche usbipd-win e WSL; nel secondo caso chiede un riavvio. Al primo avvio il
programma prepara il suo Linux interno nel tuo profilo (circa un minuto). Serve Windows 10 versione
2004 o successiva, oppure Windows 11, a 64 bit (x64), con la virtualizzazione attiva nel BIOS/UEFI
(serve a WSL 2; sulla maggior parte dei PC lo è già). Disinstallando si può scegliere se togliere anche
il Linux interno; impostazioni, calibrazione e scansioni restano.

**Dai sorgenti** (per chi sviluppa), da PowerShell nella cartella del progetto:

```powershell
powershell -ExecutionPolicy Bypass -File .\installa.ps1
```

Lo script si può rilanciare quando si vuole. Installa ciò che manca (Python, Pillow, numpy,
usbipd-win), ricrea il Linux interno dal backup `linux\GT10000-debian.tar` se è stato rimosso (o da
Debian tramite Docker), aggiorna il driver dentro Linux, condivide l'adattatore e ricrea i collegamenti.

**Costruire l'installatore**: `powershell -ExecutionPolicy Bypass -File .\installer\build.ps1`. Serve
Inno Setup 6.5 o successivo e PyInstaller; il pacchetto di usbipd-win si scarica da solo e se ne
controlla l'impronta. Il risultato è in `installer\output\`.

## Problemi comuni

- **Righe verticali sottili lungo tutta la pagina**, spesso colorate (ciano, magenta, giallo), a volte
  grigie, più scure o più chiare del resto, sempre nello stesso punto: è polvere dentro lo scanner
  (specchi, lente, sensore), quindi pulire il vetro non basta. Le toglie la **Correzione righe**
  (punto 11 di "Uso"). Se una riga cambia posto da una scansione all'altra, invece, è sporco sul vetro
  o sul foglio: lì serve un panno, non la calibrazione. Sull'esemplare dell'autore c'era una riga ciano
  a 122 mm da sinistra (misure nella sezione "Correzione righe: come funziona").
- **Dopo la correzione resta un'ombra leggerissima della riga**: è normale entro 2 livelli su 255.
  Se è più marcata, rifai la calibrazione (la polvere può essersi spostata). La correzione è tarata
  con Luminosità 0 e Nitidezza 0; con altri valori funziona, ma un po' meno precisa.

- **"WSL non riesce ad avviare la sua macchina virtuale"**: la virtualizzazione è spenta nel BIOS/UEFI
  (Intel VT-x, oppure AMD-V/SVM). Si attiva dalle impostazioni del firmware all'avvio del PC; poi si
  riavvia e si riapre il programma.
- **"[Errno 16] Resource busy" oppure "cerco lo scanner sul bus SCSI..." che non finisce**: un motore
  di un'apertura precedente (programma chiuso a forza, riavvio lento) teneva ancora l'adattatore, oppure
  è stato interrotto a metà di un comando e l'adattatore non risponde più. Dalla versione 1.0.2 il
  programma ferma da solo, in ordine, i motori rimasti e, se l'adattatore non risponde, lo scollega e
  ricollega (usbipd) e riprova una volta. Se non basta: Riconnetti, oppure staccare e riattaccare il cavo
  USB dell'adattatore. Il programma si apre una volta sola: riaprendolo si torna alla finestra aperta.
- **"Adattatore non collegato" con l'adattatore inserito**: il programma riconosce i due identificativi
  dichiarati dal driver originale Logitec (0789:00C0 e 0789:0004, il secondo dalla versione 1.0.1).
  Se in `usbipd list` l'adattatore compare con un altro identificativo, segnalalo in una Issue.
- **Registro**: il link "Mostra registro" in basso nel pannello apre una finestra con ogni passaggio.
  Gli errori SCSI riportano anche gli 8 byte di stato dell'adattatore.

- **"Adattatore Logitec USB-SCSI non collegato"**: controlla il cavo USB e premi Riconnetti.
- **"Nessuno scanner Epson trovato sul bus SCSI"**: lo scanner è spento, oppure è stato
  acceso dopo l'avvio del programma. Accendilo, aspetta le spie verdi, premi Riconnetti.
- **Richiesta di autorizzazione (UAC) al primo avvio**: serve una volta sola, per condividere
  l'adattatore con Linux (`usbipd bind`).
- **Lo scanner non risponde dopo aver cambiato presa USB**: premi Riconnetti; se non basta,
  rilancia `installa.ps1`.
- **Il registro in basso a destra** mostra ogni passaggio: in caso di errore è il primo posto
  da guardare.

## File

| Percorso | Contenuto |
| --- | --- |
| `Avvia Scanner Link Pro.bat` | avvio con doppio clic, senza finestra del prompt |
| `app\icona.ico`, `app\icona.png`, `app\icona_piccola.png` | icona del programma (la piccola, senza scritta, per 16-48 px) |
| `app\scanner_app.pyw` | interfaccia grafica |
| `app\ui.py` | tema scuro e controlli disegnati (pulsanti, segmenti, cursori) |
| `app\i18n.py` | traduzioni in 9 lingue (it, en, es, de, fr, ja, ko, zh, ru), anche dei messaggi del motore |
| `app\destripe.py` | correzione righe: calibrazione sul coperchio e correzione delle scansioni (usa numpy) |
| `gt10000\color.py` | matrice colore del modello (come SANE) e curve gamma per ESC m / ESC z |
| `gt10000\messages.py` | messaggi del motore: chiave, valori e testo italiano |
| `tests\test_color.py` | test della matrice colore e delle curve gamma |
| `tests\test_destripe.py` | test della correzione righe su dati sintetici |
| `tests\test_i18n.py` | controllo del catalogo: lingue complete, segnaposto coerenti, messaggi del motore riconosciuti |
| `tests\test_lubsc.py` | test del trasporto con un adattatore finto |
| `PRODUCT.md`, `DESIGN.md` | scheda del prodotto e regole grafiche |
| `app\bridge.py` | avvio del Linux interno, usbipd, comunicazione con il motore |
| `gt10000\lubsc.py` | trasporto SCSI per l'adattatore Logitec (protocollo ricostruito) |
| `gt10000\esci.py` | protocollo Epson ESC/I: identità, parametri, scansione a blocchi |
| `gt10000\backend.py` | motore di scansione che gira dentro Linux |
| `setup\provision.sh` | preparazione della distribuzione Debian |
| `installa.ps1` | installazione e riparazione dai sorgenti |
| `README.md` | pagina d'ingresso su GitHub, in inglese, con l'installatore in evidenza |
| `LICENSE`, `THIRD_PARTY_NOTICES.md` | licenza (GPL 2.0 o successiva) e componenti di terze parti |
| `docs/banner.jpg` | immagine di presentazione del repository |
| `installer\` | installatore Windows: `ScannerLinkPro.iss` (Inno Setup, 9 lingue), `ScannerLinkPro.spec` (PyInstaller), `build.ps1` |
| `linux\` | disco virtuale del Linux interno e suo backup |
| `riferimenti\` | pacchetto driver originale Logitec |

Impostazioni dell'interfaccia: `%APPDATA%\GT10000Scanner\impostazioni.json`; calibrazione delle righe:
`%APPDATA%\GT10000Scanner\calibrazione_righe.npz` (circa 300 KB, si rifà con "Calibra...").

## Note tecniche sull'adattatore Logitec LUB-SC / LUB-MSC (VID 0789, PID 00C0)

Interfaccia USB di classe FF (proprietaria), endpoint bulk OUT 0x01 e bulk IN 0x81.

| Fase | Richiesta USB |
| --- | --- |
| selezione bersaglio | vendor OUT `0x40`, bRequest 5, wValue `(ID << 8) \| 7` |
| comando | class OUT `0x21`, bRequest 0, dati = CDB SCSI a 12 byte |
| dati | bulk OUT 0x01 oppure bulk IN 0x81 |
| stato | vendor IN `0xC0`, bRequest 0, 8 byte: [0] 1 o 4 = concluso, [1] errore adattatore (0x11 = nessun dispositivo), [2] stato SCSI |

Se il bersaglio chiude con CHECK CONDITION senza fase dati, l'adattatore mette in stallo la
richiesta di comando: si legge lo stato e poi il REQUEST SENSE. La lettura di stato vale solo se è
lunga esattamente 8 byte: ogni tanto (circa 1 volta su 700 comandi) l'adattatore ne manda 7 e i campi
slittano; il driver originale in quel caso rilegge, e così fa `lubsc.py`. Dopo l'accensione lo
scanner risponde UNIT ATTENTION (sense 06) a tutto tranne che all'INQUIRY.

Lo scanner: `EPSON SCANNER GT-10000`, firmware 2.83, ESC/I B7, area 28080 x 40800 punti a
2400 dpi (297 x 432 mm). Ogni comando ESC/I viaggia in un SCSI WRITE(6) (0x0A), ogni
risposta in un READ(6) (0x08).

Capacità verificate sul GT-10000+ (firmware 2.83) il 2026-10-12:

| Comando | Risposta | Note |
| --- | --- | --- |
| ESC D 12 / 14 / 16 | NAK | solo 8 bit per canale: i 16 bit non sono possibili |
| ESC Z 3 + ESC z | ACK | curve gamma personalizzate (cursore Gamma) |
| ESC m | ACK | matrice colore; la correzione interna dello scanner coincide già con il profilo SANE (differenza media 1,2 livelli su 255) |
| ESC Z 0x00 / 0x10 / 0x20 | ACK | gamma preimpostate per la stampa, non usate |
| ESC ! | ACK | stato del pulsante blu di avvio: primo bit = premuto (usato dal motore 1.2) |
| ESC R asimmetrico | ACK | risoluzioni diverse in orizzontale e verticale (600 x 50 per la calibrazione righe) |
| FS I | 80 byte | identità estesa: risoluzione ottica 600 dpi (usata dal motore 1.4 sui livelli B7 e B8) |

La curva gamma predefinita dello scanner non è una gamma pura: in ombra è una potenza di circa 1,95,
nei toni medi circa 2,2, e il bianco è "stirato" (dal valore lineare 221 in su esce già 255, per questo
il coperchio chiuso risulta bianco pieno). Lo scanner la applica con più di 8 bit: nell'uscita
standard ci sono tutti i livelli, anche in ombra. La tabella misurata (codificato verso lineare) è in
`app\destripe.py`.

## Correzione righe: come funziona

Il GT-10000+ legge il vetro con un sensore lineare che scorre dall'alto in basso: un granello di
polvere nell'ottica toglie luce sempre alle stesse colonne e lascia una riga lungo tutta la pagina. È
lo stesso difetto dei satelliti a scansione "pushbroom" e si corregge allo stesso modo, con una
calibrazione relativa delle colonne (tecnica pubblica, nessun software Epson coinvolto).

1. **Calibrazione**: il coperchio bianco, a vetro vuoto, letto a 600 x 50 dpi con curva lineare
   (gamma 1,0), una volta a colori e una in grigi. Poi, se c'è una riga oltre il 5%, un quadratino
   di 14 mm attorno a lei a ogni risoluzione (50-1200 dpi e anteprima): il profilo letto si
   confronta con la calibrazione spostata di 0,25 in 0,25 colonne, e lo spostamento migliore è lo
   scarto d'origine di quella risoluzione. Circa due minuti in tutto.
2. Per ogni fascia di 20 mm il profilo delle colonne viene diviso per la sua mediana mobile su 255
   colonne (10,8 mm, molto più larga della riga): resta la sensibilità relativa di ogni colonna.
3. Lungo il vetro ogni colonna è lisciata con una mediana su 5 fasce e una media su 3: un granello
   sul vetro o sul coperchio occupa una o due fasce e sparisce, una riga vera attraversa tutto il
   vetro e resta. Si correggono le colonne che restano oltre l'1,5%.
4. **In scansione** ogni punto torna lineare (con la curva standard misurata, oppure con la gamma
   scelta), viene diviso per il fattore della sua colonna (media sull'impronta del punto a 600 dpi,
   interpolata lungo il vetro) e ricodificato. I punti a 255 restano 255.

Misure sul nostro esemplare (12/10/2026):

- la riga a 122 mm è larga circa 2 mm e cresce dall'alto in basso: rosso da 0,98 a 0,81, verde da
  0,99 a 0,88, grigi da 0,99 a 0,90; il blu "più chiaro" sulla riga non è luce in più, è la matrice
  colore interna che compensa il calo del verde (a matrice spenta il blu resta a 1,008);
- tra letture diverse a 600 dpi la riga resta allineata entro 1,5 colonne e la sua intensità varia
  dell'1-2%;
- **l'origine orizzontale dipende dalla risoluzione**: fino a 300 dpi lo scanner riduce la
  risoluzione in un altro modo e la riga cade circa 5 colonne a 600 dpi (0,2 mm) più a destra,
  da 400 dpi in su circa 2, nell'anteprima veloce 9. Senza questo scarto la correzione lasciava un
  doppio bordo. Dal 2026-10-13 la calibrazione lo misura da sola (prima prova: da +4,5 a +6,75 fino a
  300 dpi, da +0,5 a +0,75 sopra, +7,75 in anteprima); la tabella `X_OFFSET` di `app\destripe.py`
  resta per i file di calibrazione vecchi;
- con gli scarti misurati, scarto peggiore sulla riga a gamma 2,6: 1,3 a 150 dpi, 1,4 a 300 dpi,
  1,8 a 600 dpi (prima 16-17);
- risultato, scarto peggiore sulla riga (livelli su 255): colore curva standard da 16,3 a 1,9,
  colore gamma 2,6 da 17,6 a 2,3, grigi da 7,0 a 0,0, anteprima da 13,3 a 1,2;
- tempo: un A3 a colori a 600 dpi si corregge in circa 6 s, a 300 dpi in meno di 1 s.

## Licenza

Copyright (C) 2026 ShinRalexis. Scanner Link Pro è software libero: si può ridistribuire e modificare
secondo i termini della **GNU General Public License, versione 2 o (a scelta) successiva**. Testo in
`LICENSE`; componenti su cui si basa o che l'installatore contiene, con le loro licenze e i sorgenti,
in `THIRD_PARTY_NOTICES.md`. Il protocollo Epson segue il backend SANE `epson2`, anch'esso GPL 2.0 o
successiva. Epson, Logitec, Windows e WSL sono marchi dei rispettivi proprietari; Scanner Link Pro è un
progetto indipendente, non affiliato a loro.
