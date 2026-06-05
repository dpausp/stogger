# Doc-Testing Research: Preventing Documentation Drift in stogger

Forschungsbericht zu drei Throwaway-Experimenten, die untersucht haben, wie sich
stoggers Dokumentation maschinell gegen Renderer-Drift absichern lässt. Ziel: kein
handgeschriebenes Beispiel in `docs/`, das nicht gleichzeitig durch einen Test
gesichert ist.

## TL;DR

Drei Patterns wurden als separate Wurf-Experimente unter `.agents/tmp/experiments/`
gebaut und validiert: **Sybil** (Markdown-Codeblöcke werden zu pytest-Items), **Snapshot
+ `{literalinclude}`** (echtes stogger-stderr wird als Golden File in Sphinx
eingebettet) und **PEP-723 Standalone-Demo** (`uv run demo.py` ohne Installation). Alle
drei funktionieren, alle drei sichern unterschiedliche Failure-Modi, alle drei sollten
übernommen werden. Eine offene Designentscheidung (Zeitstempel-Strategie im
gesamten Pipeline) blockiert noch die Implementierung.

## Problemstellung

### Das Drift-Problem

stogger dokumentiert in `docs/user/output_gallery.md` und anderen User-Docs
handgeschriebene Beispiel-Outputs. Diese Beispiele haben **keine mechanische Kopplung**
an das, was der Renderer tatsächlich ausgibt. Wenn sich der Renderer ändert, lügt die
Dokumentation stillschweigend. Ein typischer "Renderer Change" ist alles, was die
Ausgabe verändert: neue Processor-Reihenfolge, geänderte `format_exc_info`-Ausgabe,
neue Default-Keys, geändertes Levelformat — also ganz normale Weiterentwicklung.

### Konkreter Auslöser

Der Bug-Report "log.exception traceback regression" in der 2026.6.x-Serie stellte sich
nach Prüfung als **kein** Regression heraus: Das neue Verhalten matches sowohl die
autoritative Spec (`docs/user/logging_patterns.md:107-121` — "Use `log.exception()` in
except blocks … automatically includes the full traceback. Do not pass `error=str(e)`;
the exception context is already captured.") als auch die E2E-Tests
(`tests/test_e2e_user_perspective.py:239-260` und
`tests/test_e2e_single_module_app.py:171-199`). Beide Tests prüfen explizit, dass der
Eventname, der Exception-Typ, die Exception-Message, die übergebenen kwargs und der
Traceback-String in stderr stehen.

Aber: `docs/user/output_gallery.md:122-131` (Exception Logging Section) zeigt noch den
pre-2026.6.x-Output — ohne `kwargs=`, ohne den von `format_exc_info` gerenderten
`exception:`-Block. Das ist exakt der Failure-Modus, den wir ausschalten wollen.

### User-Anforderung

Wörtlich aus dem Diskussionsverlauf:

> wir dürfen keinen kram mehr bauen der by default zu 99% wegdriftet

### Forschungsumfang

Drei Patterns wurden parallel als Throwaway-Experimente unter
`.agents/tmp/experiments/` gebaut und in je einem `RESULT.md` dokumentiert. Alle drei
sind gegangen. Dieser Bericht fasst zusammen, was gelernt wurde und was übernommen
werden soll.

## Die drei Patterns auf einen Blick

| Pattern | Sichert gegen | Betroffene Files | Status |
|---|---|---|---|
| **Sybil** (doc-is-test) | Inline-Code-Beispiele veralten | `docs/**/*.md`-`python`-Fenced-Blocks | ✅ funktioniert |
| **Snapshot + `{literalinclude}`** | Renderer-Output driftet | `docs/_generated/*.txt` → `docs/**/*.md`-Includes | ✅ funktioniert |
| **PEP-723 Standalone-Demo** | Onboarding friction | `examples/demo.py` (zero-install) | ✅ funktioniert |

Jeder Pattern sichert eine **eigene** Drift-Klasse. Sie konkurrieren nicht, sie
ergänzen sich.

## Experiment 1 — Sybil (doc-is-test)

### Konzept

[Sybil](https://sybil.readthedocs.io/) macht jeden eingezäunten ```` ```python ````-Block
in Markdown-Dateien zu einem eigenen pytest-Item. Die Blocks eines Dokuments teilen
sich einen Namespace, sodass Variablen und Imports aus Block 1 in Block 2 sichtbar
sind. Handgeschriebene Codebeispiele in der Doku werden damit maschinell ausgeführt:
ändert sich die API, schlägt der doctest an — bevor die Doku lügen kann.

Sybil wird ausschließlich über `pytest_collect_file` in einem `conftest.py`-Hook
konfiguriert; kein eigener Test-Runner, kein zusätzliches CLI-Tool.

### Setup im Experiment

Verzeichnisstruktur (siehe `exp1-sybil/RESULT.md`):

```
exp1-sybil/
├── conftest.py           # root: sys.path-fixup auf /stogger
├── pyproject.toml        # [tool.pytest.ini_options] testpaths = ["docs"]
├── docs/
│   ├── conftest.py       # Sybil-Wiring
│   └── sample_doc.md     # zwei python-Blöcke (Namespace-Sharing)
└── RESULT.md
```

`docs/conftest.py` (verkürzt):

```python
from sybil import Sybil
from sybil.parsers.markdown import PythonCodeBlockParser

pytest_collect_file = Sybil(
    parsers=[PythonCodeBlockParser()],
    patterns=["*.md"],
).pytest()
```

Wichtig: `sybil.parsers.markdown.PythonCodeBlockParser`, **nicht** das legacy-Modul
`sybil.parsers.codeblock` (siehe unten, Friction Point 2).

### Funktionierender Aufruf

```
uv run --with-editable /stogger --with "sybil[pytest]" pytest docs/ -v
```

**Exit 0**, 2 passed, 1 warning. Vollständige Ausgabe:

```
============================= test session starts ==============================
platform linux -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
collecting ... collected 2 items

docs/sample_doc.md::line:10,column:1 PASSED                              [ 50%]
docs/sample_doc.md::line:19,column:1 PASSED                              [100%]

========================= 2 passed, 1 warning in 0.05s =========================
```

Das Warning ist stogger-eigen ("test infrastructure incomplete: no
`[dependency-groups].test` found …") und für Sybil irrelevant.

### Verdict

**Funktioniert.** Niedrige Reibung. Fünf Reibungspunkte für die spätere Produktion-Adoption:

1. **`Sybil(root=...)` ist in Sybil ≥ 8 entfernt.** Spec nannte noch
   `root=Path(__file__).parent`. Ab Sybil 8 wirft das
   `TypeError: Sybil.__init__() got an unexpected keyword argument 'root'`. Fix: kwarg
   weglassen; das Such-Root wird automatisch aus dem `conftest.py`-Verzeichnis
   abgeleitet (`path="."` ist der Default).
2. **`sybil.parsers.codeblock` ist ein legacy-RST-Shim.** Es alias-t
   `sybil.parsers.rest.PythonCodeBlockParser`, also RST-`.. code-block:: python`, und
   matcht Markdown-Fenced-Blocks **gar nicht**. Erster Testlauf sammelte 2 Items mit
   0 Beispielen — der Parser matcht stillschweigend nichts. Fix:
   `sybil.parsers.markdown.PythonCodeBlockParser` für `*.md`. Wer MyST mit
   Sphinx-spezifischen Direktiven nutzt, kann auch `sybil.parsers.myst.*` verwenden.
3. **Path-Index im root-`conftest.py` stimmt nur bei richtiger Verzeichnistiefe.**
   `Path(__file__).resolve().parents[3]` resolved im Experiment nach `/stogger/.agents`
   statt `/stogger`, weil das Experiment vier Level unter dem Repo-Root liegt. Im
   echten `docs/conftest.py` ist es nur eine Ebene (`parents[1]`). Symptom: stogger
   bleibt ohne Fehlermeldung unimportierbar. Friction sinkt, sobald Sybil direkt im
   Repo installiert ist.
4. **`--with "structlog"` pullt keine transitive Deps.** Die im Spec vorgeschlagene
   Kommandozeile `uv run --with "sybil[pytest]" --with "structlog" pytest docs/`
   erzeugt einen ephemären Venv mit nur diesen zwei Paketen. stogger ist über den
   sys.path-Shim zwar importierbar, schlägt aber beim ersten `import attrs` fehl.
   Fix: `--with-editable /stogger` statt oder zusätzlich zum sys.path-Shim. Das zieht
   stoggers gesamten Dep-Closure aus `pyproject.toml` rein.
5. **Spec-Block-2 belegt Namespace-Sharing nicht.** Block 2 (`import structlog; log =
   structlog.get_logger(); log.info(…)`) läuft auch in einem frischen Namespace — er
   referenziert keinen Namen aus Block 1. Wenn künftig wirklich Namespace-Sharing
   getestet werden soll, sollte Block 2 z. B. `stogger.__version__` oder eine in Block
   1 gesetzte Variable referenzieren.

### Was Sybil NICHT sichert

Nur Inline-Code-Ausführung. Visuelle Output-Beispiele — also "so sieht stderr aus,
wenn man `log.exception()` aufruft" — sichert Sybil nicht. Genau das ist aber die
Drift-Klasse, die `output_gallery.md:122-131` trifft. Dafür braucht es Experiment 2.

## Experiment 2 — Snapshot + `{literalinclude}`-Pipeline

### Konzept

pytest captured über `capsys` den echten stogger-stderr-Output, normalisiert variable
Teile (Zeitstempel, Pfade, ANSI-Codes), und schreibt das Ergebnis in ein deterministisches
Golden File (`docs/_generated/exception_output.txt`). Sphinx bettet diese Datei über
die Standard-Direktive `{literalinclude}` 1:1 in HTML ein. Driftet der Renderer, schlägt
der pytest beim Vergleich mit dem Golden File an — bevor die Doku lügen kann.

Das ist das fehlende Stick in nixflows aktuellem doc-is-test-Setup: nixflow hat zwar
Sybil, aber keine Output-Sicherung.

### Setup im Experiment

Verzeichnis (siehe `exp2-snapshot/RESULT.md`):

```
exp2-snapshot/
├── test_capture.py                # capsys + Normalisierung + Golden-File-Vergleich
├── helpers.py                     # strip_ansi, normalize_timestamps, normalize_paths
│                                  # (portiert aus nixflow/tests/helpers.py)
├── pyproject.toml                 # non-package, stogger als [tool.uv.sources]-path-dep
└── docs/
    ├── conf.py                    # extensions = ["myst_parser"]
    ├── index.md
    ├── output_gallery.md          # enthält {literalinclude} _generated/exception_output.txt
    └── _generated/
        └── exception_output.txt   # deterministischer Snapshot, 6 Zeilen
```

Das `output_gallery.md`-Include sieht so aus:

````markdown
## Exception Logging

Real captured output from stogger:

```{literalinclude} _generated/exception_output.txt
:language: text
```
````

### Pipeline-Ergebnisse

| Schritt | Kommando | Exit |
|---|---|---|
| Capture + Snapshot (1. Run, legt Baseline an) | `uv run pytest test_capture.py -v` | `1` (by design) |
| Capture + Snapshot (2.+ Run, deterministisch) | `uv run pytest test_capture.py -v` | `0` |
| Sphinx-Build | `uv run sphinx-build -b html docs _build/html` | `0` |

Der erste Run beendet sich mit Exit 1, weil die Test-Logik lautet: "Wenn Fixture
fehlt → schreibe Baseline → `pytest.fail('fixture absent — created baseline …')`".
Zwangt den Entwickler, die Baseline einmal anzuschauen. Ab dem zweiten Run ist es ein
Byte-für-Byte-Vergleich.

### Captured Output (vollständig, aus dem Golden File)

```
<TIMESTAMP> I systemd-journal-active         Systemd journal logging active
<TIMESTAMP> E experiment-2-event             context='snapshot' exception_class='builtins.ValueError' exception_msg='snapshot trigger' exception_traceback='Traceback (most recent call last):\n  File "<PATH>", line 48, in test_captured_exception_output_matches_snapshot\n    raise ValueError("snapshot trigger")\nValueError: snapshot trigger'
exception: Traceback (most recent call last):
exception:   File "<PATH>", line 48, in test_captured_exception_output_matches_snapshot
exception:     raise ValueError("snapshot trigger")
exception: ValueError: snapshot trigger
```

Beachte die beiden Render-Wege, die stogger in der 2026.6.x-Serie für
`log.exception()` ausgibt:

1. **Strukturierte kv-Paare** in der ersten Zeile: `context='snapshot'`,
   `exception_class='builtins.ValueError'`, `exception_msg='snapshot trigger'`,
   `exception_traceback='…'`. Genau diese Felder fehlen in
   `output_gallery.md:122-131`.
2. **Multi-line `exception:`-Suffix** gerendert durch structlogs `format_exc_info` -
   Processor. Genau dieser Block fehlt ebenfalls in `output_gallery.md:122-131`.

HTML-Render: `_build/html/output_gallery.html` enthält jede Zeile 1:1 in einem
`<div class="highlight-text">`-Pygments-Block. Sphinx HTML-escaped `<` zu `&lt;`
innerhalb von `<pre>` (korrekt), also wird `<TIMESTAMP>` und `<PATH>` im Browser
exakt so angezeigt. ANSI-Codes werden von stogger selbst unterdrückt (capsys-stderr
ist kein TTY) und zusätzlich von `strip_ansi()` defensiv entfernt; `rg $'\x1b'
docs/_generated/exception_output.txt` liefert null Matches.

### Verdict

**Funktioniert end-to-end.** Erste Run legt Baseline + schlägt absichtlich an; zweite
und jede weitere Run vergleichen deterministisch. Sphinx rendert den Golden-File-Inhalt
 unverändert in HTML. Sechs Reibungspunkte für die Produktion-Adoption:

1. **stogger hat keinen `get_logger()`-Re-Export.** Man muss nach `init_logging`
   explizit `structlog.get_logger()` rufen. Ein `stogger.get_logger`-Shim würde den
   Onboarding-Tanz etwas kürzen. Nicht blockierend.
2. **First-run/Second-run-Protokoll braucht Doku oder Flag.** Das
   "fehlendes-Fixture-anlegen-dann-fail"-Verhalten ist als Default richtig, aber nicht
   selbsterklärend. Ein `--update-snapshots`-Flag wäre benutzerfreundlicher. nixflows
   `helpers.py` hat es auch nicht.
3. **Path-Normalisierung ist aggressiv.** `normalize_paths` ersetzt jedes `/…`-Token
   durch `<PATH>`, verliert also den Basename. Aus
   `/stogger/.agents/…/test_capture.py` wird `File "<PATH>", line 48` — gut für
   determinism cross-machine, schlecht für menschliche Lesbarkeit. Eine künftige
   Helper-Variante könnte den Basename erhalten (`<PATH>/test_capture.py`). Out of
   scope für das Experiment, aber für nixflow-Adoption wertvoll.
4. **`[tool.uv.sources]` ist sauberer als inline `file://`-URLs.** Die inline
   `stogger @ file:///stogger`-Form funktioniert, erzeugt aber Resolver-Warnings;
   `[tool.uv.sources]`-Deklaration plus `tool.uv.package = false` für
   Non-Package-Projekte ist die empfohlene Variante. Spec-Level-Detail, kein
   Blocker.
5. **`{literalinclude}` ist Sphinx-Core, nicht MyST.** Es gibt **nichts** in
   `myst_enable_extensions` zu aktivieren; `myst_parser` in `extensions` reicht. Das
   erste `conf.py`-Draft hat das überdacht.
6. **stogger-Warnung wegen fehlendem `[dependency-groups].test`.** Harmlos (für das
   Experiment brauchen wir `pytest-stogger`/`pytest-structlog` nicht), aber sie
   taucht im pytest-Output auf. Bei Bedarf mit `filterwarnings` stumm schalten.

### Was es sichert, was Sybil nicht sichern kann

Visueller Renderer-Output. Die exakten Bytes, die stogger auf stderr schreibt:
Level-Tags, Eventnamen, strukturierte kv-Paare, der von `format_exc_info` doppelt
gerenderte `exception:`-Block. Genau die Drift-Klasse in `output_gallery.md`.

## Experiment 3 — PEP-723 Standalone-Demo

### Konzept

[PEP-723](https://peps.python.org/pep-0723/) erlaubt Inline-Metadaten in einem
Python-Script: Ein Kommentarblock `# /// script` … `# ///` deklariert
`requires-python` und `dependencies`. `uv run demo.py` baut daraus ein ephemäres Venv,
installiert die Deps, führt das Script aus und cacht das Venv pro Script-Hash. Für
den User: ein Befehl, kein `pip install`, kein `git clone`, kein Venv-Tanz.

### Setup im Experiment

`exp3-pep723/demo.py` (vollständig):

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "stogger @ file:///stogger",
#     "structlog",
# ]
# ///
"""Stogger demo script — runnable via `uv run demo.py`."""

import stogger
import structlog

stogger.init_logging(
    logdir=None,
    log_to_console=True,
    syslog_identifier="demo",
)

log = structlog.get_logger("demo")

# Log levels
log.debug("debug-event", detail="visible-only-in-verbose")
log.info("info-event", user="alice")
log.warning("warning-event", threshold=90)
log.error("error-event", reason="something failed")

# _replace_msg
log.info(
    "login",
    _replace_msg="User {user} logged in from {ip}",
    user="bob",
    ip="10.0.0.1",
)

# log.exception with full traceback
try:
    raise ValueError("demo failure")
except ValueError:
    log.exception("demo-exception", stage="pep723-test")

print("=== Demo finished ===")
```

Die kritische Zeile ist `"stogger @ file:///stogger"` — PEP-508-Form mit
`file://`-Schema.

### Funktionierender Aufruf

```
uv run demo.py
```

**Exit 0.** Erste Auflösung in 20 ms, zweite+ Runs instant aus dem Cache (kein
Install-Banner, kein Lockfile). Ausgabe (stderr, ANSI-stripped):

```
2026-06-04T15:47:02Z I systemd-journal-active         Systemd journal logging active
2026-06-04T15:47:02Z I info-event                     user='alice'
2026-06-04T15:47:02Z W warning-event                  threshold=90
2026-06-04T15:47:02Z E error-event                    reason='something failed'
2026-06-04T15:47:02Z I login                          User bob logged in from 10.0.0.1
2026-06-04T15:47:02Z E demo-exception                 exception_class='builtins.ValueError' exception_msg='demo failure' exception_traceback='Traceback (most recent call last):\n  File "/stogger/.agents/tmp/experiments/exp3-pep723/demo.py", line 37, in <module>\n    raise ValueError("demo failure")\nValueError: demo failure' stage='pep723-test'
exception: Traceback (most recent call last):
exception:   File "/stogger/.agents/tmp/experiments/exp3-pep723/demo.py", line 37, in <module>
exception:     raise ValueError("demo failure")
exception: ValueError: demo failure
```

stdout: `=== Demo finished ===`.

### Verdict

**Funktioniert ohne jede Reibung.** Die PEP-508-Form `"stogger @ file:///stogger"`
wurde von uv 0.11.17 unverändert akzeptiert; kein `#egg=stogger`-Fragment nötig.
Alle Renderer-Features sind sichtbar: Level-Tags, Eventnamen, kv-Paare,
`_replace_msg`-Expansion, `log.exception()` mit beiden Wegen (strukturiertes Feld +
`exception:`-Block), systemd-Auto-Detection. Vier Notizen, keine davon blockiert:

1. **`requires_python`-Mismatch.** stoggers `pyproject.toml` verlangt `>=3.13`, der
   PEP-723-Block im Spec sagt `>=3.11`. uv löst korrekt (die obere Schranke gewinnt,
   also Python 3.13.x im ephemären Venv). Inline-`requires-python` ist ein Floor,
   kein Constraint; das path-dep eigene `requires-python` wird zusätzlich
   durchgesetzt.
2. **Absolute `file:///stogger`-Pfade sind host-spezifisch.** Das funktioniert nur auf
   Maschinen, die stogger exakt dort ausgecheckt haben. Für eine öffentliche Demo
   bevorzugt man (a) PyPI-Pin nach Veröffentlichung, (b) `git+https://…`-URL, oder
   (c) relative `file://`-URLs. Relative Pfade in PEP-723 sind per Spec erlaubt, wurden
   in diesem Experiment aber nicht geprüft.
3. **Kein Lockfile.** PEP-723-Scripts sind lockfile-frei; uv cachet pro Script-Hash.
   Reproduzierbarkeit hängt also am path-dep, nicht an einer Pin-Datei.
4. **systemd-Auto-Detection.** Auf dieser Maschine (systemd-Linux) wird
   `systemd-journal-active` emittiert. Auf macOS oder nicht-systemd-Linux fällt der
   Journal-Renderer stillschweigend auf Console-only zurück (verifiziert per
   Code-Inspection von `SystemdMode.AUTO`, nicht per Re-Run auf non-systemd-Host).

### Was es sichert

Onboarding-Pfad: ein neuer User kann die Demo mit einem einzigen Kommando starten und
echte stogger-Ausgabe sehen. Kein `pip install`, kein Venv, kein clone-and-install.

## Synthese: die drei Patterns ergänzen, konkurrieren nicht

Die drei Experimente sichern jeweils eine **eigene** Drift-Klasse:

- **Sybil** sichert Inline-Code-Drift: Markdown-`python`-Blöcke, in denen eine API
  gezeigt wird.
- **Snapshot + `{literalinclude}`** sichert Renderer-Output-Drift: Gallery-Sections,
  die "so sieht stderr aus" versprechen.
- **PEP-723** sichert Onboarding-Friction: ein funktionierendes zero-install-Demo.

Nur eins zu übernehmen lässt eine Lücke. Speziell: Sybil ohne Snapshot hilft nicht bei
dem konkreten Drift in `output_gallery.md:122-131`, weil der drifted Block kein
ausführbarer Python-Code ist, sondern beschreibender Beispiel-Output.

## Empfohlene Adoptions-Reihenfolge

1. **Exp 2 zuerst in Produktion.** Löst den akuten Drift-Bug in
   `output_gallery.md:122-131`. Pfad: pytest-Fixture + `docs/_generated/` +
   `{literalinclude}`. Bricht den Doc-Lüge-Zyklus direkt.
2. **Exp 3 parallel.** `exp3-pep723/demo.py` ist bereits produktionstauglich. Kann
   als `examples/demo.py` ohne Risiko übernommen werden.
3. **Exp 1 danach.** Sobald Exp 2 steht, kommt Sybil ins echte `docs/conftest.py`.
   Kleiner Footprint (3 Dateien im nixflow-Referenz-Setup), kein Risiko, schließt die
   Inline-Code-Drift-Lücke.

## Die Zeitstempel-Frage (offene Entscheidung)

Das kombinierte Pipeline (PEP-723-Demo als Capture-Source für das Snapshot-Golden-File,
das per `{literalinclude}` in der Doku landet) hat eine offene Design-Frage: Wie wird
der Zeitstempel behandelt, den stogger in jeder Log-Zeile emittiert?

### Abgewogene Optionen

| Option | Konzept | Pro | Contra |
|---|---|---|---|
| **A — `freezegun`** | Test wickelt Demo-Run in `freezegun.freeze_time(…)` ein; stogger emit-t einen fixen Zeitstempel. | Kein API-Wachstum. Golden File ist menschenlesbar. Doku sieht "echt" aus. | Test-only-Dep kommt hinzu. |
| **B — `<TIMESTAMP>`-Platzhalter** | Zeitstempel zu `<TIMESTAMP>` normalisieren (was Exp 2 aktuell macht). | Keine Extra-Dep. | Doku zeigt `<TIMESTAMP>` statt echtem Zeitstempel — wirkt weniger lebensecht. |
| **C — stogger-`force_timestamp`-Config** | Config-Knopf, um einen fixen Zeitstempel zu erzwingen. | Am flexibelsten. | API-Wachstum nur für Testzwecke — verletzt CODEX Art. 7 (convention over configuration). Ablehnen. |
| **D — Hybrid** | Golden File hat echten Beispiel-Zeitstempel, Regex-Assertion mit Platzhalter. | Doku sieht echt aus, Test ist deterministisch. | Zwei verschiedene Artefakte (Test-File ≠ Doc-File). Meh. |

### Aktuelle Empfehlung

**Option A (`freezegun`).** Test-only-Dep, kein API-Wachstum, menschenlesbares Golden
File. Der Beispielzeitstempel `2026-06-01T17:19:01Z` wird bereits in
`output_gallery.md` als Platzhalter durchgehend verwendet — er würde schlicht zum
"echten" Frozen-Time-Zeitstempel werden.

Path-Normalisierung ist ungeachtet der Zeitstempel-Strategie weiter nötig, weil
Traceback-Pfade je nach Checkout-Ort variieren. Ließe sich lösen, indem das Demo an
einer deterministischen In-Repo-Position liegt (`examples/demo.py`).

### Decision Pending

User hat Option A noch nicht bestätigt. Implementierung kann erst starten, wenn das
entschieden ist.

## Vorgeschlagenes End-to-End-Pipeline (unter Option A)

```
examples/demo.py                         (PEP-723-runnable, auch standalone nutzbar)
tests/test_doc_outputs.py::test_demo_output_matches_golden
  → freezegun.freeze_time("2026-06-01T17:19:01Z")
  → subprocess.run([uv, "run", "examples/demo.py"], capture_stderr=True)
  → normalize_paths(stderr)
  → assert == tests/golden/demo_output.txt
tests/golden/demo_output.txt             (committed, deterministisch)
docs/user/output_gallery.md
  → {literalinclude} ../../tests/golden/demo_output.txt :language: text
```

Drift-Handling: Wenn stoggers Renderer sich ändert, schlägt pytest an (stderr ≠
Golden). Dev prüft, läuft `pytest --snapshot-update` (oder manuelles Overwrite), Sphinx
 zeigt neuen Output in der Doku. Der Commit enthält Code + aktualisiertes Golden File.

## Sofort-Fix offen

`docs/user/output_gallery.md:122-131` (Exception Logging Section) ist aktuell
gedriftet. Zeigt pre-2026.6.x-Output (keine `kwargs=`, kein `exception:`-Block).
Zwei Wege:

- **Manueller Stopgap-Edit.** Niedriger Aufwand, behebt das Symptom, verhindert
  Wiederholung nicht.
- **Warten auf Exp-2-Adoption.** Höherer Aufwand, eliminiert die Drift-Klasse
  konstruktiv.

## Quellen und Reproduktion

Alle Experiment-Artefakte liegen unter `/stogger/.agents/tmp/experiments/`:

- `exp1-sybil/` — Sybil-Wiring + Sample-Doc + `RESULT.md`
- `exp2-snapshot/` — Snapshot-Pipeline + Sphinx-Config + `RESULT.md`
- `exp3-pep723/` — PEP-723-Demo-Script + gecapturete Logs + `RESULT.md`

Jedes `RESULT.md` enthält den vollständigen wörtlichen Output, alle Reibungspunkte und
die Reproduktionskommandos.

Referenz: nixflow (`/srv/s-dev/git/nixflow/`) nutzt das Sybil-Pattern in
`docs/conftest.py` und hat in `tests/helpers.py` die Normalisierungsfunktionen
(`strip_ansi`, `normalize_timestamps`, `normalize_paths`), die für Exp 2 portiert
wurden. stogger selbst portiert damit indirekt ein nixflow-Muster zurück — sinnvoll,
weil nixflow es bereits im Produktionseinsatz hat.

## Adoption Scope: 3 Experiment Conversions

Dieser Abschnitt dokumentiert drei autonome Experimente, die das Potential von
`pytest-patterns` an realen Schwachstellen im stogger-Test-Bestand validieren. Jedes
Experiment wurde von einem unabhängigen `@general`-Subagenten durchgeführt, der sich
selbst ein Beispiel aus der Schwachstellen-Liste ausgesucht und eine lauffähige
Conversion gebaut hat. Source-of-Truth sind die Marker-Files `tests/experiments/.EXP0*_CHOICE`
(jede enthält den Original-Dateipfad + Zeilenbereich) und die jeweiligen Testfiles.

### Experiment 01: Exception-Rendering

**Original-Schwachstelle:** `tests/test_e2e_user_perspective.py:239-260`
(`test_exception_renders_traceback_on_stderr`)

**Schwäche:** Vier disjunkte Substring-Assertions (`"db-connect-failed"`,
`"ConnectionError"`, `"database connection refused"`, `"db.example.com"`) prüfen nur,
dass diese Substrings *irgendwo* im stderr stehen. Der menschenlesbare Traceback-Block
(`exception: Traceback (most recent call last): …`) ist komplett ungetestet — ein
Regression, der den Renderer für `log.exception()` stillschweigend entfernt, würde
unbemerkt bleiben.

**Neuer Test:** `tests/experiments/test_exp01_exception_traceback.py`

**Was jetzt asserted wird, was vorher unsichtbar war:**

- **KV-Zeile in fester Reihenfolge** via `in_order`: Eventname, dann `exception_class`,
  `exception_msg`, `exception_traceback` (escaped-newline content), dann `host=` —
  alles auf einer Zeile. Ersetzt vier freischwebende Substrings.
- **Multi-line `exception:`-Traceback-Block** via `continuous`: Headerzeile, mind. eine
  Frame-Zeile, finale `ConnectionError: …`-Zeile, lückenlos. Genau dieser Block fehlte
  im Original komplett.
- **Sektionen-Reihenfolge** explizit: KV-Zeile VOR Traceback-Block, nicht umgekehrbar.
- **Init-Banner optional**: `systemd-journal-active` darf auftauchen, muss aber nicht —
  Test bleibt grün auf Nicht-systemd-Hosts.

### Experiment 02: Output Sections Rendering

**Original-Schwachstelle:** `tests/test_core.py:305-335`
(`TestRenderOutputSections.test_render_output_sections_all_types`)

**Schwäche:** 13 `assert "..." in output` Substring-Checks testen
`ConsoleFileRenderer._render_output_sections`. Rund die Hälfte ist tautologisch
(`"out" ⊂ "stdout"`, `"err" ⊂ "stderr"`, `"exception" ⊂ "exception_traceback"`,
`"stack" ⊂ "stack trace here"`). Section-Reihenfolge wird nicht geprüft — der
Renderer könnte Sections vertauschen und der Test würde noch grün bleiben. Die Position
des `"=" * 79` Separators (zwischen `stack` und `exception_traceback`) ist ebenfalls
ungetestet.

**Neuer Test:** `tests/experiments/test_exp02_render_output_sections.py`

**Was jetzt asserted wird, was vorher unsichtbar war:**

- **End-to-End-Sektionenreihenfolge** in einem `in_order`-Match:
  `cmd_output_line → _output → _raw_output (prefix: ty) → stdout → stderr → stack →
  "="*79 → exception_traceback`.
- **Label-Suffixe** strukturell gefordert: `out: standard out`, `err: standard error`,
  `stack: …`, `exception: …` als Zeilenanfänge statt als freischwebende Substrings,
  die auch in generischen Präfix-Wrappern matchen könnten.
- **Separator-Position** verankert: `"=" * 79` liegt *zwischen* `stack` und
  `exception_traceback`, nicht irgendwo im Output.
- **Toleranz gegenüber Präfix-Wrappern**: optionale Zeilen wie `out:`, `err:` und
  Leerzeilen werden toleriert, ohne den harten Content-Contract aufzuweichen.

### Experiment 03: Multi-Event Ordering und Console-File-Parity

**Original-Schwachstelle:** `tests/test_e2e_single_module_app.py:38-77`
(`test_single_module_app_console_and_file`)

**Schwäche:** Drei Events mit aufsteigendem Severity (`info → warning → error`) werden
via fünf unabhängiger Substring-Checks pro Sink geprüft. Drei Aspekte bleiben unsichtbar:

1. **Reihenfolge** — für eine Logging-Library ist Event-Reihenfolge der Vertrag; der
   Originaltest könnte `error` vor `warning` ausgeben und weiterhin grün sein.
2. **Same-line Binding** — `assert "version" in captured.err` prüft nur, dass das Wort
   *irgendwo* steht; wäre `version=` von der `app-started`-Zeile abgetrennt, würde der
   Test noch grün.
3. **Console/File-Parity** — der Test behauptet im Docstring "file output should contain
   the events", prüft aber zwei Sinks mit unabhängigen Assertions. Eine Divergenz zwischen
   Console und File (andere Reihenfolge, fehlendes KV) bleibt unsichtbar.

**Neuer Test:** `tests/experiments/test_exp03_event_ordering.py` (plus
`test_exp03_failure_demo.py` als `xfail`-Demo des Failure-Reports)

**Was jetzt asserted wird, was vorher unsichtbar war:**

- **Drei-Event-Reihenfolge** in einem `in_order`-Match: `app-started → disk-space-low →
  connection-failed` (zusammen mit dem Severity-Tag `I → W → E`).
- **KV-Bindings an Event-Zeile gebunden** — `version='1.0.0'`, `percent=12`, `host=…`,
  `port=…` stehen auf derselben Zeile wie der jeweilige Eventname, nicht "irgendwo".
- **Console-File-Parity durch geteiltes Pattern** — dasselbe `Pattern`-Objekt
  (`_build_event_pattern`) wird gegen ANSI-stripped Console-Output und File-Content
  gleichermaßen asserted. Jede Divergenz schlägt mit per-line-Diff an.
- **Negative Assertions** via `refused`: kein `Traceback (most recent call last)`, kein
  `CRITICAL`, kein `FATAL` — diese Keywords dürfen in einem info/warning/error-Triad
  nicht vorkommen.
- **Failure-Diagnose** in `test_exp03_failure_demo.py` (`xfail-strict`) dokumentiert den
  Failure-Report bei vertauschter Reihenfolge: jede Output-Zeile wird mit Status-Emoji
  und zuständigem Pattern-Namen annotiert
  (`🟢=EXPECTED | ⚪️=OPTIONAL | 🟡=UNEXPECTED | 🔴=REFUSED/UNMATCHED`).

### Konvergente Erkenntnisse (alle 3 Experimente unabhängig bestätigt)

1. **Failure-Reporting exzellent** — per-line Emoji-Status (🟢/⚪️/🟡/🔴), benannte
   Patterns im Output, separate "unmatched expected"-Sektion. Renderer-Drift-Diagnose
   sinkt von Minuten auf Sekunden.

2. **`patterns`-Fixture auto-injected** — Zero Setup, Plugin-Discovery funktionierte
   out-of-the-box via `[tool.uv.sources]`-path-dep auf `/srv/s-dev/git/pytest-patterns`
   plus Eintrag in `[dependency-groups].test`.

3. **ANSI-Stripping ist die einzige wirkliche Lücke** — alle 3 Experimente brauchten
   denselben ~2-Zeilen-Helper (`_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m");
   _ANSI_RE.sub("", s)`). Die `normalize`-Roadmap im `pytest-patterns`-README würde
   genau das lösen. Konkreter Contribution-Ansatz für upstream.

4. **`...`-Wildcard ist non-greedy pro Zeile** — annotiert als `^.*?…$`. Spezifität
   wichtig: ein zu kurzes Token wie `...I...` allein matcht zufällige I-Vorkommen;
   mit umgebendem Kontext (`...I...systemd-journal-active...`) wird es eindeutig.

### Bug-Fund in pytest-patterns

Experiment 03 dokumentiert im Docstring von `_build_event_pattern`: `pattern_lines`
stript entgegen seinem Source-Kommentar KEINE Indentation aus Triple-quoted-Patterns.
Der Kommentar behauptet Indentation-Stripping, der Code filtert nur Leerzeilen. Führende
Whitespace in mehrzeiligen Patterns wird als signifikant interpretiert und schlägt still
fehl. Wert ein PR upstream.

### Kosten-Nutzen-Bilanz

| Experiment | Original-LOC | Neue-LOC | Assertions vorher → nachher | Neue Properties |
|---|---|---|---|---|
| 01 Exception | 22 | 125 | 4 substring → 1 `in_order` + 1 `continuous` + 1 `merge` | Traceback-Shape, KV-Reihenfolge, optional journal |
| 02 Sections  | 31 | 120 | 13 substring (~½ tautologisch) → 1 `in_order` + 3 `optional` | Section-Reihenfolge, Separator-Position, Label-Struktur |
| 03 Ordering  | 40 | 194 (+ 73 demo) | 5+3 substring → 3× geteiltes `in_order` + 3 `refused` + `optional` | Event-Reihenfolge, KV-Same-line, Console-File-Parity, Negative |

**Netto:** Moderater LOC-Zuwachs (~3× original) für einen kategorischen Qualitäts-Sprung —
jede der ursprünglichen Schwachstellen (Reihenfolge, Co-occurrence, Parity,
Negative-Assertion) ist jetzt mechanisch gepinnt und liefert bei Drift einen präzisen
per-line-Diagnose-Report statt einer nichtssagenden `AssertionError`.

### Adoption-Status

- 3/3 Experimente grün (`uv run pytest tests/experiments/test_exp0*.py -v` = 0;
  `test_exp03_failure_demo.py` ist `xfail-strict` und liefert wie erwartet den
  Failure-Report).
- Keine Kollisionen — drei disjunkte Examples aus dem Bestand.
- `pytest-patterns` installiert als path-dep via `[tool.uv.sources]` in `pyproject.toml`
  (Zeile 211), registriert in `[dependency-groups].test` (Zeile 40).
- Files unter `tests/experiments/` werden von default `pytest`-Runs eingesammelt
  (akzeptiert für die Experiment-Phase; später via `tests/experiments/conftest.py` mit
  `collect_ignore` abtrennbar, sobald die Konversion in die echten Testfiles migriert
  ist).

## Status

- Forschung abgeschlossen: alle drei Experimente gegangen, alle drei Patterns viable.
- Entscheidung offen: Option A/B/C/D für Zeitstempel-Handling.
- Nächste Aktion: User entscheidet Zeitstempel-Option, dann Phase-1/Phase-2-Implementierung.
- Die drei Experimente sind Throwaway — sie liegen unter `.agents/tmp/` und werden
  durch die echte Produktion-Implementierung ersetzt.
