import 'package:flutter/material.dart';
import '../core/color_parser.dart';
import '../ir_codec.dart';
import 'app_bar_builder.dart';
import 'icon_resolver.dart';

/// Recursively builds a native Flutter widget from a decoded WidgetNode IR.
Widget buildFromNode(
  WidgetNode node,
  void Function(String callbackId, Map<String, String> eventData) sendEvent,
) {
  Widget widget;

  switch (node.type) {
    case 'Text':
      final text = node.props['text'] ?? '';
      final fontSize = double.tryParse(node.props['font_size'] ?? '') ?? 14.0;
      final isBold = node.props['font_weight'] == 'bold';
      final color = node.props.containsKey('color')
          ? parseHexColor(node.props['color']!)
          : null;
      widget = Text(
        text,
        style: TextStyle(
          fontSize: fontSize,
          fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
          color: color,
        ),
      );
      break;

    case 'Button':
      final label = node.props['label'] ?? 'Button';
      final iconName = node.props['icon'];
      final bgColor = node.props.containsKey('color')
          ? parseHexColor(node.props['color']!)
          : null;
      final btnStyle = bgColor != null
          ? ElevatedButton.styleFrom(backgroundColor: bgColor)
          : null;

      if (iconName != null && iconName.isNotEmpty) {
        widget = ElevatedButton.icon(
          style: btnStyle,
          onPressed: node.callbackId.isNotEmpty
              ? () => sendEvent(node.callbackId, {})
              : null,
          icon: Icon(resolveIcon(iconName), size: 18),
          label: Text(label),
        );
      } else {
        widget = ElevatedButton(
          style: btnStyle,
          onPressed: node.callbackId.isNotEmpty
              ? () => sendEvent(node.callbackId, {})
              : null,
          child: Text(label),
        );
      }
      break;

    case 'IconButton':
      final name = node.props['icon'] ?? '';
      final color = node.props.containsKey('color')
          ? parseHexColor(node.props['color']!)
          : null;
      final size = double.tryParse(node.props['size'] ?? '') ?? 24.0;
      widget = IconButton(
        icon: Icon(resolveIcon(name), size: size, color: color),
        onPressed: node.callbackId.isNotEmpty
            ? () => sendEvent(node.callbackId, {})
            : null,
      );
      break;

    case 'TextField':
      final hint = node.props['hint'] ?? '';
      widget = TextField(
        decoration: InputDecoration(
          hintText: hint,
          border: const OutlineInputBorder(),
        ),
        onChanged: (text) {
          if (node.callbackId.isNotEmpty) {
            sendEvent(node.callbackId, {'value': text});
          }
        },
      );
      break;

    case 'Column':
      final mainAlignStr = node.props['main_axis_alignment'] ?? 'start';
      final crossAlignStr = node.props['cross_axis_alignment'] ?? 'start';

      MainAxisAlignment mainAxisAlignment = MainAxisAlignment.start;
      if (mainAlignStr == 'center') mainAxisAlignment = MainAxisAlignment.center;
      else if (mainAlignStr == 'space_between') mainAxisAlignment = MainAxisAlignment.spaceBetween;
      else if (mainAlignStr == 'space_around') mainAxisAlignment = MainAxisAlignment.spaceAround;
      else if (mainAlignStr == 'space_evenly') mainAxisAlignment = MainAxisAlignment.spaceEvenly;
      else if (mainAlignStr == 'end') mainAxisAlignment = MainAxisAlignment.end;

      CrossAxisAlignment crossAxisAlignment = CrossAxisAlignment.start;
      if (crossAlignStr == 'center') crossAxisAlignment = CrossAxisAlignment.center;
      else if (crossAlignStr == 'stretch') crossAxisAlignment = CrossAxisAlignment.stretch;
      else if (crossAlignStr == 'end') crossAxisAlignment = CrossAxisAlignment.end;

      widget = Column(
        mainAxisAlignment: mainAxisAlignment,
        crossAxisAlignment: crossAxisAlignment,
        children: node.children.map((c) => buildFromNode(c, sendEvent)).toList(),
      );
      break;

    case 'Row':
      final mainAlignStr = node.props['main_axis_alignment'] ?? 'start';
      final crossAlignStr = node.props['cross_axis_alignment'] ?? 'center';

      MainAxisAlignment mainAxisAlignment = MainAxisAlignment.start;
      if (mainAlignStr == 'center') mainAxisAlignment = MainAxisAlignment.center;
      else if (mainAlignStr == 'space_between') mainAxisAlignment = MainAxisAlignment.spaceBetween;
      else if (mainAlignStr == 'space_around') mainAxisAlignment = MainAxisAlignment.spaceAround;
      else if (mainAlignStr == 'space_evenly') mainAxisAlignment = MainAxisAlignment.spaceEvenly;
      else if (mainAlignStr == 'end') mainAxisAlignment = MainAxisAlignment.end;

      CrossAxisAlignment crossAxisAlignment = CrossAxisAlignment.center;
      if (crossAlignStr == 'start') crossAxisAlignment = CrossAxisAlignment.start;
      else if (crossAlignStr == 'stretch') crossAxisAlignment = CrossAxisAlignment.stretch;
      else if (crossAlignStr == 'end') crossAxisAlignment = CrossAxisAlignment.end;

      widget = Row(
        mainAxisAlignment: mainAxisAlignment,
        crossAxisAlignment: crossAxisAlignment,
        children: node.children.map((c) => buildFromNode(c, sendEvent)).toList(),
      );
      break;

    case 'Stack':
      widget = Stack(
        children: node.children.map((c) => buildFromNode(c, sendEvent)).toList(),
      );
      break;

    case 'Positioned':
      final top = double.tryParse(node.props['top'] ?? '');
      final bottom = double.tryParse(node.props['bottom'] ?? '');
      final left = double.tryParse(node.props['left'] ?? '');
      final right = double.tryParse(node.props['right'] ?? '');
      widget = Positioned(
        top: top,
        bottom: bottom,
        left: left,
        right: right,
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : const SizedBox.shrink(),
      );
      break;

    case 'Container':
      final width = double.tryParse(node.props['width'] ?? '');
      final height = double.tryParse(node.props['height'] ?? '');
      final padding = double.tryParse(node.props['padding'] ?? '');
      final margin = double.tryParse(node.props['margin'] ?? '');
      final radius = double.tryParse(node.props['border_radius'] ?? '') ?? 0.0;
      final bgColor = node.props.containsKey('color')
          ? parseHexColor(node.props['color']!)
          : null;

      BoxDecoration? decoration;
      if (bgColor != null || radius > 0) {
        decoration = BoxDecoration(
          color: bgColor,
          borderRadius: radius > 0 ? BorderRadius.circular(radius) : null,
        );
      }

      widget = Container(
        width: width,
        height: height,
        padding: padding != null ? EdgeInsets.all(padding) : null,
        margin: margin != null ? EdgeInsets.all(margin) : null,
        decoration: decoration,
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : null,
      );
      break;

    case 'Card':
      final elevation = double.tryParse(node.props['elevation'] ?? '') ?? 1.0;
      final margin = double.tryParse(node.props['margin'] ?? '') ?? 8.0;
      final radius = double.tryParse(node.props['border_radius'] ?? '') ?? 12.0;
      Widget? cardChild = node.children.isNotEmpty
          ? buildFromNode(node.children.first, sendEvent)
          : null;
      if (cardChild != null && node.props.containsKey('padding')) {
        final p = double.tryParse(node.props['padding']!) ?? 0.0;
        cardChild = Padding(padding: EdgeInsets.all(p), child: cardChild);
      }
      widget = Card(
        elevation: elevation,
        margin: EdgeInsets.symmetric(horizontal: margin, vertical: margin / 2),
        color: node.props.containsKey('color')
            ? parseHexColor(node.props['color']!)
            : Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radius),
        ),
        clipBehavior: Clip.antiAlias,
        child: cardChild,
      );
      break;

    case 'Padding':
      final all = double.tryParse(node.props['all'] ?? '') ??
          double.tryParse(node.props['padding'] ?? '');
      final top = double.tryParse(node.props['top'] ?? '');
      final bottom = double.tryParse(node.props['bottom'] ?? '');
      final left = double.tryParse(node.props['left'] ?? '');
      final right = double.tryParse(node.props['right'] ?? '');
      final h = double.tryParse(node.props['horizontal'] ?? '') ?? 0.0;
      final v = double.tryParse(node.props['vertical'] ?? '') ?? 0.0;

      final EdgeInsets insets;
      if (all != null) {
        insets = EdgeInsets.all(all);
      } else if (top != null || bottom != null || left != null || right != null) {
        insets = EdgeInsets.only(
          top: top ?? v,
          bottom: bottom ?? v,
          left: left ?? h,
          right: right ?? h,
        );
      } else {
        insets = EdgeInsets.symmetric(horizontal: h, vertical: v);
      }
      widget = Padding(
        padding: insets,
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : null,
      );
      break;

    case 'SizedBox':
      widget = SizedBox(
        width: double.tryParse(node.props['width'] ?? ''),
        height: double.tryParse(node.props['height'] ?? ''),
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : null,
      );
      break;

    case 'Image':
      final src = node.props['src'] ?? node.props['url'] ?? '';
      final width = double.tryParse(node.props['width'] ?? '');
      final height = double.tryParse(node.props['height'] ?? '');
      final fitStr = node.props['fit'] ?? 'cover';
      BoxFit fit = BoxFit.cover;
      if (fitStr == 'contain') fit = BoxFit.contain;
      else if (fitStr == 'fill') fit = BoxFit.fill;

      Widget img;
      if (src.startsWith('http://') || src.startsWith('https://')) {
        img = Image.network(
          src,
          width: width,
          height: height,
          fit: fit,
          errorBuilder: (_, __, ___) => Container(
            width: width,
            height: height ?? 100,
            color: Colors.grey.shade300,
            child: const Icon(Icons.broken_image, color: Colors.grey),
          ),
          loadingBuilder: (_, child, progress) => progress == null
              ? child
              : Container(
                  width: width,
                  height: height ?? 100,
                  color: Colors.grey.shade200,
                  child: const Center(
                      child: CircularProgressIndicator(strokeWidth: 2)),
                ),
        );
      } else {
        img = Container(
          width: width,
          height: height ?? 60,
          color: Colors.grey.shade300,
          child: Center(child: Text(src)),
        );
      }
      if (node.props.containsKey('border_radius')) {
        final r = double.tryParse(node.props['border_radius']!) ?? 0;
        img = ClipRRect(borderRadius: BorderRadius.circular(r), child: img);
      }
      widget = img;
      break;

    case 'Icon':
      final name = node.props['name'] ?? '';
      final size = double.tryParse(node.props['size'] ?? '') ?? 24.0;
      final color = node.props.containsKey('color')
          ? parseHexColor(node.props['color']!)
          : null;
      widget = Icon(resolveIcon(name), size: size, color: color);
      break;

    case 'Divider':
      widget = Divider(
        height: double.tryParse(node.props['height'] ?? '') ?? 16.0,
        thickness: double.tryParse(node.props['thickness'] ?? '') ?? 1.0,
        color: node.props.containsKey('color')
            ? parseHexColor(node.props['color']!)
            : Colors.grey.shade300,
      );
      break;

    case 'Center':
      widget = Center(
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : null,
      );
      break;

    case 'Expanded':
      final flex = int.tryParse(node.props['flex'] ?? '') ?? 1;
      widget = Expanded(
        flex: flex,
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : const SizedBox.shrink(),
      );
      break;

    case 'Spacer':
      final flex = int.tryParse(node.props['flex'] ?? '') ?? 1;
      widget = Spacer(flex: flex);
      break;

    case 'ListView':
      final pad = double.tryParse(node.props['padding'] ?? '') ?? 0.0;
      widget = ListView(
        padding: EdgeInsets.all(pad),
        children: node.children.map((c) => buildFromNode(c, sendEvent)).toList(),
      );
      break;

    case 'SingleChildScrollView':
      final pad = double.tryParse(node.props['padding'] ?? '') ?? 0.0;
      widget = SingleChildScrollView(
        padding: EdgeInsets.all(pad),
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : null,
      );
      break;

    case 'CircularProgressIndicator':
      widget = const Center(
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: CircularProgressIndicator(),
        ),
      );
      break;

    case 'Switch':
      final value = node.props['value'] == 'true';
      widget = Switch(
        value: value,
        activeColor: node.props.containsKey('active_color')
            ? parseHexColor(node.props['active_color']!)
            : null,
        onChanged: (newVal) {
          if (node.callbackId.isNotEmpty) {
            sendEvent(node.callbackId, {'value': newVal.toString()});
          }
        },
      );
      break;

    case 'Checkbox':
      final value = node.props['value'] == 'true';
      widget = Checkbox(
        value: value,
        activeColor: node.props.containsKey('active_color')
            ? parseHexColor(node.props['active_color']!)
            : null,
        onChanged: (newVal) {
          if (node.callbackId.isNotEmpty) {
            sendEvent(node.callbackId, {'value': (newVal ?? false).toString()});
          }
        },
      );
      break;

    case 'SafeArea':
      final top = node.props['top'] != 'false';
      final bottom = node.props['bottom'] != 'false';
      final left = node.props['left'] != 'false';
      final right = node.props['right'] != 'false';
      final minPadding = double.tryParse(node.props['minimum'] ?? '') ?? 0.0;
      final maintainBottom = node.props['maintain_bottom_view_padding'] == 'true';
      widget = SafeArea(
        top: top,
        bottom: bottom,
        left: left,
        right: right,
        minimum: EdgeInsets.all(minPadding),
        maintainBottomViewPadding: maintainBottom,
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : const SizedBox.shrink(),
      );
      break;

    case 'Drawer':
      final bgColor = node.props.containsKey('background_color')
          ? parseHexColor(node.props['background_color']!)
          : null;
      final elevation = double.tryParse(node.props['elevation'] ?? '') ?? 16.0;
      final width = double.tryParse(node.props['width'] ?? '');
      widget = Drawer(
        backgroundColor: bgColor,
        elevation: elevation,
        width: width,
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : null,
      );
      break;

    case 'DrawerHeader':
      final bgColor = node.props.containsKey('background_color')
          ? parseHexColor(node.props['background_color']!)
          : null;
      final margin = double.tryParse(node.props['margin'] ?? '') ?? 12.0;
      final padding = double.tryParse(node.props['padding'] ?? '') ?? 16.0;
      widget = DrawerHeader(
        decoration: BoxDecoration(
          color: bgColor ?? const Color(0xFF1877F2),
        ),
        margin: EdgeInsets.only(bottom: margin),
        padding: EdgeInsets.all(padding),
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : null,
      );
      break;

    case 'BottomSheet':
      final bgColor = node.props.containsKey('background_color')
          ? parseHexColor(node.props['background_color']!)
          : Colors.white;
      final elevation = double.tryParse(node.props['elevation'] ?? '') ?? 8.0;
      final radius = double.tryParse(node.props['border_radius'] ?? '') ?? 16.0;
      widget = Container(
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.vertical(top: Radius.circular(radius)),
          boxShadow: [
            BoxShadow(
              color: const Color(0x1A000000),
              blurRadius: elevation,
              spreadRadius: 2,
            ),
          ],
        ),
        child: SafeArea(
          top: false,
          child: node.children.isNotEmpty
              ? buildFromNode(node.children.first, sendEvent)
              : const SizedBox.shrink(),
        ),
      );
      break;

    case 'Scaffold':
      PreferredSizeWidget? appBar;
      Widget? body;
      Widget? bottomBar;
      Widget? fab;
      Widget? drawerWidget;
      Widget? endDrawerWidget;
      Widget? bottomSheetWidget;

      for (final child in node.children) {
        final slot = child.props['slot'] ?? '';
        if (slot == 'app_bar' || child.type == 'AppBar') {
          appBar = buildAppBar(child, sendEvent, buildFromNode);
        } else if (slot == 'body') {
          body = SafeArea(
            maintainBottomViewPadding: true,
            child: buildFromNode(child, sendEvent),
          );
        } else if (slot == 'bottom_bar' || child.type == 'BottomNavigationBar') {
          bottomBar = buildFromNode(child, sendEvent);
        } else if (slot == 'fab') {
          fab = buildFromNode(child, sendEvent);
        } else if (slot == 'drawer' || child.type == 'Drawer') {
          drawerWidget = buildFromNode(child, sendEvent);
        } else if (slot == 'end_drawer') {
          endDrawerWidget = buildFromNode(child, sendEvent);
        } else if (slot == 'bottom_sheet' || child.type == 'BottomSheet') {
          bottomSheetWidget = buildFromNode(child, sendEvent);
        }
      }

      if (body == null) {
        final nonSlotChildren = node.children
            .where((c) =>
                !c.props.containsKey('slot') &&
                c.type != 'AppBar' &&
                c.type != 'Drawer' &&
                c.type != 'BottomSheet')
            .toList();
        if (nonSlotChildren.isNotEmpty) {
          body = SafeArea(
            maintainBottomViewPadding: true,
            child: buildFromNode(nonSlotChildren.first, sendEvent),
          );
        }
      }

      final bgColor = node.props.containsKey('background_color')
          ? parseHexColor(node.props['background_color']!)
          : const Color(0xFFF0F2F5);

      widget = Scaffold(
        appBar: appBar,
        body: body,
        bottomNavigationBar: bottomBar,
        floatingActionButton: fab,
        drawer: drawerWidget,
        endDrawer: endDrawerWidget,
        bottomSheet: bottomSheetWidget,
        backgroundColor: bgColor,
      );
      break;

    case 'BottomNavigationBar':
      final items = <BottomNavigationBarItem>[];
      final List<String> itemCallbackIds = [];

      for (final child in node.children) {
        if (child.type == 'BottomNavigationBarItem') {
          final iconName = child.props['icon'] ?? 'circle';
          final label = child.props['label'] ?? '';
          items.add(BottomNavigationBarItem(
            icon: Icon(resolveIcon(iconName)),
            label: label,
          ));
          itemCallbackIds.add(child.callbackId);
        }
      }

      final currentIndex = int.tryParse(node.props['current_index'] ?? '') ?? 0;
      final selectedColor = node.props.containsKey('selected_color')
          ? parseHexColor(node.props['selected_color']!)
          : null;
      final unselectedColor = node.props.containsKey('unselected_color')
          ? parseHexColor(node.props['unselected_color']!)
          : null;

      widget = BottomNavigationBar(
        items: items.isNotEmpty
            ? items
            : const [
                BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
                BottomNavigationBarItem(icon: Icon(Icons.settings), label: 'Settings'),
              ],
        currentIndex: (currentIndex >= 0 && currentIndex < (items.isNotEmpty ? items.length : 2))
            ? currentIndex
            : 0,
        selectedItemColor: selectedColor,
        unselectedItemColor: unselectedColor,
        type: items.length > 3
            ? BottomNavigationBarType.fixed
            : BottomNavigationBarType.fixed,
        onTap: (index) {
          if (node.callbackId.isNotEmpty) {
            sendEvent(node.callbackId, {'index': index.toString()});
          }
          if (index < itemCallbackIds.length && itemCallbackIds[index].isNotEmpty) {
            sendEvent(itemCallbackIds[index], {});
          }
        },
      );
      break;

    case 'PageView':
      final onPageChangedId = node.callbackId;
      final isVertical = node.props['scroll_direction'] == 'vertical';
      widget = PageView(
        scrollDirection: isVertical ? Axis.vertical : Axis.horizontal,
        onPageChanged: (pageIndex) {
          if (onPageChangedId.isNotEmpty) {
            sendEvent(onPageChangedId, {'page': pageIndex.toString()});
          }
        },
        children: node.children.map((c) => buildFromNode(c, sendEvent)).toList(),
      );
      break;

    case 'DefaultTabController':
      final length = int.tryParse(node.props['length'] ?? '') ??
          (node.children.isNotEmpty ? node.children.first.children.length : 2);
      widget = DefaultTabController(
        length: length,
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : const SizedBox.shrink(),
      );
      break;

    case 'Tab':
      final text = node.props['text'];
      final iconName = node.props['icon'];
      widget = Tab(
        text: text,
        icon: iconName != null ? Icon(resolveIcon(iconName)) : null,
      );
      break;

    case 'TabBar':
      final indicatorColor = node.props.containsKey('indicator_color')
          ? parseHexColor(node.props['indicator_color']!)
          : null;
      final labelColor = node.props.containsKey('label_color')
          ? parseHexColor(node.props['label_color']!)
          : null;
      widget = TabBar(
        indicatorColor: indicatorColor,
        labelColor: labelColor,
        tabs: node.children.map((c) => buildFromNode(c, sendEvent)).toList(),
      );
      break;

    case 'TabBarView':
      widget = TabBarView(
        children: node.children.map((c) => buildFromNode(c, sendEvent)).toList(),
      );
      break;

    default:
      widget = Text('[unknown widget: ${node.type}]');
      break;
  }

  // Generic onTap wrapper: allows ANY widget carrying a callbackId to be interactive
  if (node.callbackId.isNotEmpty &&
      node.type != 'Button' &&
      node.type != 'IconButton' &&
      node.type != 'TextField' &&
      node.type != 'Switch' &&
      node.type != 'Checkbox' &&
      node.type != 'BottomNavigationBar' &&
      node.type != 'PageView') {
    return InkWell(
      onTap: () => sendEvent(node.callbackId, {}),
      child: widget,
    );
  }

  return widget;
}
