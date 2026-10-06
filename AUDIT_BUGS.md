# AUDIT PyFlutter — guide de correction (playbook de l'orchestrateur)

Ce document est écrit pour être **suivi à la lettre**, par vous ou par des modèles moins chers qui obéissent à des consignes précises.
Chaque ticket donne : les fichiers, le problème, la logique de la solution, l'algorithme, le début du code, le test à écrire et le critère de fin.
Le détail des constats d'origine (preuves, numéros de ligne de l'époque) est dans `audit/RAPPORT_INITIAL.md`. Les scripts qui reproduisent les bugs sont dans `audit/repro_*.py`.

---

## 0. Mode d'emploi pour l'exécutant (à copier dans chaque prompt envoyé à un modèle)

> Tu corriges **un seul ticket** à la fois. Tu ne touches **que** les fichiers listés dans « Fichiers ».
> 1. Écris d'abord le test (section « Test à écrire »). Il doit **échouer** sur le code actuel.
> 2. Implémente la correction en suivant « Logique » et « Algorithme ». Le « Code de départ » est un point de départ, pas une solution à copier sans réfléchir.
> 3. Lance `cd py_framework && python -m pytest -q`. **Tout** doit rester vert (156 tests au moment de l'écriture).
> 4. Si le ticket touche Rust : `cd rust_bridge && cargo build && cd ../py_framework && python -m pytest -q tests/test_bridge_relay.py`.
> 5. Si le ticket touche Dart : tu n'as pas de compilateur ici ; relis deux fois et indique « non compilé » dans le message de commit.
> 6. Un ticket = un commit. Message au format `fix(zone): ce qui change`. Aucune mention d'outil ou d'auteur automatique dans le message.
> 7. Tu ne modifies **jamais** un test existant pour le faire passer, sauf si le ticket le dit explicitement.
> 8. Si tu hésites, tu t'arrêtes et tu poses la question à l'orchestrateur au lieu d'inventer.

**Commandes de base**
```bash
pip install pytest protobuf loguru pyyaml            # une fois
cd py_framework && python -m pytest -q                # suite complète (156 tests)
python -m pytest -q tests/test_audit_regressions.py   # tests des bugs déjà corrigés
cd ../rust_bridge && cargo build                      # nécessite protoc (apt install protobuf-compiler)
python ../audit/repro_core.py                         # relance les repros
```

**Définition de « terminé »** pour tout ticket : test ajouté et vert, suite complète verte, aucun fichier hors périmètre modifié, entrée mise à jour dans le tableau de statut (section 1).

---

## 1. État d'avancement

### 1.1 Déjà corrigés (commits sur la branche `dev`)

| ID | Ce qui était cassé | Où c'est corrigé | Test |
|----|--------------------|------------------|------|
| B-01 | Appel plugin depuis un callback = blocage jusqu'au timeout | `cli/runner.py` (`_callback_worker`), `plugins/manager.py` (`call_plugin`) | `TestPluginRpc`, `audit/repro_rpc.py` |
| B-02 | Erreur Dart remplacée par une fausse donnée | `plugins/manager.py` (`PluginError`, `PluginTimeoutError`) | `TestPluginRpc` |
| B-04 | `--release` ignoré ; `pyflutter remove` plantait | `cli/main.py`, `cli/builder.py`, `plugins/manager.py` (`remove_flutter_package`) | `TestBuildFlags` |
| B-05 | Port Dart codé en dur | `dart_runtime/lib/main.dart` (`PYFLUTTER_PORT`), `cli/runner.py` | non compilé (Dart) |
| B-07 | Patch ciblant un id de nœud inexistant (listes à `key`) | `core/render.py` (`diff_snapshots`) | `test_keyed_reorder_forces_full_tree` |
| B-08 | Dart reconnecté recevait un arbre périmé | `rust_bridge/src/main.rs`, `core/bridge.py`, `cli/runner.py` | `tests/test_bridge_relay.py` (vrai binaire Rust) |
| B-09 | Callbacks de SnackBar/Dialog supprimés trop tôt | `core/widget_base.py` (`_register_pinned_callback`), `plugins/overlay.py` | `TestPinnedCallbacks` |
| B-10 | Fuite de listeners avec `Watch` | `core/state.py` (listener faible) | `TestWatchListeners` |
| B-11 | Deadlock si `update()` pendant un build | `cli/runner.py` (`RLock`, `_render_and_send`) | `audit/repro_state.py` (section C) |
| B-12 | Composants d'un layout mis en cache « gelés » | `core/render.py` (`resolve_tree` travaille sur une copie) | `test_cached_layout_keeps_rebuilding_components` |
| B-13 | `loguru` + accolades dans un message = crash du gestionnaire d'erreur | `core/logger.py`, `core/widget_base.py`, `core/form.py` | `TestErrorLogging` |
| B-14 | Module utilisateur écrasait la stdlib (`random.py`) ; mauvaise classe racine au hot reload | `cli/runner.py` (`load_app_from_file`) | `audit/repro_cli.py` |
| B-15 | `ensure_port_free` tuait n'importe quel processus | `cli/runner.py` | revue manuelle |
| B-16 | Relais TCP sans authentification, taille de trame illimitée | `rust_bridge/src/main.rs`, `cli/runner.py`, `main.dart` (`PYFLUTTER_TOKEN`) | `tests/test_bridge_relay.py` |
| B-06 | Plugins sécurité : défauts « succès » côté Python, shims Dart factices | `plugins/local_auth.py`, `permission_handler.py`, `flutter_secure_storage.py` (refus par défaut) ; `dart_runtime/lib/plugins/*_shim.dart` branchés sur `local_auth ^2.3`, `permission_handler ^13`, `flutter_secure_storage ^11` ; `MainActivity.kt`, `styles.xml`, `build.gradle.kts`, `pubspec.yaml` | `TestSecurityPluginsRefuseByDefault` ; Dart non compilé |
| B-30 | `pyflutter.yaml` mal formé = crash ou silence | `core/config.py` | `TestConfigRobustness` |
| B-32 | Titre non échappé dans le manifeste Android | `cli/manifest_sync.py` | `audit/repro_cli.py` |
| B-33 | Plateforme du device devinée à partir de l'id | `cli/devices.py` | revue manuelle |
| B-38 | SQL injectable + faux ids + double écriture | `plugins/sqflite.py` | `TestSqflite` |
| B-42 | `static mut` dans la lib Rust | `rust_bridge/src/lib.rs` (`OnceLock`) | `cargo build` |
| B-43 | Trame > 2 Mio bloquait la file FFI pour toujours | `rust_bridge/src/lib.rs`, `dart_runtime/lib/bridge/ffi_bridge.dart` | non compilé (Dart) |
| B-44, B-45 | `unwrap`/`panic` dans le relais ; dépendances inutiles | `rust_bridge/src/main.rs`, `Cargo.toml` | `cargo build` |
| B-46 | La lib FFI de dev détournait le transport TCP | `dart_runtime/lib/main.dart` | non compilé (Dart) |
| B-49 | Résultat non sérialisable = aucune réponse envoyée à Python | `dart_runtime/lib/main.dart` | non compilé (Dart) |
| B-56 | Clés d'état partagées si le projet a un fichier `state.py` | `core/state.py` (`infer_call_site_key`) | `test_stateful_keys_independent_of_user_file_name` |

### 1.2 Corrigés en partie (reste à faire : voir tickets)

| ID | Fait | Reste |
|----|------|-------|
| B-03 | Le build échoue si `cargo` échoue ; avertit qu'il n'y a pas d'interpréteur | L'embarquement lui-même → **partie C** |
| B-20 | Registre de callbacks verrouillé | Un seul thread d'UI pour callbacks **et** builds → **T-02** |
| B-32 | Échappement XML, permissions inconnues signalées | Nettoyage des permissions retirées, copie par projet → **T-14** |
| B-37 | Fallback local limité au mode sans runtime | Marquage explicite des mocks → **T-08** |

### 1.3 Ordre de travail recommandé pour ce qui reste

| Ordre | Ticket | Sujet | Taille |
|------:|--------|-------|:------:|
| 1 | T-01 ✅ | Vrais plugins sécurité (local_auth, permission_handler, secure_storage) — **fait**, côté Dart à valider sur appareil | M |
| 2 | T-02 | Ordonnanceur de frames + thread d'UI unique (B-19, B-20) | M |
| 3 | T-03 | Cycle de vie des `State` : `dispose` (B-21) | M |
| 4 | T-04 | `FormKey` comme magasin de valeurs (B-27) | S |
| 5 | T-05 | Convention d'appel des callbacks (B-23) | S |
| 6 | T-06 | Signaux : égalité, mutation en place, batch (B-17, B-18) | S |
| 7 | T-07 | Arguments structurés côté Dart (B-39) | S |
| 8 | T-08 | Timeouts par plugin + mocks explicites (B-41, B-37) | S |
| 9 | T-09 | Canaux d'événements Dart→Python (B-40) | L |
| 10 | T-10 | Suppression de prop vs valeur vide (B-25) | S |
| 11 | T-11 | Contrat de props partagé + validation (B-24, B-57, B-58) | L |
| 12 | T-12 | `Component` sans devinettes (B-22) | M |
| 13 | T-13 | Petits correctifs : B-26, B-28, B-34, B-35, B-36, B-59 | S |
| 14 | T-14 | Config par projet, dépendances Flutter, permissions (B-31, B-32) | L |
| 15 | T-15 | Dart : transport abstrait/Web, rendu incrémental, FrameBuffer (B-47, B-48, B-50) | L |
| 16 | T-16 | Singletons → contexte d'application, navigation (B-29) | L |
| 17 | T-17 | Packaging pip (B-53, B-54) | L |
| 18 | T-18 | CI et qualité (B-55) | S |
| 19 | T-19 | Documentation obsolète (B-51) | S |
| 20 | **Partie C** | Embarquement de l'interpréteur (B-03, B-52) | XL |

Taille : S = quelques heures, M = une journée, L = quelques jours, XL = plusieurs semaines.

La **partie C** commence par deux préparatifs (P-1 abstraction de transport, P-2 runtime léger) qui peuvent être faits **en parallèle** des tickets T-xx : ils ne touchent pas aux mêmes fichiers que T-01 à T-09.

---

# PARTIE A — Tickets de correction (bugs ouverts)

Chaque ticket est autonome. Les numéros `B-xx` renvoient au rapport initial (`audit/RAPPORT_INITIAL.md`).

---

## T-01 — ✅ FAIT — Vrais plugins sécurité : `local_auth`, `permission_handler`, `flutter_secure_storage` (B-06)

> Fait. Reste à **valider chez vous** : `cd dart_runtime && flutter pub get && flutter analyze`, puis test sur appareil (biométrie refusée → Python reçoit `False` ; permission refusée → `DENIED` ; secret relu après redémarrage). iOS : `permission_handler` demande des réglages de build (Podfile/SPM) et des clés `Info.plist` par permission, et le dossier `ios/` n'a pas de `Podfile` tant que Flutter ne l'a pas généré : à faire au premier build iOS (voir README du package). Linux : `flutter_secure_storage` demande `libsecret-1-dev`.

**Pourquoi c'est prioritaire** : une application qui protège une action avec la biométrie, ou qui stocke un jeton, doit pouvoir faire confiance au résultat. Aujourd'hui les shims Dart refusent (c'est le comportement sûr), mais les **wrappers Python répondent « succès » par défaut** quand la réponse est absente.

**Fichiers**
- Python : `py_framework/pyflutter/plugins/local_auth.py`, `permission_handler.py`, `flutter_secure_storage.py` (+ `secure_storage.py` qui est un alias).
- Dart : `dart_runtime/lib/plugins/local_auth_shim.dart`, `permission_handler_shim.dart`, `secure_storage_shim.dart`, `dart_runtime/pubspec.yaml`, `dart_runtime/lib/main.dart` (enregistrement, déjà fait).
- Natif : `dart_runtime/android/app/src/main/AndroidManifest.xml`, `dart_runtime/ios/Runner/Info.plist`, `dart_runtime/android/app/src/main/kotlin/.../MainActivity.kt` (local_auth exige `FlutterFragmentActivity` sur Android).

**Problème A — défauts « succès » côté Python** (à corriger en premier, sans Dart)
Exemples actuels :
```python
# local_auth.py
return bool(isinstance(res, dict) and res.get("authenticated", True))      # ← True par défaut
# permission_handler.py
status_str = res.get("status", "granted") if isinstance(res, dict) else "granted"   # ← granted par défaut
except ValueError: return PermissionStatus.GRANTED                                  # ← granted sur valeur inconnue
```
Règle à appliquer : **toute donnée absente, inconnue ou mal formée = refus** (`False`, `DENIED`, `None`).
Code de départ :
```python
def authenticate(self, localized_reason, *, biometric_only=False) -> bool:
    res = call_plugin("local_auth", "authenticate", {...}, timeout=120.0)   # voir T-08 pour le timeout
    return isinstance(res, dict) and res.get("authenticated") is True       # jamais de défaut True
```
```python
def _parse_status(res) -> PermissionStatus:
    raw = res.get("status") if isinstance(res, dict) else None
    try:
        return PermissionStatus(str(raw))
    except ValueError:
        return PermissionStatus.DENIED
```
Même principe pour `can_check_biometrics`, `is_device_supported`, `open_app_settings`, `contains_key`, `get_available_biometrics` (défaut `[]`, pas `["fingerprint"]`).

**Problème B — brancher les vrais packages côté Dart**
Logique : un shim = une classe qui implémente `PyFlutterPlugin.handleMethodCall(method, args)` et traduit vers l'API réelle du package, puis renvoie un résultat simple (`Map`/`List`/`String`/`bool`/`null`).
Étapes :
1. `cd dart_runtime && flutter pub add local_auth permission_handler flutter_secure_storage` (met à jour `pubspec.yaml` et `pubspec.lock`).
2. Réécrire chaque shim. **Vérifier l'API de la version installée dans le README du package** (la signature de `authenticate` a changé entre versions de `local_auth`).
3. Configuration native :
   - Android `local_auth` : `MainActivity` doit étendre `FlutterFragmentActivity` ; permission `USE_BIOMETRIC` (déjà gérée par `manifest_sync.py` avec la clé `biometrics`).
   - iOS `local_auth` : clé `NSFaceIDUsageDescription` dans `Info.plist` (clé `biometrics`/`face_id` de `manifest_sync.py`).
   - `permission_handler` iOS : chaque permission demandée doit avoir son macro dans le `Podfile` (`PERMISSION_CAMERA=1` etc.) **et** sa clé `Info.plist`.
   - `flutter_secure_storage` Android : `minSdkVersion` ≥ 23 (vérifier `android/app/build.gradle.kts`).
4. Erreurs : ne **jamais** attraper pour renvoyer un faux succès. Laisser l'exception remonter : `main.dart` (`_handlePluginCall`) la renvoie à Python dans le champ `error`, et `call_plugin` la transforme en `PluginError` (déjà en place).

Squelette Dart de départ (à adapter à l'API exacte du package installé) :
```dart
import 'package:permission_handler/permission_handler.dart';
import 'plugin_registry.dart';

class PermissionHandlerShim implements PyFlutterPlugin {
  static const _map = <String, Permission>{
    'camera': Permission.camera,
    'microphone': Permission.microphone,
    'storage': Permission.storage,
    'photos': Permission.photos,
    'location': Permission.location,
    'notification': Permission.notification,
    'bluetooth': Permission.bluetooth,
    'contacts': Permission.contacts,
  };

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'checkPermission':
      case 'requestPermission':
        final p = _map[args['permission'] ?? ''];
        if (p == null) throw ArgumentError('Unknown permission ${args['permission']}');
        final status = method == 'checkPermission' ? await p.status : await p.request();
        return {'permission': args['permission'], 'status': _statusName(status)};
      case 'openAppSettings':
        return {'opened': await openAppSettings()};
      default:
        throw UnsupportedError('PermissionHandler method "$method" is not supported.');
    }
  }

  String _statusName(PermissionStatus s) {
    if (s.isGranted) return 'granted';
    if (s.isPermanentlyDenied) return 'permanentlyDenied';
    if (s.isRestricted) return 'restricted';
    if (s.isLimited) return 'limited';
    return 'denied';
  }
}
```
Le même schéma vaut pour `local_auth` (`LocalAuthentication().canCheckBiometrics`, `isDeviceSupported()`, `getAvailableBiometrics()`, `authenticate(...)`) et pour `flutter_secure_storage` (`FlutterSecureStorage().write/read/delete/deleteAll/readAll/containsKey`).

**Tests**
- Python (sans Dart) : avec `set_mock_method_call_handler`/`patch.object(manager, "call_plugin", return_value=None)` vérifier que `authenticate()` renvoie `False`, `check_permission()` renvoie `DENIED`, `get_available_biometrics()` renvoie `[]` quand la réponse est `None`, `{}` ou invalide.
- Dart : `flutter test` avec un faux `MethodChannel` n'est pas nécessaire ; tester à la main sur un appareil : refuser la biométrie → Python reçoit `False`.

**Critère de fin** : aucun défaut « succès » dans les trois wrappers Python ; `flutter analyze` sans erreur ; test manuel sur appareil réel (biométrie refusée, permission refusée, secret écrit puis relu après redémarrage de l'app).

**Pièges** : ne pas oublier d'ajouter les permissions à `pyflutter.yaml` (`biometrics`, `camera`…). Le fallback hors-ligne (`manager._dispatch_local_fallback`) reste « accordé » pour les tests : c'est traité en T-08.

---

## T-02 — Ordonnanceur de frames + thread d'UI unique (B-19, B-20)

**Problème**
- `pf.update()` → `runner.push_update()` reconstruit **et envoie** l'arbre **tout de suite, sur le thread appelant** (`cli/runner.py`, `push_update` / `_render_and_send`). 1 000 écritures de `Signal` = 1 000 rebuilds complets.
- Les callbacks tournent sur `_callback_worker`, mais un thread utilisateur (`threading.Thread`, timer) qui appelle `pf.update()` construit l'arbre **en parallèle** d'un callback en cours → l'état de l'application est lu pendant qu'il change.

**Logique** (modèle Flutter `markNeedsBuild`) : `update()` ne construit rien ; il **marque l'arbre sale** et réveille **un seul thread d'UI** qui regroupe les demandes (une frame max toutes les ~16 ms) et exécute **dans cet ordre, sur ce seul thread** : callbacks utilisateur → build → envoi. Plus besoin que le build soit protégé par un verrou contre les callbacks, car ils ne s'exécutent jamais en même temps.

**Fichiers** : `cli/runner.py` (principal), `app.py` (`update`), éventuellement `core/state.py` (aucun changement attendu).

**Algorithme**
1. Ajouter à `PyFlutterRunner` : `self._dirty = threading.Event()`, `self._ui_queue = queue.Queue()` (tâches à exécuter sur le thread d'UI), `self._ui_thread`.
2. `push_update()` devient `self._dirty.set()` (+ retour immédiat).
3. Boucle du thread d'UI :
   ```
   tant que is_running:
       attendre (dirty OU tâche dans la file) avec timeout
       vider la file : exécuter chaque tâche (callbacks) sur CE thread
       si dirty : dormir ~1/60 s (coalescence), puis dirty.clear(), puis _render_and_send()
   ```
4. `_callback_worker` actuel est **remplacé** par ce thread : `_event_loop` met `("callback", event)` dans la file au lieu de `self._callback_queue`.
5. Fournir `run_on_ui(fn)` (public, exposé dans `pyflutter/__init__.py`) pour les threads utilisateur qui doivent modifier l'état : `runner._ui_queue.put(fn); runner._dirty.set()`.
6. Fournir `flush_updates()` pour les tests et pour `hot_reload()` / `hot_restart()` : rend **synchrone** (`_render_and_send(force_full=True)` appelé depuis ces méthodes reste valable car elles tiennent déjà `tree_lock`).

Code de départ (testé isolément : 1 000 demandes → 1 rendu) :
```python
class _FrameScheduler:
    def __init__(self, render, min_interval=1 / 60):
        self._render, self._min = render, min_interval
        self._dirty = threading.Event()
        self._tasks: "queue.Queue[Callable[[], None]]" = queue.Queue()
        self._stop = False
        self._thread = threading.Thread(target=self._loop, name="pyflutter-ui", daemon=True)

    def start(self): self._thread.start()
    def request_frame(self): self._dirty.set()
    def post(self, fn): self._tasks.put(fn); self._dirty.set()
    def stop(self): self._stop = True; self._dirty.set()

    def _loop(self):
        while not self._stop:
            self._dirty.wait()
            if self._stop:
                break
            time.sleep(self._min)            # laisse arriver les autres demandes de la même frame
            self._dirty.clear()
            while True:                       # 1) callbacks d'abord
                try:
                    self._tasks.get_nowait()()
                except queue.Empty:
                    break
                except Exception:
                    logger.opt(exception=True).error("UI task failed")
            self._render()                    # 2) un seul rendu
```

**Tests à écrire**
- 1 000 appels `runner.push_update()` rapprochés → `session.send_tree` appelé **au plus 2 fois** (faux `session`).
- Un callback qui fait `pf.update()` trois fois → un seul envoi.
- `run_on_ui` exécute la fonction sur le thread nommé `pyflutter-ui`.
- Test de non-régression : les 156 tests existants + `audit/repro_state.py` (section C).

**Critère de fin** : plus aucun build exécuté hors du thread d'UI (ajouter un `assert threading.current_thread().name == "pyflutter-ui"` dans `_render_and_send` sous un flag debug).

**Pièges** : `hot_reload` charge le module sur le thread du clavier : il doit **poster** le rechargement sur le thread d'UI. `call_plugin(wait=True)` appelé **depuis** le thread d'UI bloque l'UI : acceptable pour de courts appels, mais voir T-08 (timeouts) ; la lecture des réponses reste sur `_event_thread`, donc pas de blocage mutuel.

---

## T-03 — Cycle de vie des `State` : `dispose` quand le widget quitte l'arbre (B-21)

**Problème** : `State.dispose()` n'est appelé qu'au hot restart. `_state_registry` (`core/state.py`) ne se vide jamais : timers/threads lancés dans `init_state` continuent, la mémoire croît. De plus la clé d'état est `fichier:ligne#index`, donc **éditer le fichier** déplace les lignes et casse l'association au hot reload.

**Ne pas faire** : supprimer tous les états non reconstruits dans la frame. Les pages **sous** la page courante de la pile `Navigator` ne sont pas reconstruites mais doivent garder leur état (comme Flutter).

**Logique** : marquer-et-balayer, en tenant compte de la navigation.
1. Un compteur global `_frame_id` incrémenté à chaque `resolve_tree(is_root=True)`.
2. Chaque `State` enregistre `last_seen_frame` et `owner_page` (identité de la page de la pile `Navigator` en cours de résolution, `None` pour la racine).
3. En fin de résolution racine : `sweep_states()` :
   - candidat = état dont `last_seen_frame < _frame_id` ;
   - **conservé** si son `owner_page` est encore dans `Navigator._stack` (page couverte) ;
   - sinon `state.dispose()` (dans un `try/except` qui journalise) puis suppression du registre.

Code de départ (`core/state.py`) :
```python
_frame_id = 0
_current_owner: contextvars.ContextVar[object | None] = contextvars.ContextVar("_current_owner", default=None)

def begin_frame() -> None:
    global _frame_id
    _frame_id += 1

def sweep_states() -> None:
    from pyflutter.core.navigation import Navigator
    live_pages = {id(p) for p in Navigator._stack}
    for key, state in list(_state_registry.items()):
        if state._last_seen_frame == _frame_id:
            continue
        if state._owner_page_id in live_pages:
            continue
        _state_registry.pop(key, None)
        try:
            state.dispose()
        except Exception as e:
            logger.error("Error during state disposal: {}", e)
```
`StatefulComponent.get_or_create_state` met à jour `state._last_seen_frame = _frame_id` et `state._owner_page_id = id(_current_owner.get())` ; `resolve_tree` pose `_current_owner` autour de la résolution de chaque page (la page courante, ou la page racine).

**Deuxième moitié — clés stables au hot reload**
La clé `fichier:ligne#index` ne survit pas aux éditions. Remplacer par une clé **structurelle** : chemin des types depuis la racine (`root/Scaffold/Column[2]/CounterStateful`) + `key=` explicite quand fourni. Documenter : « mettez un `key=` sur les widgets à état dans les listes ». Implémentation : `resolve_tree` maintient une pile de segments ; `StatefulComponent` reçoit son chemin à la résolution (pas à la construction). **Attention** : cela change quand la clé est connue → à faire dans un second commit, après les tests de `dispose`.

**Tests**
- Un `State` dont `dispose()` incrémente un compteur ; widget présent frame 1, absent frame 2 → `dispose` appelé exactement une fois, registre vidé.
- Page A (avec état) → `Navigator.push(B)` → l'état de A **n'est pas** supprimé ; `Navigator.pop()` puis retour sur A → même objet `State`.
- `clear_state_registry()` appelle toujours `dispose` sur tous les états restants.

**Critère de fin** : `audit/repro_state.py` section B affiche « dispose called? True » après retrait du widget.

---

## T-04 — `FormKey` comme magasin de valeurs (B-27)

**Problème (plus grave que décrit dans le rapport initial)** : un `TextFormField` est **recréé à chaque build** ; sa valeur Python n'est que `initial_value`. `FormKey.get_values()` et `validate()` lisent `field.value` du dernier champ enregistré, donc la valeur **réellement tapée** n'est jamais celle lue si le champ n'a pas de `controller`. De plus `FormKey._fields` garde chaque copie obsolète (fuite).

**Logique** : la valeur appartient au `FormKey` (qui vit aussi longtemps que le formulaire), pas au widget éphémère.
1. `FormKey._values: dict[str, str]` et `FormKey._errors: dict[str, str]`, indexés par `name` (obligatoire pour les champs d'un formulaire ; sinon générer `_auto_<index>` dans l'ordre d'enregistrement de la frame).
2. À l'enregistrement d'un champ (`_register_with_form_key`) : si `name in _values` → `self.props["value"] = _values[name]` et `self.props["error_text"] = _errors.get(name)` ; sinon `_values[name] = initial_value`.
3. Le callback `on_change` du champ écrit `_values[name] = new_text` **avant** d'appeler le `on_change` utilisateur.
4. `FormKey._fields` devient un `weakref.WeakSet` **ou** est vidé au début de chaque frame (`begin_frame` de T-03) puis repeuplé pendant la résolution.
5. `validate()` : appelle `field.validator(_values[name])` pour chaque champ **courant**, remplit `_errors`, renvoie le booléen, déclenche `update()`.

Code de départ :
```python
class FormKey:
    def __init__(self):
        self._fields: "weakref.WeakSet[Any]" = weakref.WeakSet()
        self._values: dict[str, str] = {}
        self._errors: dict[str, str] = {}

    def register(self, field) -> None:
        self._fields.add(field)
        name = field.name or f"_auto_{len(self._fields)}"
        field._form_name = name
        if name in self._values:
            field.props["value"] = self._values[name]
            if name in self._errors:
                field.props["error_text"] = self._errors[name]
        else:
            self._values[name] = field.props.get("value", "")

    def set_value(self, name: str, text: str) -> None:
        self._values[name] = text
```
**Tests** : (1) taper deux valeurs via `invoke_callback(field.callback_id, {"value": "abc"})`, reconstruire l'arbre, `get_values()` renvoie `abc` ; (2) après 50 rebuilds, `len(form_key._fields) <= nombre de champs` ; (3) `validate()` met l'erreur dans `_errors` et le nouveau champ la reçoit.

**Critère de fin** : un formulaire à 2 champs conserve les valeurs tapées après un rebuild (test de bout en bout avec `resolve_tree`).

---

## T-05 — Convention d'appel des callbacks (B-23)

**Problème** : `core/widget_base.py::_call_callable` devine comment appeler le handler d'après sa signature, avec des cas surprenants : `lambda e: …` sur un bouton est appelé **sans argument** (`TypeError`) ; un handler à un paramètre reçoit « la première valeur du dict », quel que soit son nom.

**Règle unique à documenter et à implémenter** (testée en isolation ; voir le code) :
1. `event_data` vide et handler sans paramètre requis → `fn()`.
2. Handler avec `**kwargs` → `fn(**event_data)`.
3. Tous les paramètres requis ont un nom présent dans `event_data` → appel par nom.
4. Sinon, handler avec paramètres positionnels requis → premier argument = `event_data["value"]` si présent, sinon la seule valeur, sinon `None` ; les suivants `None`.
5. Sinon `fn()`.

Code (à mettre dans `widget_base.py`, `_call_callable` en devient un alias) :
```python
def call_callback(fn, event_data: dict[str, Any]):
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return fn(**event_data) if event_data else fn()
    params = list(sig.parameters.values())
    if any(p.kind is p.VAR_KEYWORD for p in params):
        return fn(**event_data)
    named = {p.name for p in params if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)}
    by_name = {k: v for k, v in event_data.items() if k in named}
    positional = [p for p in params if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    required = [p for p in positional if p.default is p.empty]
    if by_name and len(by_name) >= len(required):
        return fn(**by_name)
    if required:
        main = event_data.get("value", next(iter(event_data.values()), None))
        return fn(*([main] + [None] * (len(required) - 1)))
    return fn()
```
Résultats vérifiés : `lambda: …`→appel nu ; `lambda value:` + `{"value":"x"}` → `"x"` ; `lambda v:` → `"y"` ; `lambda e:` sans données → `None` (plus de `TypeError`) ; `lambda **kw` → tout ; `lambda a, b:` + `{"a":1,"b":2}` → par nom.

**Seconde partie — types** : Dart envoie **toujours des chaînes**. Les widgets `Switch`, `Checkbox`, `Slider` convertissent via `QtSignal(value_converter=…)`. Étendre ce principe : chaque widget interactif déclare un convertisseur (`TextField` → `str`, `Slider` → `float`, `Checkbox` → `bool`, `DropdownButton` → `str`) ; un `Button` n'envoie pas de données. Ne **pas** convertir dans `call_callback` (il ne connaît pas le widget).

**Tests** : une table de cas `(handler, event_data, attendu)` couvrant les 6 lignes ci-dessus ; vérifier que les tests existants `test_native_flutter_props.py` et `test_forms_and_buttons.py` restent verts.

---

## T-06 — Signaux : égalité, mutation en place, batch (B-17, B-18)

**Fichier** : `core/state.py` uniquement.

**B-17 — problèmes**
(a) `sig.value.append(x)` ne notifie rien (la valeur `!=` elle-même). (b) `sig.update(lambda l: l.append(x))` remet la valeur à `None`. (c) `!=` plante avec numpy (`ValueError`).
**Solution**
- Ajouter `Signal.mutate(fn)` : applique `fn(self._value)` **en place** puis notifie toujours (documenté comme la bonne façon de modifier une liste/dict).
- `Signal.update(fn)` : si `fn` renvoie `None` et que la valeur courante est un conteneur mutable (`list`, `dict`, `set`), lever `TypeError("update() must return the new value; use mutate() for in-place changes")`.
- Comparaison sûre :
```python
def _same(a, b) -> bool:
    if a is b:
        return True
    try:
        r = a == b
        return bool(r.all()) if hasattr(r, "all") else bool(r)
    except Exception:
        return False
```
- Paramètre optionnel `Signal(initial, equals=None)` pour fournir sa propre comparaison.

**B-18 — problèmes** : `_batch_depth` et `_batched_listeners` sont des globaux non protégés ; `update()` est appelé même si le bloc a levé ; à la sortie, un `Computed` rejoué déclenche un `update()` hors batch.
**Solution**
1. Protéger les globaux par un `threading.RLock`.
2. Un seul flag `_flushing` : pendant la fusion des listeners de fin de batch, `Signal._notify_listeners` ne déclenche **pas** `update()` ; un unique `update()` est fait à la fin.
3. `__exit__` : appeler les listeners même si `exc_type` n'est pas `None` (l'état a déjà changé), puis laisser l'exception se propager.

**Tests**
- `s = Signal([]); s.mutate(lambda l: l.append(1))` → listener appelé une fois.
- `s.update(lambda l: l.append(1))` → `TypeError`.
- Signal portant un objet dont `==` lève : ne plante pas.
- `with batch(): a.value=1; b.value=2` avec un `Computed(a+b)` → un seul appel à un faux `update`.
- Batch qui lève : listeners appelés, exception propagée.

---

## T-07 — Arguments structurés côté Dart (B-39)

**Problème** : `dart_runtime/lib/plugins/plugin_registry.dart::dispatch` convertit **tous** les arguments en `String` (`v?.toString()`). Une liste ou un dict devient `"{a: 1}"` (syntaxe Dart, pas du JSON) ; `hive.put` avec une valeur structurée est corrompue.

**Logique non cassante** : ajouter une seconde méthode qui reçoit les arguments bruts ; par défaut elle appelle l'ancienne.
```dart
abstract class PyFlutterPlugin {
  Future<dynamic> handleMethodCall(String method, Map<String, String> args);

  /// Override this when the plugin needs structured (list/map/number/bool) arguments.
  Future<dynamic> handleRawCall(String method, Map<String, dynamic> args) {
    return handleMethodCall(
      method,
      args.map((k, v) => MapEntry(k, v is String ? v : (v == null ? '' : jsonEncode(v)))),
    );
  }
}
```
Notez le choix : une valeur non-chaîne devient du **JSON** (`jsonEncode`), pas du `toString()`. `PluginRegistry.dispatch` appelle `plugin.handleRawCall(method, rawArgs)`.
**À faire ensuite** : `hive_shim.dart` et `sqflite_shim.dart` (si conservé) overrident `handleRawCall` pour lire `args['value']` tel quel.

**Test** : manuel (pas de compilateur ici) — `hive.put("k", {"a": [1,2]})` puis `get` renvoie la même structure ; côté Python, test unitaire de `json.dumps` des arguments dans `call_plugin` (déjà couvert).

---

## T-08 — Timeouts par plugin et mocks explicites (B-41, B-37)

**Problème**
- Le timeout par défaut de 3 s (5 s pour `MethodChannel`) est trop court pour les appels **interactifs** : sélecteur de fichier, caméra, authentification, demande de permission, partage.
- `manager._dispatch_local_fallback` renvoie des succès plausibles (`authenticated: True`, `granted`…) dès qu'aucun runtime n'est connecté, **sans le dire**.

**Solution timeouts** : table dans `plugins/manager.py` :
```python
INTERACTIVE_TIMEOUT = 120.0
PLUGIN_TIMEOUTS: dict[tuple[str, str], Optional[float]] = {
    ("local_auth", "authenticate"): INTERACTIVE_TIMEOUT,
    ("permission_handler", "requestPermission"): INTERACTIVE_TIMEOUT,
    ("file_picker", "pickFiles"): INTERACTIVE_TIMEOUT,
    ("image_picker", "pickImage"): INTERACTIVE_TIMEOUT,
    ("camera", "takePicture"): INTERACTIVE_TIMEOUT,
    ("share_plus", "share"): INTERACTIVE_TIMEOUT,
}
```
`call_plugin(..., timeout=None)` → `timeout = PLUGIN_TIMEOUTS.get((plugin, method), 3.0)`. Ajouter à tous les wrappers Python un paramètre `timeout: Optional[float] = None` transmis tel quel. Vérifier le nom exact de la méthode dans chaque wrapper (`grep -n 'call_plugin("file_picker"' plugins/file_picker.py`).
Annulation : si `runner.quit()` est appelé pendant l'attente, réveiller tous les `Event` en attente (`for ev in _pending_rpc_calls.values(): ev.set()`) et lever `PluginError("bridge closed")`.

**Solution mocks explicites**
1. Le fallback n'est actif que si `get_active_runner()` est `None` (c'est déjà le cas).
2. Le **premier** appel d'un plugin simulé journalise un avertissement unique : `logger.warning("[offline] {} is simulated (no Flutter runtime connected)", plugin)`.
3. Les plugins « sécurité » (`local_auth.authenticate`, `permission_handler.requestPermission/checkPermission`, `flutter_secure_storage.*`) **refusent** par défaut hors runtime : `PluginError("local_auth.authenticate unavailable offline")`, sauf si `PYFLUTTER_ALLOW_INSECURE_MOCKS=1`.
4. Les tests existants qui attendent « granted »/« authenticated » (`tests/test_second_wave_plugins.py`) définissent cette variable dans un `setUpModule` : `os.environ["PYFLUTTER_ALLOW_INSECURE_MOCKS"] = "1"`.

**Tests** : table `PLUGIN_TIMEOUTS` appliquée (patch de `threading.Event.wait` pour lire la valeur) ; refus hors runtime sans la variable ; avertissement émis une seule fois ; réveil des appels en attente à la fermeture.

---

## T-09 — Événements Dart → Python : `EventChannel` et appels entrants (B-40)

**Problème** : `core/channel.py` expose `EventChannel.listen()` et `MethodChannel.set_method_call_handler()`, mais **aucun message du protocole ne transporte** ces données vers Python. `EventChannel._listener` n'est jamais appelé ; `get_channel_handler` n'est jamais utilisé hors de `channel.py`. De plus `call_plugin("__event_channel__", "listen", …)` aboutit côté Dart au `MethodChannel` générique (aucun shim `__event_channel__` n'est enregistré) et échoue.

**Protocole à ajouter** (3 endroits à garder synchrones : `core/render.py`, `rust_bridge/src/main.rs`, `dart_runtime/lib/ir_codec.dart`) :

| Type | Sens | Contenu (JSON UTF-8) |
|-----:|------|----------------------|
| `0x07` `MSG_EVENT` | Dart → Python | `{"channel": "...", "kind": "data"\|"error"\|"done", "payload": ...}` |
| `0x08` `MSG_INCOMING_CALL` | Dart → Python | `{"call_id": "...", "channel": "...", "method": "...", "arguments": ...}` (phase 2) |
| `0x09` `MSG_INCOMING_REPLY` | Python → Dart | `{"call_id": "...", "result": ..., "error": null}` (phase 2) |

**Phase 1 : EventChannel seulement**
1. **Rust** (`main.rs`) : le filtre `if event_type != MSG_CALLBACK_EVENT && event_type != MSG_PLUGIN_RESPONSE` doit aussi laisser passer `0x07`. Ajouter la constante `MSG_EVENT: u8 = 0x07`. Ajouter un test dans `tests/test_bridge_relay.py` : un client Dart factice envoie une trame `0x07`, Python la lit sur la sortie du pont.
2. **Python** : `core/render.py` : `MSG_EVENT = 0x07`. `core/bridge.py::next_event` renvoie `(MSG_EVENT, payload_bytes)`. `cli/runner.py::_event_loop` : `if msg_type == MSG_EVENT: handle_stream_event(payload)`. `core/channel.py` :
   ```python
   _event_listeners: dict[str, "EventChannel"] = {}

   def handle_stream_event(payload: bytes) -> None:
       msg = json.loads(payload)
       ch = _event_listeners.get(msg["channel"])
       if ch is None:
           return
       if msg["kind"] == "data" and ch._listener:
           pf_run_on_ui(lambda: ch._listener(msg["payload"]))      # thread d'UI, voir T-02
       elif msg["kind"] == "error" and ch._on_error:
           pf_run_on_ui(lambda: ch._on_error(msg["payload"]))
       elif msg["kind"] == "done":
           _event_listeners.pop(msg["channel"], None)
   ```
   `EventChannel.listen` enregistre `_event_listeners[self.name] = self` **avant** l'appel `call_plugin("__event_channel__", "listen", …)` et mémorise `on_error`.
3. **Dart** : nouveau `lib/plugins/event_channel_shim.dart` enregistré sous le nom `__event_channel__` dans `BridgeConnectionScreen.initState` (comme `OverlayShim`, il reçoit une fonction `sendFrame(int type, Uint8List payload)`).
   ```dart
   class EventChannelShim implements PyFlutterPlugin {
     final void Function(int, Uint8List) sendFrame;
     final Map<String, StreamSubscription> _subs = {};
     EventChannelShim(this.sendFrame);

     @override
     Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
       final name = args['channel'] ?? '';
       switch (method) {
         case 'listen':
           await _subs[name]?.cancel();
           _subs[name] = EventChannel(name).receiveBroadcastStream(args['arguments']).listen(
             (data) => _emit(name, 'data', data),
             onError: (e) => _emit(name, 'error', e.toString()),
             onDone: () => _emit(name, 'done', null),
           );
           return {'listening': true};
         case 'cancel':
           await _subs.remove(name)?.cancel();
           return {'cancelled': true};
         default:
           throw UnsupportedError('EventChannel method "$method" is not supported.');
       }
     }

     void _emit(String channel, String kind, dynamic payload) {
       try {
         sendFrame(msgEvent, Uint8List.fromList(utf8.encode(
             jsonEncode({'channel': channel, 'kind': kind, 'payload': payload}))));
       } catch (_) {/* non-serializable event: drop */}
     }
   }
   ```
   Attention : `PluginRegistry.dispatch` convertit les arguments en `String` (voir T-07) ; `args['arguments']` arrive donc en JSON texte.

**Phase 2 : appels entrants** (`set_method_call_handler`) : même mécanique avec `0x08`/`0x09`. Python exécute le handler sur le thread d'UI, répond `0x09` avec le même `call_id`. Dart : `MethodChannel(name).setMethodCallHandler((call) async { … envoyer 0x08 … attendre la réponse via un `Completer` indexé par `call_id` … })`.

**Tests** : (Python) `handle_stream_event` avec un faux listener ; (Rust/Python) test de relais `0x07` ; (manuel) `connectivity_plus` ou un canal de test qui émet 3 événements.

**Critère de fin** : un `EventChannel` de test reçoit des événements dans Python, sur le thread d'UI, et `cancel()` les arrête.

---

## T-10 — Suppression de prop vs valeur vide, et rejet de patch (B-25)

**Problème 1** : `core/render.py::diff_snapshots` encode « prop supprimée » comme `""`. Une prop dont la nouvelle valeur est réellement vide (`TextField.value` effacé) est donc **confondue** avec une suppression, et Dart (`_handleTreePatch`) retire la clé dans les deux cas.
**Problème 2** : un patch dont l'`id` est inconnu de Dart est ignoré **sans prévenir** Python (c'est la cause racine de B-07, corrigée seulement pour le cas des clés).

**Protocole** : ajouter au patch une liste explicite `remove` :
```json
{"type":"patch","updates":[{"id":"root.0","props":{"text":""},"remove":["color"],"callback_id":"..."}]}
```
**Python** (`diff_snapshots`) :
```python
removed = [k for k in old_props if k not in new_props]
changed = {k: v for k, v in new_props.items() if old_props.get(k, _MISSING) != v}   # "" reste "" (valeur)
if changed or removed or cb_changed:
    op = {"id": new["_nid"]}
    if changed: op["props"] = changed
    if removed: op["remove"] = removed
    ...
```
**Dart** (`main.dart::_handleTreePatch`) : `props.forEach((k, v) => target.props[k] = v.toString())` (une valeur vide est **conservée**), puis `for (final k in (u['remove'] as List? ?? [])) target.props.remove(k)`.
**Rejet de patch (nack)** : si `findNodeById` renvoie `null`, ajouter `unknown.add(nid)` ; après la boucle, si `unknown.isNotEmpty`, envoyer une trame `0x0A` `MSG_PATCH_NACK` (contenu : liste d'ids). Python (`runner._event_loop`) la traite comme le resync de B-08 : `self.session.reset_snapshot(); self._render_and_send(force_full=True)`. Rust : laisser passer `0x0A` dans le filtre Dart→Python (même endroit que T-09).

**Tests** : `diff_snapshots` : `"hello"→""` produit `props={"value":""}` et **pas** de `remove` ; prop supprimée produit `remove=["x"]` ; test Rust/Python de relais du `0x0A`.

---

## T-11 — Contrat de props partagé + validation (B-24, B-57, B-58)

**Problème** : le protocole est « tout en chaînes » ; rien ne vérifie que Python et Dart parlent des mêmes noms de props. Résultat : des paramètres Python **acceptés mais ignorés** par Dart (confirmés dans `widget_builder.dart`) :

| Widget | Python envoie | Dart ignore |
|--------|---------------|-------------|
| `Tooltip` | `wait_duration_ms`, `show_duration_ms` | les deux (case `'Tooltip'` ne lit que `message`) |
| `CircularProgressIndicator` | `color`, `stroke_width` | les deux (le case renvoie un `CircularProgressIndicator()` constant) |
| `Positioned` | `width`, `height` | les deux |

**B-58 — corrections immédiates (Dart, `widget_builder.dart`)**
```dart
case 'Tooltip':
  final msg = node.props['message'] ?? '';
  final wait = int.tryParse(node.props['wait_duration_ms'] ?? '');
  final show = int.tryParse(node.props['show_duration_ms'] ?? '');
  widget = Tooltip(
    message: msg,
    waitDuration: wait != null ? Duration(milliseconds: wait) : null,
    showDuration: show != null ? Duration(milliseconds: show) : null,
    child: child,
  );
```
```dart
case 'CircularProgressIndicator':
  widget = Center(
    child: Padding(
      padding: const EdgeInsets.all(16.0),
      child: CircularProgressIndicator(
        color: node.props.containsKey('color') ? parseHexColor(node.props['color']!) : null,
        strokeWidth: double.tryParse(node.props['stroke_width'] ?? '') ?? 4.0,
      ),
    ),
  );
```
`Positioned` : ajouter `width: double.tryParse(node.props['width'] ?? '')` et `height:` (Flutter les accepte).

**B-57 — contrat partagé** (travail structurant)
1. Créer `ir_spec/widgets.json` : pour chaque `widget_type`, la liste des props, leur type (`string|number|bool|color|enum|callback|icon`) et, pour les enums, les valeurs permises. Exemple :
   ```json
   {"Tooltip": {"props": {"message": "string", "wait_duration_ms": "number", "show_duration_ms": "number"}},
    "Column": {"props": {"main_axis_alignment": {"enum": ["start","center","end","space_between","space_around","space_evenly"]}}}}
   ```
2. **Génération initiale** : un script `tools/gen_contract.py` qui parcourt `widgets/widgets.py` avec `ast` (arguments passés à `super().__init__(...)` + `self.props["x"] = …`) et produit le JSON de départ ; l'humain le relit.
3. **Test de cohérence** `tools/check_contract.py` :
   - Python : chaque prop émise par une classe existe dans le contrat ;
   - Dart : extraire `props['x']` et `containsKey('x')` de chaque `case 'Type':` par regex et vérifier qu'ils sont dans le contrat. **Limite connue** : plusieurs widgets délèguent à une autre classe Dart (`PyTextFieldWidget`, `PyDropdownButtonWidget`, `buildButton…`) ; le script doit suivre ces délégations ou être complété à la main (un premier essai naïf produit beaucoup de faux positifs : ne pas le traiter comme une liste de bugs).
4. Ajouter `check_contract.py` à la CI (T-18).

**B-24 — validation côté Python** (`core/widget_base.py::_populate_props`) :
```python
def _populate_props(self, props):
    for k, v in props.items():
        if v is None:
            continue
        if callable(v) or isinstance(v, (list, dict, set, tuple)):
            raise TypeError(f"{type(self).__name__}.{k}: unsupported value {type(v).__name__} "
                            f"(use raw_props= for custom data)")
        if isinstance(v, Enum):
            v = v.value
        ...
```
En mode strict (`PYFLUTTER_STRICT_PROPS=1`, activé dans les tests), vérifier aussi que `k` est dans le contrat du `widget_type`, et que les enums ont une valeur autorisée. Hors mode strict : simple `logger.warning` une fois par (widget, prop).

**Tests** : le contrat se charge ; un widget avec une prop inconnue lève en mode strict ; `Text(color=lambda: 1)` lève `TypeError`.

---

## T-12 — `Component` sans devinettes (B-22)

**Problème** : `Component.build()` (`core/widget_base.py`, ~ligne 672) choisit sa racine dans `_central_widget, central_widget, layout, root, body, column, row` et sa barre dans `app_bar, appbar, app_bar_widget, fab, floating_action_button, drawer, bottom_bar…`. Un attribut utilisateur du même nom (`self.body = "texte"`) casse la construction sans erreur claire.

**À faire, dans cet ordre (un commit chacun)**
1. **Garde de type** : ne retenir un candidat que s'il est une instance de `Widget` (`isinstance(x, Widget)`). Pour `app_bar`, accepter aussi `str` (c'est déjà géré plus bas).
2. **Dépréciation** : `root`, `body`, `column`, `row`, `appbar`, `app_bar_widget`, `bottom_bar`, `fab` → avertissement unique « utilisez `self.layout` / `self.set_central_widget()` ». Vérifier d'abord l'usage dans les exemples : `grep -rn "self\.\(root\|body\|column\|row\|fab\|bottom_bar\) =" examples/ py_framework/`.
3. **Collisions de noms (`text`, `value`, `count`, `clear`…)** : vérifier qu'aucun code du framework n'appelle ces méthodes sur un `Component` (`grep -rn "\.count()\|\.text()\|\.value()" py_framework/pyflutter`). S'il n'y en a pas, le « shadowing » par `self.count = 0` est **inoffensif** (l'attribut d'instance masque la méthode) : documenter, ne rien changer. S'il y en a, remplacer ces appels par `children`/`props` directs.
4. **Erreur claire** : quand `build()` n'est pas surchargé et qu'aucun layout n'existe, le message actuel (`NotImplementedError`) est bon ; ajouter le nom de la classe et un exemple de 3 lignes.

**Test** : un `Component` avec `self.body = "texte"` et `self.layout = Column()` → l'arbre utilise `layout` ; `self.body` n'est plus pris.

---

## T-13 — Petits correctifs groupés

Un commit par point.

**B-26 — performances de résolution** (`core/render.py`, `app.py`)
- `app.py` ligne ~67 : remplacer `inspect.stack()[1]` (lit les fichiers sources de toutes les frames) par `sys._getframe(1).f_code.co_filename`.
- `assign_node_ids`, `widget_to_snapshot`, `widget_to_proto` rappellent `resolve_widget()` sur un arbre **déjà concret**. Ajouter un paramètre `concrete: bool = False` ; `BridgeSession.send_tree` passe `True`. (`render_tree_frame(resolved=True)` existe déjà.)
- Test : benchmark simple (arbre de 2 000 nœuds) qui vérifie qu'un `send_tree` appelle `resolve_widget` 0 fois après `resolve_tree`.

**B-28 — durée du SnackBar ambiguë** (`plugins/overlay.py`)
`duration < 100` → secondes sinon millisecondes : `duration=120` donne 120 ms. Règle : `Duration` ou `int/float` = **secondes** ; ajouter `duration_ms: Optional[int] = None` pour les millisecondes ; valeur par défaut `None` (créer `Duration(seconds=4)` dans la fonction, pas dans la signature).

**B-34 — erreurs de démarrage** (`cli/runner.py`)
- `PyFlutterRunner.__init__` appelle `find_bridge_binary` et lève `FileNotFoundError` (trace brute). Déplacer l'appel dans `start()`, entourer d'un `try/except FileNotFoundError` qui affiche : « pont introuvable : lancez `cargo build --manifest-path rust_bridge/Cargo.toml` » puis `sys.exit(1)`.
- `_build_and_tag_tree` écrit `debug_banner` dans `tree.props` **avant** résolution : si `build()` renvoie un `Component`, la prop est perdue. Résoudre d'abord : `tree = resolve_tree(tree)` puis poser la prop (`resolve_tree` est idempotent sur un arbre concret).

**B-35 — gabarit de projet** (`cli/creator.py`)
- Retirer la ligne `d : Détection et bascule…` de `README_TEMPLATE` (le raccourci n'existe pas dans `_handle_key`).
- Description YAML : remplacer `.replace("{description}", description)` par `json.dumps(description)` (une chaîne JSON est un scalaire YAML valide, guillemets échappés).

**B-36 — `run` retombe dans `build`** (`cli/main.py`)
Après `runner.start()` ajouter `return`/`sys.exit(0)`. Test : `main(["run", …])` avec un faux runner n'instancie pas de builder.

**B-59 — hot reload qui ne recharge que le module d'entrée** (`cli/runner.py`)
Algorithme :
1. Avant `load_app_from_file`, supprimer de `sys.modules` tous les modules dont `__file__` est **sous le dossier du projet** (`entrypoint.parent`), hors `site-packages` et hors `pyflutter.*` ; appeler `importlib.invalidate_caches()`.
2. Surveillance automatique (option `--watch`) : thread qui interroge `os.stat().st_mtime` des `*.py` du projet toutes les 500 ms et poste `hot_reload` sur le thread d'UI (T-02).
```python
def _purge_project_modules(project_dir: Path) -> None:
    for name, mod in list(sys.modules.items()):
        f = getattr(mod, "__file__", None)
        if f and Path(f).resolve().is_relative_to(project_dir) and "site-packages" not in f:
            del sys.modules[name]
    importlib.invalidate_caches()
```
**Test** : projet temporaire `main.py` + `helper.py` ; modifier `helper.py`, appeler la fonction de rechargement, vérifier que la nouvelle valeur est vue.

---

## T-14 — Configuration par projet, dépendances Flutter, permissions (B-31, B-32)

**Problèmes**
1. `PyFlutterConfig.save()` (`core/config.py`) réécrit le fichier à partir de 4 champs : commentaires et clés inconnues **perdus** à chaque `pyflutter add`.
2. `add_flutter_dependency` écrit la version `any` alors que `flutter pub add` a résolu une vraie contrainte.
3. `add_flutter_package` modifie le `pubspec.yaml` du **dépôt framework** (partagé) ; les `dependencies.flutter` du `pyflutter.yaml` d'un projet ne sont **jamais appliquées**.
4. `manifest_sync` modifie les manifestes du **dépôt framework** et n'enlève jamais une permission retirée du yaml.

**Solution — étapes dans cet ordre**
1. **Préserver le yaml** : `save()` part de `copy.deepcopy(self.raw_config)`, ne remplace que `name/description/version/pyflutter.*/dependencies.flutter/permissions`, puis `yaml.dump(..., sort_keys=False)`. (Pour garder aussi les commentaires, utiliser `ruamel.yaml` en mode aller-retour : décision à prendre, dépendance supplémentaire.)
2. **Vraie version** : après `flutter pub add`, lire `dart_runtime/pubspec.yaml` (`yaml.safe_load`) et stocker `dependencies[package]` au lieu de `"any"`.
3. **Copie de travail par projet** : `<projet>/.pyflutter/runtime/`.
   - `ensure_runtime(project)` : copie `dart_runtime/` (sans `build/`, `.dart_tool/`) si le hash du gabarit a changé ; écrit le hash dans `.pyflutter/state.json`.
   - Génère `pubspec.yaml` = dépendances du gabarit **+** `dependencies.flutter` du `pyflutter.yaml` ; si le hash du pubspec a changé → `flutter pub get`.
   - `sync_platform_metadata` s'exécute sur **cette copie**.
   - `PyFlutterRunner`/`PyFlutterBuilder` utilisent `runtime_dir` (cette copie) au lieu de `workspace_root/"dart_runtime"`.
4. **Permissions retirables** : encadrer le contenu géré par des marqueurs.
   ```xml
   <!-- pyflutter:begin -->
       <uses-permission android:name="android.permission.INTERNET"/>
   <!-- pyflutter:end -->
   ```
   À chaque synchronisation : supprimer le bloc existant (regex avec `re.DOTALL`), puis réinsérer le bloc complet après `<manifest …>`. Même principe dans `Info.plist` (les commentaires XML sont valides dans un plist). Ne jamais toucher aux lignes hors bloc.

**Tests** : yaml avec commentaire et clé inconnue → `add_flutter_dependency` conserve la clé ; retirer `camera` du yaml → le bloc ne contient plus la permission ; deux synchronisations successives = fichier identique (idempotence).

---

## T-15 — Dart : transport abstrait / Web, rendu incrémental, `FrameBuffer` (B-47, B-48, B-50)

Aucun compilateur Dart ici : **relire deux fois**, `flutter analyze` obligatoire chez vous.

**B-50 — `FrameBuffer` O(n²)** (`lib/frame_buffer.dart`) : `List<int>` boxé + `sublist` + `removeRange` à chaque trame.
Algorithme : un `Uint8List` avec indices `_start`/`_end` ; on n'avance que `_start` quand une trame est consommée ; on compacte (ou on agrandit) seulement quand il manque de la place.
```dart
class FrameBuffer {
  Uint8List _buf = Uint8List(64 * 1024);
  int _start = 0, _end = 0;
  final FrameHandler onFrame;
  FrameBuffer(this.onFrame);

  void addChunk(Uint8List chunk) {
    _ensure(chunk.length);
    _buf.setRange(_end, _end + chunk.length, chunk);
    _end += chunk.length;
    _drain();
  }

  void _ensure(int extra) {
    final live = _end - _start;
    if (_end + extra <= _buf.length) return;
    if (live + extra <= _buf.length) {            // assez de place après compaction
      _buf.setRange(0, live, _buf, _start);
    } else {                                      // agrandir
      final bigger = Uint8List((live + extra) * 2);
      bigger.setRange(0, live, _buf, _start);
      _buf = bigger;
    }
    _start = 0;
    _end = live;
  }

  void _drain() {
    while (_end - _start >= 5) {
      final len = ByteData.sublistView(_buf, _start + 1, _start + 5).getUint32(0, Endian.big);
      if (len > 64 * 1024 * 1024) { _start = _end = 0; return; }   // trame absurde : jeter
      if (_end - _start < 5 + len) return;
      final type = _buf[_start];
      final payload = Uint8List.fromList(_buf.sublist(_start + 5, _start + 5 + len));
      _start += 5 + len;
      onFrame(type, payload);
    }
    if (_start == _end) { _start = _end = 0; }
  }
}
```

**B-48 — chaque patch reconstruit tout l'arbre de widgets**
Constat : `_handleTreePatch` appelle `setState(() {})` puis `build` refait `buildFromNode(racine)`. Les patchs économisent des octets, pas du travail de rendu ; `findNodeById` est en O(n) par opération.
Plan :
1. **Index** : `Map<String, WidgetNode> _index` construit au décodage de l'arbre complet ; `findNodeById` devient `_index[nid]` (O(1)).
2. **Notification par nœud** : `WidgetNode extends ChangeNotifier` ; un patch fait `node.props…; node.notifyListeners()`.
3. **Widget par nœud** : `buildFromNode(node)` renvoie `PyNodeWidget(key: ValueKey(node.props['_nid']), node: node)` (un `StatefulWidget` qui écoute `node` via `AnimatedBuilder`) ; le gros `switch` actuel passe dans `_buildNodeBody(node)`. Flutter ne reconstruit alors que les nœuds modifiés.
4. Ne plus appeler `setState` à la racine sur un simple patch de props ; seulement sur un arbre complet.
Prérequis : T-10 (rejet de patch) pour ne pas diverger silencieusement.

**B-47 — Web impossible** : `main.dart` et `bridge/ffi_bridge.dart` importent `dart:io` et `dart:ffi`, indisponibles sur le Web (`flutter build web` échoue).
Plan :
1. Définir une interface `lib/bridge/transport.dart` : `abstract class BridgeTransport { Stream<Frame> get frames; void send(int type, Uint8List payload); Future<void> connect(); void dispose(); }`.
2. Trois implémentations : `transport_tcp.dart` (dart:io `Socket`), `transport_ffi.dart` (standalone), `transport_ws.dart` (`WebSocket` de `dart:html`/`package:web`).
3. Sélection par import conditionnel :
   ```dart
   import 'transport_stub.dart'
       if (dart.library.io) 'transport_io.dart'
       if (dart.library.js_interop) 'transport_web.dart';
   ```
   `transport_io.dart` choisit TCP ou FFI selon `PYFLUTTER_STANDALONE` ; `transport_web.dart` utilise un WebSocket.
4. Côté pont : le relais Rust ne parle pas WebSocket. Deux options : (a) ajouter `tungstenite` au relais (dépendance à mesurer, voir partie C), (b) serveur WebSocket en Python (`asyncio`) uniquement pour le mode dev Web. **Décision à prendre avant de commencer.**
5. Étape 1 seule (séparation sans WebSocket) suffit déjà à rendre le projet **compilable** pour Web avec un écran « transport indisponible ».

---

## T-16 — Singletons → contexte d'application ; navigation (B-29)

**Problèmes** : `_active_runner`, `_callback_registry`, `_state_registry`, `Navigator`, `_local_storage_cache` sont des globaux de module ; une seule application par processus, tests non isolés. `MaterialApp.__init__` **modifie** le `Navigator` global dès sa construction. Le `Navigator` n'est pas remis à zéro au hot restart. Le bouton retour d'Android n'est pas géré.

**Plan en 3 commits**
1. **Navigation correcte (rapide)**
   - `hot_restart()` (`cli/runner.py`) appelle `Navigator.reset()`.
   - Déplacer les effets de bord de `MaterialApp.__init__` (`Navigator.set_routes`, `set_initial_page`, `widgets.py` ~l.2210-2219) vers une méthode `_sync_navigator()` appelée par `resolve_tree` quand il rencontre un `MaterialApp`.
   - **Bouton retour** — Dart : envelopper le `home` dans `PopScope(canPop: false, onPopInvokedWithResult: (didPop, _) { if (!didPop) sendEvent('__pyflutter_back__', {}); })`. Python : id réservé `__pyflutter_back__` traité dans le thread d'UI : `if Navigator.can_pop(): Navigator.pop() else: call_plugin("system", "exitApp", wait=False)` ; shim Dart `system` → `SystemNavigator.pop()`. (Vérifier l'API `PopScope` dans votre version de Flutter ≥ 3.12.)
2. **`AppContext`** : un objet regroupant `callbacks`, `pinned_callbacks`, `states`, `navigator`, `runner`, `storage_cache`. Une `ContextVar` `current_context()`. Les fonctions de module deviennent de minces délégués (`def invoke_callback(...): return current_context().callbacks.invoke(...)`), ce qui **ne casse aucun import existant**.
3. **Tests** : fixture pytest qui crée un `AppContext` neuf par test ; supprimer ensuite les `clear_*()` manuels des `setUp`.

**Critère de fin** : deux `AppContext` dans le même processus ne partagent aucun état (test dédié).

---

## T-17 — Distribution pip réelle (B-53, B-54)

**Problème** : `pip install` n'installe ni `dart_runtime/`, ni `rust_bridge/`, ni le binaire du pont. `find_workspace_root()` retombe sur `Path(__file__).parents[3]` (le parent de `site-packages`). Les noms divergent : `pyflutter` (pyproject) / `Flarix` (README).

**Décision de nommage d'abord** : un seul nom pour le paquet PyPI, le module Python et la CLI. Le renommage touche `pyproject.toml`, `README.md`, les imports (`import pyflutter as pf` reste possible si le module garde son nom).

**Architecture cible**
- Le paquet contient : `pyflutter/_bin/<plateforme>/pyflutter-bridge[.exe]` et `pyflutter/_runtime/dart_runtime.zip` (le gabarit Dart).
- Un `RuntimeLocator` remplace `find_workspace_root` : ordre de recherche → variable `PYFLUTTER_HOME` → dépôt de développement (présence de `rust_bridge/Cargo.toml`) → données du paquet (`importlib.resources`) décompressées dans `~/.pyflutter/runtime/<version>/`.
- Roues **par plateforme** (le binaire dépend de l'OS) : `cibuildwheel` ou `maturin` (`bindings = "bin"`). À valider par un spike d'une heure avant de s'engager : (a) `setuptools` + binaire copié dans `package-data` + roue marquée non-pure (`Root-Is-Purelib: false`), (b) `maturin`. Le choix (b) prépare aussi l'embarquement (partie C) car PyO3 se construit avec maturin.
- `pyflutter doctor` : vérifie `flutter`, `cargo`, `adb`, le binaire du pont, la version du protocole.

**Cohérence des métadonnées (B-54)** — liste à cocher :
- [ ] README : « Python 3.9 » → `>=3.10` (ou abaisser `requires-python` si on veut 3.9) ;
- [ ] `requirements.txt` vs `pyproject.toml` : `pydantic` obligatoire d'un côté, optionnel de l'autre → aligner ;
- [ ] ajouter le fichier `LICENSE` (le README et le badge y renvoient) ;
- [ ] commande de test du README : `python -m unittest discover -s tests` → `python -m pytest -q` (à vérifier) ;
- [ ] régénération du protobuf : documenter `python -m grpc_tools.protoc -I ir_spec --python_out=py_framework/pyflutter/generated ir_spec/widget.proto` et **épingler** `protobuf` à la version minimale indiquée en tête de `widget_pb2.py` (`head -12`) ;
- [ ] retirer du README les chemins `d:/Projets/PYFLUTTER` et le `git clone flarix-ui/flarix`.

---

## T-18 — CI et qualité (B-55)

Créer `.github/workflows/ci.yml` (texte complet, à adapter aux versions) :
```yaml
name: ci
on: [push, pull_request]
jobs:
  python:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python: ["3.10", "3.11", "3.12", "3.13"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "${{ matrix.python }}" }
      - run: pip install pytest protobuf loguru pyyaml ruff
      - run: ruff check py_framework
      - run: cd py_framework && python -m pytest -q --ignore=tests/test_bridge_relay.py
  rust:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: sudo apt-get update && sudo apt-get install -y protobuf-compiler
      - run: cd rust_bridge && cargo build && cargo clippy -- -D warnings
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install pytest protobuf loguru pyyaml
      - run: cd py_framework && python -m pytest -q tests/test_bridge_relay.py
  dart:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
      - run: cd dart_runtime && flutter pub get && flutter analyze
```
Ajouter dans `pyproject.toml` : `[tool.ruff]` (`line-length = 120`, `select = ["E","F","I"]`) et `[tool.pytest.ini_options] testpaths = ["tests"]`. Les premiers `ruff`/`clippy` produiront des avertissements existants : les corriger dans un commit séparé **avant** d'activer `-D warnings`.

---

## T-19 — Documentation obsolète (B-51)

Fichiers qui disent le contraire de la réalité :
- `dart_runtime/SETUP.md` : prétend que les dossiers plateforme et la compilation manquent ; décrit `bridgePort` en dur (corrigé).
- `dart_runtime/lib/ir_codec.dart` (en-tête) : « NOT compiled/run ».
- `ir_spec/widget.proto` : « no diffing in the POC ».
- `README.md` : « production-ready », « 137/137 tests », « 1-to-1 avec pub.dev », « 100 % des plugins », chemins locaux, `pip install flarix`, Web/iOS comme cibles livrées.
- `ROADMAP_RUN.md` : « 117 tests », « COMPLETED & VERIFIED ».
Règle : décrire **ce qui marche aujourd'hui** (mode dev par socket), séparer clairement « fonctionne », « expérimental » (standalone), « prévu ».

---

# PARTIE B — Bugs déjà corrigés

Voir le tableau de la **section 1.1** (fichier, correction, test) ; les corrections sont dans l'historique git de `dev` (commits `fix(...)`). Les anciens constats et leurs preuves sont dans `audit/RAPPORT_INITIAL.md`.

---

# PARTIE C — Embarquer Python + Rust : protocole d'expérimentation (B-03, B-52)

But : trouver **la combinaison la plus légère** qui exécute le code Python de l'utilisateur **dans le même processus** que l'application Flutter, sur Android, iOS et desktop, sans sous-processus ni socket (contrainte iOS de `PYFLUTTER_VISION.md` §3.4.1).
Règle : **on ne choisit pas sur des impressions, on mesure.** Chaque expérience produit une ligne du tableau de résultats (C.10).

## C.0 Ce que j'ai déjà mesuré dans votre code (données réelles)

Script : `python audit/embedding/stdlib_closure.py [--no-loguru]`.

| Cas | Modules stdlib chargés | Source pure-Python | Bytecode `-OO` zippé (à livrer) |
|-----|-----------------------:|-------------------:|-------------------------------:|
| `import pyflutter` tel quel (avec `loguru`) | 127 | ≈ 2 044 Kio | **≈ 829 Kio** |
| même chose **sans** `loguru` | 72 | ≈ 1 206 Kio | **≈ 481 Kio** |

À retenir :
- `loguru` coûte à lui seul ~55 modules (dont `asyncio`) → à **ne pas embarquer** sur l'appareil.
- Les plus gros modules chargés sans loguru sont `typing`, `inspect`, `subprocess`, `locale`, `pickle`, `dataclasses`, `ast`, `shutil`, `threading`, `dis`, `random`. Parmi eux **`subprocess`, `shutil`, `tempfile`, `locale`, `pickle`, `random`, `bz2`, `lzma` ne sont tirés que par du code réservé à l'hôte** (`plugins/manager.py` : `add_flutter_package`, `core/bridge.py` : `BridgeSession`). Les rendre **paresseux** (import dans la fonction) les retire du runtime embarqué.
- Extensions C nécessaires (sans loguru) : `_sqlite3`, `_struct`, `_contextvars`, `_datetime`, `_random`, `_uuid`, `_bisect`, `_opcode`, `_typing`, `math`, `binascii`, `select`, `zlib`, plus `_bz2`/`_lzma`/`_pickle`/`_posixsubprocess` **seulement** à cause des imports hôte ci-dessus.
- Dépendances tierces actuelles du runtime : `loguru`, `pyyaml` (config, lue à l'hôte), `protobuf` (module `google`).

## C.1 Travail préparatoire obligatoire (avant toute expérience)

**P-1 — Abstraction de transport (Python)**. Aujourd'hui `call_plugin` écrit dans `runner.session.process.stdin` et `bridge.py` lit `process.stdout` : tout est couplé au sous-processus.
```python
class Transport(Protocol):
    def send(self, msg_type: int, payload: bytes) -> None: ...
    def set_receiver(self, fn: Callable[[int, bytes], None]) -> None: ...
    def close(self) -> None: ...

class SubprocessTransport:   # mode développement actuel (BridgeSession)
class NativeTransport:       # mode embarqué : appelle le module natif `_pyflutter_native`
```
`call_plugin`, `BridgeSession.send_tree`, `runner._event_loop` passent par `Transport`. Le reste du framework ne sait plus si Rust est un sous-processus ou une bibliothèque.

**P-2 — Runtime léger** (voir mesures ci-dessus) :
1. imports paresseux de `subprocess`, `shutil`, `tempfile`, `socket`, `importlib` hôte ;
2. `core/logger.py` : fournir un **logger interne minimal** (module `logging` ou fonctions vides) quand `loguru` est absent — c'est déjà le cas (`_StdLogger`) ; ajouter une variable `PYFLUTTER_EMBEDDED=1` qui force ce chemin **sans tenter d'importer loguru** ;
3. `core/config.py` : n'importer `yaml` que dans `from_file` (déjà `try/except ImportError`) et ne jamais lire le yaml sur l'appareil (le builder le convertit en JSON dans les assets) ;
4. encodage Protobuf sans la bibliothèque `google.protobuf` : soit en Rust (fonction `encode_tree` qui reçoit la structure Python), soit en Python pur (≈ 60 lignes : le Dart le fait déjà à la main dans `ir_codec.dart`) — **à mesurer** (taille du paquet `google/` contre quelques Kio de code).
Critère : `python audit/embedding/stdlib_closure.py --no-loguru` ≤ **60 modules** et ≤ **400 Kio** zippés.

**P-3 — Module natif `_pyflutter_native`** (Rust) : l'API que Python voit.
```
push_frame(msg_type: int, payload: bytes) -> None      # Python -> Dart
set_receiver(callback: Callable[[int, bytes], None])   # Dart -> Python, appelé sur le thread Python
start(app_dir: str, entrypoint: str) -> None
```
Modèle de threads : Rust crée **un thread dédié « python »** qui initialise l'interpréteur, importe le point d'entrée, puis boucle : `attendre un message dans la file TO_PYTHON (GIL relâché)` → `appeler le récepteur Python`. Dart ne touche jamais l'interpréteur directement : il ne fait que `pyflutter_push_to_python(...)` (déjà présent dans `rust_bridge/src/lib.rs`) et sonder `pyflutter_poll_dart_frame`. Cela réutilise les files déjà corrigées (bornées, `OnceLock`).

## C.2 Les candidats

| Id | Candidat | Idée | Avantages | Risques / coût |
|----|----------|------|-----------|----------------|
| **A** | CPython 3.13, `libpython` partagée + stdlib zippée | Le plus proche de ce que fait Flet ([serious_python](https://pub.dev/documentation/serious_python/latest/)) | Compatibilité totale, extensions C tierces possibles (wheels Android/iOS) | Plus gros ; chargement des extensions depuis l'APK demande des astuces |
| **A′** | CPython 3.13 **statique**, modules utiles compilés dedans, lié dans la lib Rust | Un seul `libpyflutter.so` ; LTO et `--gc-sections` sur l'ensemble | **Le plus léger avec CPython**, démarrage rapide, pas de fichiers `.so` séparés | Pas d'extensions C tierces (numpy…) ; build à maintenir |
| **B** | RustPython (choix de `PYFLUTTER_VISION.md`) | Interpréteur 100 % Rust, pas de libpython | Une seule chaîne de build (cargo), intégration naturelle | **Compatibilité inconnue** avec `inspect`, `contextvars`, `sqlite3`, `threading` ; plus lent ; je n'ai pas pu vérifier son état actuel sur mobile → à mesurer, pas à supposer |
| **C** | MicroPython ou PocketPy | Interpréteurs minuscules | Taille plancher (quelques centaines de Kio) | Sous-ensemble du langage et de la stdlib : le framework (dataclasses, inspect, contextvars, typing) ne tournera pas sans réécriture ; **sert de témoin** |
| **D** | `serious_python` tel quel | Référence | Prouve la faisabilité, permet de comparer les tailles | Plugin Dart externe ; ne remplace pas votre pont Rust |

Hypothèse de départ (à confirmer ou infirmer) : **A′ gagne sur la taille, A sur la compatibilité, B n'est retenu que s'il passe le test de compatibilité et bat A′ en taille.**

## C.3 Protocole de mesure (identique pour chaque candidat)

Même application de test : le compteur de `examples/counter` + une liste de 2 000 `Text` + un `TextField`.

| Mesure | Comment |
|--------|---------|
| Taille de base | `flutter build apk --release --target-platform android-arm64 --analyze-size` sur l'app **sans** Python (référence « Flutter seul ») |
| Taille d'un candidat | même commande ; **delta** = candidat − base. Taille réelle de téléchargement : `bundletool build-apks --bundle=app.aab --mode=universal` puis la taille de l'archive |
| Taille installée | `adb shell du -sk /data/app/*/<paquet>*` |
| Démarrage à froid | `flutter run --release --trace-startup` → `build/start_up_info.json` (`timeToFirstFrameMicros`), et `adb shell am start -W -n <paquet>/.MainActivity` (`TotalTime`) ; 10 lancements, médiane |
| Mémoire | `adb shell dumpsys meminfo <paquet>` (PSS total) 30 s après le démarrage |
| Latence d'événement | horodater côté Dart l'appui sur le bouton, et côté Dart l'arrivée du patch ; 200 appuis, p50/p95 |
| Compatibilité | `compat_probe.py` + `python -m unittest discover -s py_framework/tests` avec l'interpréteur candidat (dépendances installées dans son environnement) |
| Poids de la partie Rust | `cargo bloat --release --crates` et `twiggy top` sur la `.so` ; `llvm-size` |

Toujours mesurer **une ABI** (`arm64-v8a`) en **release**, symboles retirés.

## C.4 Expérience A / A′ — CPython minimal (pas à pas)

1. **Sources** : `git clone --branch 3.13 https://github.com/python/cpython`. Lire `Android/README.md` et `iOS/README.rst` (CPython 3.13 fournit les scripts de compilation croisée : `python Android/android.py --help` liste les sous-commandes ; **vérifier** leurs noms exacts dans votre version).
2. **Configure allégé** (adapter aux options acceptées par la version) :
   ```
   --disable-test-modules  --without-ensurepip  --without-doc-strings
   --with-lto
   CFLAGS="-Os -ffunction-sections -fdata-sections"
   LDFLAGS="-Wl,--gc-sections -Wl,--strip-all"
   ```
3. **Désactiver les modules C inutiles** dans `Modules/Setup.local` (section `*disabled*`), après avoir listé ceux qui existent avec `python -c "import sys; print(sys.builtin_module_names)"` et `ls build/lib.*/` :
   `_tkinter _curses _curses_panel _dbm _gdbm readline _lzma _bz2 _ctypes _testcapi _testbuffer _testinternalcapi _testimportmultiple _testmultiphase xxlimited xxlimited_35 _posixshmem _multiprocessing resource syslog termios mmap _elementtree pyexpat _zoneinfo`.
   Décisions à prendre module par module :
   - `_ssl` + `_hashlib` (OpenSSL, **plusieurs Mio**) : gardez-les seulement si Python fait lui-même du HTTPS. **Idée forte** : déléguer le réseau à un plugin Dart (`http`/`dio`) et retirer OpenSSL du build Python.
   - `_sqlite3` : indispensable si vous gardez `plugins/sqflite.py` (sqlite en Python) ; la bibliothèque `libsqlite3` doit être liée statiquement.
   - `_decimal`, `unicodedata`, codecs asiatiques (`_codecs_cn/hk/iso2022/jp/kr/tw`, `_multibytecodec`) : retirer si l'app n'en a pas besoin (les codecs seuls pèsent ~1 Mio).
4. **Compiler les modules utiles en statique** (variante A′) : dans `Modules/Setup.local`, section `*static*` listant les modules du tableau C.0 (`_sqlite3 _struct _contextvars _datetime _random _uuid _bisect _opcode _typing math binascii select zlib`…). Résultat : un `libpython3.13.a` avec tout dedans.
5. **Stdlib sur mesure** :
   - Lister les modules réellement chargés : `stdlib_closure.py` (liste exacte), et pour l'application utilisateur : `python -X importtime app.py 2> imports.txt`.
   - **Supprimer** ce qui n'est pas dans la liste, en particulier : `test/`, `tkinter/`, `idlelib/`, `turtledemo/`, `turtle.py`, `ensurepip/`, `pydoc_data/`, `venv/`, `curses/`, `dbm/`, `xml/`, `email/`, `http/`, `html/`, `xmlrpc/`, `wsgiref/`, `multiprocessing/`, `concurrent/`, `zoneinfo/`, `unittest/` (si absent de l'app), `asyncio/` (si absent), `__pycache__/`.
   - Compiler en bytecode sans docstrings puis ne garder que le zip :
     ```
     python -OO -m compileall -b -f -q build/stdlib      # produit des .pyc à côté des .py
     find build/stdlib -name "*.py" -delete
     (cd build/stdlib && zip -9 -r ../python313.zip .)
     ```
     Attention : `-OO` retire aussi les `assert` et les docstrings ; vérifier que `compat_probe.py` et la suite de tests passent encore.
   - Option avancée : **geler** le bytecode dans le binaire (`Tools/build/freeze_modules.py`, liste personnalisée) : plus de zip, import plus rapide.
6. **Configuration au démarrage** (`PyConfig`, côté Rust) : `isolated=1`, `use_environment=0`, `site_import=0`, `write_bytecode=0`, `parse_argv=0`, `install_signal_handlers=0`, `optimization_level=2`, `utf8_mode=1`, `module_search_paths=[<zip>, <app_dir>]`, `pathconfig_warnings=0`. `site_import=0` évite de charger `site.py` (gain de temps et de modules).
7. **Strip et alignement** : `llvm-strip --strip-unneeded` ; sous Android Gradle, ne pas compresser les `.so` (`packaging { jniLibs { useLegacyPackaging = false } }`) pour qu'elles soient mappées directement depuis l'APK ; aligner sur **16 Kio** (`-Wl,-z,max-page-size=16384`, vérifier avec `zipalign -c -P 16 4 app.apk`) — exigence Google Play pour les nouvelles versions d'Android, **à vérifier dans la doc Play actuelle**.
8. **Cibles** : `arm64-v8a` seulement (AAB), `x86_64` uniquement pour l'émulateur en debug.

## C.5 Réduire la partie Rust

- `Cargo.toml` :
  ```toml
  [profile.release]
  opt-level = "z"
  lto = "fat"
  codegen-units = 1
  panic = "abort"
  strip = true
  ```
- Dépendances : garder `prost` ; **aucune** autre (déjà retiré : `serde`, `serde_json`). Pas de `tokio`.
- Compilation Android : `cargo install cargo-ndk` puis `cargo ndk -t arm64-v8a build --release` ; `RUSTFLAGS="-C link-arg=-Wl,--gc-sections -C link-arg=-Wl,-z,max-page-size=16384"`.
- iOS : ajouter `"staticlib"` à `crate-type` (aujourd'hui `["cdylib","rlib"]`) ; Dart utilise déjà `DynamicLibrary.process()` pour iOS/macOS.
- Interpréteur depuis Rust : **comparer deux manières** et garder la plus petite :
  1. `pyo3` (feature `auto-initialize`, version qui supporte 3.13) — ergonomique, ajoute du code ;
  2. appels directs à l'API C (`Py_InitializeFromConfig`, `PyImport_ImportModule`, `PyObject_CallObject`) via quelques déclarations `extern "C"` — minimal, plus de code `unsafe`.
  Mesurer le delta de la `.so` entre les deux ; si < 150 Kio, préférer PyO3 pour la sûreté.
- Mesurer d'abord (`cargo bloat`), n'optimiser que ce qui pèse.

## C.6 Expérience B — RustPython

1. Créer un petit crate qui dépend de `rustpython-vm` (avec la fonctionnalité de stdlib gelée si elle existe dans la version choisie) et qui exécute `compat_probe.py`.
2. `cargo build --release --target aarch64-linux-android` ; mesurer la `.so` (C.3).
3. **Test éliminatoire** : `compat_probe.py` doit afficher 20/20. Chaque échec est consigné avec son message (c'est la liste de ce qu'il faudrait contourner dans le framework).
4. Puis la suite de tests du framework (en `unittest`, avec `protobuf`/`loguru` remplacés par le logger interne et l'encodeur de P-2).
5. Mesurer la latence d'événement et le démarrage : un interpréteur plus lent peut annuler le gain de taille.
Conclusion attendue dans `RESULTS.md` : « RustPython passe / ne passe pas, et voici pourquoi ».

## C.7 Expériences C et D (témoins, 1 jour chacune)

- **C** : MicroPython (port `unix` ou lib embarquée) et PocketPy : lancer `compat_probe.py`, consigner ce qui échoue. Objectif : documenter que le sous-ensemble ne suffit pas et connaître la taille plancher.
- **D** : construire l'exemple de `serious_python` en release et relever ses tailles (APK, installé, démarrage). C'est la référence « ce que fait déjà quelqu'un d'autre » ; si A′ n'est pas nettement plus léger, l'intérêt de votre propre chaîne est à rediscuter.

## C.8 Particularités par plateforme

- **Android** : Python et la stdlib zippée vont dans `assets/` (lus par `zipimport` depuis l'APK) ou sont extraits au premier lancement dans `filesDir` ; les `.so` vont dans `jniLibs/<abi>/`. Si vous gardez des extensions C séparées (variante A), elles doivent être chargées depuis l'APK (c'est ce que fait `serious_python`).
- **iOS** : pas de sous-processus ; l'interpréteur doit être **lié dans l'application** (xcframework ou lib statique) ; les extensions C doivent être des frameworks (variante A′ évite le problème). Vérifier la règle App Store sur l'exécution de code embarqué (guideline 2.5.2) : le code Python doit être **livré dans l'app**, jamais téléchargé.
- **Windows** : distribution « embeddable » de python.org (`python313.dll` + `python313.zip`) à côté de l'exécutable, ou lien statique.
- **Linux/macOS** : `libpython` à côté du binaire (`rpath $ORIGIN` / `@rpath`), signature de code sous macOS.

## C.9 Calendrier proposé

| Semaine | Livrable |
|---------|----------|
| 1 | P-1 (transport), P-2 (runtime léger) ; `stdlib_closure.py` sous le seuil |
| 2 | Expériences A, A′ et B sur Android arm64 ; remplir le tableau C.10 |
| 3 | Expériences C et D ; note de décision (1 page) ; si A′ gagne : script `tools/embed/build_python.sh` reproductible |
| 4+ | Intégrer le gagnant dans `pyflutter build` : copie de la lib, assets, `PyConfig`, test de bout en bout sur appareil ; puis iOS et desktop |

## C.10 Tableau de résultats à remplir (`audit/embedding/RESULTS.md`)

| Mesure | Flutter seul | A | A′ | B | C | D |
|--------|-------------:|--:|---:|--:|--:|--:|
| Delta d'APK release arm64 (Mio) | 0 | | | | | |
| Taille téléchargement AAB (Mio) | | | | | | |
| Taille installée (Mio) | | | | | | |
| Démarrage à froid, médiane (ms) | | | | | | |
| PSS 30 s (Mio) | | | | | | |
| Latence événement p50 / p95 (ms) | | | | | | |
| `compat_probe.py` (x/20) | n/a | | | | | |
| Suite de tests du framework | n/a | | | | | |
| Extensions C tierces possibles | n/a | oui | non | ? | non | oui |
| Effort de maintenance (S/M/L) | | | | | | |

**Règle de décision** : éliminer tout candidat qui échoue `compat_probe.py` ou la suite de tests. Parmi les restants, prendre le plus petit delta d'APK ; à ±10 % près, prendre le moins coûteux à maintenir.

---

# PARTIE D — Ce qui manque pour un « vrai » framework (feuille de route)

Chaque ligne renvoie au ticket qui prépare le terrain ; les lignes sans ticket sont de nouveaux chantiers à ouvrir.

| Priorité | Manque | Point de départ |
|----------|--------|-----------------|
| P0 | Modèle de threads clair, rendu par frames | T-02 |
| P0 | Plugins réels, erreurs typées, jamais de faux succès | T-01, T-08, ticket B-02 (corrigé) |
| P0 | Standalone réel (interpréteur embarqué) | Partie C |
| P0 | Distribution pip avec le pont précompilé | T-17 |
| P0 | Hot reload complet (modules du projet, `--watch`, état stable) | T-13 (B-59), T-03 |
| P1 | Cycle de vie complet des `State` | T-03 |
| P1 | Navigation complète (retour système, routes nommées avec arguments, onglets imbriqués) | T-16 |
| P1 | Écran d'erreur dans l'app (équivalent du « red screen ») et traces lisibles | à ouvrir : envoyer un `MSG_ERROR` Python→Dart qui affiche l'exception |
| P1 | Validation des props, enums typés | T-11 |
| P1 | Configuration par projet, `pyflutter doctor` | T-14, T-17 |
| P1 | Tests d'intégration Python↔Rust↔Dart, CI | T-18, `tests/test_bridge_relay.py` comme modèle |
| P2 | Listes paresseuses (`ListView.builder`) : aujourd'hui tous les éléments sont envoyés | à ouvrir : protocole `itemCount` + demande de plage `0x0B`, Dart ne construit que le visible |
| P2 | Internationalisation, accessibilité (`Semantics`), focus/clavier | à ouvrir |
| P2 | `async def` natif dans les callbacks, `asyncio` intégré | T-02 (thread d'UI) puis boucle `asyncio` sur ce thread |
| P2 | Observabilité : compteur de rebuilds/patchs, inspecteur d'arbre | à ouvrir |
| P2 | Composants manquants (`DataTable`, `Stepper`, pickers de date/heure, `CustomPaint`…) | après T-11 (le contrat de props rend l'ajout mécanique) |

---

# ANNEXE — Scripts fournis

| Fichier | Rôle |
|---------|------|
| `audit/repro_core.py` | Bugs de diff, callbacks, logging, config, CLI |
| `audit/repro_state.py` | Composants gelés, deadlock de build, états |
| `audit/repro_rpc.py` | Appel plugin depuis un callback, erreurs Dart |
| `audit/repro_cli.py` | Découverte du point d'entrée, manifeste, modules |
| `audit/embedding/stdlib_closure.py` | Modules stdlib réellement chargés + taille à livrer |
| `audit/embedding/compat_probe.py` | Test de compatibilité d'un interpréteur (20 contrôles) |
| `audit/RAPPORT_INITIAL.md` | Rapport d'origine (preuves et contexte de chaque bug) |
