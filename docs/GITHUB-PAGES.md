# Automatyczna strona instalacyjna (hubertuhubertu.github.io)

## Co jest zautomatyzowane

| Co | Jak |
|----|-----|
| **Aktualizacje ChaturbateTV w Kodi** | Push do `repository.dobbelina` → `chaturbatetv-addons.xml` + zip addonu. Użytkownicy z już zainstalowanym repo **nie robią nic**. |
| **Strona instalacyjna + zip repozytorium** | Workflow `.github/workflows/deploy-pages.yml` → buduje zip + `index.html` → wrzuca na `HubertuHubertu.github.io`. |

Workflow uruchamia się gdy zmienisz `repository.chaturbatetv/` (np. podbijasz `version` w `addon.xml`) lub ręcznie: **Actions → Deploy Kodi install page → Run workflow**.

## Jednorazowa konfiguracja (ok. 5 min)

### 1. Utwórz puste repo strony

Na GitHubie: **New repository**

- Nazwa: `HubertuHubertu.github.io`
- Public
- Może być pusty (README wystarczy)

Włącz **Settings → Pages → Deploy from branch → master → / (root)**.

### 2. Token do publikacji

1. GitHub → **Settings** (konta, nie repo) → **Developer settings** → **Personal access tokens** → **Tokens (classic)**.
2. **Generate new token (classic)**.
3. Zakres: zaznacz **`repo`** (pełny dostęp do prywatnych repozytoriów — potrzebny do push na drugie repo).
4. Skopiuj token (pokazuje się raz).

### 3. Sekret w repozytorium addonów

W repo **`HubertuHubertu/repository.dobbelina`**:

**Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|------|--------|
| `PAGES_DEPLOY_TOKEN` | wklej token z kroku 2 |

### 4. Pierwsze uruchomienie

Push na `master` (albo **Actions → Deploy Kodi install page → Run workflow**).

Po ~1 min sprawdź: https://hubertuhubertu.github.io/

## Późniejsze wydania

Gdy chcesz nowy zip instalacyjny repozytorium (np. zmiana URL w `repository.chaturbatetv/addon.xml`):

1. Podbij `version` w `repository.chaturbatetv/addon.xml` (np. `1.0.0` → `1.0.1`).
2. Commit + push na `master`.
3. GitHub Actions sam zbuduje `repository.chaturbatetv-1.0.1.zip` i zaktualizuje `index.html`.

**Nie musisz** ręcznie edytować strony ani zipów.

Dla samej aktualizacji **pluginu** ChaturbateTV wystarczy podbić wersję w `plugin.video.chaturbate/addon.xml` i `chaturbatetv-addons.xml` — strona Pages **nie jest wtedy wymagana**.
