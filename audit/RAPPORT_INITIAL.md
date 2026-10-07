> Document historique : constats d'origine avec preuves. Le guide de correction à suivre est `AUDIT_BUGS.md` (racine du dépôt).

# AUDIT Afik — bugs, erreurs de logique, manques

Date : 2026-10-06 · Périmètre : `py_framework/`, `rust_bridge/`, `dart_runtime/`, CLI, exemples, README.

## Comment lire ce document

- **[V]** = **vérifié par exécution** (script de repro dans `audit/`, sortie réelle observée).
- **[L]** = **lu dans le code, non exécuté** (Dart et Rust : aucun SDK Flutter/cargo ici, donc rien n'a été compilé ni lancé de ce côté).
- Sévérité : 🔴 bloquant / dangereux · 🟠 majeur · 🟡 moyen · ⚪ mineur.
- Les 137 tests existants passent (`pytest`) : ils ne couvrent aucun des bugs ci-dessous. Le badge « production-ready » du README est faux en l'état.

Repros (depuis la racine du dépôt, `pip install pytest protobuf loguru pyyaml` requis) : `python audit/repro_core.py` (B-07, B-09, B-10, B-13, B-30, B-04), `python audit/repro_state.py` (B-11, B-12), `python audit/repro_rpc.py` (B-01, B-02), `python audit/repro_cli.py` (B-14, B-32).

---

## Statut des corrections (mis à jour)

**Corrigés et couverts par des tests** (`py_framework/tests/test_audit_regressions.py`, `test_bridge_relay.py` — ce dernier lance le vrai binaire Rust) :
B-01, B-02 (RPC non bloquant, erreurs explicites ; le fallback local n'est utilisé que sans runtime connecté), B-04 (`--release`/`--profile`, `remove_flutter_package`), B-05 (port transmis au Dart), B-07, B-08 (resync après reconnexion, un thread par client), B-09, B-10, B-11, B-12, B-13, B-14 (module nommé `afik_app_<nom>`, classe conservée au hot reload), B-15, B-16 (jeton de session + limite de trame), B-30, B-32, B-33, B-38 (sqlite réel, identifiants validés, erreurs propagées), B-42, B-43, B-46, B-49, plus la fiabilité de la boucle d'événements (B-20 partiel : registre de callbacks verrouillé).

**Corrigés côté Dart/Rust mais non compilés ici** (pas de SDK Flutter ; `cargo build` OK) : B-05, B-43, B-46, B-49 et le handshake `hello` du client Dart. À vérifier avec `flutter run`.

**Corrigés partiellement** : B-06 (`local_auth`, `permission_handler`, `secure_storage` refusent désormais au lieu de simuler un succès ; les vrais packages restent à brancher), B-03 (le build échoue si `cargo` échoue et avertit qu'aucun interpréteur n'est embarqué ; l'embarquement lui-même reste à faire), B-37 (fallback local limité au mode hors runtime).

**Ouverts** : B-17, B-18, B-19, B-21 (dispose des `State` — le faire mal casserait l'état des pages empilées), B-22, B-23, B-24, B-27, B-29, B-31, B-34 à B-36, B-39 à B-41, B-44, B-45, B-47, B-48, B-50 à B-55, et toute la section 4.

**Nouveau bug trouvé pendant les corrections (corrigé)** — B-56 🟠 [V] : `infer_call_site_key` (`core/state.py`) ignorait toute frame dont le **nom de fichier** finit par `state.py`, `widget_base.py` ou `render.py`. Un projet utilisateur avec un fichier `state.py` (très courant) donnait la **même clé** à tous les `StatefulComponent` d'une même ligne → états partagés. Le test se fait maintenant sur le nom de **module** (`afik.*`).

---

## 0. Résumé — les 10 problèmes qui comptent le plus

| # | Sév. | Problème |
|---|------|----------|
| 1 | 🔴 | Tout appel plugin fait **depuis un callback** (clic bouton) bloque la boucle d'événements jusqu'au timeout, puis renvoie une **fausse valeur** (`authenticated: True`, `permission: granted`) [V] |
| 2 | 🔴 | Une erreur renvoyée par Dart est **avalée** et remplacée par la donnée factice locale [V] |
| 3 | 🔴 | Le build « standalone » est une façade : aucun interpréteur Python n'est embarqué, la lib Rust ne fait que deux files d'attente, le build affiche « succès » [L] |
| 4 | 🔴 | `afik build --release` construit **toujours en debug** ; `afik remove` plante (`ImportError`) [V] |
| 5 | 🔴 | `--port` / `port:` du yaml cassé : le Dart a `7879` en dur [L] |
| 6 | 🟠 | Plugins « sécurité » factices côté Dart : `local_auth` renvoie toujours authentifié, `permission_handler` toujours accordé, `secure_storage` en RAM et en clair [L] |
| 7 | 🟠 | Patch d'arbre incorrect pour les listes à `key` réordonnées → UI Dart périmée [V] |
| 8 | 🟠 | Relais Rust : un client Dart qui se reconnecte reçoit un **arbre périmé** (les patchs ne sont jamais appliqués au cache) [L] |
| 9 | 🟠 | Callbacks de SnackBar/Dialog supprimés dès la frame suivante → bouton « Annuler » mort [V] |
| 10 | 🟠 | Fuite + tempête de rebuilds avec `Watch` ; blocage définitif (`tree_lock` non réentrant) si un signal est écrit pendant un build [V] |

---

## 1. Bugs bloquants / critiques

### B-01 🔴 [V] Appel plugin depuis un callback = deadlock jusqu'au timeout + faux succès
- `cli/runner.py:446-484` (`_event_loop`) exécute `invoke_callback()` **dans le thread qui lit aussi les réponses Dart** (`session.next_event()`).
- `plugins/manager.py:39-76` (`call_plugin`) envoie la requête puis `event.wait(timeout)`. La réponse ne peut pas être lue tant que le callback n'a pas rendu la main → **timeout systématique**.
- Après timeout on tombe dans `_dispatch_local_fallback` (`manager.py:76`), qui renvoie des données **inventées**.
- Preuve (`audit/repro_rpc.py`) : Dart répond `authenticated: False`, appel depuis un callback → bloque 2.0 s puis retourne `{'authenticated': True}`. Le même appel depuis un autre thread renvoie correctement `False`.
- Conséquences concrètes : `show_snack_bar` / `show_dialog` (qui passent par `invoke_plugin_method` → `call_plugin`) **gèlent la boucle d'événements 3 s** à chaque appel depuis un handler ; `local_auth.authenticate()` → toujours « OK » ; `permission_handler` → toujours « granted » ; `shared_preferences.get_*` depuis un handler → lit le cache mémoire Python au lieu du vrai stockage.
- Correctif : ne jamais bloquer le thread de lecture. Soit un thread de lecture dédié qui ne fait que router (réponses → `Event`, callbacks → file vers un worker), soit API `async`/future. Les appels « fire-and-forget » (`invoke_plugin_method`) ne doivent **pas** attendre de réponse.

### B-02 🔴 [V] Erreurs Dart avalées, remplacées par des données factices
- `manager.py:64-72` : le `raise RuntimeError("Error in ...")` est levé **dans** le `try`, attrapé par `except Exception` (ligne 71, log en `debug`), puis le code continue vers `_dispatch_local_fallback`.
- Preuve : Dart renvoie `error: "UnsupportedError: boom"` → l'appelant reçoit `{'authenticated': True}`.
- Idem si `json.dumps(args)` échoue (argument non sérialisable) : l'exception est avalée et on obtient une fausse réponse.
- Correctif : séparer « transport indisponible → fallback dev explicite » de « erreur du plugin → lever `PlatformException` ». Le fallback ne doit jamais être silencieux en production (flag explicite `AFIK_OFFLINE_MOCKS=1`, ou lever `PluginUnavailableError`).

### B-03 🔴 [L] Build standalone (APK/IPA/desktop) : non fonctionnel
- `rust_bridge/src/lib.rs` ne contient que deux `VecDeque` ; **rien** n'embarque ni ne lance Python (`afik_poll_python_frame` / `afik_push_to_dart` n'ont aucun appelant). Aucun CPython/PyO3/Chaquopy/BeeWare.
- `cli/builder.py:89-101` : `cargo build` pour l'**hôte** (pas de cible Android `aarch64-linux-android` via `cargo-ndk`, pas de `.so` copié dans `jniLibs`, pas de `.a` iOS). Un échec de `cargo` est un simple `warning` (ligne 100) puis le build continue.
- `builder.py:72-86` copie `*.py` dans `dart_runtime/assets/app/` mais `pubspec.yaml` ne déclare **aucun** `assets:` → les fichiers ne sont pas empaquetés. Sous-dossiers/paquets/images utilisateur non copiés.
- `flutter build` réussit → log `🎉 build completed successfully!` alors que l'app obtenue est un écran de chargement infini.
- Le README (« Build APKs… zero-config », « production-ready ») est donc trompeur. Voir §4 pour ce qu'il faut réellement.

### B-04 🔴 [V] CLI : `--release` ignoré, `remove` cassé
- `cli/main.py:139` : `--debug` a `default=True`, puis `main.py:246` `if args.debug or ...: is_release = False` **écrase toujours** `--release`. Repro : `main(["build","apk","--release"])` → `AfikBuilder(release=False)`. Le mode `profile` accepté par `--mode` est aussi ignoré.
- `cli/main.py:179` importe `remove_flutter_package` qui **n'existe pas** dans `plugins/manager.py` → `ImportError` (documenté dans le README comme commande).
- `app.py:81-91` (`python main.py build …`) lit `sys.argv` à la main : tout script utilisateur dont le premier argument est `build` est détourné vers le build ; aucun autre argument (`--device`, `--port`) n'est lu.

### B-05 🔴 [L] Port configurable non honoré
- `dart_runtime/lib/main.dart:213` : `static const int bridgePort = 7879`. Le runner passe `--dart-port <port>` à Rust (`runner.py:347`) et `adb reverse tcp:<port>`, mais Dart se connecte toujours à 7879. `afik run -p 9000` ou `port:` dans le yaml ⇒ jamais de connexion. (`dart_runtime/SETUP.md` le reconnaît.) Correctif : `--dart-define=AFIK_PORT=…` passé par `_start_flutter`.

### B-06 🟠 [L] Plugins Dart factices présentés comme natifs (sécurité)
- `lib/plugins/local_auth_shim.dart` : `authenticate` → toujours `{'authenticated': True}` (aucun appel au package `local_auth`).
- `permission_handler_shim.dart` : `checkPermission` → `granted` par défaut, `requestPermission` → `granted` sans rien demander.
- `secure_storage_shim.dart` : `Map` en mémoire, non chiffrée, perdue au redémarrage (le README annonce Keychain/KeyStore).
- `hive_shim.dart`, `sqflite_shim.dart` : stockage en mémoire (sqflite : `execute`/`update` ne font rien, `delete` vide la table entière, aucune requête réelle). `camera`, `audioplayers`, `video_player`, `share_plus`, `webview_flutter`, `chewie`, `printing`/pdf, `flutter_local_notifications` : aucun de ces packages n'est dans `pubspec.yaml` (seuls `device_info_plus`, `file_picker`, `path_provider`, `shared_preferences`, `url_launcher` le sont). Le README annonce « 1-to-1 parity avec pub.dev » : faux pour ~20 plugins.
- Un développeur qui protège une action avec `local_auth` n'a **aucune** protection.

---

## 2. Bugs majeurs

### B-07 🟠 [V] Diff d'arbre : listes à `key` réordonnées
- `core/render.py:65-73` met la `key` dans l'identifiant de nœud (`root.0[a]`). `diff_snapshots` compare **par position** : après un swap `[a,b]→[b,a]`, il émet des ops `{"id": "root.0[b]", ...}` ; côté Dart `findNodeById` cherche `root.0[b]` qui n'existe pas (l'arbre Dart a `root.0[a]`) → `ir_codec.dart` ignore silencieusement l'op (`if (target != null)`). **L'UI reste périmée** alors que Python croit l'avoir mise à jour (`_last_snapshot` déjà avancé).
- Même cause : une prop `_nid` figure dans les props modifiées.
- Correctif : si un `_nid` change entre ancien et nouveau nœud → retourner `None` (arbre complet), ou implémenter un vrai diff par clé (insert/remove/move).

### B-08 🟠 [L] Relais Rust : cache d'arbre périmé à la reconnexion
- `rust_bridge/src/main.rs:166-174` ne met en cache que `MSG_RENDER_TREE`. Les `MSG_TREE_PATCH` sont relayés mais **jamais appliqués** au cache. Si Dart se (re)connecte (hot restart `R`, crash, veille mobile), il reçoit l'arbre d'origine alors que `BridgeSession._last_snapshot` (Python) suppose Dart à jour ⇒ divergence permanente jusqu'au prochain changement structurel.
- Correctif : Python doit renvoyer un arbre complet à chaque (re)connexion (signal `hello` de Dart), ou le relais doit invalider le cache à chaque patch et demander un resync.
- Aussi : la boucle d'`accept` (`main.rs:~195-240`) lit le premier client **sur le thread principal** ; un second client (ancien socket zombie après hot restart/Wi-Fi) n'est jamais accepté tant que le premier n'est pas fermé.

### B-09 🟠 [V] Callbacks hors-arbre purgés immédiatement
- `core/widget_base.py:133-143` : `sweep_stale_callbacks` supprime **tout** id absent des widgets des 2 dernières frames. Les callbacks de `show_snack_bar(on_action=…)` / `show_dialog(on_confirm/on_cancel=…)` (`plugins/overlay.py`, enregistrés par `_register_callback(id, fn)`) ne sont dans aucun widget → supprimés dès le prochain `send_tree`. Preuve : enregistré puis après une frame → `[]`. Le bouton « Annuler »/« Confirmer » d'un dialog ouvert reste cliquable mais ne fait plus rien dès que l'UI se met à jour (ex. un `Signal` avec `auto_update`).
- Bonus : en chemin « arbre complet » `sweep` est appelé **deux fois** par frame (`bridge.py:79` puis `render.py:175`), donc les « 2 générations conservées » sont la même frame → un clic arrivé pendant un rebuild est ignoré sans log (`invoke_callback` retourne silencieusement si id inconnu, `widget_base.py:95-96`).
- Correctif : un registre séparé pour callbacks « éphémères » avec TTL / dispose explicite.

### B-10 🟠 [V] `Watch` : fuite de listeners et rebuilds en cascade
- `core/state.py:321-332` : chaque rebuild crée un **nouveau** `Watch` qui ajoute `self._on_signal_changed` au signal sans jamais le retirer. Repro : 50 frames → 50 listeners. Un `signal.value = x` déclenche alors 50 `update()` (chacun = rebuild complet + envoi), N croissant à chaque frame.
- Même problème pour `Computed` (jamais disposé, `state.py:178-194`) et `Effect` non disposé.
- Correctif : désinscription au prochain build / `dispose()` lié au cycle de vie, listeners faibles (`weakref.WeakMethod`).

### B-11 🟠 [V] Deadlock : écrire un état pendant un build
- `runner.py:282` `tree_lock = threading.Lock()` (non réentrant) est pris autour de `build()` + `send_tree()` (`runner.py:361/479/490/512/543`). Tout `update()` déclenché **pendant** le build (`Signal.value = …`, `State.set_state()` dans `init_state`/`did_update_widget`, `Navigator.push`, `show_snack_bar`, `Widget.set_text()` auto-update) rappelle `push_update` qui reprend le même lock → **blocage définitif**. Repro : signal écrit dans `State.init_state()` → `push_update` ne finit jamais (>2 s).
- Correctif : `RLock` + drapeau « build en cours » qui transforme `update()` en « marquer sale, rebuild après ».

### B-12 🟠 [V] Un composant enfant d'un layout persistant est « gelé »
- `core/render.py:48` : `current.children = [resolve_tree(c) …]` **remplace en place** la liste d'enfants du widget retourné. Avec le style impératif (`self.layout = Column(); self.layout.add_widget(MonComposant())` puis `build()` renvoie `self.layout`), le composant est remplacé par son premier rendu : il n'est **jamais reconstruit**. Repro : `Badge.build` appelé 1 fois en 2 frames, le texte reste `build#1`.
- Concerne aussi `StatefulComponent`/`Watch`/`SignalBuilder` placés dans un layout mis en cache → la réactivité s'arrête silencieusement.
- Correctif : `resolve_tree` doit produire un **nouvel** arbre (copie) sans muter les widgets source.

### B-13 🟠 [V] Gestion d'erreur du logging qui plante : `loguru` + accolades
- `widget_base.py:105,498` : `logger.error(f"... {e}", exc_info=True)`. Avec loguru, la présence d'un kwarg déclenche `message.format(**kwargs)`; si le message de l'exception contient `{` `}` (dict, JSON, `KeyError("{id}")`…) → **`KeyError`/`IndexError` levé dans le gestionnaire d'erreur**, le traceback d'origine est perdu et la suite du callback (re-render) est sautée. Repro : `invoke_callback` d'une fonction qui lève `KeyError("{id}")` → `invoke_callback CRASH KeyError`.
- `exc_info=True` n'est pas une option loguru (il faut `logger.opt(exception=True)`), donc aucune stack trace n'est jamais affichée de toute façon.
- `core/form.py:61` : `logger.error("… %s", e)` (style `%`) avec loguru → le `%s` s'affiche littéralement.
- Plus largement `core/logger.py` appelle `logger.remove()` sur le logger **global** de loguru à l'import : une bibliothèque ne doit pas détruire la config de l'application hôte ; niveau `DEBUG` forcé, non configurable.

### B-14 🟠 [V] Entrypoint : découverte non déterministe + hot-reload qui ignore `pf.run(app)`
- `runner.py:98-207` : `load_app_from_file` choisit une classe par heuristiques sur `dir(module)` (ordre alphabétique) : avec `AboutPage` et `HomePage` zéro-arg, c'est `AboutPage` qui devient la racine, même si l'utilisateur a écrit `pf.run(HomePage())`. Repro confirmé. Et `hot_reload`/`hot_restart` repassent par cette heuristique et **jettent l'instance passée à `pf.run`**.
- `runner.py:117-119` : `sys.modules[module_name] = module` avec `module_name = stem` ⇒ un script nommé `random.py`, `json.py`, `logging.py`, `typing.py`… **remplace le module de la stdlib** pour tout le process. Repro : `sys.modules['random']` devient le fichier utilisateur.
- `runner.py:504-507` (hot reload « avec état ») copie tous les attributs publics de l'ancienne instance vers la nouvelle : les widgets créés dans `__init__` (style Qt : `self.layout`, `self.button`…) écrasent ceux du code rechargé → **les modifications d'UI ne sont jamais visibles** après `r`.
- Seul le module d'entrée est rechargé : un fichier importé (`from screens import home`) n'est pas rechargé (`importlib.reload` absent, pas de file watcher, `r` manuel uniquement). Le README liste « hot-reload daemon » en TODO mais annonce « hot reload » partout.

### B-15 🟠 [L] `ensure_port_free` tue un processus arbitraire
- `runner.py:61-95` : si le port est occupé, `fuser -k <port>/tcp` (Linux/mac) ou `taskkill /F /PID` (Windows) **tue ce qui écoute dessus**, sans vérifier que c'est un pont Afik. `7879` peut être n'importe quel service de l'utilisateur. De plus `fuser` est absent sur macOS et sur beaucoup d'images minimales (échec silencieux).
- Correctif : essayer de se connecter/handshaker, sinon choisir un autre port libre et le propager (cf. B-05).

### B-16 🟠 [L] Relais TCP sans authentification
- `main.rs:~155` : `TcpListener::bind("127.0.0.1:port")` accepte **n'importe quel processus local** : il peut lire l'arbre UI (données potentiellement sensibles) et injecter des `CallbackEvent` / `PluginResponse` (ex. fausse réponse `local_auth`). Sur machine multi-utilisateurs ou avec une page malveillante qui pivote via un autre service local, c'est exploitable. Pas de jeton de session.
- `read_frame` (`main.rs:45`) : `vec![0u8; len]` avec `len` (u32) non borné → 4 Gio alloués par une trame forgée. Même défaut côté Python `bridge.py:28-37` (pas de limite, lecture courte non vérifiée).
- Correctif : jeton aléatoire par session passé à Rust et à Dart (`--dart-define`), taille max de trame.

---

## 3. Bugs moyens et mineurs

### Python — cœur / état
- **B-17 🟡 [L]** `Signal.value` setter (`state.py:96`) compare avec `!=` : mutation en place d'une liste/dict (`sig.value.append(x)`) ne notifie jamais ; `sig.update(lambda l: l.append(x))` met la valeur à `None` (piège classique, aucune garde). Comparaison `!=` explose avec numpy/pandas (`ValueError: truth value ambiguous`).
- **B-18 🟡 [L]** `batch()` (`state.py:268-286`) : variables globales non thread-safe (`_batch_depth`, `_batched_listeners`) ; `update()` appelé même si le bloc a levé ; un `Computed` rejoué à la sortie déclenche son propre `update()` hors batch → rebuilds multiples.
- **B-19 🟡 [L]** `update()` est **synchrone, sans coalescence** : 1 000 écritures de signal = 1 000 rebuilds complets + envois sur le thread appelant. Pas de planificateur de frame (`markNeedsBuild` + rebuild au prochain tick), pas de debounce.
- **B-20 🟡 [L]** Aucune synchronisation autour de l'état utilisateur : `invoke_callback` s'exécute **hors** `tree_lock` (`runner.py:476`) pendant qu'un thread (`pf.update()` depuis un worker) construit l'arbre. `_callback_registry` est itéré (`widget_base.py:141`) pendant que d'autres threads y insèrent → `RuntimeError: dictionary changed size during iteration` possible.
- **B-21 🟡 [L]** `State` : `dispose()` n'est **jamais appelé** quand un widget quitte l'arbre (seulement au hot restart, `state.py:52-60`). `_state_registry` ne se vide jamais : fuite mémoire + timers/threads lancés dans `init_state` jamais arrêtés. La clé d'état est `fichier:ligne#index` → après toute édition du fichier qui décale des lignes (cas typique du hot reload) l'état est perdu ou, pire, réattribué à un autre widget ; dans une liste, insérer en tête décale l'état sur le mauvais élément.
- **B-22 🟡 [L]** `Component.build()` (`widget_base.py:628-695`) devine le widget racine via les attributs `_central_widget`, `central_widget`, `layout`, `root`, `body`, `column`, `row`, et l'AppBar via `app_bar`/`appbar`/`app_bar_widget`/`fab`… Un attribut utilisateur qui porte un de ces noms (`self.body = "texte"`) casse silencieusement la construction. Idem pour les noms de méthodes publiques de `Widget` (`text()`, `value()`, `count()`, `clear()`, `center()`, `card()`, `padding()`, `add()`) : `self.count = 0` (exemple du README) **écrase** la méthode `count()` ; `self.value`/`self.text` aussi.
- **B-23 🟡 [L]** `_call_callable` (`widget_base.py:41-90`) dispatche par introspection de signature : un handler `lambda e: …` sur un bouton (pas de données) est appelé **sans argument** → `TypeError` (confirmé : « missing 1 required positional argument: 'e' »). Pour un handler à 1 paramètre positionnel, `list(kwargs.values())[:1]` prend la **première valeur du dict** quel que soit son nom. Les `event_data` sont toujours des `str` côté Dart ; seules certaines classes (`Switch`, `Checkbox`, `Slider`) convertissent les types — un `on_click` générique reçoit des chaînes (`"false"` truthy).
- **B-24 ⚪ [L]** `Widget._populate_props` (`widget_base.py:162-172`) convertit tout en `str(v)` : une liste/dict/lambda passée par erreur devient une chaîne `"<function …>"` sans erreur ; aucune validation de nom de prop ni de valeur (couleurs invalides, enums mal orthographiés) → erreurs visibles uniquement à l'écran.
- **B-25 ⚪ [L]** Prop vide ambiguë : diff envoie `""` pour « prop supprimée » et pour « valeur devenue vide » (`render.py:131-133`) ; Dart supprime la clé dans les deux cas (`main.dart` `_handleTreePatch`).
- **B-26 ⚪ [L]** `resolve_tree`/`assign_node_ids`/`widget_to_snapshot`/`widget_to_proto` rappellent `resolve_widget` à chaque étape et `render_tree_frame` re-résout et re-numérote un arbre déjà concret → 3-4 parcours complets par frame ; `inspect.stack()` dans `pf.run` (`app.py:67`, coûteux) au lieu de `sys._getframe`.
- **B-27 🟡 [L]** `Form` (`core/form.py`) : `FormKey._fields` garde des références fortes à **chaque** champ recréé à chaque rebuild (fuite) ; `validate()`/`get_values()` parcourent les copies obsolètes. `Form` n'enregistre que les enfants présents à la construction.
- **B-28 ⚪ [L]** `overlay.py:44-47` : `duration` ambigu (`< 100` = secondes, sinon millisecondes ; `duration=120` → 120 ms). Le `Duration(seconds=4)` par défaut est un objet partagé.
- **B-29 ⚪ [L]** Singletons globaux partout (`_active_runner`, `_callback_registry`, `_state_registry`, `Navigator`, `_local_storage_cache`) : une seule app par process, tests non isolés, `MaterialApp.__init__` **mute** le `Navigator` global à la construction (`widgets.py:~2205`) et `Navigator` n'est pas réinitialisé au hot restart (pages empilées conservées). Aucune gestion du bouton retour système Android (pas de `PopScope` côté Dart : le retour quitte l'app au lieu de dépiler la pile Python).

### Python — config / CLI / manifests
- **B-30 🟠 [V]** `AfikConfig.from_file` (`core/config.py`) plante : `dependencies:` vide (→ `AttributeError: NoneType`), fichier racine en liste, `port: abc` (`ValueError`). À l'inverse, un YAML invalide est **avalé** (`except Exception: data = {}`) → config vide sans avertissement : les permissions disparaissent silencieusement.
- **B-31 🟡 [L]** `AfikConfig.save()` réécrit le fichier à partir de 4 champs : commentaires et toute clé inconnue sont **perdus** à chaque `afik add`. `add_flutter_package` écrit la version `any` et modifie le `pubspec.yaml` du dépôt framework (`manager.py:455-487`), pas celui du projet : les `dependencies.flutter` du `afik.yaml` utilisateur ne sont **jamais** appliquées au runtime Dart (aucun code ne les lit pour générer le pubspec).
- **B-32 🟠 [V]** `manifest_sync.py` : le titre n'est **pas échappé** → `name: "Tom & Jerry"` produit un `AndroidManifest.xml` invalide (repro : `INVALID XML`), et le build échoue. Permission inconnue/typo (`camara`) ignorée sans warning. Les permissions retirées du yaml ne sont jamais retirées du manifeste. Le fichier modifié est celui du **dépôt framework partagé**, pas d'une copie par projet. `if perm not in content` détecte aussi la permission dans un commentaire XML. Aucune des permissions n'est fournie pour les plateformes desktop.
- **B-33 🟡 [L]** `devices.py:94-105` : si `-d <id>` est donné, la plateforme est **devinée** par `isdigit()` / `len > 10` / `startswith("1")` → un id commençant par « 1 » ou long est traité comme Android (adb reverse inutile, mauvais `targetPlatform`). `EOFError` à l'invite interactive → `sys.exit(0)` (succès silencieux).
- **B-34 🟡 [L]** `runner.py` : `AfikRunner.__init__` lève `FileNotFoundError` si le binaire Rust manque (`find_bridge_binary`), même avec `--attach` ; trace Python brute au lieu d'un message. `_build_and_tag_tree` (`runner.py:291-304`) écrit `debug_banner` dans `tree.props` **avant** la résolution : si `build()` renvoie un `Component`, la prop est perdue au `resolve_tree`.
- **B-35 ⚪ [L]** Modèle de projet (`cli/creator.py`) : le README généré annonce un raccourci `d` qui n'existe pas dans `_handle_key` ; `--description` avec des guillemets casse le YAML généré.
- **B-36 ⚪ [L]** `cli/main.py` : `--debug` et `--release` ne sont pas exclusifs ; `run` tombe dans le `if args.command == "build"` suivant sans `return` (inoffensif mais fragile).

### Plugins Python (`plugins/`)
- **B-37 🔴 [L]** `manager._dispatch_local_fallback` (400 lignes) : tout appel, **y compris en production** si le runtime est lent/absent, renvoie des valeurs plausibles et fausses : permissions `granted`, biométrie `authenticated`, `connectivity = wifi`, `sqflite.insert → id 1`, `notifications actives` fictives, `device_info` = valeurs en dur (`numberOfProcessors: 4`, `hostname: localhost`). Un échec réel est indiscernable d'un succès (cf. B-01/B-02).
- **B-38 🟠 [L]** `plugins/sqflite.py` : noms de table/colonnes interpolés dans du SQL par f-string (`INSERT INTO {table} ({cols})…`) → **injection SQL** si un nom provient d'une entrée utilisateur ; chaque opération est exécutée **deux fois** (shim Dart factice + `sqlite3` local), les erreurs SQL sont avalées (`except Exception: return 1`, id d'insertion fictif), `query` retourne les lignes du faux Dart si non vide, sinon la base locale : deux sources de vérité qui divergent.
- **B-39 🟡 [L]** `Dart plugin_registry.dart` convertit tous les arguments en `String` (`v?.toString()`) : dicts/listes/bools arrivent sous forme `"{a: 1}"` (syntaxe Dart, pas du JSON). Seuls les shims dont l'appelant Python a déjà `json.dumps` (sqflite `values`) fonctionnent ; `hive.put` avec une valeur structurée est corrompue.
- **B-40 🟡 [L]** `MethodChannel.set_method_call_handler` et `EventChannel.listen` sont **non fonctionnels** : `get_channel_handler` n'est appelé nulle part hors de `channel.py`, aucun message protocolaire n'achemine des appels/événements Dart → Python, et `EventChannel._listener` n'est jamais invoqué. Le « fallback universel MethodChannel » ne marche que pour des canaux que le plugin expose réellement (la plupart des packages pub.dev utilisent Pigeon / des canaux privés) : l'affirmation « 100 % des plugins pub.dev » est fausse.
- **B-41 ⚪ [L]** `call_plugin` timeout par défaut 3 s (5 s côté `MethodChannel`) : un `file_picker`/`camera`/`authenticate` interactif (secondes à minutes) expire toujours, puis renvoie le faux fallback.

### Rust (`rust_bridge/`)
- **B-42 🟠 [L]** `lib.rs:27-28` : `static mut` + `&` sur statiques mutables (UB / lint `static_mut_refs`, erreur en édition 2024) ; remplacer par `OnceLock<Mutex<VecDeque>>`. `afik_bridge_destroy` n'appelle pas `ensure_initialized`. Files **non bornées** (aucune contre-pression).
- **B-43 🟠 [L]** `lib.rs:139` / `ffi_bridge.dart:186-188` : si une trame dépasse 2 Mio (arbre volumineux, images base64), `poll` renvoie `-1` **sans la dépiler** ; Dart fait `break` et recommence 8 ms plus tard → la file est **bloquée définitivement** (head-of-line). Le buffer n'est jamais agrandi.
- **B-44 🟡 [L]** `main.rs` : un seul client Dart géré à la fois (voir B-08), `.unwrap()` sur `Mutex::lock` (panique en cascade si empoisonné), `panic!` au `bind` (message brut), `std::process::exit(0)` quand stdin se ferme sans vider le socket.
- **B-45 🟡 [L]** `Cargo.toml` : `serde`/`serde_json` déclarés mais inutilisés ; `crate-type = ["cdylib","rlib"]` + binaire dans le même paquet ⇒ le `cargo build` dev produit aussi `afik_bridge.dll/.so`.

### Dart (`dart_runtime/`)
- **B-46 🟠 [L]** `ffi_bridge.dart:65-86` : en dev, si `libafik_bridge.so/.dll` est trouvable (sur Windows : `../rust_bridge/target/debug/afik_bridge.dll`, présent après un simple `cargo build`), `ffi.isAvailable` est vrai et `main.dart:~235` bascule en **mode FFI** : l'app n'essaie plus jamais le socket TCP et attend éternellement des trames qui ne viendront pas. Le mode doit être choisi par `AFIK_STANDALONE` seulement.
- **B-47 🟠 [L]** Le runtime importe `dart:io` **et** `dart:ffi` (`main.dart`, `ffi_bridge.dart`) : non compilable pour **Web** (`flutter build web` échoue), alors que le README liste Web comme cible. Pas de transport WebSocket.
- **B-48 🟡 [L]** `_handleTreePatch` (`main.dart`) : `setState` reconstruit **tout** l'arbre de widgets à chaque patch (`buildFromNode(root)`) ; le « sub-millisecond diffing » économise des octets, pas du travail de rendu. `findNodeById` est O(n) par opération (O(n·m)). Un patch dont l'`id` est inconnu est ignoré sans log ni demande de resync (cf. B-07).
- **B-49 🟡 [L]** `_handlePluginCall` : les erreurs d'appels à 3 champs (fire-and-forget) sont perdues ; `_sendPluginResponse` fait `jsonEncode(result)` — un résultat non sérialisable (ex. `Uint8List`, `DateTime`) lève hors `try` et **aucune réponse n'est envoyée** → côté Python, timeout + faux fallback (B-01).
- **B-50 🟡 [L]** `FrameBuffer` (`frame_buffer.dart`) copie les octets à chaque trame (`Uint8List.fromList(_buffer.sublist(...))`, `List<int>` boxé) : O(n²) pour les gros arbres.
- **B-51 ⚪ [L]** `dart_runtime/SETUP.md`, l'en-tête de `ir_codec.dart` et `proto` (« no diffing in the POC ») sont **obsolètes** : ils prétendent que rien n'a été compilé et que les dossiers plateformes sont absents alors qu'ils existent.
- **B-52 ⚪ [L]** Pas d'`android/app/src/main/jniLibs`, pas de lien statique iOS pour la lib Rust, aucune configuration `ios/` pour l'embarquement : le chemin « IPA » du CLI (`ipa`/`ios`) ne peut pas aboutir.

### Packaging / dépôt
- **B-53 🔴 [L]** Le framework n'est **pas installable en dehors d'un clone du dépôt** : `pyproject.toml` n'embarque ni `dart_runtime/`, ni `rust_bridge/`, ni binaire du pont. `find_workspace_root()` retombe sur `Path(__file__).parents[3]` (le dossier parent de `site-packages` !). `pip install afik` (annoncé) ne peut pas fonctionner ; le projet s'appelle `afik` dans `pyproject.toml` et `Afik` dans le README, `git clone afik-ui/afik` / chemins `d:/Projets/AFIK` en dur dans les liens du README.
- **B-54 🟡 [L]** Incohérences : README « Python 3.9 » vs `requires-python >=3.10` ; `pydantic` obligatoire dans `requirements.txt` mais optionnel dans `pyproject.toml` ; commande de test `python -m unittest discover -s tests` alors que les tests utilisent des imports de package (à vérifier) ; `generated/widget_pb2.py` committé sans commande de régénération ni contrainte de version `protobuf` correspondante ; pas de `LICENSE` alors que le README et le badge y renvoient.
- **B-55 🟡 [L]** Pas de CI (`.github/` absent), pas de lint/typage (`ruff` en dev-dependency mais non configuré, `mypy`/`py.typed` absents), pas de tests Dart/Rust, pas de tests d'intégration bout-en-bout (le fake Dart client n'est pas dans la suite).

---

## 4. Ce qui manque vraiment pour un framework Python robuste

Classé par priorité. Ce sont des **manques**, pas des bugs ponctuels.

### P0 — sans cela, ce n'est pas utilisable en production
1. **Modèle de threading/réentrance clair** : un thread UI/event unique, une file de tâches, `run_on_ui()`, un vrai « scheduler de frames » avec coalescence (`update()` = marquer sale, rebuild au prochain tick). Aujourd'hui : callbacks, builds et envois s'entrelacent (B-01, B-11, B-19, B-20).
2. **API plugins asynchrone et honnête** : `await plugin.call()` / futures / callbacks ; erreurs typées (`PlatformException`, `PluginUnavailable`) ; **jamais** de faux fallback silencieux ; mocks activables explicitement pour les tests. Identifier chaque plugin comme *réel* ou *simulé* (B-01, B-02, B-06, B-37).
3. **Un vrai chemin standalone** : embarquer CPython (Chaquopy/Android, BeeWare-Python-Apple-support/iOS, embed desktop) ou PyO3 ; empaqueter code + dépendances + assets ; cibles Rust cross-compilées ; sinon retirer APK/IPA du README (B-03, B-52).
4. **Distribution pip réelle** : roues contenant le pont Rust précompilé par plateforme, le runtime Dart (ou un binaire shell Flutter prébuilt), versionnement du protocole (`hello` + version) entre Python/Rust/Dart (B-53).
5. **Hot reload digne de ce nom** : file watcher, rechargement transitif des modules, conservation de l'état par identité stable (pas ligne:fichier), restauration de l'instance racine, resync complet de Dart à chaque reconnexion (B-08, B-14, B-21).
6. **Sécurité du pont** : jeton de session, taille max de trame, plus de `kill` de processus tiers, refuser les connexions non authentifiées (B-15, B-16).
7. **Diff/réconciliation correct** : identité par `key` (insert/move/remove), resync explicite quand un patch est rejeté (Dart doit répondre `ack`/`nack`), mise à jour de la dernière snapshot **seulement après** accusé de réception (B-07, B-12, B-48).

### P1 — attendu d'un framework « sérieux »
8. **Cycle de vie complet** : `init_state` / `did_update_widget` / `dispose` appelés au bon moment, `mount`/`unmount`, nettoyage des listeners (`Watch`, `Computed`, `Effect`, `FormKey`), `weakref` (B-10, B-21, B-27).
9. **Navigation complète** : bouton retour système, routes nommées avec arguments, transitions, `WillPop`, deep links, onglets imbriqués ; état de navigation lié à l'app (pas un singleton global).
10. **Gestion d'erreurs/diagnostic** : écran d'erreur dans l'app (équivalent du « red screen »), traces Python lisibles côté terminal, `logger` configurable sans toucher à loguru global, mode `--verbose` (B-13, B-34).
11. **Validation des props** : widgets typés, enums réels (`MainAxisAlignment.CENTER` plutôt que chaînes libres), erreurs précoces et claires en Python au lieu de props ignorées côté Dart (B-24).
12. **Configuration par projet** : copie de travail du runtime Dart par projet (pas de mutation du dépôt framework), génération du `pubspec.yaml` à partir de `afik.yaml`, résolution des versions, `afik doctor` (Flutter, Rust, adb, ports) (B-31, B-32).
13. **Plugins réels** : câbler les vrais packages (`local_auth`, `permission_handler`, `flutter_secure_storage`, `sqflite`, `camera`, `audioplayers`, `video_player`, `share_plus`, `webview_flutter`, `image_picker`…) dans `pubspec.yaml` + permissions plateforme ; flux d'événements Dart→Python (EventChannel, streams : connectivité, position, lecteur audio…) ; handlers d'appels entrants (B-06, B-39, B-40).
14. **Tests sérieux** : tests d'intégration Python↔Rust↔Dart (au minimum avec un faux client Dart dans la suite), tests de propriétés sur le diff, tests de concurrence, golden tests des widgets, `flutter analyze`/`cargo clippy`/`ruff`/`mypy` en CI, matrice Python 3.10-3.13 × OS (B-55).

### P2 — confort et écosystème
15. Thèmes et composants manquants (animations implicites complètes/Hero réel, `Stepper`, `DataTable`, `Table`, `ExpansionTile`, `DatePicker`/`TimePicker`, `Dismissible` effectif, `CustomPaint`/canvas, `ListView.builder` **paresseux** — aujourd'hui les listes envoient tous les éléments, pas de virtualisation → trames énormes, cf. B-43).
16. Internationalisation (`intl`, locales, RTL), accessibilité (`Semantics`), gestes avancés (drag, pinch, long-press avec données d'événement typées), focus/clavier (`FocusNode`, `TextInputAction`).
17. Persistance d'état de l'app (restauration), `async`/`await` natif dans les callbacks (`async def on_click`) avec annulation ; `asyncio` intégré plutôt que threads manuels.
18. Documentation réelle (référence API générée, guides), changelog, gouvernance de version du protocole IR (`ir_spec/widget.proto` sans version) ; publier une feuille de route honnête (retirer « production-ready »).
19. Observabilité : profiler de frames, compteur de rebuilds/patchs, inspecteur d'arbre.

---

## 5. Ce que j'ai écarté après vérification (faux positifs)

- Les validateurs de `TextFormField`/`FormKey.validate()` fonctionnent : `value` est bien une propriété qui renvoie une `str` (vérifié).
- `Navigator.can_pop` / `current_page` existent (je l'avais cru manquant à la première lecture).
- L'état `StatefulComponent` **est** conservé entre frames quand le widget est créé dans `app.build()` (vérifié sur 3 frames).
- `Switch`/`Checkbox`/`Slider` convertissent bien les chaînes Dart en `bool`/`float` pour les handlers déclarés via `on_change`.
- Les trois exemples (`counter`, `facebook_feed`, `pyshop`) et le modèle généré par `afik create` se chargent et se résolvent en arbre sans erreur côté Python.

## 6. Limites de cet audit

- **Dart et Rust n'ont pas été compilés ni exécutés** (pas de SDK ici). Les points marqués [L] sur ces deux couches sont des lectures de code à confirmer sur une machine avec Flutter/cargo ; le comportement exact du Dart (ex. B-07, B-46, B-47) est déduit du code.
- Les ~3 000 lignes de `widgets/widgets.py` et les shims Dart du côté « widgets » (`widget_builder.dart`, 2 867 lignes) n'ont été sondés que sur les composants interactifs (TextField, Switch, Checkbox, Slider, MaterialApp, Form) ; un audit widget par widget (props mal nommées entre Python et Dart) reste à faire — c'est un gros risque de divergence silencieuse vu que le protocole est « tout en chaînes ».
