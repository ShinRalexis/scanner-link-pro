# Product

<!-- impeccable:product-schema 1 -->

## Platform

Desktop Windows 11 (Tkinter + Pillow, interfaccia nativa), non web.

## Users

Primario: l'autore (MetaDarko / ShinRalexis), che usa uno scanner Epson GT-10000+ per digitalizzare illustrazioni, fino al formato A3 e ad alta risoluzione. Uso secondario: documenti.
Secondario: chi troverà il progetto su GitHub, proprietari di vecchi scanner SCSI Epson collegati con un adattatore Logitec LUB-SC / LUB-MSC.

## Product Purpose

Far funzionare su Windows 11 uno scanner SCSI di fine anni '90 attraverso un adattatore USB-SCSI che nessun sistema supporta più, e salvare scansioni fedeli nei Documenti. Successo: un'illustrazione A3 acquisita a 600 dpi senza errori, con un flusso semplice (anteprima, area, scansione).

## Positioning

Il driver dell'adattatore Logitec è stato ricostruito dal driver originale per Windows XP e gira in spazio utente dentro un Linux minimale dedicato (WSL); nessun altro software fa funzionare questa combinazione.

## Operating Context

Scrivania di casa, schermo 2560 x 1600 al 150%. Scansioni lunghe (un A3 a 600 dpi circa 6-7 minuti, limite USB 1.1): l'utente avvia e aspetta, guardando l'avanzamento.

## Capabilities and Constraints

- Modalità colore, grigi, bianco e nero; 50-2400 dpi (ottica misurata: 600 dpi; oltre è in gran parte interpolata).
- Vetro 297 x 432 mm; anteprima a 50 dpi in circa 9 s.
- Formati: JPEG, PNG, TIFF, PDF, con dpi nei metadati. Cartella predefinita `Documenti\Scansioni GT-10000`.
- Lato Windows solo Tkinter, Pillow e numpy (correzione righe): niente web, niente librerie grafiche esterne.
- Interfaccia in 9 lingue. Pubblicato su GitHub: nessun percorso personale o dato privato nel codice.

## Brand Commitments

Link fissi a <https://liberapay.com/MetaDarko> e <https://github.com/ShinRalexis/scanner-link-pro> nell'interfaccia.
Stile visivo scelto dall'autore (2026-09-29): standard pulito, tema scuro neutro sul modello di Lightroom e dell'app Foto di Windows 11; vedi DESIGN.md.

## Evidence on Hand

Foto dell'hardware reale, scansioni di prova, misura della risoluzione ottica (2026-09-29). Nessuna testimonianza o dato d'uso di terzi.

## Product Principles

1. L'illustrazione è la protagonista: l'interfaccia le cede lo spazio.
2. Fedeltà prima della velocità: i valori predefiniti puntano alla qualità reale (600 dpi ottici).
3. Onestà sullo stato: l'hardware è vecchio e lento, l'interfaccia dice sempre cosa sta facendo e quanto manca.
