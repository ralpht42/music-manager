# music-manager

## Status
[![Last PR](https://github.com/ralpht42/music-manager/actions/workflows/build-pr.yml/badge.svg)](https://github.com/ralpht42/music-manager/actions/workflows/build-pr.yml)
[![Last Release](https://github.com/ralpht42/music-manager/actions/workflows/create-release.yml/badge.svg)](https://github.com/ralpht42/music-manager/actions/workflows/create-release.yml)
[![Build and Publish to GitHub Container Registry](https://github.com/ralpht42/music-manager/actions/workflows/build-release.yml/badge.svg)](https://github.com/ralpht42/music-manager/actions/workflows/build-release.yml)
[![CodeQL](https://github.com/ralpht42/music-manager/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/ralpht42/music-manager/actions/workflows/github-code-scanning/codeql)


## Beschreibung

... TODO ...

## Lokale Entwicklung

### Beschreibung

Dieses Programm ist in Docker verpackt und bietet mehrere Startoptionen, um den Entwicklungs- und Testprozess zu unterstützen. Während es möglich ist, das Programm lokal zu starten und die Abhängigkeiten über pip global oder in einer virtuellen Umgebung zu installieren, wird empfohlen, Docker zu verwenden, um die Abhängigkeiten zu verwalten und die Entwicklungsumgebung zu vereinfachen. Damit wird sichergestellt, dass der Code in einer Umgebung ausgeführt wird, die der Produktionsumgebung ähnelt.

### Voraussetzungen

- Docker

### Umgebungvariablen

Die folgenden Umgebungsvariablen müssen gesetzt werden, um das Programm auszuführen. Die Werte können in der Datei ".env" gesetzt werden. Die Datei ".env.example" enthält die erforderlichen Variablen und kann als Vorlage verwendet werden.

| Variable                | Beschreibung                                                     | Notwendig |
| ----------------------- | ---------------------------------------------------------------- | --------- |
| SECRET_KEY              | Geheimer Schlüssel die Session Verschlüsselung                   | Ja        |


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

Führen Sie die in VS-Code als Debug Task verwendete "Docker - Debug with hot-reloading" Funktion aus.
Hierbei wird ein zufälliger Port von VS-Code vergeben. Es ist die Hot-Reload-Modus verfügbar, d. h. Änderungen am Code werden sofort automatisch geladen und die Anwendung neu gestartet. Es können Breakpoints gesetzt und Variablenwerte am Breakpoint bearbeitet werden.
