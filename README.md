# music-manager

## Beschreibung

... TODO ...


## Lokale Entwicklung

### Beschreibung
Dieses Programm ist in Docker verpackt und bietet mehrere Startoptionen, um den Entwicklungs- und Testprozess zu unterstützen. Während es möglich ist, das Programm lokal zu starten und die Abhängigkeiten über pip global oder in einer virtuellen Umgebung zu installieren, wird empfohlen, Docker zu verwenden, um die Abhängigkeiten zu verwalten und die Entwicklungsumgebung zu vereinfachen. Damit wird sichergestellt, dass der Code in einer Umgebung ausgeführt wird, die der Produktionsumgebung ähnelt.

### Docker-Startoptionen
#### 1. Produktionsmodus (Gunicorn) - Lokaler Build
Um das Programm im Produktionsmodus zu starten, führen Sie den folgenden Befehl aus:

```bash
docker-compose up -d
```
Dies führt zu einem lokalen Build und erstellt ein "production" Image. Gunicorn wird als Server verwendet, um die Anwendung zu starten. Die Anwendung wird auf Port 8080 gestartet. Die Anwendung wird im Hintergrund ausgeführt. Um die Anwendung zu stoppen, führen Sie den folgenden Befehl aus:

```bash
docker-compose down
```

#### 2. Debugging-Modus - Lokaler Build (VS-Code)
Um das Programm im Debugging-Modus mit VS-Code zu starten, gibt es zwei Möglichkeiten:

##### 2.1. VS-Code Debug Task mit Docker Run
Führen Sie die in VS-Code als Debug Task verwendete "Docker Run - Debug (no hot-reloading)" Funktion aus.
Hierbei wird ein zufälliger Port von VS-Code vergeben. Es ist kein Hot-Reload-Modus verfügbar, d. h. Änderungen am Code werden nicht automatisch geladen. Es können Breakpoints gesetzt und Variablenwerte am Breakpoint bearbeitet werden.

##### 2.2. VS-Code Debug Task mit Docker Compose
Führen Sie die in VS-Code als Debug Task verwendete "Docker Compose - Debug (no hot-reloading)" Funktion aus.
Bei diesem Befehl wird der Port 8080 verwendet. Es ist kein Hot-Reload-Modus verfügbar, d. h. Änderungen am Code werden nicht automatisch geladen. Es können Breakpoints gesetzt und Variablenwerte am Breakpoint bearbeitet werden.

#### 3. Hot-Reload-Modus (Kein Debugging über VS-Code)
Für den Hot-Reload-Modus, der Änderungen am Code direkt durch erneutes Laden umsetzt, verwenden Sie:

```bash
docker-compose -f docker-compose.hot-reload.yml up --build
```
Diese Option eignet sich gut für schnelle Tests kleiner Codeänderungen. Zum Beispiel für das Anpassen einer Webseite. Hierbei ist zu beachten, dass der Hot-Reload-Modus nicht für das Debugging über VS-Code geeignet ist. Es kann kein Breakpoint gesetzt werden und es können keine Variablenwerte am Breakpoint bearbeitet werden.