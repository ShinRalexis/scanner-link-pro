# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Traduzioni dell'interfaccia. L'italiano è la lingua di riferimento.

Ogni chiave ha le traduzioni nell'ordine di LANGUAGES. I messaggi del motore Linux arrivano
in italiano: from_backend() li riconosce con i modelli b_* e li traduce; un messaggio non
riconosciuto resta com'è.
"""

import re

LANGUAGES = [
    ("it", "Italiano"), ("en", "English"), ("es", "Español"), ("de", "Deutsch"), ("fr", "Français"),
    ("ja", "日本語"), ("ko", "한국어"), ("zh", "中文"), ("ru", "Русский"),
]
CODES = [c for c, _ in LANGUAGES]
DECIMAL_COMMA = {"it", "es", "de", "fr", "ru"}

#            it, en, es, de, fr, ja, ko, zh, ru
STRINGS = {
    # sezioni ed etichette
    "sec_acquisition": ("Acquisizione", "Acquisition", "Adquisición", "Erfassung", "Acquisition",
                        "スキャン設定", "스캔 설정", "扫描设置", "Сканирование"),
    "lbl_mode": ("Modalità", "Mode", "Modo", "Modus", "Mode", "モード", "모드", "模式", "Режим"),
    "lbl_resolution": ("Risoluzione", "Resolution", "Resolución", "Auflösung", "Résolution",
                       "解像度", "해상도", "分辨率", "Разрешение"),
    "sec_adjust": ("Regolazioni", "Adjustments", "Ajustes", "Anpassungen", "Réglages",
                   "調整", "조정", "调整", "Настройки"),
    "lbl_brightness": ("Luminosità", "Brightness", "Brillo", "Helligkeit", "Luminosité",
                       "明るさ", "밝기", "亮度", "Яркость"),
    "lbl_sharpness": ("Nitidezza", "Sharpness", "Nitidez", "Schärfe", "Netteté",
                      "シャープネス", "선명도", "锐度", "Резкость"),
    "sec_file": ("File", "File", "Archivo", "Datei", "Fichier", "ファイル", "파일", "文件", "Файл"),
    "lbl_name": ("Nome", "Name", "Nombre", "Name", "Nom", "ファイル名", "파일 이름", "文件名", "Имя"),
    "lbl_folder": ("Cartella di salvataggio", "Save folder", "Carpeta de destino", "Speicherordner",
                   "Dossier d'enregistrement", "保存先フォルダー", "저장 폴더", "保存文件夹", "Папка для сохранения"),
    "lbl_language": ("Lingua", "Language", "Idioma", "Sprache", "Langue", "言語", "언어", "语言", "Язык"),
    # pulsanti e link
    "btn_change_folder": ("Cambia cartella", "Change folder", "Cambiar carpeta", "Ordner ändern",
                          "Changer de dossier", "フォルダーを変更", "폴더 변경", "更改文件夹", "Сменить папку"),
    "btn_open_folder": ("Apri cartella", "Open folder", "Abrir carpeta", "Ordner öffnen", "Ouvrir le dossier",
                        "フォルダーを開く", "폴더 열기", "打开文件夹", "Открыть папку"),
    "btn_reconnect": ("Riconnetti", "Reconnect", "Reconectar", "Neu verbinden", "Reconnecter",
                      "再接続", "다시 연결", "重新连接", "Переподключить"),
    "btn_preview": ("Anteprima", "Preview", "Vista previa", "Vorschau", "Aperçu",
                    "プレビュー", "미리 보기", "预览", "Просмотр"),
    "btn_scan": ("Scansiona", "Scan", "Escanear", "Scannen", "Numériser", "スキャン", "스캔", "扫描", "Сканировать"),
    "btn_cancel": ("Annulla", "Cancel", "Cancelar", "Abbrechen", "Annuler", "キャンセル", "취소", "取消", "Отмена"),
    "log_show": ("Mostra registro", "Show log", "Mostrar registro", "Protokoll anzeigen", "Afficher le journal",
                 "ログを表示", "로그 보기", "显示日志", "Показать журнал"),
    "log_hide": ("Nascondi registro", "Hide log", "Ocultar registro", "Protokoll ausblenden", "Masquer le journal",
                 "ログを隠す", "로그 숨기기", "隐藏日志", "Скрыть журнал"),
    "log_window_title": ("Registro", "Log", "Registro", "Protokoll", "Journal", "ログ", "로그", "日志", "Журнал"),
    "dpi_more": ("Altre...", "More...", "Más...", "Weitere...", "Autres...", "その他...", "기타...", "更多...",
                 "Другие..."),
    "dpi_more_value": ("Altre: {dpi} dpi", "Other: {dpi} dpi", "Otra: {dpi} dpi", "Andere: {dpi} dpi",
                       "Autre : {dpi} dpi", "その他: {dpi} dpi", "기타: {dpi} dpi", "其他：{dpi} dpi",
                       "Другое: {dpi} dpi"),
    # modalità e formati d'area
    "mode_color": ("Colore", "Color", "Color", "Farbe", "Couleur", "カラー", "컬러", "彩色", "Цвет"),
    "mode_gray": ("Grigi", "Grayscale", "Grises", "Graustufen", "Gris", "グレー", "회색조", "灰度", "Серый"),
    "mode_lineart": ("Bianco e nero", "Black & white", "Blanco y negro", "Schwarzweiß", "Noir et blanc",
                     "白黒", "흑백", "黑白", "Ч/б"),
    "preset_glass": ("Vetro", "Glass", "Cristal", "Glas", "Vitre", "全面", "전체", "全幅", "Стекло"),
    "preset_a4_land": ("A4 orizz.", "A4 land.", "A4 apais.", "A4 quer", "A4 pays.", "A4横", "A4 가로", "A4横向",
                       "A4 альб."),
    # risoluzione
    "dpi_optical": ("ottica", "optical", "óptica", "optisch", "optique", "光学", "광학", "光学", "оптическое"),
    "dpi_interpolated": ("interpolata", "interpolated", "interpolada", "interpoliert", "interpolée",
                         "補間", "보간", "插值", "интерполированное"),
    "dpi_note_optical": (
        "{dpi} dpi è la risoluzione ottica dello scanner.",
        "{dpi} dpi is the scanner's optical resolution.",
        "{dpi} dpi es la resolución óptica del escáner.",
        "{dpi} dpi ist die optische Auflösung des Scanners.",
        "{dpi} dpi est la résolution optique du scanner.",
        "{dpi} dpi がスキャナーの光学解像度です。",
        "{dpi} dpi가 스캐너의 광학 해상도입니다.",
        "{dpi} dpi 是扫描仪的光学分辨率。",
        "{dpi} dpi: оптическое разрешение сканера."),
    "dpi_note_over": (
        "Oltre {dpi} dpi il dettaglio in più è in gran parte interpolato: dati e tempi crescono molto.",
        "Above {dpi} dpi the extra detail is mostly interpolated: data size and time grow a lot.",
        "Por encima de {dpi} dpi el detalle extra es en gran parte interpolado: datos y tiempos crecen mucho.",
        "Über {dpi} dpi ist das zusätzliche Detail größtenteils interpoliert: Datenmenge und Dauer steigen stark.",
        "Au-delà de {dpi} dpi, le détail supplémentaire est surtout interpolé : volume et durée augmentent "
        "fortement.",
        "{dpi} dpi を超える分の細部はほぼ補間です。データ量と時間が大きく増えます。",
        "{dpi} dpi를 넘는 추가 디테일은 대부분 보간입니다. 데이터와 시간이 크게 늘어납니다.",
        "超过 {dpi} dpi 的额外细节大多是插值得到的，数据量和时间会大幅增加。",
        "Выше {dpi} dpi дополнительная детализация в основном интерполирована: объём данных и время сильно "
        "растут."),
    # vetro e area
    "glass_empty_title": ("Il vetro è vuoto", "The glass is empty", "El cristal está vacío", "Das Glas ist leer",
                          "La vitre est vide", "ガラス面は空です", "유리면이 비어 있습니다", "玻璃面上没有内容",
                          "Стекло пустое"),
    "glass_empty_hint": (
        "Premi Anteprima per vedere cosa c'è sullo scanner,\npoi trascina per scegliere l'area.",
        "Press Preview to see what is on the scanner,\nthen drag to choose the area.",
        "Pulsa Vista previa para ver qué hay en el escáner,\ny arrastra para elegir el área.",
        "Klicke auf Vorschau, um zu sehen, was auf dem Scanner liegt,\nund ziehe dann den Bereich auf.",
        "Cliquez sur Aperçu pour voir ce qui est sur le scanner,\npuis faites glisser pour choisir la zone.",
        "プレビューを押してスキャナー上の内容を確認し、\nドラッグして範囲を選んでください。",
        "미리 보기를 눌러 스캐너 위의 내용을 확인한 뒤\n드래그해서 영역을 고르세요.",
        "点击“预览”查看扫描仪上的内容，\n然后拖动选择区域。",
        "Нажмите «Просмотр», чтобы увидеть, что лежит на сканере,\nзатем выделите область мышью."),
    "area_label": ("{w} x {h} mm   da {x}, {y} mm", "{w} x {h} mm   from {x}, {y} mm",
                   "{w} x {h} mm   desde {x}, {y} mm", "{w} x {h} mm   ab {x}, {y} mm",
                   "{w} x {h} mm   depuis {x}, {y} mm", "{w} x {h} mm   位置 {x}, {y} mm",
                   "{w} x {h} mm   위치 {x}, {y} mm", "{w} x {h} mm   起点 {x}, {y} mm",
                   "{w} x {h} мм   от {x}, {y} мм"),
    # stima e avanzamento
    "summary": ("{w} x {h} px   ·   {size}   ·   circa {time}", "{w} x {h} px   ·   {size}   ·   about {time}",
                "{w} x {h} px   ·   {size}   ·   aprox. {time}", "{w} x {h} px   ·   {size}   ·   ca. {time}",
                "{w} x {h} px   ·   {size}   ·   environ {time}", "{w} x {h} px   ·   {size}   ·   約 {time}",
                "{w} x {h} px   ·   {size}   ·   약 {time}", "{w} x {h} px   ·   {size}   ·   约 {time}",
                "{w} x {h} px   ·   {size}   ·   около {time}"),
    "progress_running": (
        "{pct}%   ·   {speed}/s   ·   mancano circa {time}", "{pct}%   ·   {speed}/s   ·   about {time} left",
        "{pct}%   ·   {speed}/s   ·   quedan aprox. {time}", "{pct}%   ·   {speed}/s   ·   noch ca. {time}",
        "{pct}%   ·   {speed}/s   ·   environ {time} restant", "{pct}%   ·   {speed}/s   ·   残り約 {time}",
        "{pct}%   ·   {speed}/s   ·   약 {time} 남음", "{pct}%   ·   {speed}/s   ·   剩余约 {time}",
        "{pct}%   ·   {speed}/s   ·   осталось около {time}"),
    "progress_preparing": ("Preparazione e riscaldamento della lampada...", "Preparing and warming up the lamp...",
                           "Preparando y calentando la lámpara...", "Vorbereitung, die Lampe wärmt auf...",
                           "Préparation et préchauffage de la lampe...", "準備中、ランプをウォームアップしています...",
                           "준비 중, 램프 예열 중...", "正在准备并预热灯管...", "Подготовка и прогрев лампы..."),
    "progress_cancelling": ("Annullamento...", "Cancelling...", "Cancelando...", "Wird abgebrochen...",
                            "Annulation...", "キャンセル中...", "취소 중...", "正在取消...", "Отмена..."),
    "progress_saving": ("Salvataggio del file...", "Saving the file...", "Guardando el archivo...",
                        "Datei wird gespeichert...", "Enregistrement du fichier...", "ファイルを保存中...",
                        "파일 저장 중...", "正在保存文件...", "Сохранение файла..."),
    "preview_done": ("Anteprima completata in {time}", "Preview done in {time}", "Vista previa lista en {time}",
                     "Vorschau fertig in {time}", "Aperçu terminé en {time}", "プレビュー完了（{time}）",
                     "미리 보기 완료 ({time})", "预览完成，用时 {time}", "Просмотр готов за {time}"),
    "scan_done": ("Scansione completata in {time}", "Scan completed in {time}", "Escaneo completado en {time}",
                  "Scan abgeschlossen in {time}", "Numérisation terminée en {time}", "スキャン完了（{time}）",
                  "스캔 완료 ({time})", "扫描完成，用时 {time}", "Сканирование завершено за {time}"),
    "scan_cancelled": ("Scansione annullata", "Scan cancelled", "Escaneo cancelado", "Scan abgebrochen",
                       "Numérisation annulée", "スキャンをキャンセルしました", "스캔이 취소되었습니다", "扫描已取消",
                       "Сканирование отменено"),
    "scan_interrupted": ("Scansione interrotta", "Scan interrupted", "Escaneo interrumpido", "Scan unterbrochen",
                         "Numérisation interrompue", "スキャンが中断されました", "스캔이 중단되었습니다", "扫描已中断",
                         "Сканирование прервано"),
    "progress_scan_error": (
        "Errore durante la scansione: riprova, o premi Riconnetti se si ripete",
        "Error during the scan: try again, or press Reconnect if it happens again",
        "Error durante el escaneo: vuelve a intentarlo o pulsa Reconectar si se repite",
        "Fehler beim Scannen: erneut versuchen oder bei Wiederholung Neu verbinden drücken",
        "Erreur pendant la numérisation : réessayez, ou cliquez sur Reconnecter si elle se répète",
        "スキャン中にエラーが発生しました。もう一度試すか、繰り返す場合は「再接続」を押してください",
        "스캔 중 오류: 다시 시도하거나, 반복되면 다시 연결을 누르세요",
        "扫描时出错：请重试，若反复出现请点击“重新连接”",
        "Ошибка при сканировании: повторите или нажмите «Переподключить», если она повторится"),
    "progress_save_error": ("Errore di salvataggio", "Save error", "Error al guardar", "Fehler beim Speichern",
                            "Erreur d'enregistrement", "保存エラー", "저장 오류", "保存错误", "Ошибка сохранения"),
    # stato
    "status_starting": ("Avvio...", "Starting...", "Iniciando...", "Wird gestartet...", "Démarrage...",
                        "起動中...", "시작 중...", "正在启动...", "Запуск..."),
    "status_linux_starting": ("Avvio del sistema Linux interno...", "Starting the built-in Linux system...",
                              "Iniciando el sistema Linux interno...", "Internes Linux-System wird gestartet...",
                              "Démarrage du système Linux intégré...", "内蔵 Linux を起動中...",
                              "내장 리눅스 시작 중...", "正在启动内置 Linux 系统...",
                              "Запуск встроенной системы Linux..."),
    "status_previewing": ("Anteprima in corso...", "Preview in progress...", "Vista previa en curso...",
                          "Vorschau läuft...", "Aperçu en cours...", "プレビュー中...", "미리 보기 중...",
                          "正在预览...", "Идёт просмотр..."),
    "status_scanning": ("Scansione in corso...", "Scanning...", "Escaneando...", "Scan läuft...",
                        "Numérisation en cours...", "スキャン中...", "스캔 중...", "正在扫描...",
                        "Идёт сканирование..."),
    "ready": ("{vendor} {model} pronto  ·  firmware {fw}  ·  ID SCSI {id}",
              "{vendor} {model} ready  ·  firmware {fw}  ·  SCSI ID {id}",
              "{vendor} {model} listo  ·  firmware {fw}  ·  ID SCSI {id}",
              "{vendor} {model} bereit  ·  Firmware {fw}  ·  SCSI-ID {id}",
              "{vendor} {model} prêt  ·  firmware {fw}  ·  ID SCSI {id}",
              "{vendor} {model} 準備完了  ·  ファームウェア {fw}  ·  SCSI ID {id}",
              "{vendor} {model} 준비됨  ·  펌웨어 {fw}  ·  SCSI ID {id}",
              "{vendor} {model} 已就绪  ·  固件 {fw}  ·  SCSI ID {id}",
              "{vendor} {model} готов  ·  прошивка {fw}  ·  SCSI ID {id}"),
    "status_need_auth": ("Autorizzazione richiesta per condividere l'adattatore con Linux...",
                         "Authorization needed to share the adapter with Linux...",
                         "Se necesita autorización para compartir el adaptador con Linux...",
                         "Autorisierung nötig, um den Adapter für Linux freizugeben...",
                         "Autorisation requise pour partager l'adaptateur avec Linux...",
                         "アダプターを Linux と共有するための許可が必要です...",
                         "어댑터를 리눅스와 공유하려면 권한이 필요합니다...",
                         "需要授权才能与 Linux 共享适配器...",
                         "Нужно разрешение, чтобы передать адаптер в Linux..."),
    "status_attaching": ("Collegamento dell'adattatore al sistema Linux...", "Attaching the adapter to Linux...",
                         "Conectando el adaptador al sistema Linux...", "Adapter wird mit Linux verbunden...",
                         "Connexion de l'adaptateur au système Linux...", "アダプターを Linux に接続中...",
                         "어댑터를 리눅스에 연결하는 중...", "正在将适配器连接到 Linux 系统...",
                         "Подключение адаптера к Linux..."),
    "status_engine_closed": ("Motore Linux chiuso: premi Riconnetti.", "Linux engine stopped: press Reconnect.",
                             "Motor Linux cerrado: pulsa Reconectar.", "Linux-Engine beendet: Neu verbinden drücken.",
                             "Moteur Linux arrêté : cliquez sur Reconnecter.",
                             "Linux エンジンが停止しました。「再接続」を押してください。",
                             "리눅스 엔진 종료됨: 다시 연결을 누르세요.", "Linux 引擎已关闭：请点击“重新连接”。",
                             "Движок Linux остановлен: нажмите «Переподключить»."),
    "error_generic": ("Errore", "Error", "Error", "Fehler", "Erreur", "エラー", "오류", "错误", "Ошибка"),
    # errori di avvio
    "fatal_no_distro": (
        'Manca la distribuzione Linux "{name}". Reinstalla Scanner Link Pro (dai sorgenti: esegui installa.ps1).',
        'The Linux distribution "{name}" is missing. Reinstall Scanner Link Pro (from source: run installa.ps1).',
        'Falta la distribución Linux "{name}". Reinstala Scanner Link Pro (desde el código fuente: ejecuta '
        'installa.ps1).',
        'Die Linux-Distribution "{name}" fehlt. Scanner Link Pro neu installieren (aus dem Quellcode: installa.ps1 '
        'ausführen).',
        'La distribution Linux « {name} » est absente. Réinstallez Scanner Link Pro (depuis les sources : '
        'exécutez installa.ps1).',
        'Linux ディストリビューション「{name}」がありません。Scanner Link Pro を再インストールしてください'
        '（ソースから使う場合は installa.ps1 を実行）。',
        'Linux 배포판 "{name}"이(가) 없습니다. Scanner Link Pro를 다시 설치하세요(소스에서 사용하는 경우 '
        'installa.ps1 실행).',
        '缺少 Linux 发行版“{name}”。请重新安装 Scanner Link Pro（从源代码使用时：运行 installa.ps1）。',
        'Отсутствует дистрибутив Linux «{name}». Переустановите Scanner Link Pro (из исходного кода: '
        'запустите installa.ps1).'),
    "fatal_no_usbipd": (
        "Manca usbipd-win. Reinstalla Scanner Link Pro (dai sorgenti: esegui installa.ps1).",
        "usbipd-win is missing. Reinstall Scanner Link Pro (from source: run installa.ps1).",
        "Falta usbipd-win. Reinstala Scanner Link Pro (desde el código fuente: ejecuta installa.ps1).",
        "usbipd-win fehlt. Scanner Link Pro neu installieren (aus dem Quellcode: installa.ps1 ausführen).",
        "usbipd-win est absent. Réinstallez Scanner Link Pro (depuis les sources : exécutez installa.ps1).",
        "usbipd-win がありません。Scanner Link Pro を再インストールしてください（ソースから使う場合は installa.ps1 を実行）。",
        "usbipd-win이 없습니다. Scanner Link Pro를 다시 설치하세요(소스에서 사용하는 경우 installa.ps1 실행).",
        "缺少 usbipd-win。请重新安装 Scanner Link Pro（从源代码使用时：运行 installa.ps1）。",
        "Отсутствует usbipd-win. Переустановите Scanner Link Pro (из исходного кода: запустите installa.ps1)."),
    "fatal_no_wsl": (
        'WSL (il sottosistema Linux di Windows) non è installato. Reinstalla Scanner Link Pro oppure esegui '
        '"wsl --install" da amministratore e riavvia.',
        'WSL (the Windows Subsystem for Linux) is not installed. Reinstall Scanner Link Pro or run '
        '"wsl --install" as administrator and restart.',
        'WSL (el subsistema de Windows para Linux) no está instalado. Reinstala Scanner Link Pro o ejecuta '
        '"wsl --install" como administrador y reinicia.',
        'WSL (das Windows-Subsystem für Linux) ist nicht installiert. Scanner Link Pro neu installieren oder '
        '"wsl --install" als Administrator ausführen und neu starten.',
        "WSL (le sous-système Windows pour Linux) n'est pas installé. Réinstallez Scanner Link Pro ou exécutez "
        "« wsl --install » en administrateur, puis redémarrez.",
        "WSL（Windows Subsystem for Linux）がインストールされていません。Scanner Link Pro を再インストールするか、"
        "管理者として「wsl --install」を実行して再起動してください。",
        'WSL(Linux용 Windows 하위 시스템)이 설치되어 있지 않습니다. Scanner Link Pro를 다시 설치하거나 관리자 '
        '권한으로 "wsl --install"을 실행한 뒤 다시 시작하세요.',
        "未安装 WSL（适用于 Linux 的 Windows 子系统）。请重新安装 Scanner Link Pro，或以管理员身份运行"
        "“wsl --install”并重启。",
        "WSL (подсистема Windows для Linux) не установлена. Переустановите Scanner Link Pro или выполните "
        "«wsl --install» от имени администратора и перезагрузите компьютер."),
    "status_adapter_reset": (
        "L'adattatore non risponde: lo ricollego e riprovo...",
        "The adapter is not responding: reconnecting it and trying again...",
        "El adaptador no responde: lo vuelvo a conectar y lo intento de nuevo...",
        "Der Adapter antwortet nicht: wird neu verbunden, neuer Versuch...",
        "L'adaptateur ne répond pas : reconnexion et nouvel essai...",
        "アダプターが応答しません。接続し直して再試行しています...",
        "어댑터가 응답하지 않습니다. 다시 연결하고 재시도하는 중...",
        "适配器无响应：正在重新连接并重试...",
        "Адаптер не отвечает: переподключаю и пробую снова..."),
    "fatal_virtualization": (
        "WSL non riesce ad avviare la sua macchina virtuale: probabilmente la virtualizzazione è spenta nel "
        "BIOS/UEFI (Intel VT-x o AMD-V/SVM). Attivala, riavvia il computer e riapri il programma.",
        "WSL cannot start its virtual machine: virtualization is probably turned off in the BIOS/UEFI "
        "(Intel VT-x or AMD-V/SVM). Turn it on, restart the computer and open the program again.",
        "WSL no puede iniciar su máquina virtual: probablemente la virtualización está desactivada en la "
        "BIOS/UEFI (Intel VT-x o AMD-V/SVM). Actívala, reinicia el equipo y vuelve a abrir el programa.",
        "WSL kann seine virtuelle Maschine nicht starten: Wahrscheinlich ist die Virtualisierung im BIOS/UEFI "
        "ausgeschaltet (Intel VT-x oder AMD-V/SVM). Einschalten, den Computer neu starten und das Programm "
        "erneut öffnen.",
        "WSL ne peut pas démarrer sa machine virtuelle : la virtualisation est probablement désactivée dans "
        "le BIOS/UEFI (Intel VT-x ou AMD-V/SVM). Activez-la, redémarrez l'ordinateur et rouvrez le programme.",
        "WSL が仮想マシンを起動できません。BIOS/UEFI で仮想化（Intel VT-x または AMD-V/SVM）が無効になって"
        "いる可能性があります。有効にして PC を再起動し、プログラムを開き直してください。",
        "WSL이 가상 머신을 시작할 수 없습니다. BIOS/UEFI에서 가상화(Intel VT-x 또는 AMD-V/SVM)가 꺼져 있을 "
        "가능성이 큽니다. 켜고 컴퓨터를 다시 시작한 뒤 프로그램을 다시 여세요.",
        "WSL 无法启动其虚拟机：很可能在 BIOS/UEFI 中关闭了虚拟化（Intel VT-x 或 AMD-V/SVM）。请开启后"
        "重启电脑，再重新打开程序。",
        "WSL не может запустить виртуальную машину: вероятно, в BIOS/UEFI отключена виртуализация "
        "(Intel VT-x или AMD-V/SVM). Включите ее, перезагрузите компьютер и снова откройте программу."),
    "fatal_linux_import": (
        "Non sono riuscito a preparare il Linux interno: i dettagli sono nel registro.",
        "The built-in Linux could not be set up: details are in the log.",
        "No se pudo preparar el Linux interno: los detalles están en el registro.",
        "Das interne Linux konnte nicht eingerichtet werden: Details im Protokoll.",
        "Impossible de préparer le Linux intégré : les détails sont dans le journal.",
        "内蔵 Linux を準備できませんでした。詳細はログにあります。",
        "내장 Linux를 준비하지 못했습니다. 자세한 내용은 로그에 있습니다.",
        "无法准备内置 Linux：详情见日志。",
        "Не удалось подготовить встроенный Linux: подробности в журнале."),
    "status_preparing_linux": (
        "Preparo il Linux interno (solo la prima volta, circa un minuto)...",
        "Setting up the built-in Linux (first time only, about one minute)...",
        "Preparando el Linux interno (solo la primera vez, alrededor de un minuto)...",
        "Internes Linux wird eingerichtet (nur beim ersten Mal, etwa eine Minute)...",
        "Préparation du Linux intégré (la première fois seulement, environ une minute)...",
        "内蔵 Linux を準備しています（初回のみ、約1分）...",
        "내장 Linux를 준비하는 중(처음 한 번만, 약 1분)...",
        "正在准备内置 Linux（仅首次，约一分钟）...",
        "Подготовка встроенного Linux (только в первый раз, около минуты)..."),
    "log_linux_imported": ("Linux interno pronto in {path}", "Built-in Linux ready in {path}",
                           "Linux interno listo en {path}", "Internes Linux bereit in {path}",
                           "Linux intégré prêt dans {path}", "内蔵 Linux の準備完了: {path}",
                           "내장 Linux 준비 완료: {path}", "内置 Linux 已就绪：{path}",
                           "Встроенный Linux готов: {path}"),
    "fatal_adapter_absent": (
        "Adattatore USB-SCSI non collegato: collegalo e premi Riconnetti.",
        "USB-SCSI adapter not connected: plug it in and press Reconnect.",
        "Adaptador USB-SCSI no conectado: conéctalo y pulsa Reconectar.",
        "USB-SCSI-Adapter nicht angeschlossen: anschließen und Neu verbinden drücken.",
        "Adaptateur USB-SCSI non branché : branchez-le puis cliquez sur Reconnecter.",
        "USB-SCSI アダプターが接続されていません。接続して「再接続」を押してください。",
        "USB-SCSI 어댑터가 연결되지 않았습니다. 연결한 뒤 다시 연결을 누르세요.",
        "USB-SCSI 适配器未连接：请插上后点击“重新连接”。",
        "Адаптер USB-SCSI не подключён: подключите его и нажмите «Переподключить»."),
    "fatal_auth_denied": ("Condivisione dell'adattatore non autorizzata.", "Adapter sharing was not authorized.",
                          "No se autorizó compartir el adaptador.", "Freigabe des Adapters nicht erlaubt.",
                          "Partage de l'adaptateur non autorisé.", "アダプターの共有が許可されませんでした。",
                          "어댑터 공유가 허용되지 않았습니다.", "未授权共享适配器。", "Передача адаптера не разрешена."),
    "fatal_attach_failed": (
        "Non riesco a collegare l'adattatore a Linux (usbipd attach).",
        "Could not attach the adapter to Linux (usbipd attach).",
        "No se pudo conectar el adaptador a Linux (usbipd attach).",
        "Adapter konnte nicht mit Linux verbunden werden (usbipd attach).",
        "Impossible de connecter l'adaptateur à Linux (usbipd attach).",
        "アダプターを Linux に接続できません (usbipd attach)。",
        "어댑터를 리눅스에 연결할 수 없습니다 (usbipd attach).",
        "无法将适配器连接到 Linux（usbipd attach）。",
        "Не удалось подключить адаптер к Linux (usbipd attach)."),
    "fatal_startup_error": ("Errore di avvio: {error}", "Startup error: {error}", "Error de inicio: {error}",
                            "Startfehler: {error}", "Erreur de démarrage : {error}", "起動エラー: {error}",
                            "시작 오류: {error}", "启动错误：{error}", "Ошибка запуска: {error}"),
    # stati dell'adattatore
    "state_absent": ("assente", "not connected", "no conectado", "nicht angeschlossen", "non branché",
                     "未接続", "연결 안 됨", "未连接", "не подключён"),
    "state_not_shared": ("non condiviso", "not shared", "no compartido", "nicht freigegeben", "non partagé",
                         "未共有", "공유 안 됨", "未共享", "не передан"),
    "state_shared": ("condiviso", "shared", "compartido", "freigegeben", "partagé", "共有済み", "공유됨",
                     "已共享", "передан"),
    "state_attached": ("collegato", "attached", "conectado", "verbunden", "connecté", "接続済み", "연결됨",
                       "已连接", "подключён"),
    "state_unknown": ("sconosciuto", "unknown", "desconocido", "unbekannt", "inconnu", "不明", "알 수 없음",
                      "未知", "неизвестно"),
    "state_no_usbipd": ("usbipd mancante", "usbipd missing", "falta usbipd", "usbipd fehlt", "usbipd absent",
                        "usbipd なし", "usbipd 없음", "缺少 usbipd", "нет usbipd"),
    # registro
    "log_adapter_state": ("Adattatore USB-SCSI: {state}", "USB-SCSI adapter: {state}", "Adaptador USB-SCSI: {state}",
                          "USB-SCSI-Adapter: {state}", "Adaptateur USB-SCSI : {state}", "USB-SCSI アダプター: {state}",
                          "USB-SCSI 어댑터: {state}", "USB-SCSI 适配器：{state}", "Адаптер USB-SCSI: {state}"),
    "log_adapter_state_bus": (
        "Adattatore USB-SCSI: {state} (bus {bus})", "USB-SCSI adapter: {state} (bus {bus})",
        "Adaptador USB-SCSI: {state} (bus {bus})", "USB-SCSI-Adapter: {state} (Bus {bus})",
        "Adaptateur USB-SCSI : {state} (bus {bus})", "USB-SCSI アダプター: {state} (バス {bus})",
        "USB-SCSI 어댑터: {state} (버스 {bus})", "USB-SCSI 适配器：{state}（总线 {bus}）",
        "Адаптер USB-SCSI: {state} (шина {bus})"),
    "log_driver_updated": ("Driver aggiornato nel sistema Linux interno", "Driver updated in the built-in Linux system",
                           "Controlador actualizado en el sistema Linux interno",
                           "Treiber im internen Linux-System aktualisiert",
                           "Pilote mis à jour dans le système Linux intégré", "内蔵 Linux のドライバーを更新しました",
                           "내장 리눅스의 드라이버를 업데이트했습니다", "已更新内置 Linux 系统中的驱动",
                           "Драйвер во встроенной системе Linux обновлён"),
    "log_engine_started": ("Motore Linux avviato (Python {version})", "Linux engine started (Python {version})",
                           "Motor Linux iniciado (Python {version})", "Linux-Engine gestartet (Python {version})",
                           "Moteur Linux démarré (Python {version})", "Linux エンジン起動 (Python {version})",
                           "리눅스 엔진 시작됨 (Python {version})", "Linux 引擎已启动（Python {version}）",
                           "Движок Linux запущен (Python {version})"),
    "log_engine_closed": ("Il motore Linux si è chiuso", "The Linux engine has stopped", "El motor Linux se ha cerrado",
                          "Die Linux-Engine wurde beendet", "Le moteur Linux s'est arrêté",
                          "Linux エンジンが終了しました", "리눅스 엔진이 종료되었습니다", "Linux 引擎已关闭",
                          "Движок Linux остановлен"),
    "log_scanner_ready": (
        "Scanner pronto: {vendor} {product}, ESC/I {level}, vetro {w} x {h} mm",
        "Scanner ready: {vendor} {product}, ESC/I {level}, glass {w} x {h} mm",
        "Escáner listo: {vendor} {product}, ESC/I {level}, cristal {w} x {h} mm",
        "Scanner bereit: {vendor} {product}, ESC/I {level}, Glas {w} x {h} mm",
        "Scanner prêt : {vendor} {product}, ESC/I {level}, vitre {w} x {h} mm",
        "スキャナー準備完了: {vendor} {product}, ESC/I {level}, ガラス面 {w} x {h} mm",
        "스캐너 준비됨: {vendor} {product}, ESC/I {level}, 유리면 {w} x {h} mm",
        "扫描仪已就绪：{vendor} {product}，ESC/I {level}，玻璃面 {w} x {h} mm",
        "Сканер готов: {vendor} {product}, ESC/I {level}, стекло {w} x {h} мм"),
    "log_saved": ("Salvato {path} ({w} x {h}, {time})", "Saved {path} ({w} x {h}, {time})",
                  "Guardado {path} ({w} x {h}, {time})", "Gespeichert: {path} ({w} x {h}, {time})",
                  "Enregistré : {path} ({w} x {h}, {time})", "保存しました: {path} ({w} x {h}, {time})",
                  "저장됨: {path} ({w} x {h}, {time})", "已保存：{path}（{w} x {h}，{time}）",
                  "Сохранено: {path} ({w} x {h}, {time})"),
    "log_error": ("Errore: {error}", "Error: {error}", "Error: {error}", "Fehler: {error}", "Erreur : {error}",
                  "エラー: {error}", "오류: {error}", "错误：{error}", "Ошибка: {error}"),
    "log_save_error": ("Errore di salvataggio: {error}", "Save error: {error}", "Error al guardar: {error}",
                       "Fehler beim Speichern: {error}", "Erreur d'enregistrement : {error}", "保存エラー: {error}",
                       "저장 오류: {error}", "保存错误：{error}", "Ошибка сохранения: {error}"),
    "log_language": ("Lingua: {name}", "Language: {name}", "Idioma: {name}", "Sprache: {name}", "Langue : {name}",
                     "言語: {name}", "언어: {name}", "语言：{name}", "Язык: {name}"),
    # ultima scansione
    "last_name": ("Ultima: {name}", "Last: {name}", "Último: {name}", "Zuletzt: {name}", "Dernier : {name}",
                  "前回: {name}", "최근: {name}", "最近：{name}", "Последний: {name}"),
    "last_detail": ("{w} x {h} px  ·  {size}  ·  clic per aprire", "{w} x {h} px  ·  {size}  ·  click to open",
                    "{w} x {h} px  ·  {size}  ·  clic para abrir", "{w} x {h} px  ·  {size}  ·  zum Öffnen klicken",
                    "{w} x {h} px  ·  {size}  ·  cliquer pour ouvrir", "{w} x {h} px  ·  {size}  ·  クリックで開く",
                    "{w} x {h} px  ·  {size}  ·  클릭해서 열기", "{w} x {h} px  ·  {size}  ·  点击打开",
                    "{w} x {h} px  ·  {size}  ·  нажмите, чтобы открыть"),
    # finestre di dialogo
    "dlg_choose_folder": ("Cartella delle scansioni", "Scan folder", "Carpeta de escaneos", "Scan-Ordner",
                          "Dossier des numérisations", "スキャンの保存先", "스캔 폴더", "扫描文件夹", "Папка для сканов"),
    "dlg_save_error": ("Impossibile salvare il file:\n{error}", "Cannot save the file:\n{error}",
                       "No se puede guardar el archivo:\n{error}", "Die Datei kann nicht gespeichert werden:\n{error}",
                       "Impossible d'enregistrer le fichier :\n{error}", "ファイルを保存できません:\n{error}",
                       "파일을 저장할 수 없습니다:\n{error}", "无法保存文件：\n{error}", "Не удалось сохранить файл:\n{error}"),
    "dlg_no_space": (
        "Spazio su disco insufficiente per i dati temporanei: servono {need}, liberi {free}.",
        "Not enough disk space for temporary data: {need} needed, {free} free.",
        "Espacio en disco insuficiente para los datos temporales: se necesitan {need}, libres {free}.",
        "Nicht genug Speicherplatz für temporäre Daten: {need} benötigt, {free} frei.",
        "Espace disque insuffisant pour les données temporaires : {need} nécessaires, {free} libres.",
        "一時データ用のディスク容量が足りません。必要: {need}、空き: {free}。",
        "임시 데이터용 디스크 공간이 부족합니다. 필요: {need}, 여유: {free}.",
        "临时数据所需磁盘空间不足：需要 {need}，可用 {free}。",
        "Недостаточно места на диске для временных данных: нужно {need}, свободно {free}."),
    "dlg_large_scan": (
        "Questa scansione produrrà {size} di dati e durerà circa {time}.\n\nContinuare?",
        "This scan will produce {size} of data and take about {time}.\n\nContinue?",
        "Este escaneo generará {size} de datos y durará aprox. {time}.\n\n¿Continuar?",
        "Dieser Scan erzeugt {size} Daten und dauert ca. {time}.\n\nFortfahren?",
        "Cette numérisation produira {size} de données et durera environ {time}.\n\nContinuer ?",
        "このスキャンは {size} のデータになり、約 {time} かかります。\n\n続けますか？",
        "이 스캔은 {size}의 데이터를 만들고 약 {time} 걸립니다.\n\n계속할까요?",
        "此次扫描将产生 {size} 数据，耗时约 {time}。\n\n是否继续？",
        "Это сканирование даст {size} данных и займёт около {time}.\n\nПродолжить?"),
    "dlg_close_scanning": ("Una scansione è in corso. Chiudere comunque?", "A scan is in progress. Close anyway?",
                           "Hay un escaneo en curso. ¿Cerrar de todos modos?", "Ein Scan läuft. Trotzdem schließen?",
                           "Une numérisation est en cours. Fermer quand même ?", "スキャン中です。終了しますか？",
                           "스캔이 진행 중입니다. 그래도 닫을까요?", "正在扫描。仍要关闭吗？",
                           "Идёт сканирование. Всё равно закрыть?"),
    # tono: gamma (colore e grigi) o soglia (bianco e nero)
    "lbl_gamma": ("Gamma", "Gamma", "Gamma", "Gamma", "Gamma", "ガンマ", "감마", "伽马", "Гамма"),
    "gamma_standard": ("Standard", "Standard", "Estándar", "Standard", "Standard", "標準", "표준", "标准",
                       "Стандарт"),
    "lbl_threshold": ("Soglia", "Threshold", "Umbral", "Schwelle", "Seuil", "しきい値", "임계값", "阈值", "Порог"),
    # più pagine
    "lbl_pages": ("Pagine", "Pages", "Páginas", "Seiten", "Pages", "ページ", "페이지", "页面", "Страницы"),
    "pages_single": ("Singola", "Single", "Individual", "Einzeln", "Unique", "単独", "단일", "单页", "Одна"),
    "pages_sequence": ("Sequenza", "Sequence", "Secuencia", "Serie", "Série", "連続", "연속", "连续", "Серия"),
    "seq_note_files": (
        "Ogni scansione prende il numero successivo: {name}",
        "Each scan gets the next number: {name}",
        "Cada escaneo recibe el número siguiente: {name}",
        "Jeder Scan erhält die nächste Nummer: {name}",
        "Chaque numérisation reçoit le numéro suivant : {name}",
        "スキャンごとに次の番号が付きます: {name}",
        "스캔할 때마다 다음 번호가 붙습니다: {name}",
        "每次扫描使用下一个编号：{name}",
        "Каждый скан получает следующий номер: {name}"),
    "seq_note_pdf": (
        "Le scansioni diventano pagine di un unico PDF.",
        "Scans become pages of a single PDF.",
        "Los escaneos se convierten en páginas de un único PDF.",
        "Die Scans werden Seiten eines einzigen PDFs.",
        "Les numérisations deviennent les pages d'un seul PDF.",
        "スキャンは 1 つの PDF のページになります。",
        "스캔이 하나의 PDF의 페이지가 됩니다.",
        "扫描内容将作为同一个 PDF 的页面。",
        "Сканы становятся страницами одного PDF."),
    "seq_status_files": ("Pagine: {n} · ultima {name}", "Pages: {n} · last {name}", "Páginas: {n} · última {name}",
                         "Seiten: {n} · zuletzt {name}", "Pages : {n} · dernière {name}", "ページ数: {n} · 最新 {name}",
                         "페이지: {n} · 마지막 {name}", "页数：{n} · 最近 {name}", "Страниц: {n} · последняя {name}"),
    "seq_status_pdf": ("{name} · pagine: {n}", "{name} · pages: {n}", "{name} · páginas: {n}", "{name} · Seiten: {n}",
                       "{name} · pages : {n}", "{name} · ページ数: {n}", "{name} · 페이지: {n}", "{name} · 页数：{n}",
                       "{name} · страниц: {n}"),
    "seq_button_hint": (
        "Puoi avviare ogni pagina anche con il pulsante blu dello scanner.",
        "You can also start each page with the scanner's blue button.",
        "También puedes iniciar cada página con el botón azul del escáner.",
        "Jede Seite lässt sich auch mit der blauen Taste am Scanner starten.",
        "Chaque page peut aussi être lancée avec le bouton bleu du scanner.",
        "各ページはスキャナーの青いボタンでも開始できます。",
        "각 페이지는 스캐너의 파란 버튼으로도 시작할 수 있습니다.",
        "也可以用扫描仪上的蓝色按钮开始每一页。",
        "Каждую страницу можно запустить и синей кнопкой на сканере."),
    "log_button": ("Pulsante dello scanner premuto", "Scanner button pressed", "Botón del escáner pulsado",
                   "Scannertaste gedrückt", "Bouton du scanner pressé", "スキャナーのボタンが押されました",
                   "스캐너 버튼이 눌렸습니다", "扫描仪按钮已按下", "Нажата кнопка сканера"),
    "seq_end": ("Termina sequenza", "End sequence", "Terminar secuencia", "Serie beenden", "Terminer la série",
                "連続を終了", "연속 종료", "结束连续扫描", "Завершить серию"),
    "log_seq_end": ("Sequenza terminata (pagine: {n})", "Sequence ended (pages: {n})", "Secuencia terminada (páginas: {n})",
                    "Serie beendet (Seiten: {n})", "Série terminée (pages : {n})", "連続スキャン終了（ページ数: {n}）",
                    "연속 스캔 종료 (페이지: {n})", "连续扫描结束（页数：{n}）", "Серия завершена (страниц: {n})"),
    "log_pdf_page": ("Pagina {n} aggiunta a {path}", "Page {n} added to {path}", "Página {n} añadida a {path}",
                     "Seite {n} zu {path} hinzugefügt", "Page {n} ajoutée à {path}", "{path} に {n} ページ目を追加",
                     "{path}에 {n}페이지 추가", "已将第 {n} 页添加到 {path}", "Страница {n} добавлена в {path}"),
    # promemoria sull'intestazione chiusa di Regolazioni
    "adjust_modified": ("Modificate", "Changed", "Modificados", "Geändert", "Modifiés", "変更あり", "변경됨",
                        "已更改", "Изменены"),
    # correzione righe (calibrazione sul coperchio)
    "lbl_streaks": ("Correzione righe", "Streak correction", "Corrección de rayas", "Streifenkorrektur",
                    "Correction des lignes", "すじ補正", "줄무늬 보정", "条纹校正", "Коррекция полос"),
    "streaks_off": ("Spenta", "Off", "Desactivada", "Aus", "Désactivée", "オフ", "끔", "关闭", "Выкл."),
    "streaks_on": ("Attiva", "On", "Activada", "Ein", "Activée", "オン", "켬", "开启", "Вкл."),
    "streaks_calibrate": ("Calibra...", "Calibrate...", "Calibrar...", "Kalibrieren...", "Calibrer...",
                          "キャリブレーション...", "캘리브레이션...", "校准...", "Калибровать..."),
    "streaks_need_cal": (
        "Serve prima una calibrazione: vetro vuoto e coperchio chiuso, circa due minuti.",
        "A calibration is needed first: empty glass and closed lid, about two minutes.",
        "Primero hace falta una calibración: cristal vacío y tapa cerrada, unos dos minutos.",
        "Zuerst ist eine Kalibrierung nötig: leeres Glas, Deckel geschlossen, etwa zwei Minuten.",
        "Un calibrage est d'abord nécessaire : vitre vide, capot fermé, environ deux minutes.",
        "先にキャリブレーションが必要です。ガラスを空にしてカバーを閉じてください（約2分）。",
        "먼저 캘리브레이션이 필요합니다. 유리를 비우고 덮개를 닫으세요(약 2분).",
        "需要先校准：清空玻璃并合上盖板，约两分钟。",
        "Сначала нужна калибровка: пустое стекло и закрытая крышка, около двух минут."),
    "streaks_info": ("Calibrata il {date} · righe evidenti: {n}", "Calibrated on {date} · visible streaks: {n}",
                     "Calibrado el {date} · rayas visibles: {n}", "Kalibriert am {date} · sichtbare Streifen: {n}",
                     "Calibré le {date} · lignes visibles : {n}", "{date} にキャリブレーション済み · 目立つすじ: {n}",
                     "{date} 캘리브레이션 · 눈에 띄는 줄: {n}", "校准于 {date} · 明显条纹：{n}",
                     "Калибровка от {date} · заметных полос: {n}"),
    "streaks_lineart": ("Non si applica al bianco e nero.", "Does not apply to black and white.",
                        "No se aplica al blanco y negro.", "Gilt nicht für Schwarzweiß.",
                        "Ne s'applique pas au noir et blanc.", "白黒には適用されません。", "흑백에는 적용되지 않습니다.",
                        "不适用于黑白模式。", "Не применяется к черно-белому режиму."),
    "streaks_no_numpy": ("Serve il modulo numpy: esegui di nuovo installa.ps1.",
                         "The numpy module is required: run installa.ps1 again.",
                         "Hace falta el módulo numpy: vuelve a ejecutar installa.ps1.",
                         "Das Modul numpy wird benötigt: installa.ps1 erneut ausführen.",
                         "Le module numpy est nécessaire : relancez installa.ps1.",
                         "numpy モジュールが必要です。installa.ps1 をもう一度実行してください。",
                         "numpy 모듈이 필요합니다. installa.ps1을 다시 실행하세요.",
                         "需要 numpy 模块：请重新运行 installa.ps1。",
                         "Нужен модуль numpy: запустите installa.ps1 еще раз."),
    "dlg_calibrate": (
        "Calibrazione delle righe\n\nTogli tutto dal vetro (fogli, accessori) e chiudi il coperchio. Lo scanner "
        "legge il coperchio bianco a colori e in grigi, poi qualche piccola zona a ogni risoluzione: circa due "
        "minuti.\n\nContinuare?",
        "Streak calibration\n\nRemove everything from the glass (sheets, accessories) and close the lid. The "
        "scanner reads the white lid in color and in grayscale, then a few small areas at each resolution: about "
        "two minutes.\n\nContinue?",
        "Calibración de rayas\n\nQuita todo del cristal (hojas, accesorios) y cierra la tapa. El escáner lee la "
        "tapa blanca en color y en grises, y luego algunas zonas pequeñas en cada resolución: unos dos minutos."
        "\n\n¿Continuar?",
        "Streifenkalibrierung\n\nAlles vom Glas nehmen (Blätter, Zubehör) und den Deckel schließen. Der Scanner "
        "liest den weißen Deckel in Farbe und in Graustufen, dann einige kleine Bereiche in jeder Auflösung: etwa "
        "zwei Minuten.\n\nFortfahren?",
        "Calibrage des lignes\n\nRetirez tout de la vitre (feuilles, accessoires) et fermez le capot. Le scanner "
        "lit le capot blanc en couleur et en niveaux de gris, puis quelques petites zones à chaque résolution : "
        "environ deux minutes.\n\nContinuer ?",
        "すじのキャリブレーション\n\nガラスの上のもの（原稿、アクセサリー）をすべて取り除き、カバーを閉じてください。"
        "スキャナーが白いカバーをカラーとグレーで読み取り、続いて各解像度で小さな範囲を読み取ります。約2分かかります。"
        "\n\n続けますか？",
        "줄무늬 캘리브레이션\n\n유리 위의 모든 것(원고, 액세서리)을 치우고 덮개를 닫으세요. 스캐너가 흰 덮개를 "
        "컬러와 회색조로 읽은 뒤, 해상도마다 작은 영역을 읽습니다. 약 2분 걸립니다.\n\n계속할까요?",
        "条纹校准\n\n请移开玻璃上的所有物品（文稿、附件）并合上盖板。扫描仪以彩色和灰度读取白色盖板，然后在每种"
        "分辨率下读取几个小区域，约需两分钟。\n\n继续吗？",
        "Калибровка полос\n\nУберите все со стекла (листы, принадлежности) и закройте крышку. Сканер читает "
        "белую крышку в цвете и в оттенках серого, затем несколько небольших участков на каждом разрешении: около "
        "двух минут.\n\nПродолжить?"),
    "dlg_streaks_need_cal": (
        "La correzione righe richiede una calibrazione (vetro vuoto, coperchio chiuso, circa due minuti). "
        "Calibrare adesso?",
        "Streak correction needs a calibration (empty glass, closed lid, about two minutes). Calibrate now?",
        "La corrección de rayas necesita una calibración (cristal vacío, tapa cerrada, unos dos "
        "minutos). ¿Calibrar ahora?",
        "Die Streifenkorrektur braucht eine Kalibrierung (leeres Glas, Deckel geschlossen, etwa zwei Minuten). "
        "Jetzt kalibrieren?",
        "La correction des lignes nécessite un calibrage (vitre vide, capot fermé, environ deux minutes). "
        "Calibrer maintenant ?",
        "すじ補正にはキャリブレーションが必要です（ガラスを空にしてカバーを閉じ、約2分）。今すぐ実行しますか？",
        "줄무늬 보정에는 캘리브레이션이 필요합니다(유리를 비우고 덮개를 닫은 상태, 약 2분). 지금 할까요?",
        "条纹校正需要先校准（清空玻璃、合上盖板，约两分钟）。现在校准吗？",
        "Для коррекции полос нужна калибровка (пустое стекло, закрытая крышка, около двух минут). Выполнить сейчас?"),
    "status_calibrating": ("Calibrazione righe: lettura {n} di {total}...",
                           "Streak calibration: reading {n} of {total}...",
                           "Calibración de rayas: lectura {n} de {total}...",
                           "Streifenkalibrierung: Lesung {n} von {total}...",
                           "Calibrage des lignes : lecture {n} sur {total}...",
                           "すじのキャリブレーション: 読み取り {n}/{total}...",
                           "줄무늬 캘리브레이션: {total}회 중 {n}번째 읽기...",
                           "条纹校准：第 {n} 次读取，共 {total} 次...", "Калибровка полос: чтение {n} из {total}..."),
    "calib_done": ("Calibrazione completata", "Calibration complete", "Calibración completada",
                   "Kalibrierung abgeschlossen", "Calibrage terminé", "キャリブレーション完了", "캘리브레이션 완료",
                   "校准完成", "Калибровка завершена"),
    "calib_failed": ("Calibrazione non riuscita", "Calibration failed", "Calibración fallida",
                     "Kalibrierung fehlgeschlagen", "Échec du calibrage", "キャリブレーションに失敗しました",
                     "캘리브레이션 실패", "校准失败", "Калибровка не удалась"),
    "log_calib_done": ("Calibrazione righe salvata. Righe evidenti: {n} a colori, {g} in grigi",
                       "Streak calibration saved. Visible streaks: {n} in color, {g} in grayscale",
                       "Calibración de rayas guardada. Rayas visibles: {n} en color, {g} en grises",
                       "Streifenkalibrierung gespeichert. Sichtbare Streifen: {n} in Farbe, {g} in Graustufen",
                       "Calibrage des lignes enregistré. Lignes visibles : {n} en couleur, {g} en gris",
                       "すじのキャリブレーションを保存しました。目立つすじ: カラー {n}、グレー {g}",
                       "줄무늬 캘리브레이션 저장됨. 눈에 띄는 줄: 컬러 {n}, 회색조 {g}",
                       "条纹校准已保存。明显条纹：彩色 {n}，灰度 {g}",
                       "Калибровка полос сохранена. Заметных полос: цвет {n}, серый {g}"),
    "log_calib_offsets": ("Calibrazione righe: misuro l'allineamento a {n} risoluzioni",
                          "Streak calibration: measuring alignment at {n} resolutions",
                          "Calibración de rayas: midiendo la alineación en {n} resoluciones",
                          "Streifenkalibrierung: Ausrichtung wird bei {n} Auflösungen gemessen",
                          "Calibrage des lignes : mesure de l'alignement à {n} résolutions",
                          "すじのキャリブレーション: {n} 種類の解像度で位置合わせを測定中",
                          "줄무늬 캘리브레이션: 해상도 {n}개에서 정렬 측정 중",
                          "条纹校准：正在 {n} 种分辨率下测量对齐",
                          "Калибровка полос: измерение выравнивания на {n} разрешениях"),
    "log_calib_offsets_done": ("Allineamento misurato, in colonne a 600 dpi: {list}",
                               "Measured alignment, in columns at 600 dpi: {list}",
                               "Alineación medida, en columnas a 600 dpi: {list}",
                               "Gemessene Ausrichtung, in Spalten bei 600 dpi: {list}",
                               "Alignement mesuré, en colonnes à 600 dpi : {list}",
                               "測定した位置ずれ（600 dpiの列単位）: {list}",
                               "측정한 정렬(600 dpi 열 단위): {list}",
                               "测得的对齐偏移（以 600 dpi 列为单位）：{list}",
                               "Измеренное смещение, в столбцах при 600 dpi: {list}"),
    "dlg_calib_error": ("Calibrazione non riuscita:\n{error}", "Calibration failed:\n{error}",
                        "La calibración no se ha completado:\n{error}", "Kalibrierung fehlgeschlagen:\n{error}",
                        "Échec du calibrage :\n{error}", "キャリブレーションに失敗しました:\n{error}",
                        "캘리브레이션 실패:\n{error}", "校准失败：\n{error}", "Калибровка не удалась:\n{error}"),
    "calib_err_dark": (
        "Il coperchio risulta troppo scuro (livello {level}): è chiuso? La lampada è accesa?",
        "The lid reads too dark (level {level}): is it closed? Is the lamp on?",
        "La tapa aparece demasiado oscura (nivel {level}): ¿está cerrada? ¿Está encendida la lámpara?",
        "Der Deckel ist zu dunkel (Wert {level}): Ist er geschlossen? Leuchtet die Lampe?",
        "Le capot paraît trop sombre (niveau {level}) : est-il fermé ? La lampe est-elle allumée ?",
        "カバーが暗すぎます（レベル {level}）。カバーは閉じていますか？ランプは点灯していますか？",
        "덮개가 너무 어둡습니다(레벨 {level}). 덮개가 닫혀 있나요? 램프가 켜져 있나요?",
        "盖板读数太暗（{level}）：盖板合上了吗？灯管亮了吗？",
        "Крышка слишком темная (уровень {level}): она закрыта? Лампа горит?"),
    "calib_err_saturated": (
        "La lettura del coperchio è satura: la calibrazione non è affidabile.",
        "The lid reading is saturated: the calibration is not reliable.",
        "La lectura de la tapa está saturada: la calibración no es fiable.",
        "Der Deckel wird übersteuert gelesen: Die Kalibrierung ist nicht zuverlässig.",
        "La lecture du capot est saturée : le calibrage n'est pas fiable.",
        "カバーの読み取りが飽和しています。キャリブレーションは信頼できません。",
        "덮개 판독값이 포화되었습니다. 캘리브레이션을 신뢰할 수 없습니다.",
        "盖板读数饱和，校准不可靠。",
        "Показания крышки в насыщении: калибровка ненадежна."),
    "calib_err_not_empty": (
        "Sul vetro sembra esserci qualcosa: toglilo, chiudi il coperchio e riprova.",
        "Something seems to be on the glass: remove it, close the lid and try again.",
        "Parece que hay algo en el cristal: quítalo, cierra la tapa y vuelve a intentarlo.",
        "Auf dem Glas scheint etwas zu liegen: entfernen, Deckel schließen und erneut versuchen.",
        "Quelque chose semble posé sur la vitre : retirez-le, fermez le capot et réessayez.",
        "ガラスの上に何かあるようです。取り除いてカバーを閉じ、もう一度お試しください。",
        "유리 위에 무언가 있는 것 같습니다. 치우고 덮개를 닫은 뒤 다시 시도하세요.",
        "玻璃上似乎有东西：请移开，合上盖板后重试。",
        "Похоже, на стекле что-то лежит: уберите, закройте крышку и повторите."),
    "calib_err_short": (
        "La lettura del coperchio è troppo corta per la calibrazione.",
        "The lid reading is too short for a calibration.",
        "La lectura de la tapa es demasiado corta para la calibración.",
        "Die Lesung des Deckels ist für die Kalibrierung zu kurz.",
        "Lecture du capot trop courte pour le calibrage.",
        "キャリブレーションにはカバーの読み取りが短すぎます。",
        "캘리브레이션을 하기에는 덮개 판독이 너무 짧습니다.",
        "盖板读取太短，无法校准。",
        "Слишком короткое чтение крышки для калибровки."),
    "log_streaks_applied": ("Correzione righe: colonne corrette {n}", "Streak correction: corrected columns {n}",
                            "Corrección de rayas: columnas corregidas {n}",
                            "Streifenkorrektur: korrigierte Spalten {n}",
                            "Correction des lignes : colonnes corrigées {n}", "すじ補正: 補正した列 {n}",
                            "줄무늬 보정: 보정한 열 {n}", "条纹校正：已校正 {n} 列",
                            "Коррекция полос: исправлено столбцов {n}"),
    "log_streaks_error": ("Correzione righe non applicata: {error}", "Streak correction not applied: {error}",
                          "Corrección de rayas no aplicada: {error}", "Streifenkorrektur nicht angewendet: {error}",
                          "Correction des lignes non appliquée : {error}", "すじ補正は適用されませんでした: {error}",
                          "줄무늬 보정을 적용하지 못했습니다: {error}", "未应用条纹校正：{error}",
                          "Коррекция полос не применена: {error}"),
    # finestra informativa sulla correzione righe
    "streaks_help_tip": ("Che cos'è la correzione righe?", "What is streak correction?",
                         "¿Qué es la corrección de rayas?", "Was ist die Streifenkorrektur?",
                         "Qu'est-ce que la correction des lignes ?", "すじ補正とは？", "줄무늬 보정이란?",
                         "什么是条纹校正？", "Что такое коррекция полос?"),
    "streaks_help_before": ("Senza correzione", "Without correction", "Sin corrección", "Ohne Korrektur",
                            "Sans correction", "補正なし", "보정 없음", "校正前", "Без коррекции"),
    "streaks_help_after": ("Con correzione", "With correction", "Con corrección", "Mit Korrektur",
                           "Avec correction", "補正あり", "보정 적용", "校正后", "С коррекцией"),
    "streaks_help_h1": ("Da dove vengono le righe", "Where the streaks come from", "De dónde salen las rayas",
                        "Woher die Streifen kommen", "D'où viennent les lignes", "すじの原因", "줄무늬가 생기는 이유",
                        "条纹从何而来", "Откуда берутся полосы"),
    "streaks_help_b1": (
        "Lo scanner legge la pagina con una fila di sensori che scorre dall'alto in basso. Un granello di "
        "polvere dentro lo scanner, sugli specchi o sulla lente, toglie luce sempre agli stessi punti della "
        "fila: nell'immagine diventa una riga verticale lungo tutta la pagina. Spesso è colorata (ciano, "
        "magenta o giallo), perché la polvere toglie luce soprattutto a uno o due dei tre colori; altre volte "
        "è grigia, più scura o più chiara del resto.",
        "The scanner reads the page with a row of sensors that moves from top to bottom. A speck of dust "
        "inside the scanner, on the mirrors or the lens, always takes light away from the same points of the "
        "row: in the image it becomes a vertical line down the whole page. It is often colored (cyan, "
        "magenta or yellow), because the dust takes light mainly from one or two of the three colors; other "
        "times it is gray, darker or lighter than the rest.",
        "El escáner lee la página con una fila de sensores que se desplaza de arriba abajo. Una mota de polvo "
        "dentro del escáner, en los espejos o en la lente, quita luz siempre a los mismos puntos de la fila: "
        "en la imagen se convierte en una línea vertical a lo largo de toda la página. A menudo tiene color (cian, "
        "magenta o amarillo), porque el polvo quita luz sobre todo a uno o dos de los tres colores; otras "
        "veces es gris, más oscura o más clara que el resto.",
        "Der Scanner liest die Seite mit einer Sensorzeile, die von oben nach unten fährt. Ein Staubkorn im "
        "Inneren, auf den Spiegeln oder auf der Linse, nimmt immer denselben Punkten der Zeile Licht weg: Im "
        "Bild wird daraus eine senkrechte Linie über die ganze Seite. Oft ist sie farbig (Cyan, "
        "Magenta oder Gelb), weil der Staub vor allem einer oder zwei der drei Farben Licht wegnimmt; "
        "manchmal ist sie grau, dunkler oder heller als der Rest.",
        "Le scanner lit la page avec une rangée de capteurs qui se déplace de haut en bas. Un grain de "
        "poussière à l'intérieur, sur les miroirs ou sur l'objectif, retire toujours de la lumière aux mêmes "
        "points de la rangée : dans l'image, cela devient une ligne verticale sur toute la page. Elle est souvent "
        "colorée (cyan, magenta ou jaune), car la poussière retire surtout de la lumière à une ou deux des "
        "trois couleurs ; d'autres fois elle est grise, plus sombre ou plus claire que le reste.",
        "スキャナーは、上から下へ動く一列のセンサーでページを読み取ります。内部のミラーやレンズに付いたほこりは、"
        "いつも同じ位置のセンサーの光を遮るため、画像ではページ全体を貫く縦線になります。ほこりが3色のうち1色か2色の"
        "光を主に遮るため、すじはシアン、マゼンタ、黄色などに色づくことがよくあります。灰色で、周りより暗い場合や"
        "明るい場合もあります。",
        "스캐너는 위에서 아래로 움직이는 한 줄의 센서로 페이지를 읽습니다. 내부의 거울이나 렌즈에 붙은 먼지는 "
        "항상 같은 위치의 센서에서 빛을 가리기 때문에, 이미지에서는 페이지 전체를 지나는 세로줄이 됩니다. "
        "먼지가 세 가지 색 중 한두 가지 빛을 주로 가리기 때문에 줄은 청록색, 자홍색, 노란색처럼 색을 띠는 경우가 "
        "많습니다. 회색이거나 주변보다 어둡거나 밝을 때도 있습니다.",
        "扫描仪用一排自上而下移动的传感器读取页面。扫描仪内部反光镜或镜头上的灰尘总是挡住这排传感器中相同位置的"
        "光线，在图像中就成了一条贯穿整页的竖线。由于灰尘主要挡住三种颜色中的"
        "一两种光，条纹常常带有颜色（青色、品红或黄色）；有时也是灰色的，比周围更暗或更亮。",
        "Сканер читает страницу рядом датчиков, который движется сверху вниз. Пылинка внутри сканера, на "
        "зеркалах или на объективе, всегда закрывает свет одним и тем же точкам ряда: на изображении "
        "получается вертикальная линия через всю страницу. Часто она цветная (голубая, "
        "пурпурная или желтая), потому что пыль закрывает в основном один или два из трех цветов; иногда "
        "она серая, темнее или светлее остального."),
    "streaks_help_h2": ("Cosa fa", "What it does", "Qué hace", "Was sie tut", "Ce qu'elle fait", "補正のしくみ",
                        "보정 방법", "校正的作用", "Что она делает"),
    "streaks_help_b2": (
        "La calibrazione legge il coperchio bianco e misura quanta luce perde ogni colonna del sensore. A "
        "ogni scansione il programma restituisce a ogni colonna la luce mancante, e la riga sparisce. È la "
        "stessa tecnica usata per ripulire le immagini dei satelliti. Vale per anteprima, colore e grigi.",
        "The calibration reads the white lid and measures how much light each sensor column loses. On every "
        "scan the program gives each column back the missing light, and the streak disappears. It is the same "
        "technique used to clean up satellite images. It applies to preview, color and grayscale.",
        "La calibración lee la tapa blanca y mide cuánta luz pierde cada columna del sensor. En cada escaneo "
        "el programa devuelve a cada columna la luz que le falta, y la raya desaparece. Es la misma técnica "
        "que se usa para limpiar las imágenes de los satélites. Se aplica a la vista previa, al color y a los "
        "grises.",
        "Die Kalibrierung liest den weißen Deckel und misst, wie viel Licht jede Spalte des Sensors verliert. "
        "Bei jedem Scan gibt das Programm jeder Spalte das fehlende Licht zurück, und der Streifen "
        "verschwindet. Es ist dieselbe Technik, mit der Satellitenbilder bereinigt werden. Sie gilt für "
        "Vorschau, Farbe und Graustufen.",
        "Le calibrage lit le capot blanc et mesure la lumière perdue par chaque colonne du capteur. À chaque "
        "numérisation, le programme rend à chaque colonne la lumière manquante et la ligne disparaît. C'est la "
        "même technique que pour nettoyer les images satellite. Elle s'applique à l'aperçu, à la couleur et "
        "aux niveaux de gris.",
        "キャリブレーションでは白いカバーを読み取り、センサーの列ごとに失われる光の量を測ります。スキャンのたびに"
        "各列へ足りない光を戻すので、すじが消えます。人工衛星の画像をきれいにするのと同じ技術です。プレビュー、"
        "カラー、グレーに適用されます。",
        "캘리브레이션은 흰 덮개를 읽어 센서의 열마다 잃는 빛의 양을 측정합니다. 스캔할 때마다 프로그램이 각 열에 "
        "부족한 빛을 되돌려 주어 줄무늬가 사라집니다. 위성 영상을 깨끗하게 만드는 것과 같은 기술입니다. 미리 보기, "
        "컬러, 회색조에 적용됩니다.",
        "校准时读取白色盖板，测量传感器每一列损失了多少光。每次扫描时，程序为每一列补回缺少的光，条纹就消失了。"
        "这与清理卫星图像所用的技术相同。适用于预览、彩色和灰度。",
        "При калибровке сканер читает белую крышку и измеряет, сколько света теряет каждый столбец датчика. "
        "При каждом сканировании программа возвращает каждому столбцу недостающий свет, и полоса исчезает. "
        "Так же очищают снимки со спутников. Работает для просмотра, цвета и оттенков серого."),
    "streaks_help_h3": ("Quando calibrare", "When to calibrate", "Cuándo calibrar", "Wann kalibrieren",
                        "Quand calibrer", "キャリブレーションの時期", "캘리브레이션 시기", "何时校准",
                        "Когда калибровать"),
    "streaks_help_b3": (
        "La prima volta e quando compaiono righe nuove, perché la polvere si può spostare. Servono il vetro "
        "vuoto e il coperchio chiuso; dura circa due minuti.",
        "The first time, and whenever new streaks appear, because dust can move. The glass must be empty and "
        "the lid closed; it takes about two minutes.",
        "La primera vez y cuando aparezcan rayas nuevas, porque el polvo se puede mover. El cristal debe estar "
        "vacío y la tapa cerrada; tarda unos dos minutos.",
        "Beim ersten Mal und wenn neue Streifen auftauchen, denn Staub kann wandern. Das Glas muss leer und "
        "der Deckel geschlossen sein; es dauert etwa zwei Minuten.",
        "La première fois, puis quand de nouvelles lignes apparaissent, car la poussière peut se déplacer. La "
        "vitre doit être vide et le capot fermé ; cela prend environ deux minutes.",
        "初回と、新しいすじが現れたときです。ほこりは動くことがあります。ガラスを空にしてカバーを閉じてください。"
        "約2分かかります。",
        "처음 한 번, 그리고 새 줄무늬가 보일 때입니다. 먼지는 움직일 수 있습니다. 유리를 비우고 덮개를 닫아야 "
        "하며 약 2분 걸립니다.",
        "第一次使用时，以及出现新条纹时，因为灰尘可能移动。玻璃上须清空并合上盖板，约需两分钟。",
        "В первый раз и когда появляются новые полосы: пыль может сместиться. Стекло должно быть пустым, "
        "крышка закрытой; это занимает около двух минут."),
    "streaks_help_h4": ("Cosa non fa", "What it does not do", "Qué no hace", "Was sie nicht tut",
                        "Ce qu'elle ne fait pas", "補正できないもの", "보정하지 않는 것", "它做不到的",
                        "Чего она не делает"),
    "streaks_help_b4": (
        "Non toglie polvere, peli o graffi sul vetro o sul foglio: quelli sono macchie, non righe. Il bianco "
        "e nero non ne ha bisogno. Dà il meglio con Luminosità e Nitidezza a 0.",
        "It does not remove dust, hairs or scratches on the glass or on the sheet: those are spots, not "
        "streaks. Black and white does not need it. It works best with Brightness and Sharpness at 0.",
        "No quita el polvo, los pelos ni los arañazos del cristal o de la hoja: eso son manchas, no rayas. El "
        "blanco y negro no la necesita. Funciona mejor con Brillo y Nitidez a 0.",
        "Sie entfernt keinen Staub, keine Haare und keine Kratzer auf dem Glas oder dem Blatt: Das sind "
        "Flecken, keine Streifen. Schwarzweiß braucht sie nicht. Am besten wirkt sie mit Helligkeit und "
        "Schärfe auf 0.",
        "Elle n'enlève pas la poussière, les cheveux ni les rayures sur la vitre ou sur la feuille : ce sont "
        "des taches, pas des lignes. Le noir et blanc n'en a pas besoin. Elle donne le meilleur avec "
        "Luminosité et Netteté à 0.",
        "ガラスや原稿の上のほこり、髪の毛、傷は取り除けません。これらはすじではなく点です。白黒には不要です。"
        "明るさとシャープネスが0のときに最もよく効きます。",
        "유리나 원고 위의 먼지, 머리카락, 긁힘은 없애지 못합니다. 그것은 줄이 아니라 점입니다. 흑백에는 필요 "
        "없습니다. 밝기와 선명도가 0일 때 가장 잘 작동합니다.",
        "它不能去除玻璃或文稿上的灰尘、毛发和划痕：那些是斑点，不是条纹。黑白模式不需要它。亮度和锐度为 0 时"
        "效果最好。",
        "Она не убирает пыль, волоски и царапины на стекле или на листе: это пятна, а не полосы. "
        "Черно-белому режиму она не нужна. Лучше всего работает при Яркости и Резкости 0."),
    "streaks_help_not_cal": ("Non ancora calibrata.", "Not calibrated yet.", "Todavía sin calibrar.",
                             "Noch nicht kalibriert.", "Pas encore calibré.", "まだキャリブレーションしていません。",
                             "아직 캘리브레이션하지 않았습니다.", "尚未校准。", "Калибровка еще не выполнена."),
    "streaks_help_need_scanner": (
        "Per calibrare serve lo scanner acceso e pronto.", "Calibration needs the scanner switched on and ready.",
        "Para calibrar, el escáner debe estar encendido y listo.",
        "Zum Kalibrieren muss der Scanner eingeschaltet und bereit sein.",
        "Pour calibrer, le scanner doit être allumé et prêt.",
        "キャリブレーションには、スキャナーの電源が入り準備ができている必要があります。",
        "캘리브레이션하려면 스캐너가 켜져 있고 준비되어 있어야 합니다.", "校准需要扫描仪已开启并就绪。",
        "Для калибровки сканер должен быть включен и готов."),
    "btn_calibrate_now": ("Calibra adesso", "Calibrate now", "Calibrar ahora", "Jetzt kalibrieren",
                          "Calibrer maintenant", "今すぐキャリブレーション", "지금 캘리브레이션", "立即校准",
                          "Калибровать сейчас"),
    "btn_close": ("Chiudi", "Close", "Cerrar", "Schließen", "Fermer", "閉じる", "닫기", "关闭", "Закрыть"),
    # scelta rapida (profili) e compressione
    "sec_quick": ("Scelta rapida", "Quick setup", "Ajuste rápido", "Schnellwahl", "Choix rapide", "クイック設定",
                  "빠른 설정", "快速设置", "Быстрый выбор"),
    "profile_document": ("Documento", "Document", "Documento", "Dokument", "Document", "文書", "문서", "文档",
                         "Документ"),
    "profile_medium": ("Media", "Medium", "Media", "Mittel", "Moyenne", "標準", "보통", "中等", "Средняя"),
    "profile_art": ("Illustrazione", "Illustration", "Ilustración", "Illustration", "Illustration", "イラスト",
                    "일러스트", "插画", "Графика"),
    "profile_document_tip": (
        "Colore, 200 dpi, PDF compatto: pagine leggere ma ben leggibili, circa 200-300 KB per un A4. "
        "Scorciatoia: {shortcut}",
        "Color, 200 dpi, compact PDF: light pages that stay easy to read, about 200-300 KB per A4 page. "
        "Shortcut: {shortcut}",
        "Color, 200 dpi, PDF compacto: páginas ligeras y bien legibles, unos 200-300 KB por A4. Atajo: {shortcut}",
        "Farbe, 200 dpi, kompaktes PDF: leichte, gut lesbare Seiten, etwa 200-300 KB pro A4. Tastenkürzel: {shortcut}",
        "Couleur, 200 dpi, PDF compact : pages légères et bien lisibles, environ 200-300 Ko par A4. "
        "Raccourci : {shortcut}",
        "カラー、200 dpi、コンパクトなPDF: 軽くて読みやすいページ。A4で約200-300 KB。ショートカット: {shortcut}",
        "컬러, 200 dpi, 작은 PDF: 가볍고 읽기 쉬운 페이지, A4 한 장에 약 200-300 KB. 단축키: {shortcut}",
        "彩色、200 dpi、紧凑 PDF：页面小巧且清晰易读，每页 A4 约 200-300 KB。快捷键：{shortcut}",
        "Цвет, 200 dpi, компактный PDF: легкие и хорошо читаемые страницы, около 200-300 КБ на A4. "
        "Сочетание клавиш: {shortcut}"),
    "profile_medium_tip": (
        "Colore, 300 dpi, JPEG equilibrato: per foto e stampe di tutti i giorni. Scorciatoia: {shortcut}",
        "Color, 300 dpi, balanced JPEG: for everyday photos and prints. Shortcut: {shortcut}",
        "Color, 300 dpi, JPEG equilibrado: para fotos e impresos del día a día. Atajo: {shortcut}",
        "Farbe, 300 dpi, ausgewogenes JPEG: für alltägliche Fotos und Drucke. Tastenkürzel: {shortcut}",
        "Couleur, 300 dpi, JPEG équilibré : pour les photos et imprimés de tous les jours. Raccourci : {shortcut}",
        "カラー、300 dpi、バランスの取れたJPEG: 日常の写真や印刷物に。ショートカット: {shortcut}",
        "컬러, 300 dpi, 균형 잡힌 JPEG: 일상적인 사진과 인쇄물에. 단축키: {shortcut}",
        "彩色、300 dpi、均衡 JPEG：适合日常照片和印刷品。快捷键：{shortcut}",
        "Цвет, 300 dpi, сбалансированный JPEG: для повседневных фото и печати. Сочетание клавиш: {shortcut}"),
    "profile_art_tip": (
        "Colore, 600 dpi (la risoluzione ottica massima), TIFF senza perdita: per illustrazioni e archivio. "
        "Scorciatoia: {shortcut}",
        "Color, 600 dpi (the highest optical resolution), lossless TIFF: for illustrations and archiving. "
        "Shortcut: {shortcut}",
        "Color, 600 dpi (la resolución óptica máxima), TIFF sin pérdida: para ilustraciones y archivo. "
        "Atajo: {shortcut}",
        "Farbe, 600 dpi (höchste optische Auflösung), verlustfreies TIFF: für Illustrationen und Archiv. "
        "Tastenkürzel: {shortcut}",
        "Couleur, 600 dpi (la résolution optique maximale), TIFF sans perte : pour les illustrations et "
        "l'archivage. Raccourci : {shortcut}",
        "カラー、600 dpi（光学最大解像度）、可逆圧縮のTIFF: イラストや保存用に。ショートカット: {shortcut}",
        "컬러, 600 dpi(최대 광학 해상도), 무손실 TIFF: 일러스트와 보관용. 단축키: {shortcut}",
        "彩色、600 dpi（最高光学分辨率）、无损 TIFF：适合插画和存档。快捷键：{shortcut}",
        "Цвет, 600 dpi (максимальное оптическое разрешение), TIFF без потерь: для иллюстраций и архива. "
        "Сочетание клавиш: {shortcut}"),
    "lbl_quality": ("Compressione", "Compression", "Compresión", "Kompression", "Compression", "圧縮", "압축",
                    "压缩", "Сжатие"),
    "quality_max": ("Massima", "Best", "Máxima", "Maximal", "Maximale", "最高画質", "최고 화질", "最高质量",
                    "Максимум"),
    "quality_balanced": ("Equilibrata", "Balanced", "Equilibrada", "Ausgewogen", "Équilibrée", "バランス", "균형",
                         "均衡", "Баланс"),
    "quality_compact": ("Compatta", "Compact", "Compacta", "Kompakt", "Compacte", "コンパクト", "작게", "紧凑",
                        "Компактно"),
    "quality_lossless_note": (
        "PNG e TIFF salvano senza perdita: non c'è una compressione da scegliere.",
        "PNG and TIFF are saved without loss: there is no compression to choose.",
        "PNG y TIFF se guardan sin pérdida: no hay compresión que elegir.",
        "PNG und TIFF speichern verlustfrei: Es gibt keine Kompression zu wählen.",
        "PNG et TIFF sont enregistrés sans perte : aucune compression à choisir.",
        "PNGとTIFFは可逆圧縮で保存されるため、選べる圧縮はありません。",
        "PNG와 TIFF는 무손실로 저장되므로 선택할 압축이 없습니다.",
        "PNG 和 TIFF 为无损保存，无需选择压缩。",
        "PNG и TIFF сохраняются без потерь: выбирать сжатие не нужно."),
    "quality_g4_note": (
        "In bianco e nero il PDF usa la compressione dei fax (CCITT G4): pagine già leggerissime.",
        "In black and white the PDF uses fax compression (CCITT G4): pages are already very light.",
        "En blanco y negro el PDF usa la compresión del fax (CCITT G4): páginas ya muy ligeras.",
        "In Schwarzweiß nutzt das PDF die Faxkompression (CCITT G4): Die Seiten sind bereits sehr klein.",
        "En noir et blanc, le PDF utilise la compression des fax (CCITT G4) : pages déjà très légères.",
        "白黒のPDFはファクスの圧縮方式（CCITT G4）を使うので、ページはもともと非常に軽量です。",
        "흑백 PDF는 팩스 압축(CCITT G4)을 사용하므로 페이지가 이미 매우 가볍습니다.",
        "黑白 PDF 使用传真压缩（CCITT G4），页面本已非常小。",
        "В черно-белом режиме PDF использует факсовое сжатие (CCITT G4): страницы и так очень легкие."),
    "log_profile": ("Scelta rapida: {name}", "Quick setup: {name}", "Ajuste rápido: {name}", "Schnellwahl: {name}",
                    "Choix rapide : {name}", "クイック設定: {name}", "빠른 설정: {name}", "快速设置：{name}",
                    "Быстрый выбор: {name}"),
    # file e unità
    "default_prefix": ("Scansione", "Scan", "Escaneo", "Scan", "Numérisation", "スキャン", "스캔", "扫描", "Скан"),
    "unit_byte": ("byte", "bytes", "bytes", "Byte", "octets", "バイト", "바이트", "字节", "байт"),
    "unit_kb": ("KB", "KB", "KB", "KB", "Ko", "KB", "KB", "KB", "КБ"),
    "unit_mb": ("MB", "MB", "MB", "MB", "Mo", "MB", "MB", "MB", "МБ"),
    "unit_gb": ("GB", "GB", "GB", "GB", "Go", "GB", "GB", "GB", "ГБ"),
    "time_s": ("{n} s", "{n} s", "{n} s", "{n} s", "{n} s", "{n} 秒", "{n}초", "{n} 秒", "{n} с"),
    "time_min": ("{n} min", "{n} min", "{n} min", "{n} Min.", "{n} min", "{n} 分", "{n}분", "{n} 分钟", "{n} мин"),
    "time_h": ("{n} ore", "{n} h", "{n} h", "{n} Std.", "{n} h", "{n} 時間", "{n}시간", "{n} 小时", "{n} ч"),

    # messaggi del motore Linux (il testo italiano è anche il modello per riconoscerli)
    "b_wait_adapter": ("In attesa dell'adattatore USB-SCSI...", "Waiting for the USB-SCSI adapter...",
                       "Esperando el adaptador USB-SCSI...", "Warte auf den USB-SCSI-Adapter...",
                       "En attente de l'adaptateur USB-SCSI...", "USB-SCSI アダプターを待っています...",
                       "USB-SCSI 어댑터를 기다리는 중...", "正在等待 USB-SCSI 适配器...", "Ожидание адаптера USB-SCSI..."),
    "b_adapter_not_visible": (
        "Adattatore Logitec USB-SCSI non visibile da Linux", "Logitec USB-SCSI adapter not visible from Linux",
        "El adaptador Logitec USB-SCSI no es visible desde Linux", "Logitec-USB-SCSI-Adapter für Linux nicht sichtbar",
        "Adaptateur Logitec USB-SCSI invisible depuis Linux", "Linux から Logitec USB-SCSI アダプターが見えません",
        "리눅스에서 Logitec USB-SCSI 어댑터가 보이지 않습니다", "Linux 中看不到 Logitec USB-SCSI 适配器",
        "Адаптер Logitec USB-SCSI не виден из Linux"),
    "b_adapter_found": (
        "Adattatore trovato, cerco lo scanner sul bus SCSI...",
        "Adapter found, looking for the scanner on the SCSI bus...",
        "Adaptador encontrado, buscando el escáner en el bus SCSI...",
        "Adapter gefunden, suche den Scanner am SCSI-Bus...",
        "Adaptateur trouvé, recherche du scanner sur le bus SCSI...",
        "アダプターを検出しました。SCSI バス上のスキャナーを探しています...",
        "어댑터를 찾았습니다. SCSI 버스에서 스캐너를 찾는 중...",
        "已找到适配器，正在 SCSI 总线上查找扫描仪...",
        "Адаптер найден, поиск сканера на шине SCSI..."),
    "b_scsi_device": ("ID SCSI {id}: {device}", "SCSI ID {id}: {device}", "ID SCSI {id}: {device}",
                      "SCSI-ID {id}: {device}", "ID SCSI {id} : {device}", "SCSI ID {id}: {device}",
                      "SCSI ID {id}: {device}", "SCSI ID {id}：{device}", "SCSI ID {id}: {device}"),
    "b_no_scanner": (
        "Nessuno scanner Epson trovato sul bus SCSI (scanner acceso? cavo collegato?)",
        "No Epson scanner found on the SCSI bus (is the scanner on? is the cable connected?)",
        "No se encontró ningún escáner Epson en el bus SCSI (¿escáner encendido? ¿cable conectado?)",
        "Kein Epson-Scanner am SCSI-Bus gefunden (Scanner eingeschaltet? Kabel angeschlossen?)",
        "Aucun scanner Epson trouvé sur le bus SCSI (scanner allumé ? câble branché ?)",
        "SCSI バス上に Epson スキャナーが見つかりません（電源は入っていますか？ケーブルは接続されていますか？）",
        "SCSI 버스에서 Epson 스캐너를 찾지 못했습니다 (전원이 켜져 있나요? 케이블이 연결되어 있나요?)",
        "在 SCSI 总线上未找到 Epson 扫描仪（扫描仪是否开机？线缆是否连接？）",
        "Сканер Epson на шине SCSI не найден (сканер включён? кабель подключён?)"),
    "b_no_data": ("Lo scanner non ha inviato dati", "The scanner sent no data", "El escáner no envió datos",
                  "Der Scanner hat keine Daten gesendet", "Le scanner n'a envoyé aucune donnée",
                  "スキャナーからデータが届きません", "스캐너가 데이터를 보내지 않았습니다", "扫描仪未发送数据",
                  "Сканер не прислал данные"),
    "b_nak_params": ("Lo scanner rifiuta i parametri di {cmd} (NAK)", "The scanner rejects the parameters of {cmd} (NAK)",
                     "El escáner rechaza los parámetros de {cmd} (NAK)", "Der Scanner lehnt die Parameter von {cmd} ab (NAK)",
                     "Le scanner refuse les paramètres de {cmd} (NAK)", "スキャナーが {cmd} のパラメーターを拒否しました (NAK)",
                     "스캐너가 {cmd}의 매개변수를 거부했습니다 (NAK)", "扫描仪拒绝了 {cmd} 的参数（NAK）",
                     "Сканер отклонил параметры {cmd} (NAK)"),
    "b_nak": ("Lo scanner rifiuta {cmd} (NAK)", "The scanner rejects {cmd} (NAK)", "El escáner rechaza {cmd} (NAK)",
              "Der Scanner lehnt {cmd} ab (NAK)", "Le scanner refuse {cmd} (NAK)", "スキャナーが {cmd} を拒否しました (NAK)",
              "스캐너가 {cmd}을(를) 거부했습니다 (NAK)", "扫描仪拒绝了 {cmd}（NAK）", "Сканер отклонил {cmd} (NAK)"),
    "b_unexpected_params": (
        "Risposta inattesa a i parametri di {cmd}: {code}", "Unexpected reply to the parameters of {cmd}: {code}",
        "Respuesta inesperada a los parámetros de {cmd}: {code}", "Unerwartete Antwort auf die Parameter von {cmd}: {code}",
        "Réponse inattendue aux paramètres de {cmd} : {code}", "{cmd} のパラメーターに予期しない応答: {code}",
        "{cmd} 매개변수에 대한 예기치 않은 응답: {code}", "{cmd} 参数的响应异常：{code}",
        "Неожиданный ответ на параметры {cmd}: {code}"),
    "b_unexpected": ("Risposta inattesa a {cmd}: {code}", "Unexpected reply to {cmd}: {code}",
                     "Respuesta inesperada a {cmd}: {code}", "Unerwartete Antwort auf {cmd}: {code}",
                     "Réponse inattendue à {cmd} : {code}", "{cmd} に予期しない応答: {code}",
                     "{cmd}에 대한 예기치 않은 응답: {code}", "{cmd} 的响应异常：{code}",
                     "Неожиданный ответ на {cmd}: {code}"),
    "b_esc_unsupported": ("Comando ESC {cmd} non supportato", "ESC {cmd} command not supported",
                          "Comando ESC {cmd} no compatible", "Befehl ESC {cmd} nicht unterstützt",
                          "Commande ESC {cmd} non prise en charge", "ESC {cmd} コマンドは非対応です",
                          "ESC {cmd} 명령은 지원되지 않습니다", "不支持 ESC {cmd} 命令",
                          "Команда ESC {cmd} не поддерживается"),
    "b_expected_stx": ("Atteso STX, ricevuto {code}", "Expected STX, got {code}", "Se esperaba STX, se recibió {code}",
                       "STX erwartet, {code} erhalten", "STX attendu, {code} reçu", "STX を期待しましたが {code} を受信",
                       "STX를 기대했으나 {code} 수신", "应为 STX，收到 {code}", "Ожидался STX, получен {code}"),
    "b_warming": ("Riscaldamento lampada in corso...", "Warming up the lamp...", "Calentando la lámpara...",
                  "Lampe wärmt auf...", "Préchauffage de la lampe...", "ランプをウォームアップ中...", "램프 예열 중...",
                  "正在预热灯管...", "Прогрев лампы..."),
    "b_lamp_timeout": ("La lampada non si è riscaldata in tempo", "The lamp did not warm up in time",
                       "La lámpara no se calentó a tiempo", "Die Lampe ist nicht rechtzeitig warm geworden",
                       "La lampe n'a pas chauffé à temps", "ランプが時間内に温まりませんでした",
                       "램프가 제시간에 예열되지 않았습니다", "灯管未能及时预热", "Лампа не прогрелась вовремя"),
    "b_res_unsupported": ("Risoluzione {dpi} non supportata", "Resolution {dpi} not supported",
                          "Resolución {dpi} no compatible", "Auflösung {dpi} nicht unterstützt",
                          "Résolution {dpi} non prise en charge", "解像度 {dpi} は非対応です",
                          "해상도 {dpi}은(는) 지원되지 않습니다", "不支持分辨率 {dpi}", "Разрешение {dpi} не поддерживается"),
    "b_scan_start": (
        "Scansione {mode} {dpi} dpi, {w}x{h} punti ({bpl} byte/riga)",
        "Scanning {mode} {dpi} dpi, {w}x{h} pixels ({bpl} bytes/line)",
        "Escaneo {mode} {dpi} dpi, {w}x{h} puntos ({bpl} bytes/línea)",
        "Scan {mode} {dpi} dpi, {w}x{h} Pixel ({bpl} Byte/Zeile)",
        "Numérisation {mode} {dpi} dpi, {w}x{h} points ({bpl} octets/ligne)",
        "スキャン {mode} {dpi} dpi, {w}x{h} ドット ({bpl} バイト/行)",
        "스캔 {mode} {dpi} dpi, {w}x{h} 픽셀 ({bpl} 바이트/줄)",
        "扫描 {mode} {dpi} dpi，{w}x{h} 像素（{bpl} 字节/行）",
        "Сканирование {mode} {dpi} dpi, {w}x{h} точек ({bpl} байт/строка)"),
    "b_start_rejected": ("Lo scanner rifiuta l'avvio della scansione", "The scanner refuses to start the scan",
                         "El escáner rechaza iniciar el escaneo", "Der Scanner verweigert den Scanstart",
                         "Le scanner refuse de démarrer la numérisation", "スキャナーがスキャン開始を拒否しました",
                         "스캐너가 스캔 시작을 거부했습니다", "扫描仪拒绝开始扫描", "Сканер отказался начать сканирование"),
    "b_bad_block": ("Blocco dati non valido (atteso STX, ricevuto {code})", "Invalid data block (expected STX, got {code})",
                    "Bloque de datos no válido (se esperaba STX, se recibió {code})",
                    "Ungültiger Datenblock (STX erwartet, {code} erhalten)",
                    "Bloc de données non valide (STX attendu, {code} reçu)",
                    "無効なデータブロック (STX を期待、{code} を受信)", "잘못된 데이터 블록 (STX 기대, {code} 수신)",
                    "数据块无效（应为 STX，收到 {code}）", "Неверный блок данных (ожидался STX, получен {code})"),
    "b_fatal": ("Errore fatale dello scanner (stato {code})", "Fatal scanner error (status {code})",
                "Error fatal del escáner (estado {code})", "Schwerer Scannerfehler (Status {code})",
                "Erreur fatale du scanner (état {code})", "スキャナーの致命的エラー (状態 {code})",
                "스캐너 치명적 오류 (상태 {code})", "扫描仪严重错误（状态 {code}）", "Критическая ошибка сканера (состояние {code})"),
    "b_busy_other": ("Scanner occupato su un'altra interfaccia", "Scanner busy on another interface",
                     "Escáner ocupado en otra interfaz", "Scanner an einer anderen Schnittstelle belegt",
                     "Scanner occupé sur une autre interface", "スキャナーは別のインターフェースで使用中です",
                     "스캐너가 다른 인터페이스에서 사용 중입니다", "扫描仪正被其他接口占用", "Сканер занят другим интерфейсом"),
    "b_adapter_not_found": (
        "Adattatore Logitec USB-SCSI (0789:00C0, 0789:0004) non trovato", "Logitec USB-SCSI adapter (0789:00C0, 0789:0004) not found",
        "No se encontró el adaptador Logitec USB-SCSI (0789:00C0, 0789:0004)", "Logitec-USB-SCSI-Adapter (0789:00C0, 0789:0004) nicht gefunden",
        "Adaptateur Logitec USB-SCSI (0789:00C0, 0789:0004) introuvable", "Logitec USB-SCSI アダプター (0789:00C0, 0789:0004) が見つかりません",
        "Logitec USB-SCSI 어댑터(0789:00C0, 0789:0004)를 찾을 수 없습니다", "未找到 Logitec USB-SCSI 适配器（0789:00C0）",
        "Адаптер Logitec USB-SCSI (0789:00C0, 0789:0004) не найден"),
    "b_status_timeout": ("Timeout in attesa dello stato SCSI ({st})", "Timeout waiting for SCSI status ({st})",
                         "Tiempo agotado esperando el estado SCSI ({st})", "Zeitüberschreitung beim SCSI-Status ({st})",
                         "Délai dépassé en attendant l'état SCSI ({st})", "SCSI 状態待ちがタイムアウト ({st})",
                         "SCSI 상태 대기 시간 초과 ({st})", "等待 SCSI 状态超时（{st}）",
                         "Тайм-аут ожидания состояния SCSI ({st})"),
    "b_no_answer": ("Nessuna risposta dall'ID {id} al comando {cmd} ({err})", "No reply from ID {id} to command {cmd} ({err})",
                    "Sin respuesta del ID {id} al comando {cmd} ({err})", "Keine Antwort von ID {id} auf Befehl {cmd} ({err})",
                    "Pas de réponse de l'ID {id} à la commande {cmd} ({err})", "ID {id} からコマンド {cmd} への応答なし ({err})",
                    "ID {id}에서 명령 {cmd}에 응답 없음 ({err})", "ID {id} 未响应命令 {cmd}（{err}）",
                    "Нет ответа от ID {id} на команду {cmd} ({err})"),
    "b_check_condition": ("CHECK CONDITION sul comando {cmd}, sense {sense}", "CHECK CONDITION on command {cmd}, sense {sense}",
                          "CHECK CONDITION en el comando {cmd}, sense {sense}", "CHECK CONDITION bei Befehl {cmd}, Sense {sense}",
                          "CHECK CONDITION sur la commande {cmd}, sense {sense}", "コマンド {cmd} で CHECK CONDITION、sense {sense}",
                          "명령 {cmd}에서 CHECK CONDITION, sense {sense}", "命令 {cmd} 出现 CHECK CONDITION，sense {sense}",
                          "CHECK CONDITION на команде {cmd}, sense {sense}"),
    "b_cmd_rejected": ("Comando {cmd} rifiutato, stato {st}", "Command {cmd} rejected, status {st}",
                       "Comando {cmd} rechazado, estado {st}", "Befehl {cmd} abgelehnt, Status {st}",
                       "Commande {cmd} refusée, état {st}", "コマンド {cmd} が拒否されました、状態 {st}",
                       "명령 {cmd} 거부됨, 상태 {st}", "命令 {cmd} 被拒绝，状态 {st}", "Команда {cmd} отклонена, состояние {st}"),
    "b_usb_error": ("Errore USB durante il comando {cmd}: {err}", "USB error during command {cmd}: {err}",
                    "Error USB durante el comando {cmd}: {err}", "USB-Fehler bei Befehl {cmd}: {err}",
                    "Erreur USB pendant la commande {cmd} : {err}", "コマンド {cmd} の実行中に USB エラー: {err}",
                    "명령 {cmd} 중 USB 오류: {err}", "命令 {cmd} 执行时 USB 错误：{err}",
                    "Ошибка USB во время команды {cmd}: {err}"),
    "b_no_device": ("Nessun dispositivo SCSI all'ID {id}", "No SCSI device at ID {id}", "Ningún dispositivo SCSI en el ID {id}",
                    "Kein SCSI-Gerät an ID {id}", "Aucun périphérique SCSI à l'ID {id}", "ID {id} に SCSI デバイスがありません",
                    "ID {id}에 SCSI 장치가 없습니다", "ID {id} 上没有 SCSI 设备", "Нет SCSI-устройства с ID {id}"),
    "b_adapter_error": ("Errore adattatore 0x{code} (comando {cmd}, stato {st})", "Adapter error 0x{code} (command {cmd}, status {st})",
                        "Error del adaptador 0x{code} (comando {cmd}, estado {st})",
                        "Adapterfehler 0x{code} (Befehl {cmd}, Status {st})",
                        "Erreur de l'adaptateur 0x{code} (commande {cmd}, état {st})",
                        "アダプターエラー 0x{code} (コマンド {cmd}、状態 {st})", "어댑터 오류 0x{code} (명령 {cmd}, 상태 {st})",
                        "适配器错误 0x{code}（命令 {cmd}，状态 {st}）", "Ошибка адаптера 0x{code} (команда {cmd}, состояние {st})"),
    "b_scsi_status": ("Stato SCSI 0x{code} sul comando {cmd} (stato {st})", "SCSI status 0x{code} on command {cmd} (status {st})",
                      "Estado SCSI 0x{code} en el comando {cmd} (estado {st})", "SCSI-Status 0x{code} bei Befehl {cmd} (Status {st})",
                      "État SCSI 0x{code} sur la commande {cmd} (état {st})", "コマンド {cmd} で SCSI 状態 0x{code} (状態 {st})",
                      "명령 {cmd}에서 SCSI 상태 0x{code} (상태 {st})", "命令 {cmd} 的 SCSI 状态 0x{code}（状态 {st}）",
                      "Состояние SCSI 0x{code} на команде {cmd} (состояние {st})"),
    "b_unknown_cmd": ("Comando sconosciuto: {cmd}", "Unknown command: {cmd}", "Comando desconocido: {cmd}",
                      "Unbekannter Befehl: {cmd}", "Commande inconnue : {cmd}", "不明なコマンド: {cmd}",
                      "알 수 없는 명령: {cmd}", "未知命令：{cmd}", "Неизвестная команда: {cmd}"),
    "b_stale_engines": (
        "Fermati {n} motori rimasti attivi da un avvio precedente (tenevano occupato l'adattatore)",
        "Stopped {n} engines left running from a previous start (they were holding the adapter)",
        "Detenidos {n} motores que seguían activos de un inicio anterior (tenían ocupado el adaptador)",
        "{n} Engines aus einem früheren Start beendet (sie hielten den Adapter belegt)",
        "{n} moteurs restés actifs d'un démarrage précédent ont été arrêtés (ils occupaient l'adaptateur)",
        "前回の起動から残っていたエンジンを {n} 個停止しました（アダプターを占有していました）",
        "이전 실행에서 남아 있던 엔진 {n}개를 중지했습니다(어댑터를 점유하고 있었습니다)",
        "已停止上次启动遗留的 {n} 个引擎（它们占用了适配器）",
        "Остановлено двигателей, оставшихся от прошлого запуска: {n} (они занимали адаптер)"),
    "b_level_unsupported": (
        "Scanner con protocollo ESC/I livello {level}: non supportato (servono i livelli da B4 a B8)",
        "Scanner with ESC/I protocol level {level}: not supported (levels B4 to B8 are needed)",
        "Escáner con protocolo ESC/I de nivel {level}: no compatible (se necesitan los niveles B4 a B8)",
        "Scanner mit ESC/I-Protokoll der Stufe {level}: nicht unterstützt (erforderlich sind die Stufen B4 bis B8)",
        "Scanner au protocole ESC/I de niveau {level} : non pris en charge (niveaux B4 à B8 requis)",
        "ESC/I レベル {level} のスキャナーには対応していません（レベル B4 から B8 が必要です）",
        "ESC/I 프로토콜 레벨 {level} 스캐너는 지원하지 않습니다(레벨 B4부터 B8까지 필요)",
        "不支持 ESC/I 协议级别为 {level} 的扫描仪（需要 B4 至 B8 级别）",
        "Сканер с протоколом ESC/I уровня {level} не поддерживается (нужны уровни с B4 по B8)"),
    "b_color_level": (
        "A colori questo scanner (livello {level}) non è supportato: usa Grigi o Bianco e nero",
        "Color scanning is not supported on this scanner (level {level}): use Grayscale or Black & white",
        "El escaneo en color no es compatible con este escáner (nivel {level}): usa Grises o Blanco y negro",
        "Farbscans werden bei diesem Scanner (Stufe {level}) nicht unterstützt: Graustufen oder Schwarzweiß "
        "verwenden",
        "La numérisation couleur n'est pas prise en charge sur ce scanner (niveau {level}) : utilisez Gris ou "
        "Noir et blanc",
        "このスキャナー（レベル {level}）ではカラーに対応していません。グレーまたは白黒を使ってください",
        "이 스캐너(레벨 {level})는 컬러를 지원하지 않습니다. 회색조 또는 흑백을 사용하세요",
        "此扫描仪（级别 {level}）不支持彩色扫描：请使用灰度或黑白",
        "Цветное сканирование на этом сканере (уровень {level}) не поддерживается: используйте Серый или Ч/б"),
}

# ordine di prova: i modelli più specifici prima di quelli generici che li contengono
BACKEND_KEYS = [
    "b_wait_adapter", "b_adapter_not_visible", "b_adapter_found", "b_scsi_device", "b_no_scanner", "b_no_data",
    "b_nak_params", "b_nak", "b_unexpected_params", "b_unexpected", "b_esc_unsupported", "b_expected_stx",
    "b_warming", "b_lamp_timeout", "b_res_unsupported", "b_scan_start", "b_start_rejected", "b_bad_block",
    "b_fatal", "b_busy_other", "b_adapter_not_found", "b_status_timeout", "b_no_answer", "b_check_condition",
    "b_cmd_rejected", "b_usb_error", "b_no_device", "b_adapter_error", "b_scsi_status", "b_unknown_cmd",
    "b_level_unsupported", "b_color_level", "b_stale_engines",
]
MODE_KEYS = {"color": "mode_color", "gray": "mode_gray", "lineart": "mode_lineart"}

_lang = "it"


def set_language(code):
    global _lang
    _lang = code if code in CODES else "it"


def language():
    return _lang


def language_name(code=None):
    return dict(LANGUAGES).get(code or _lang, code)


def tr(key, **kw):
    entry = STRINGS.get(key)
    if entry is None:
        return key
    template = entry[CODES.index(_lang)] or entry[0]
    values = {}
    for k, v in kw.items():
        if k == "mode" and v in MODE_KEYS:
            v = tr(MODE_KEYS[v])
        values[k] = str(v)
    return template.format(**values)


class Msg:
    """Testo tradotto al momento della visualizzazione: cambiando lingua si ritraduce."""

    def __init__(self, key=None, raw=None, **kw):
        self.key, self.raw, self.kw = key, raw, kw

    def __str__(self):
        return tr(self.key, **self.kw) if self.key else str(self.raw)


def _pattern(template):
    parts = re.split(r"\{(\w+)\}", template)
    rx = "".join(re.escape(p) if i % 2 == 0 else "(?P<%s>.+?)" % p for i, p in enumerate(parts))
    return re.compile("^" + rx + "$", re.S)


_BACKEND_PATTERNS = [(key, _pattern(STRINGS[key][0])) for key in BACKEND_KEYS]


def from_backend(text):
    """Messaggio del motore Linux (in italiano) come Msg traducibile; se non riconosciuto resta com'è."""
    for key, rx in _BACKEND_PATTERNS:
        m = rx.match(text)
        if m:
            return Msg(key, **m.groupdict())
    return Msg(raw=text)


def number(value, decimals=1):
    s = "%.*f" % (decimals, value)
    return s.replace(".", ",") if _lang in DECIMAL_COMMA else s


def size(n):
    if n < 1024:
        return "%d %s" % (n, tr("unit_byte"))
    for unit in ("unit_kb", "unit_mb", "unit_gb"):
        n /= 1024.0
        if n < 1024 or unit == "unit_gb":
            return "%s %s" % (number(n), tr(unit))


def duration(seconds):
    if seconds < 90:
        return tr("time_s", n=max(1, round(seconds)))
    if seconds < 90 * 60:
        return tr("time_min", n=round(seconds / 60))
    return tr("time_h", n=number(seconds / 3600))


class Size:
    """Dimensione dentro un Msg: si formatta nella lingua del momento."""

    def __init__(self, n):
        self.n = n

    def __str__(self):
        return size(self.n)


class Duration:
    """Durata dentro un Msg: si formatta nella lingua del momento."""

    def __init__(self, seconds):
        self.seconds = seconds

    def __str__(self):
        return duration(self.seconds)
