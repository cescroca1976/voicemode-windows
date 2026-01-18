# Voice-Mode MCP Server - Windows 11 Edition

🎤 **Servidor MCP de mode de veu per a Antigravity amb suport complet per Windows 11**

Aquest és un fork modificat de [mbailey/voicemode](https://github.com/mbailey/voicemode) amb correccions específiques per a Windows 11.

## ✨ Característiques

- ✅ **Compatible amb Windows 11** - Totes les dependències funcionen sense compilació
- ✅ **Instal·lació automàtica** - Script PowerShell que ho configura tot
- ✅ **Python 3.12** - Versió estable amb suport complet
- ✅ **FFmpeg integrat** - Instal·lació automàtica via Chocolatey
- ✅ **Singleton pattern** - Evita problemes de doble-importació
- ✅ **Integració Antigravity** - Configuració automàtica

## 🚀 Instal·lació Ràpida

### Prerequisits

- Windows 11
- [Chocolatey](https://chocolatey.org/install) (per FFmpeg)
- [uv](https://github.com/astral-sh/uv) (gestor de paquets Python)
- Clau API d'OpenAI

### Pas 1: Clonar el Repositori

```powershell
cd C:\Users\$env:USERNAME
git clone https://github.com/TU_USUARIO/voicemode-windows.git
cd voicemode-windows
```

### Pas 2: Configurar API Key

Edita el fitxer `config.env` i afegeix la teva clau API d'OpenAI:

```env
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXX
```

### Pas 3: Executar l'Instal·lador

```powershell
.\install.ps1
```

Aquest script farà:
1. ✅ Instal·lar Python 3.12
2. ✅ Instal·lar FFmpeg
3. ✅ Crear entorn virtual
4. ✅ Instal·lar dependències
5. ✅ Configurar Antigravity
6. ✅ Verificar la instal·lació

### Pas 4: Reiniciar Antigravity

Tanca i torna a obrir Antigravity. El servidor `voicemode` hauria d'aparèixer en **verd** amb les eines:
- `converse` - Conversa per veu
- `service` - Gestió de serveis
- `internal_list_tools` - Llista d'eines

## 🎯 Ús

### Activar Mode de Veu

A Antigravity, simplement diu:
```
Activa el mode de veu
```

O utilitza directament l'eina `converse`:
```
Utilitza l'eina converse per escoltar-me
```

### Configuració Avançada

Edita `C:\Users\TU_USUARIO\.gemini\antigravity\mcp_config.json` per personalitzar:

```json
{
  "mcpServers": {
    "voicemode": {
      "env": {
        "VOICEMODE_DEBUG": "true",
        "VOICEMODE_DISABLE_SILENCE_DETECTION": "true",
        "VOICEMODE_DEFAULT_LISTEN_DURATION": "10.0",
        "VOICEMODE_AUDIO_FEEDBACK": "true"
      }
    }
  }
}
```

## 🔧 Modificacions Respecte a l'Original

### Dependències Actualitzades
- `simpleaudio` → `simpleaudio-patched` (wheels per Windows)
- `webrtcvad` → `webrtcvad-wheels` (wheels per Windows)

### Codi Modificat
- **Singleton MCP** (`mcp_instance.py`) - Evita doble-importació
- **Windows compatibility** - `fcntl` i `resource` opcionals
- **Imports actualitzats** - Tots els mòduls usen el singleton

### Fitxers Nous
- `install.ps1` - Script d'instal·lació automàtic
- `verify.ps1` - Script de verificació
- `config.env` - Plantilla de configuració
- `mcp_config.template.json` - Plantilla per Antigravity

## 📚 Documentació

- [Guia d'Instal·lació Completa](docs/INSTALLATION.md)
- [Configuració](docs/CONFIGURATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Arquitectura](docs/ARCHITECTURE.md)

## 🐛 Problemes Comuns

### El servidor surt en vermell
```powershell
# Verificar instal·lació
.\verify.ps1

# Reinstal·lar
.\install.ps1 -Force
```

### No sento el chime
Comprova que `VOICEMODE_AUDIO_FEEDBACK` està a `true` a la configuració.

### Error "No module named..."
```powershell
# Reinstal·lar dependències
cd voicemode-windows
.\.venv\Scripts\python.exe -m pip install -e .
```

## 🤝 Contribucions

Aquest és un fork amb modificacions específiques per Windows. Per contribuir:

1. Fork aquest repositori
2. Crea una branca (`git checkout -b feature/millora`)
3. Commit els canvis (`git commit -am 'Afegeix millora'`)
4. Push a la branca (`git push origin feature/millora`)
5. Obre un Pull Request

## 📝 Llicència

Mateix que l'original: [Llicència del projecte original](https://github.com/mbailey/voicemode)

## 🙏 Agraïments

- [mbailey/voicemode](https://github.com/mbailey/voicemode) - Projecte original
- Comunitat d'Antigravity
- Tots els contribuïdors

## 📞 Suport

Si tens problemes:
1. Revisa la [documentació](docs/)
2. Comprova els [problemes comuns](#-problemes-comuns)
3. Obre un [issue](https://github.com/TU_USUARIO/voicemode-windows/issues)

---

**Fet amb ❤️ per a la comunitat d'Antigravity**
