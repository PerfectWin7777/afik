import 'dart:async';

import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:afik_dart_runtime/plugins/plugin_registry.dart';

/// Local notifications (flutter_local_notifications).
///
/// Android needs core library desugaring and a launcher icon named `@mipmap/ic_launcher`
/// (both handled by the catalog entry and the runtime template). Notification permission on
/// Android 13+ is requested by `initialize`.
class LocalNotificationsShim implements AfikPlugin {
  final FlutterLocalNotificationsPlugin _plugin = FlutterLocalNotificationsPlugin();
  bool _initialized = false;

  Future<void> _ensureInitialized() async {
    if (_initialized) return;
    const settings = InitializationSettings(
      android: AndroidInitializationSettings('@mipmap/ic_launcher'),
      iOS: DarwinInitializationSettings(),
      macOS: DarwinInitializationSettings(),
      linux: LinuxInitializationSettings(defaultActionName: 'Open'),
    );
    final ok = await _plugin.initialize(settings: settings);
    if (ok == false) {
      throw StateError('flutter_local_notifications could not be initialised on this platform.');
    }
    _initialized = true;
  }

  @override
  Future<dynamic> handleMethodCall(String method, Map<String, String> args) async {
    switch (method) {
      case 'initialize':
        await _ensureInitialized();
        final android = _plugin
            .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();
        final granted = await android?.requestNotificationsPermission();
        return {'initialized': true, 'permissionGranted': granted};

      case 'show':
        await _ensureInitialized();
        final id = int.tryParse(args['id'] ?? '');
        if (id == null) throw ArgumentError('Notification id must be an integer.');
        final channelId = args['channelId'] ?? 'default_channel';
        await _plugin.show(
          id: id,
          title: args['title'],
          body: args['body'],
          notificationDetails: NotificationDetails(
            android: AndroidNotificationDetails(
              channelId,
              args['channelName'] ?? channelId,
              importance: Importance.defaultImportance,
              priority: Priority.defaultPriority,
            ),
            iOS: const DarwinNotificationDetails(),
            macOS: const DarwinNotificationDetails(),
            linux: const LinuxNotificationDetails(),
          ),
          payload: args['payload'],
        );
        return {'shown': true, 'id': id};

      case 'cancel':
        await _ensureInitialized();
        final id = int.tryParse(args['id'] ?? '');
        if (id == null) throw ArgumentError('Notification id must be an integer.');
        await _plugin.cancel(id: id);
        return {'cancelled': true, 'id': id};

      case 'cancelAll':
        await _ensureInitialized();
        await _plugin.cancelAll();
        return {'cancelled': true};

      case 'getActiveNotifications':
        await _ensureInitialized();
        final active = await _plugin.getActiveNotifications();
        return [
          for (final n in active) {'id': n.id, 'title': n.title, 'body': n.body, 'channelId': n.channelId},
        ];

      default:
        throw UnsupportedError('LocalNotifications method "$method" is not supported.');
    }
  }
}

void register() {
  final shim = LocalNotificationsShim();
  PluginRegistry.register('flutter_local_notifications', shim);
  PluginRegistry.register('local_notifications', shim);
}
