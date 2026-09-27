import 'package:flutter/material.dart';
import '../core/color_parser.dart';
import '../ir_codec.dart';

typedef WidgetNodeBuilder = Widget Function(
  WidgetNode node,
  void Function(String callbackId, Map<String, String> eventData) sendEvent,
);

/// Constructs an AppBar from a WidgetNode definition.
PreferredSizeWidget? buildAppBar(
  WidgetNode node,
  void Function(String callbackId, Map<String, String> eventData) sendEvent,
  WidgetNodeBuilder buildChild,
) {
  Widget? titleWidget;
  Widget? leadingWidget;
  final List<Widget> actionsList = [];
  PreferredSizeWidget? bottomWidget;

  // Extract slots from children
  for (final child in node.children) {
    final slot = child.props['slot'] ?? '';
    if (slot == 'title') {
      titleWidget = buildChild(child, sendEvent);
    } else if (slot == 'leading') {
      leadingWidget = buildChild(child, sendEvent);
    } else if (slot == 'action') {
      actionsList.add(buildChild(child, sendEvent));
    } else if (slot == 'bottom') {
      final built = buildChild(child, sendEvent);
      if (built is PreferredSizeWidget) {
        bottomWidget = built;
      } else {
        bottomWidget = PreferredSize(
          preferredSize: const Size.fromHeight(48.0),
          child: built,
        );
      }
    }
  }

  // Fallback title from props string
  if (titleWidget == null && node.props.containsKey('title')) {
    titleWidget = Text(
      node.props['title']!,
      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
    );
  }

  Color? bgColor;
  if (node.props.containsKey('background_color')) {
    bgColor = parseHexColor(node.props['background_color']!);
  }

  final elevation = double.tryParse(node.props['elevation'] ?? '') ?? 0.0;
  final centerTitle = node.props['center_title'] == 'true';

  return AppBar(
    title: titleWidget,
    leading: leadingWidget,
    actions: actionsList.isNotEmpty ? actionsList : null,
    bottom: bottomWidget,
    backgroundColor: bgColor,
    elevation: elevation,
    centerTitle: centerTitle,
  );
}
