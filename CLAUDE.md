# AlbionCreateImageBuild

Lib Python publique : images PNG de builds/compos Albion. Utilisée par `botDiscord` et `lilium-site` (installée par URL de tag dans leurs `requirements.txt`), mais **générique** : rien de propre à Lilium ici.

## Règles
- Aucun import du bot ni du site, aucune variable d'environnement ; dépendances = Pillow + aiohttp seulement.
- Rendu = fonctions pures (`render_build_image`, `render_compo_image`) qui reçoivent les icônes ; réseau uniquement dans `icons.py` / `aio.py`.
- Pas d'état global hors `default_fetcher()` ; couleurs → `Theme`, textes → `Labels` (FR + EN tenus à jour ensemble).
- Défauts (thème lilas, FR) = images de `tests/golden/` au pixel près. Changement de rendu voulu : `python tests/test_golden.py --update` et regarder les PNG.
- Assets uniquement dans `src/albion_create_image_build/assets/` ; icônes via `scripts/download_icons.py`.

## Workflow
- Tests (`.venv/Scripts/python -m pytest --cov`, couverture 100 %) + `ruff check .` avant tout commit ; README à jour si l'API change.
- Push direct sur `main`. Publier : bump `__version__` (semver), commit, `git tag vX.Y.Z`, `git push origin main --tags` → `release.yml` publie sur PyPI ; puis monter la version dans `botDiscord/requirements.txt` et `lilium-site/api/requirements.txt` (bot avant site).
