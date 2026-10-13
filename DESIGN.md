# Design

Stile scelto dall'autore il 2026-09-29: **standard pulito**, tema scuro neutro sul modello di
Lightroom e dell'app Foto di Windows 11. L'illustrazione domina, i comandi stanno in un pannello
laterale ordinato. Implementazione: `app/ui.py` (token e controlli), `app/scanner_app.pyw` (layout).

## Principi

- **Neutro davvero.** Tutti i grigi sono senza dominante: attorno a un'illustrazione un grigio
  colorato falsa il giudizio sui colori. Nessun colore decorativo.
- **Un solo accento**, blu, per azione principale, selezione e avanzamento. Verde, ambra e rosso
  solo per gli stati (pronto, in corso o avviso, errore).
- **L'immagine prima di tutto.** Il vetro occupa tutto lo spazio libero; fuori dall'area scelta
  l'anteprima è scurita al 42%, non coperta da trame.
- **Onestà sullo stato.** Stima di dimensioni, peso e tempo sempre visibile; durante la scansione
  percentuale, velocità, tempo residuo e posizione della testina sull'anteprima.

## Colori (`ui.Theme`)

| Ruolo | Valore |
| --- | --- |
| attorno al vetro | `#1c1c1d` |
| vetro vuoto | `#29292b` |
| pannelli (barra superiore, laterale) | `#242426` |
| fondo dei controlli / hover / selezionato | `#2e2e31` / `#363639` / `#46464b` |
| bordi | `#3a3a3e` |
| testo / secondario / terziario / disattivato | `#ededee` / `#b0b0b5` / `#96969c` / `#6c6c72` |
| accento / hover / pressione | `#2b73d6` / `#3a82e4` / `#2563bb` |
| selezione sopra l'immagine, focus | `#5ea2ff` |
| pronto / attesa e avvisi / errore | `#3fb950` / `#d9a441` / `#f0524f` |

## Tipografia

Una sola famiglia di sistema: Segoe UI Variable (Text per l'interfaccia, Display per il titolo),
con ripiego su Segoe UI. Corpo 10 pt, etichette e note 9 pt, sezioni 11 pt semibold, titolo 13 pt.
Il registro usa Cascadia Mono (ripiego Consolas) perché è testo tecnico.

## Componenti

- **Pulsanti**: `primary` (Scansiona), `secondary` (Anteprima), `danger` (Annulla durante la
  scansione, stesso posto di Scansiona), `ghost` (Riconnetti). Angoli 6 px, altezza 40 per le azioni.
- **Selettori a segmenti** per modalità, risoluzione (150, 300, 600, 1200 + menu "Altre..."),
  formato e formati d'area. Frecce sinistra e destra da tastiera.
- **Cursori** con lo zero marcato; doppio clic riporta a zero. Il valore a destra può avere un formato
  proprio (`fmt`): il terzo cursore mostra "Standard" o "γ 2,4" per la gamma, il numero per la soglia.
  Gamma e Soglia occupano lo stesso posto e si scambiano secondo la modalità (la soglia vale solo in
  bianco e nero, la gamma solo in colore e grigi).
- **Pagine**: selettore Singola / Sequenza; sotto, una riga di nota che dice cosa succederà (prossimo
  numero o PDF unico) e, a sequenza avviata, il link "Termina sequenza".
- **Scelta rapida** (`ui.ProfileCards`): in cima al pannello, tre schede affiancate con nome e dettaglio
  ("PDF · 200 dpi"); la scheda che corrisponde alle impostazioni correnti ha il contorno azzurro, se
  si cambia qualcosa a mano nessuna è evidenziata. Suggerimento per scheda con la scorciatoia
  (Ctrl+1/2/3); nomi troppo lunghi per la scheda vanno accorciati nella traduzione, non troncati.
- **Compressione** nella sezione File, sotto il formato: selettore Massima / Equilibrata / Compatta solo
  per JPEG e PDF a colori o in grigi; negli altri casi al suo posto una nota (senza perdita, oppure
  compressione dei fax per il PDF in bianco e nero).
- **Sezioni a tendina** (`ui.Collapsible`): Regolazioni e Correzione righe, chiuse all'avvio. Il titolo
  resta allineato agli altri titoli del pannello, la freccia sta in fondo a destra (a destra se chiusa,
  in giù se aperta); intestazione intera cliccabile, freccia raggiungibile da tastiera, azzurro al
  passaggio. A sezione chiusa un promemoria a destra dice lo stato: "Modificate" (giallo) se un
  cursore non è a zero, "Attiva" (verde) o "Spenta" per la correzione righe. Aperta o chiusa resta
  com'era anche al cambio di lingua, ma a ogni avvio si riparte chiuse.
- **Correzione righe**: accanto al titolo, visibile anche a tendina chiusa, un pulsante tondo "i"
  (`ui.InfoButton`, si accende d'azzurro al passaggio) apre una finestra scura con un disegno
  senza / con correzione, quattro risposte brevi (da dove vengono le righe, cosa fa, quando calibrare,
  cosa non fa), lo stato della calibrazione e "Calibra adesso". Dentro la tendina: selettore Spenta /
  Attiva, una riga di nota a tutta larghezza (data della calibrazione e righe evidenti, oppure cosa
  serve: calibrazione, numpy; o che in bianco e nero non si applica) e sotto il link "Calibra...". Attiva senza calibrazione propone di calibrare; la calibrazione
  chiede conferma con le istruzioni (vetro vuoto, coperchio chiuso) e usa lo stato e l'avanzamento
  normali, con Annulla al solito posto.
- **Link testuali** per azioni secondarie (Cambia, Apri, Altre, Calibra, registro, Liberapay, GitHub).
- Ogni controllo ha hover, pressione, disattivato e anello di focus (`#5ea2ff`).
- Registro in una finestra separata: è diagnostica, non occupa il pannello.
- Barra del titolo scura tramite DWM su Windows 10 e 11.

## Layout

Barra superiore 52 px: marchio (icona 32 px, "Scanner Link Pro" e sotto "SCSI/USB to Scanner" in
grigio piccolo; il sottotitolo non si traduce), stato (pallino + testo), ultima scansione con
miniatura, Riconnetti.
Centro: vetro con righelli in mm (tacche ogni 10, numeri ogni 50) e barra dei formati d'area.
Destra: pannello di 344 px con Acquisizione, Regolazioni (a tendina), Correzione righe (a tendina),
File; in basso stima, avanzamento, azioni,
link. Tutte le misure passano da `Theme.px()` per la scala di Windows (collaudato al 150%).
