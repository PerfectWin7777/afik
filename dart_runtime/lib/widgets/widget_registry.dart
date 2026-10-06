import 'package:flutter/widgets.dart';

import '../ir_codec.dart';

/// Builds the Flutter widget for one node of the tree sent by Python.
typedef PyWidgetFactory = Widget Function(
  WidgetNode node,
  void Function(String callbackId, Map<String, String> eventData) sendEvent,
);

/// Registry of widgets provided by installed plugins.
///
/// The core runtime knows nothing about optional packages (video player, web
/// view, camera...). A plugin's `register()` function adds its widget types
/// here, and `buildFromNode` falls back to this registry for any node type it
/// does not handle itself.
class WidgetRegistry {
  static final Map<String, PyWidgetFactory> _factories = {};

  static void register(String type, PyWidgetFactory factory) {
    _factories[type] = factory;
  }

  static PyWidgetFactory? lookup(String type) => _factories[type];
}
