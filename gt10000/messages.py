# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Messaggi del motore: chiave, valori e testo italiano.

Il motore invia all'interfaccia sia il testo italiano (per il registro di chi legge l'output
grezzo) sia la chiave con i valori, che l'interfaccia traduce. Le chiavi e i testi coincidono con
le voci b_* di app/i18n.py: tests/test_i18n.py controlla che restino allineati.
"""

TEMPLATES = {
    'b_wait_adapter': "In attesa dell'adattatore USB-SCSI...",
    'b_adapter_not_visible': 'Adattatore Logitec USB-SCSI non visibile da Linux',
    'b_adapter_found': 'Adattatore trovato, cerco lo scanner sul bus SCSI...',
    'b_scsi_device': 'ID SCSI {id}: {device}',
    'b_no_scanner': 'Nessuno scanner Epson trovato sul bus SCSI (scanner acceso? cavo collegato?)',
    'b_no_data': 'Lo scanner non ha inviato dati',
    'b_nak_params': 'Lo scanner rifiuta i parametri di {cmd} (NAK)',
    'b_nak': 'Lo scanner rifiuta {cmd} (NAK)',
    'b_unexpected_params': 'Risposta inattesa a i parametri di {cmd}: {code}',
    'b_unexpected': 'Risposta inattesa a {cmd}: {code}',
    'b_esc_unsupported': 'Comando ESC {cmd} non supportato',
    'b_expected_stx': 'Atteso STX, ricevuto {code}',
    'b_warming': 'Riscaldamento lampada in corso...',
    'b_lamp_timeout': 'La lampada non si è riscaldata in tempo',
    'b_res_unsupported': 'Risoluzione {dpi} non supportata',
    'b_scan_start': 'Scansione {mode} {dpi} dpi, {w}x{h} punti ({bpl} byte/riga)',
    'b_start_rejected': "Lo scanner rifiuta l'avvio della scansione",
    'b_bad_block': 'Blocco dati non valido (atteso STX, ricevuto {code})',
    'b_fatal': 'Errore fatale dello scanner (stato {code})',
    'b_busy_other': "Scanner occupato su un'altra interfaccia",
    'b_adapter_not_found': 'Adattatore Logitec USB-SCSI (0789:00C0) non trovato',
    'b_status_timeout': 'Timeout in attesa dello stato SCSI ({st})',
    'b_no_answer': "Nessuna risposta dall'ID {id} al comando {cmd} ({err})",
    'b_check_condition': 'CHECK CONDITION sul comando {cmd}, sense {sense}',
    'b_cmd_rejected': 'Comando {cmd} rifiutato, stato {st}',
    'b_usb_error': 'Errore USB durante il comando {cmd}: {err}',
    'b_no_device': "Nessun dispositivo SCSI all'ID {id}",
    'b_adapter_error': 'Errore adattatore 0x{code} (comando {cmd}, stato {st})',
    'b_scsi_status': 'Stato SCSI 0x{code} sul comando {cmd} (stato {st})',
    'b_unknown_cmd': 'Comando sconosciuto: {cmd}',
    'b_level_unsupported': 'Scanner con protocollo ESC/I livello {level}: non supportato (servono i livelli da B4 a B8)',
    'b_color_level': 'A colori questo scanner (livello {level}) non è supportato: usa Grigi o Bianco e nero',
}


def render(key, **args):
    return TEMPLATES[key].format(**{k: str(v) for k, v in args.items()})


class Note:
    """Messaggio informativo del motore (registro, stato)."""

    def __init__(self, key, **args):
        self.key = key
        self.args = {k: str(v) for k, v in args.items()}

    def __str__(self):
        return render(self.key, **self.args)

    def payload(self):
        return {"message": str(self), "key": self.key, "args": self.args}


class KeyedError(IOError):
    """Errore con chiave e valori, oltre al testo italiano."""

    def __init__(self, key, **args):
        self.key = key
        self.msg_args = {k: str(v) for k, v in args.items()}
        super().__init__(render(key, **self.msg_args))

    def payload(self):
        return {"message": str(self), "key": self.key, "args": self.msg_args}


def payload(item):
    """Dati da inviare all'interfaccia per un messaggio, con o senza chiave."""
    if hasattr(item, "payload"):
        return item.payload()
    return {"message": str(item)}
