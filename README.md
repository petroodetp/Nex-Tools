# Nex Tools

Outil Windows de la communauté Nexora pour nettoyer FiveM, les fichiers temporaires et le cache réseau.

## Fonctions

- **Clean Basic** : logs, crashes, cache, nui-storage, server-cache et server-cache-priv de FiveM.
- **Clean Advanced** : Clean Basic, plus le dossier citizen, le dossier Temp de l'utilisateur, Windows\Temp et Windows\Prefetch.
- **Network Clean** : flush DNS, réenregistrement DNS, cache NetBIOS et cache ARP.

Les chemins s'adaptent automatiquement au nom d'utilisateur Windows.

## Utilisation

1. Télécharge `NexTools.exe` dans l'onglet Releases.
2. Ferme FiveM.
3. Lance le programme (il demande les droits administrateur) et clique sur l'option voulue.

## Compilation

```
pip install -r requirements.txt
build.bat
```

Le résultat est dans `dist\NexTools.exe`.
