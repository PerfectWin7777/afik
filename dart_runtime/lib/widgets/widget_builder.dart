import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import '../core/color_parser.dart';
import '../ir_codec.dart';
import 'app_bar_builder.dart';
import 'icon_resolver.dart';

/// Parses an animation curve name into a Flutter Curve.
Curve parseCurve(String? curveStr) {
  switch (curveStr) {
    case 'linear': return Curves.linear;
    case 'easeIn': return Curves.easeIn;
    case 'easeOut': return Curves.easeOut;
    case 'easeInOut': return Curves.easeInOut;
    case 'bounceIn': return Curves.bounceIn;
    case 'bounceOut': return Curves.bounceOut;
    case 'bounceInOut': return Curves.bounceInOut;
    case 'elasticIn': return Curves.elasticIn;
    case 'elasticOut': return Curves.elasticOut;
    case 'elasticInOut': return Curves.elasticInOut;
    case 'fastOutSlowIn': return Curves.fastOutSlowIn;
    default: return Curves.easeInOut;
  }
}

/// Parses a 2D alignment string into a Flutter Alignment.
Alignment parseAlignment(String? alignStr) {
  switch (alignStr) {
    case 'top_left': return Alignment.topLeft;
    case 'top_center': return Alignment.topCenter;
    case 'top_right': return Alignment.topRight;
    case 'center_left': return Alignment.centerLeft;
    case 'center': return Alignment.center;
    case 'center_right': return Alignment.centerRight;
    case 'bottom_left': return Alignment.bottomLeft;
    case 'bottom_center': return Alignment.bottomCenter;
    case 'bottom_right': return Alignment.bottomRight;
    default: return Alignment.center;
  }
}

/// Recursively builds a native Flutter widget from a decoded WidgetNode IR.
Widget buildFromNode(
  WidgetNode node,
  void Function(String callbackId, Map<String, String> eventData) sendEvent,
) {
  Widget widget;

  switch (node.type) {
    case 'Text':
      final text = node.props['text'] ?? node.props['value'] ?? '';
      final themeStyleName = node.props['style'] ?? node.props['theme_style'];
      final fontSize = double.tryParse(node.props['font_size'] ?? '');

      FontWeight? fontWeight;
      final fwStr = node.props['font_weight'];
      if (fwStr != null) {
        switch (fwStr) {
          case 'bold': fontWeight = FontWeight.bold; break;
          case 'normal': fontWeight = FontWeight.normal; break;
          case 'w100': fontWeight = FontWeight.w100; break;
          case 'w200': fontWeight = FontWeight.w200; break;
          case 'w300': fontWeight = FontWeight.w300; break;
          case 'w400': fontWeight = FontWeight.w400; break;
          case 'w500': fontWeight = FontWeight.w500; break;
          case 'w600': fontWeight = FontWeight.w600; break;
          case 'w700': fontWeight = FontWeight.w700; break;
          case 'w800': fontWeight = FontWeight.w800; break;
          case 'w900': fontWeight = FontWeight.w900; break;
        }
      }

      final fontStyle = node.props['font_style'] == 'italic' ? FontStyle.italic : null;
      final fontFamily = node.props['font_family'];
      final letterSpacing = double.tryParse(node.props['letter_spacing'] ?? '');
      final wordSpacing = double.tryParse(node.props['word_spacing'] ?? '');
      final height = double.tryParse(node.props['height'] ?? '');

      TextDecoration? decoration;
      final decStr = node.props['decoration'];
      if (decStr != null) {
        switch (decStr) {
          case 'underline': decoration = TextDecoration.underline; break;
          case 'lineThrough': decoration = TextDecoration.lineThrough; break;
          case 'overline': decoration = TextDecoration.overline; break;
          case 'none': decoration = TextDecoration.none; break;
        }
      }
      final decorationColor = node.props.containsKey('decoration_color')
          ? parseHexColor(node.props['decoration_color']!)
          : null;

      final color = node.props.containsKey('color')
          ? parseHexColor(node.props['color']!)
          : null;

      TextAlign? textAlign;
      final taStr = node.props['text_align'];
      if (taStr != null) {
        switch (taStr) {
          case 'left': textAlign = TextAlign.left; break;
          case 'center': textAlign = TextAlign.center; break;
          case 'right': textAlign = TextAlign.right; break;
          case 'justify': textAlign = TextAlign.justify; break;
          case 'start': textAlign = TextAlign.start; break;
          case 'end': textAlign = TextAlign.end; break;
        }
      }

      final maxLines = int.tryParse(node.props['max_lines'] ?? '');

      TextOverflow? overflow;
      final ovStr = node.props['overflow'];
      if (ovStr != null) {
        switch (ovStr) {
          case 'ellipsis': overflow = TextOverflow.ellipsis; break;
          case 'clip': overflow = TextOverflow.clip; break;
          case 'fade': overflow = TextOverflow.fade; break;
        }
      }

      final softWrap = node.props['soft_wrap'] != 'false';

      widget = Builder(
        builder: (ctx) {
          TextStyle baseStyle = const TextStyle();
          if (themeStyleName != null && themeStyleName.isNotEmpty) {
            final textTheme = Theme.of(ctx).textTheme;
            switch (themeStyleName) {
              case 'displayLarge': baseStyle = textTheme.displayLarge ?? baseStyle; break;
              case 'displayMedium': baseStyle = textTheme.displayMedium ?? baseStyle; break;
              case 'displaySmall': baseStyle = textTheme.displaySmall ?? baseStyle; break;
              case 'headlineLarge': baseStyle = textTheme.headlineLarge ?? baseStyle; break;
              case 'headlineMedium': baseStyle = textTheme.headlineMedium ?? baseStyle; break;
              case 'headlineSmall': baseStyle = textTheme.headlineSmall ?? baseStyle; break;
              case 'titleLarge': baseStyle = textTheme.titleLarge ?? baseStyle; break;
              case 'titleMedium': baseStyle = textTheme.titleMedium ?? baseStyle; break;
              case 'titleSmall': baseStyle = textTheme.titleSmall ?? baseStyle; break;
              case 'bodyLarge': baseStyle = textTheme.bodyLarge ?? baseStyle; break;
              case 'bodyMedium': baseStyle = textTheme.bodyMedium ?? baseStyle; break;
              case 'bodySmall': baseStyle = textTheme.bodySmall ?? baseStyle; break;
              case 'labelLarge': baseStyle = textTheme.labelLarge ?? baseStyle; break;
              case 'labelMedium': baseStyle = textTheme.labelMedium ?? baseStyle; break;
              case 'labelSmall': baseStyle = textTheme.labelSmall ?? baseStyle; break;
            }
          }

          final finalStyle = baseStyle.copyWith(
            fontSize: fontSize,
            fontWeight: fontWeight,
            fontStyle: fontStyle,
            fontFamily: fontFamily,
            letterSpacing: letterSpacing,
            wordSpacing: wordSpacing,
            height: height,
            decoration: decoration,
            decorationColor: decorationColor,
            color: color,
          );

          return Text(
            text,
            style: finalStyle,
            textAlign: textAlign,
            maxLines: maxLines,
            overflow: overflow,
            softWrap: softWrap,
          );
        },
      );
      break;

    case 'Button':
    case 'ElevatedButton':
      final label = node.props['label'] ?? 'Button';
      final iconName = node.props['icon'];
      final bgColor = node.props.containsKey('background_color')
          ? parseHexColor(node.props['background_color']!)
          : (node.props.containsKey('color') ? parseHexColor(node.props['color']!) : null);
      final fgColor = (node.props.containsKey('background_color') && node.props.containsKey('color'))
          ? parseHexColor(node.props['color']!)
          : null;
      final radius = double.tryParse(node.props['border_radius'] ?? '');
      final elevation = double.tryParse(node.props['elevation'] ?? '');

      final btnStyle = ElevatedButton.styleFrom(
        backgroundColor: bgColor,
        foregroundColor: fgColor,
        elevation: elevation,
        shape: radius != null
            ? RoundedRectangleBorder(borderRadius: BorderRadius.circular(radius))
            : null,
      );

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

    case 'OutlinedButton':
      final label = node.props['label'] ?? '';
      final iconName = node.props['icon'];
      final color = node.props.containsKey('color')
          ? parseHexColor(node.props['color']!)
          : null;
      final borderColor = node.props.containsKey('border_color')
          ? parseHexColor(node.props['border_color']!)
          : color;
      final borderWidth = double.tryParse(node.props['border_width'] ?? '') ?? 1.0;
      final radius = double.tryParse(node.props['border_radius'] ?? '') ?? 8.0;

      final btnStyle = OutlinedButton.styleFrom(
        foregroundColor: color,
        side: borderColor != null
            ? BorderSide(color: borderColor, width: borderWidth)
            : null,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(radius)),
      );

      if (iconName != null && iconName.isNotEmpty) {
        widget = OutlinedButton.icon(
          style: btnStyle,
          onPressed: node.callbackId.isNotEmpty
              ? () => sendEvent(node.callbackId, {})
              : null,
          icon: Icon(resolveIcon(iconName), size: 18),
          label: Text(label),
        );
      } else {
        widget = OutlinedButton(
          style: btnStyle,
          onPressed: node.callbackId.isNotEmpty
              ? () => sendEvent(node.callbackId, {})
              : null,
          child: Text(label),
        );
      }
      break;

    case 'TextButton':
      final label = node.props['label'] ?? '';
      final iconName = node.props['icon'];
      final color = node.props.containsKey('color')
          ? parseHexColor(node.props['color']!)
          : null;
      final radius = double.tryParse(node.props['border_radius'] ?? '') ?? 8.0;

      final btnStyle = TextButton.styleFrom(
        foregroundColor: color,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(radius)),
      );

      if (iconName != null && iconName.isNotEmpty) {
        widget = TextButton.icon(
          style: btnStyle,
          onPressed: node.callbackId.isNotEmpty
              ? () => sendEvent(node.callbackId, {})
              : null,
          icon: Icon(resolveIcon(iconName), size: 18),
          label: Text(label),
        );
      } else {
        widget = TextButton(
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
      final padVal = double.tryParse(node.props['padding'] ?? '');
      widget = IconButton(
        icon: Icon(resolveIcon(name), size: size, color: color),
        padding: padVal != null ? EdgeInsets.all(padVal) : null,
        constraints: padVal != null ? const BoxConstraints() : null,
        onPressed: node.callbackId.isNotEmpty
            ? () => sendEvent(node.callbackId, {})
            : null,
      );
      break;

    case 'TextField':
    case 'TextFormField':
      final fieldKey = node.props['key'] ??
          (node.callbackId.isNotEmpty
              ? node.callbackId
              : 'text_field_${node.props['placeholder'] ?? node.props['hint'] ?? 'default'}');
      widget = PyTextFieldWidget(
        key: ValueKey(fieldKey),
        node: node,
        sendEvent: sendEvent,
      );
      break;

    case 'DropdownButton':
      widget = PyDropdownButtonWidget(node: node, sendEvent: sendEvent);
      break;

    case 'DropdownMenu':
      widget = PyDropdownMenuWidget(node: node, sendEvent: sendEvent);
      break;

    case 'Form':
      widget = Form(
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : const SizedBox.shrink(),
      );
      break;

    case 'Column':
      final mainAlignStr = node.props['main_axis_alignment'] ?? 'start';
      final crossAlignStr = node.props['cross_axis_alignment'] ?? 'start';
      final mainAxisSize = node.props['main_axis_size'] == 'min' ? MainAxisSize.min : MainAxisSize.max;

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
        mainAxisSize: mainAxisSize,
        children: node.children.map((c) => buildFromNode(c, sendEvent)).toList(),
      );
      break;

    case 'Row':
      final mainAlignStr = node.props['main_axis_alignment'] ?? 'start';
      final crossAlignStr = node.props['cross_axis_alignment'] ?? 'center';
      final mainAxisSize = node.props['main_axis_size'] == 'min' ? MainAxisSize.min : MainAxisSize.max;

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
        mainAxisSize: mainAxisSize,
        children: node.children.map((c) => buildFromNode(c, sendEvent)).toList(),
      );
      break;

    case 'Wrap':
      final spacing = double.tryParse(node.props['spacing'] ?? '') ?? 8.0;
      final runSpacing = double.tryParse(node.props['run_spacing'] ?? '') ?? 8.0;
      final alignStr = node.props['alignment'] ?? 'start';
      WrapAlignment align = WrapAlignment.start;
      if (alignStr == 'center') align = WrapAlignment.center;
      else if (alignStr == 'end') align = WrapAlignment.end;
      else if (alignStr == 'space_between') align = WrapAlignment.spaceBetween;
      else if (alignStr == 'space_around') align = WrapAlignment.spaceAround;
      else if (alignStr == 'space_evenly') align = WrapAlignment.spaceEvenly;

      widget = Wrap(
        spacing: spacing,
        runSpacing: runSpacing,
        alignment: align,
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
      final alignment = parseAlignment(node.props['alignment']);

      final borderColor = node.props.containsKey('border_color')
          ? parseHexColor(node.props['border_color']!)
          : null;
      final borderWidth = double.tryParse(node.props['border_width'] ?? '') ?? 1.0;
      final isCircle = node.props['shape'] == 'circle';

      final shadowColor = node.props.containsKey('shadow_color')
          ? parseHexColor(node.props['shadow_color']!)
          : null;
      final shadowBlur = double.tryParse(node.props['shadow_blur'] ?? '') ?? 4.0;

      BoxDecoration? decoration;
      if (bgColor != null || radius > 0 || borderColor != null || isCircle || shadowColor != null) {
        decoration = BoxDecoration(
          color: bgColor,
          shape: isCircle ? BoxShape.circle : BoxShape.rectangle,
          borderRadius: !isCircle && radius > 0 ? BorderRadius.circular(radius) : null,
          border: borderColor != null ? Border.all(color: borderColor, width: borderWidth) : null,
          boxShadow: shadowColor != null
              ? [
                  BoxShadow(
                    color: shadowColor,
                    blurRadius: shadowBlur,
                    spreadRadius: 1,
                  ),
                ]
              : null,
        );
      }

      widget = Container(
        width: width,
        height: height,
        alignment: alignment,
        padding: padding != null ? EdgeInsets.all(padding) : null,
        margin: margin != null ? EdgeInsets.all(margin) : null,
        decoration: decoration,
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : null,
      );
      break;

    case 'AnimatedContainer':
      final animDuration = Duration(
        milliseconds: int.tryParse(node.props['duration_ms'] ?? '300') ?? 300,
      );
      final animCurve = parseCurve(node.props['curve']);
      final animWidth = double.tryParse(node.props['width'] ?? '');
      final animHeight = double.tryParse(node.props['height'] ?? '');
      final animPadding = double.tryParse(node.props['padding'] ?? '');
      final animMargin = double.tryParse(node.props['margin'] ?? '');
      final animRadius = double.tryParse(node.props['border_radius'] ?? '') ?? 0.0;
      final animBgColor = node.props.containsKey('color')
          ? parseHexColor(node.props['color']!)
          : null;

      BoxDecoration? animDecoration;
      if (animBgColor != null || animRadius > 0) {
        animDecoration = BoxDecoration(
          color: animBgColor,
          borderRadius: animRadius > 0 ? BorderRadius.circular(animRadius) : null,
        );
      }

      widget = AnimatedContainer(
        duration: animDuration,
        curve: animCurve,
        width: animWidth,
        height: animHeight,
        padding: animPadding != null ? EdgeInsets.all(animPadding) : null,
        margin: animMargin != null ? EdgeInsets.all(animMargin) : null,
        decoration: animDecoration,
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : null,
      );
      break;

    case 'AnimatedOpacity':
      final opacity = (double.tryParse(node.props['opacity'] ?? '1.0') ?? 1.0).clamp(0.0, 1.0);
      final animDuration = Duration(
        milliseconds: int.tryParse(node.props['duration_ms'] ?? '300') ?? 300,
      );
      final animCurve = parseCurve(node.props['curve']);
      widget = AnimatedOpacity(
        opacity: opacity,
        duration: animDuration,
        curve: animCurve,
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : const SizedBox.shrink(),
      );
      break;

    case 'AnimatedScale':
      final scale = double.tryParse(node.props['scale'] ?? '1.0') ?? 1.0;
      final animDuration = Duration(
        milliseconds: int.tryParse(node.props['duration_ms'] ?? '300') ?? 300,
      );
      final animCurve = parseCurve(node.props['curve']);
      widget = AnimatedScale(
        scale: scale,
        duration: animDuration,
        curve: animCurve,
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : const SizedBox.shrink(),
      );
      break;

    case 'AnimatedRotation':
      final turns = double.tryParse(node.props['turns'] ?? '0.0') ?? 0.0;
      final animDuration = Duration(
        milliseconds: int.tryParse(node.props['duration_ms'] ?? '300') ?? 300,
      );
      final animCurve = parseCurve(node.props['curve']);
      widget = AnimatedRotation(
        turns: turns,
        duration: animDuration,
        curve: animCurve,
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : const SizedBox.shrink(),
      );
      break;

    case 'AnimatedAlign':
      final alignment = parseAlignment(node.props['alignment']);
      final animDuration = Duration(
        milliseconds: int.tryParse(node.props['duration_ms'] ?? '300') ?? 300,
      );
      final animCurve = parseCurve(node.props['curve']);
      widget = AnimatedAlign(
        alignment: alignment,
        duration: animDuration,
        curve: animCurve,
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : const SizedBox.shrink(),
      );
      break;

    case 'AnimatedCrossFade':
      final animDuration = Duration(
        milliseconds: int.tryParse(node.props['duration_ms'] ?? '300') ?? 300,
      );
      final animCurve = parseCurve(node.props['curve']);
      final showFirst = node.props['show_first'] != 'false';

      Widget firstChild = const SizedBox.shrink();
      Widget secondChild = const SizedBox.shrink();

      for (final child in node.children) {
        if (child.props['slot'] == 'first_child') {
          firstChild = buildFromNode(child, sendEvent);
        } else if (child.props['slot'] == 'second_child') {
          secondChild = buildFromNode(child, sendEvent);
        }
      }
      if (node.children.length >= 2 && firstChild is SizedBox && secondChild is SizedBox) {
        firstChild = buildFromNode(node.children[0], sendEvent);
        secondChild = buildFromNode(node.children[1], sendEvent);
      }

      widget = AnimatedCrossFade(
        duration: animDuration,
        firstCurve: animCurve,
        secondCurve: animCurve,
        crossFadeState: showFirst ? CrossFadeState.showFirst : CrossFadeState.showSecond,
        firstChild: firstChild,
        secondChild: secondChild,
      );
      break;

    case 'Hero':
      final tag = node.props['tag'] ?? '';
      widget = Hero(
        tag: tag,
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : const SizedBox.shrink(),
      );
      break;

    case 'GestureDetector':
      final behaviorStr = node.props['behavior'] ?? 'opaque';
      HitTestBehavior behavior = HitTestBehavior.opaque;
      if (behaviorStr == 'translucent') behavior = HitTestBehavior.translucent;
      else if (behaviorStr == 'defer_to_child') behavior = HitTestBehavior.deferToChild;

      final onTapId = node.props['on_tap_callback_id'] ?? node.callbackId;
      final onDoubleTapId = node.props['on_double_tap_callback_id'];
      final onLongPressId = node.props['on_long_press_callback_id'];
      final onSwipeLeftId = node.props['on_swipe_left_callback_id'];
      final onSwipeRightId = node.props['on_swipe_right_callback_id'];
      final onSwipeUpId = node.props['on_swipe_up_callback_id'];
      final onSwipeDownId = node.props['on_swipe_down_callback_id'];

      widget = GestureDetector(
        behavior: behavior,
        onTap: onTapId.isNotEmpty ? () => sendEvent(onTapId, {}) : null,
        onDoubleTap: (onDoubleTapId != null && onDoubleTapId.isNotEmpty)
            ? () => sendEvent(onDoubleTapId, {})
            : null,
        onLongPress: (onLongPressId != null && onLongPressId.isNotEmpty)
            ? () => sendEvent(onLongPressId, {})
            : null,
        onHorizontalDragEnd: (details) {
          final v = details.primaryVelocity;
          if (v != null) {
            if (v < -100 && onSwipeLeftId != null && onSwipeLeftId.isNotEmpty) {
              sendEvent(onSwipeLeftId, {});
            } else if (v > 100 && onSwipeRightId != null && onSwipeRightId.isNotEmpty) {
              sendEvent(onSwipeRightId, {});
            }
          }
        },
        onVerticalDragEnd: (details) {
          final v = details.primaryVelocity;
          if (v != null) {
            if (v < -100 && onSwipeUpId != null && onSwipeUpId.isNotEmpty) {
              sendEvent(onSwipeUpId, {});
            } else if (v > 100 && onSwipeDownId != null && onSwipeDownId.isNotEmpty) {
              sendEvent(onSwipeDownId, {});
            }
          }
        },
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : const SizedBox.shrink(),
      );
      break;

    case 'InkWell':
      final onTapId = node.props['on_tap_callback_id'] ?? node.callbackId;
      final onDoubleTapId = node.props['on_double_tap_callback_id'];
      final onLongPressId = node.props['on_long_press_callback_id'];
      final splashColor = node.props.containsKey('splash_color')
          ? parseHexColor(node.props['splash_color']!)
          : null;
      final highlightColor = node.props.containsKey('highlight_color')
          ? parseHexColor(node.props['highlight_color']!)
          : null;
      final radius = double.tryParse(node.props['border_radius'] ?? '');

      widget = InkWell(
        onTap: onTapId.isNotEmpty ? () => sendEvent(onTapId, {}) : null,
        onDoubleTap: (onDoubleTapId != null && onDoubleTapId.isNotEmpty)
            ? () => sendEvent(onDoubleTapId, {})
            : null,
        onLongPress: (onLongPressId != null && onLongPressId.isNotEmpty)
            ? () => sendEvent(onLongPressId, {})
            : null,
        splashColor: splashColor,
        highlightColor: highlightColor,
        borderRadius: radius != null ? BorderRadius.circular(radius) : null,
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : null,
      );
      break;

    case 'Dismissible':
      final keyStr = node.props['key'] ?? (node.callbackId.isNotEmpty ? node.callbackId : 'dismiss_${node.hashCode}');
      Widget? background;
      Widget? secondaryBackground;
      Widget? dismissChild;

      for (final child in node.children) {
        if (child.props['slot'] == 'background') {
          background = buildFromNode(child, sendEvent);
        } else if (child.props['slot'] == 'secondary_background') {
          secondaryBackground = buildFromNode(child, sendEvent);
        } else {
          dismissChild = buildFromNode(child, sendEvent);
        }
      }

      final dirStr = node.props['direction'] ?? 'horizontal';
      DismissDirection direction = DismissDirection.horizontal;
      if (dirStr == 'end_to_start') direction = DismissDirection.endToStart;
      else if (dirStr == 'start_to_end') direction = DismissDirection.startToEnd;
      else if (dirStr == 'vertical') direction = DismissDirection.vertical;
      else if (dirStr == 'up') direction = DismissDirection.up;
      else if (dirStr == 'down') direction = DismissDirection.down;

      widget = Dismissible(
        key: Key(keyStr),
        direction: direction,
        background: background,
        secondaryBackground: secondaryBackground,
        onDismissed: (dir) {
          if (node.callbackId.isNotEmpty) {
            sendEvent(node.callbackId, {'direction': dir.name});
          }
        },
        child: dismissChild ?? const SizedBox.shrink(),
      );
      break;

    case 'Card':
      final elevation = double.tryParse(node.props['elevation'] ?? '') ?? 1.0;
      final margin = double.tryParse(node.props['margin'] ?? '') ?? 8.0;
      final radius = double.tryParse(node.props['border_radius'] ?? '') ?? 12.0;
      final shadowColor = node.props.containsKey('shadow_color')
          ? parseHexColor(node.props['shadow_color']!)
          : null;
      final surfaceTintColor = node.props.containsKey('surface_tint_color')
          ? parseHexColor(node.props['surface_tint_color']!)
          : null;
      final borderColor = node.props.containsKey('border_color')
          ? parseHexColor(node.props['border_color']!)
          : null;
      final borderWidth = double.tryParse(node.props['border_width'] ?? '') ?? 1.0;

      Widget? cardChild = node.children.isNotEmpty
          ? buildFromNode(node.children.first, sendEvent)
          : null;
      if (cardChild != null && node.props.containsKey('padding')) {
        final p = double.tryParse(node.props['padding']!) ?? 0.0;
        cardChild = Padding(padding: EdgeInsets.all(p), child: cardChild);
      }
      widget = Card(
        key: node.props.containsKey('key') ? ValueKey(node.props['key']!) : null,
        elevation: elevation,
        shadowColor: shadowColor,
        surfaceTintColor: surfaceTintColor,
        margin: EdgeInsets.symmetric(horizontal: margin, vertical: margin / 2),
        color: node.props.containsKey('color')
            ? parseHexColor(node.props['color']!)
            : Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radius),
          side: borderColor != null
              ? BorderSide(color: borderColor, width: borderWidth)
              : BorderSide.none,
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
        indent: double.tryParse(node.props['indent'] ?? ''),
        endIndent: double.tryParse(node.props['end_indent'] ?? ''),
        color: node.props.containsKey('color')
            ? parseHexColor(node.props['color']!)
            : Colors.grey.shade300,
      );
      break;

    case 'VerticalDivider':
      widget = VerticalDivider(
        width: double.tryParse(node.props['width'] ?? '') ?? 16.0,
        thickness: double.tryParse(node.props['thickness'] ?? '') ?? 1.0,
        indent: double.tryParse(node.props['indent'] ?? ''),
        endIndent: double.tryParse(node.props['end_indent'] ?? ''),
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

    case 'Flexible':
      final flex = int.tryParse(node.props['flex'] ?? '') ?? 1;
      final fitStr = node.props['fit'] ?? 'loose';
      final fit = fitStr == 'tight' ? FlexFit.tight : FlexFit.loose;
      widget = Flexible(
        flex: flex,
        fit: fit,
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : const SizedBox.shrink(),
      );
      break;

    case 'FittedBox':
      final fitStr = node.props['fit'] ?? 'scale_down';
      BoxFit fit = BoxFit.scaleDown;
      if (fitStr == 'contain') fit = BoxFit.contain;
      else if (fitStr == 'cover') fit = BoxFit.cover;
      else if (fitStr == 'fill') fit = BoxFit.fill;
      widget = FittedBox(
        fit: fit,
        child: node.children.isNotEmpty
            ? buildFromNode(node.children.first, sendEvent)
            : null,
      );
      break;

    case 'Spacer':
      final flex = int.tryParse(node.props['flex'] ?? '') ?? 1;
      widget = Spacer(flex: flex);
      break;

    case 'ListView':
      final pad = double.tryParse(node.props['padding'] ?? '') ?? 0.0;
      final isHorizontal = node.props['scroll_direction'] == 'horizontal';
      final shrinkWrap = node.props['shrink_wrap'] == 'true';
      final reverse = node.props['reverse'] == 'true';

      ScrollPhysics? listPhysics;
      final physStr = node.props['physics'];
      if (physStr == 'bouncing') listPhysics = const BouncingScrollPhysics();
      else if (physStr == 'clamping') listPhysics = const ClampingScrollPhysics();
      else if (physStr == 'never') listPhysics = const NeverScrollableScrollPhysics();
      else if (physStr == 'always') listPhysics = const AlwaysScrollableScrollPhysics();

      widget = ListView.custom(
        key: node.props.containsKey('key') ? ValueKey(node.props['key']!) : null,
        scrollDirection: isHorizontal ? Axis.horizontal : Axis.vertical,
        reverse: reverse,
        shrinkWrap: shrinkWrap,
        physics: listPhysics,
        padding: EdgeInsets.all(pad),
        childrenDelegate: SliverChildListDelegate(
          node.children.map((c) => buildFromNode(c, sendEvent)).toList(),
          addAutomaticKeepAlives: false,
          addRepaintBoundaries: true,
          addSemanticIndexes: true,
        ),
      );
      break;

    case 'SingleChildScrollView':
      final pad = double.tryParse(node.props['padding'] ?? '') ?? 0.0;
      final isHorizontal = node.props['scroll_direction'] == 'horizontal';
      final reverse = node.props['reverse'] == 'true';

      ScrollPhysics? scrollPhysics;
      final physStr = node.props['physics'];
      if (physStr == 'bouncing') scrollPhysics = const BouncingScrollPhysics();
      else if (physStr == 'clamping') scrollPhysics = const ClampingScrollPhysics();
      else if (physStr == 'never') scrollPhysics = const NeverScrollableScrollPhysics();
      else if (physStr == 'always') scrollPhysics = const AlwaysScrollableScrollPhysics();

      widget = SingleChildScrollView(
        key: node.props.containsKey('key') ? ValueKey(node.props['key']!) : null,
        scrollDirection: isHorizontal ? Axis.horizontal : Axis.vertical,
        reverse: reverse,
        physics: scrollPhysics,
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

    case 'Slider':
      final double value = double.tryParse(node.props['value'] ?? '0.0') ?? 0.0;
      final double min = double.tryParse(node.props['min'] ?? '0.0') ?? 0.0;
      final double max = double.tryParse(node.props['max'] ?? '1.0') ?? 1.0;
      final int? divisions = int.tryParse(node.props['divisions'] ?? '');
      final String? label = node.props['label'];
      final activeColor = node.props.containsKey('active_color')
          ? parseHexColor(node.props['active_color']!)
          : null;
      final inactiveColor = node.props.containsKey('inactive_color')
          ? parseHexColor(node.props['inactive_color']!)
          : null;

      final double clampedValue = value.clamp(min, max);

      widget = Slider(
        value: clampedValue,
        min: min,
        max: max,
        divisions: divisions,
        label: label,
        activeColor: activeColor,
        inactiveColor: inactiveColor,
        onChanged: node.callbackId.isNotEmpty
            ? (newVal) {
                sendEvent(node.callbackId, {'value': newVal.toString()});
              }
            : null,
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

      FloatingActionButtonLocation? fabLocation;
      final fabLocStr = node.props['floating_action_button_location'];
      if (fabLocStr == 'centerFloat') fabLocation = FloatingActionButtonLocation.centerFloat;
      else if (fabLocStr == 'centerDocked') fabLocation = FloatingActionButtonLocation.centerDocked;
      else if (fabLocStr == 'endFloat') fabLocation = FloatingActionButtonLocation.endFloat;
      else if (fabLocStr == 'endDocked') fabLocation = FloatingActionButtonLocation.endDocked;
      else if (fabLocStr == 'startFloat') fabLocation = FloatingActionButtonLocation.startFloat;
      else if (fabLocStr == 'startDocked') fabLocation = FloatingActionButtonLocation.startDocked;

      final resizeToAvoidBottomInset = node.props['resize_to_avoid_bottom_inset'] != 'false';
      final extendBody = node.props['extend_body'] == 'true';
      final extendBodyBehindAppBar = node.props['extend_body_behind_app_bar'] == 'true';

      widget = Scaffold(
        appBar: appBar,
        body: body,
        bottomNavigationBar: bottomBar,
        floatingActionButton: fab,
        floatingActionButtonLocation: fabLocation,
        drawer: drawerWidget,
        endDrawer: endDrawerWidget,
        bottomSheet: bottomSheetWidget,
        backgroundColor: bgColor,
        resizeToAvoidBottomInset: resizeToAvoidBottomInset,
        extendBody: extendBody,
        extendBodyBehindAppBar: extendBodyBehindAppBar,
      );
      break;

    case 'FloatingActionButton':
      final iconName = node.props['icon'];
      final labelText = node.props['label'];
      final tooltip = node.props['tooltip'];
      final mini = node.props['mini'] == 'true';
      final elevation = double.tryParse(node.props['elevation'] ?? '');
      final bgColor = node.props.containsKey('background_color')
          ? parseHexColor(node.props['background_color']!)
          : null;
      final fgColor = node.props.containsKey('foreground_color')
          ? parseHexColor(node.props['foreground_color']!)
          : null;

      final onPressed = node.callbackId.isNotEmpty
          ? () => sendEvent(node.callbackId, {})
          : null;

      Widget? fabChild;
      if (node.children.isNotEmpty) {
        fabChild = buildFromNode(node.children.first, sendEvent);
      } else if (iconName != null && iconName.isNotEmpty) {
        fabChild = Icon(resolveIcon(iconName));
      }

      if (labelText != null && labelText.isNotEmpty) {
        widget = FloatingActionButton.extended(
          onPressed: onPressed,
          tooltip: tooltip,
          elevation: elevation,
          backgroundColor: bgColor,
          foregroundColor: fgColor,
          icon: iconName != null ? Icon(resolveIcon(iconName)) : null,
          label: Text(labelText),
        );
      } else {
        widget = FloatingActionButton(
          onPressed: onPressed,
          tooltip: tooltip,
          mini: mini,
          elevation: elevation,
          backgroundColor: bgColor,
          foregroundColor: fgColor,
          child: fabChild,
        );
      }
      break;

    case 'ListTile':
      Widget? leading;
      Widget? title;
      Widget? subtitle;
      Widget? trailing;

      for (final child in node.children) {
        final slot = child.props['slot'];
        if (slot == 'leading') leading = buildFromNode(child, sendEvent);
        else if (slot == 'title') title = buildFromNode(child, sendEvent);
        else if (slot == 'subtitle') subtitle = buildFromNode(child, sendEvent);
        else if (slot == 'trailing') trailing = buildFromNode(child, sendEvent);
      }

      if (title == null && node.props.containsKey('title')) {
        title = Text(node.props['title']!);
      }
      if (subtitle == null && node.props.containsKey('subtitle')) {
        subtitle = Text(node.props['subtitle']!);
      }

      final isThreeLine = node.props['is_three_line'] == 'true';
      final dense = node.props['dense'] == 'true';
      final enabled = node.props['enabled'] != 'false';
      final selected = node.props['selected'] == 'true';
      final tileColor = node.props.containsKey('tile_color')
          ? parseHexColor(node.props['tile_color']!)
          : null;
      final selectedTileColor = node.props.containsKey('selected_tile_color')
          ? parseHexColor(node.props['selected_tile_color']!)
          : null;

      widget = ListTile(
        leading: leading,
        title: title,
        subtitle: subtitle,
        trailing: trailing,
        isThreeLine: isThreeLine,
        dense: dense,
        enabled: enabled,
        selected: selected,
        tileColor: tileColor,
        selectedTileColor: selectedTileColor,
        onTap: node.callbackId.isNotEmpty
            ? () => sendEvent(node.callbackId, {})
            : null,
      );
      break;

    case 'Badge':
      final label = node.props['label'];
      final bgColor = node.props.containsKey('background_color')
          ? parseHexColor(node.props['background_color']!)
          : null;
      final textColor = node.props.containsKey('text_color')
          ? parseHexColor(node.props['text_color']!)
          : null;
      final isSmall = node.props['is_small'] == 'true';

      Widget? badgeChild = node.children.isNotEmpty
          ? buildFromNode(node.children.first, sendEvent)
          : null;

      widget = Badge(
        backgroundColor: bgColor,
        textColor: textColor,
        label: !isSmall && label != null ? Text(label) : null,
        child: badgeChild,
      );
      break;

    case 'Chip':
    case 'ActionChip':
      final label = node.props['label'] ?? '';
      final avatarIcon = node.props['avatar'];
      final bgColor = node.props.containsKey('background_color')
          ? parseHexColor(node.props['background_color']!)
          : null;

      widget = ActionChip(
        label: Text(label),
        avatar: avatarIcon != null ? Icon(resolveIcon(avatarIcon), size: 18) : null,
        backgroundColor: bgColor,
        onPressed: node.callbackId.isNotEmpty
            ? () => sendEvent(node.callbackId, {})
            : null,
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

    case 'MaterialApp':
      if (node.children.isNotEmpty) {
        final home = node.children.firstWhere(
          (c) => c.props['slot'] == 'home',
          orElse: () => node.children.first,
        );
        widget = buildFromNode(home, sendEvent);
      } else {
        widget = const SizedBox.shrink();
      }
      break;

    case 'GridView':
      final crossAxisCount = int.tryParse(node.props['cross_axis_count'] ?? '') ?? 2;
      final mainAxisSpacing = double.tryParse(node.props['main_axis_spacing'] ?? '') ?? 8.0;
      final crossAxisSpacing = double.tryParse(node.props['cross_axis_spacing'] ?? '') ?? 8.0;
      final childAspectRatio = double.tryParse(node.props['child_aspect_ratio'] ?? '') ?? 1.0;
      final shrinkWrap = node.props['shrink_wrap'] == 'true';
      final paddingVal = double.tryParse(node.props['padding'] ?? '');
      final physStr = node.props['physics'];
      ScrollPhysics? gridPhysics;
      if (physStr == 'bouncing') gridPhysics = const BouncingScrollPhysics();
      else if (physStr == 'clamping') gridPhysics = const ClampingScrollPhysics();
      else if (physStr == 'never') gridPhysics = const NeverScrollableScrollPhysics();
      else if (physStr == 'always') gridPhysics = const AlwaysScrollableScrollPhysics();

      widget = GridView.count(
        crossAxisCount: crossAxisCount,
        mainAxisSpacing: mainAxisSpacing,
        crossAxisSpacing: crossAxisSpacing,
        childAspectRatio: childAspectRatio,
        shrinkWrap: shrinkWrap,
        physics: gridPhysics,
        padding: paddingVal != null ? EdgeInsets.all(paddingVal) : null,
        children: node.children.map((c) => buildFromNode(c, sendEvent)).toList(),
      );
      break;

    case 'Radio':
      final val = node.props['value'] ?? '';
      final groupVal = node.props['group_value'] ?? '';
      final activeColor = parseHexColor(node.props['active_color'] ?? '');
      widget = Radio<String>(
        value: val,
        groupValue: groupVal,
        activeColor: activeColor,
        onChanged: (v) {
          if (node.callbackId.isNotEmpty) {
            sendEvent(node.callbackId, {'value': v ?? ''});
          }
        },
      );
      break;

    case 'RadioListTile':
      final val = node.props['value'] ?? '';
      final groupVal = node.props['group_value'] ?? '';
      final activeColor = parseHexColor(node.props['active_color'] ?? '');
      Widget? titleW;
      Widget? subtitleW;
      for (final c in node.children) {
        if (c.props['slot'] == 'title') titleW = buildFromNode(c, sendEvent);
        else if (c.props['slot'] == 'subtitle') subtitleW = buildFromNode(c, sendEvent);
      }
      widget = RadioListTile<String>(
        value: val,
        groupValue: groupVal,
        activeColor: activeColor,
        title: titleW,
        subtitle: subtitleW,
        onChanged: (v) {
          if (node.callbackId.isNotEmpty) {
            sendEvent(node.callbackId, {'value': v ?? ''});
          }
        },
      );
      break;

    case 'Tooltip':
      final msg = node.props['message'] ?? '';
      Widget child = const SizedBox.shrink();
      if (node.children.isNotEmpty) {
        child = buildFromNode(node.children.first, sendEvent);
      }
      widget = Tooltip(
        message: msg,
        child: child,
      );
      break;

    case 'RichText':
      final spans = <InlineSpan>[];
      for (final c in node.children) {
        if (c.type == 'TextSpan') {
          spans.add(_buildTextSpan(c, sendEvent));
        }
      }
      TextAlign? richAlign;
      final ta = node.props['text_align'];
      if (ta == 'left') richAlign = TextAlign.left;
      else if (ta == 'center') richAlign = TextAlign.center;
      else if (ta == 'right') richAlign = TextAlign.right;
      else if (ta == 'justify') richAlign = TextAlign.justify;

      widget = Text.rich(
        TextSpan(children: spans),
        textAlign: richAlign,
      );
      break;

    case 'CircleAvatar':
      final radius = double.tryParse(node.props['radius'] ?? '');
      final bgColor = parseHexColor(node.props['background_color'] ?? '');
      final fgColor = parseHexColor(node.props['foreground_color'] ?? '');
      final imgUrl = node.props['image_url'];
      ImageProvider? imgProvider;
      if (imgUrl != null && imgUrl.isNotEmpty) {
        imgProvider = NetworkImage(imgUrl);
      }
      Widget? childW;
      if (node.children.isNotEmpty) {
        childW = buildFromNode(node.children.first, sendEvent);
      }
      widget = CircleAvatar(
        radius: radius,
        backgroundColor: bgColor,
        foregroundColor: fgColor,
        backgroundImage: imgProvider,
        child: childW,
      );
      break;

    case 'LinearProgressIndicator':
      final val = double.tryParse(node.props['value'] ?? '');
      final color = parseHexColor(node.props['color'] ?? '');
      final bgColor = parseHexColor(node.props['background_color'] ?? '');
      final minHeight = double.tryParse(node.props['min_height'] ?? '');
      widget = LinearProgressIndicator(
        value: val,
        color: color,
        backgroundColor: bgColor,
        minHeight: minHeight,
      );
      break;

    case 'PopupMenuButton':
      final iconName = node.props['icon'];
      final tooltip = node.props['tooltip'];
      widget = PopupMenuButton<String>(
        icon: iconName != null ? Icon(resolveIcon(iconName)) : null,
        tooltip: tooltip,
        onSelected: (val) {
          if (node.callbackId.isNotEmpty) {
            sendEvent(node.callbackId, {'value': val});
          }
        },
        itemBuilder: (ctx) {
          return node.children.where((c) => c.type == 'PopupMenuItem').map((c) {
            final itemVal = c.props['value'] ?? '';
            final enabled = c.props['enabled'] != 'false';
            Widget childW = const SizedBox.shrink();
            if (c.children.isNotEmpty) {
              childW = buildFromNode(c.children.first, sendEvent);
            }
            return PopupMenuItem<String>(
              value: itemVal,
              enabled: enabled,
              child: childW,
            );
          }).toList();
        },
      );
      break;

    case 'RefreshIndicator':
      final color = parseHexColor(node.props['color'] ?? '');
      final bgColor = parseHexColor(node.props['background_color'] ?? '');
      final displacement = double.tryParse(node.props['displacement'] ?? '') ?? 40.0;
      Widget childW = const SizedBox.shrink();
      if (node.children.isNotEmpty) {
        childW = buildFromNode(node.children.first, sendEvent);
      }
      widget = RefreshIndicator(
        color: color,
        backgroundColor: bgColor,
        displacement: displacement,
        onRefresh: () async {
          if (node.callbackId.isNotEmpty) {
            sendEvent(node.callbackId, {});
            await Future.delayed(const Duration(milliseconds: 500));
          }
        },
        child: childW,
      );
      break;

    case 'AlertDialog':
      Widget? titleW;
      Widget? contentW;
      final actions = <Widget>[];
      for (final c in node.children) {
        if (c.props['slot'] == 'title') titleW = buildFromNode(c, sendEvent);
        else if (c.props['slot'] == 'content') contentW = buildFromNode(c, sendEvent);
        else if (c.props['slot'] == 'action') actions.add(buildFromNode(c, sendEvent));
        else actions.add(buildFromNode(c, sendEvent));
      }
      final bgColor = parseHexColor(node.props['background_color'] ?? '');
      final elevation = double.tryParse(node.props['elevation'] ?? '');
      widget = AlertDialog(
        title: titleW,
        content: contentW,
        actions: actions.isNotEmpty ? actions : null,
        backgroundColor: bgColor,
        elevation: elevation,
      );
      break;

    case 'SimpleDialog':
      Widget? titleW;
      final children = <Widget>[];
      for (final c in node.children) {
        if (c.props['slot'] == 'title') titleW = buildFromNode(c, sendEvent);
        else children.add(buildFromNode(c, sendEvent));
      }
      final bgColor = parseHexColor(node.props['background_color'] ?? '');
      final elevation = double.tryParse(node.props['elevation'] ?? '');
      widget = SimpleDialog(
        title: titleW,
        backgroundColor: bgColor,
        elevation: elevation,
        children: children.isNotEmpty ? children : null,
      );
      break;

    case 'WebView':
      widget = PyWebViewWidget(node: node, sendEvent: sendEvent);
      break;

    case 'VideoPlayer':
      widget = PyVideoPlayerWidget(node: node, sendEvent: sendEvent);
      break;

    case 'CameraPreview':
      widget = PyCameraPreviewWidget(node: node, sendEvent: sendEvent);
      break;

    case 'Chewie':
      widget = PyChewieWidget(node: node, sendEvent: sendEvent);
      break;

    default:
      widget = Text('[unknown widget: ${node.type}]');
      break;


  }

  // Generic onTap wrapper: allows ANY widget carrying a callbackId to be interactive
  if (node.callbackId.isNotEmpty &&
      node.type != 'Button' &&
      node.type != 'ElevatedButton' &&
      node.type != 'OutlinedButton' &&
      node.type != 'TextButton' &&
      node.type != 'IconButton' &&
      node.type != 'TextField' &&
      node.type != 'TextFormField' &&
      node.type != 'DropdownButton' &&
      node.type != 'DropdownMenu' &&
      node.type != 'GestureDetector' &&
      node.type != 'InkWell' &&
      node.type != 'Dismissible' &&
      node.type != 'Switch' &&
      node.type != 'Checkbox' &&
      node.type != 'Slider' &&
      node.type != 'Radio' &&
      node.type != 'RadioListTile' &&
      node.type != 'PopupMenuButton' &&
      node.type != 'RefreshIndicator' &&
      node.type != 'BottomNavigationBar' &&
      node.type != 'PageView') {
    return InkWell(
      onTap: () => sendEvent(node.callbackId, {}),
      child: widget,
    );
  }

  return widget;
}

/// Native interactive TextField/TextFormField preserving state, cursor, and validation.
class PyTextFieldWidget extends StatefulWidget {
  final WidgetNode node;
  final void Function(String callbackId, Map<String, String> eventData) sendEvent;

  const PyTextFieldWidget({
    super.key,
    required this.node,
    required this.sendEvent,
  });

  @override
  State<PyTextFieldWidget> createState() => _PyTextFieldWidgetState();
}

class _PyTextFieldWidgetState extends State<PyTextFieldWidget> {
  late TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.node.props['value'] ?? '');
  }

  @override
  void didUpdateWidget(covariant PyTextFieldWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    final incomingVal = widget.node.props['value'] ?? '';
    if (incomingVal != _controller.text) {
      _controller.value = _controller.value.copyWith(
        text: incomingVal,
        selection: TextSelection.collapsed(offset: incomingVal.length),
      );
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final props = widget.node.props;
    final isObscure = props['obscure_text'] == 'true';
    final readOnly = props['read_only'] == 'true';
    final enabled = props['enabled'] != 'false';

    final maxLines = isObscure ? 1 : (int.tryParse(props['max_lines'] ?? '1') ?? 1);
    final minLines = isObscure ? 1 : int.tryParse(props['min_lines'] ?? '');

    // Keyboard type
    TextInputType keyboardType = TextInputType.text;
    final kt = props['keyboard_type'];
    if (kt == 'email' || kt == 'email_address') {
      keyboardType = TextInputType.emailAddress;
    } else if (kt == 'number') {
      keyboardType = TextInputType.number;
    } else if (kt == 'phone') {
      keyboardType = TextInputType.phone;
    } else if (kt == 'multiline') {
      keyboardType = TextInputType.multiline;
    } else if (kt == 'url') {
      keyboardType = TextInputType.url;
    }

    // Text alignment
    TextAlign textAlign = TextAlign.start;
    final ta = props['text_align'];
    if (ta == 'center') {
      textAlign = TextAlign.center;
    } else if (ta == 'right' || ta == 'end') {
      textAlign = TextAlign.end;
    }

    // Border parsing
    final borderType = props['border'] ?? 'outline';
    final radiusVal = double.tryParse(props['border_radius'] ?? '') ?? 8.0;
    final borderRadius = BorderRadius.circular(radiusVal);
    final borderColor = props.containsKey('border_color')
        ? parseHexColor(props['border_color']!)
        : null;
    final focusedBorderColor = props.containsKey('focused_border_color')
        ? parseHexColor(props['focused_border_color']!)
        : null;

    InputBorder border;
    InputBorder? focusedBorder;
    if (borderType == 'none') {
      border = InputBorder.none;
    } else if (borderType == 'underline') {
      border = UnderlineInputBorder(
        borderSide: borderColor != null ? BorderSide(color: borderColor) : const BorderSide(),
      );
      if (focusedBorderColor != null) {
        focusedBorder = UnderlineInputBorder(
          borderSide: BorderSide(color: focusedBorderColor, width: 2.0),
        );
      }
    } else {
      border = OutlineInputBorder(
        borderRadius: borderRadius,
        borderSide: borderColor != null ? BorderSide(color: borderColor) : const BorderSide(),
      );
      if (focusedBorderColor != null) {
        focusedBorder = OutlineInputBorder(
          borderRadius: borderRadius,
          borderSide: BorderSide(color: focusedBorderColor, width: 2.0),
        );
      }
    }

    // Prefix icon
    Widget? prefixIcon;
    final prefixName = props['prefix_icon'];
    if (prefixName != null && prefixName.isNotEmpty) {
      prefixIcon = Icon(resolveIcon(prefixName));
    }

    // Suffix icon
    Widget? suffixIcon;
    final suffixName = props['suffix_icon'];
    final suffixCallbackId = props['suffix_callback_id'];
    if (suffixName != null && suffixName.isNotEmpty) {
      if (suffixCallbackId != null && suffixCallbackId.isNotEmpty) {
        suffixIcon = IconButton(
          icon: Icon(resolveIcon(suffixName)),
          onPressed: () => widget.sendEvent(suffixCallbackId, {}),
        );
      } else {
        suffixIcon = Icon(resolveIcon(suffixName));
      }
    }

    final filled = props['filled'] == 'true';
    final fillColor = props.containsKey('fill_color')
        ? parseHexColor(props['fill_color']!)
        : null;

    final autofocus = props['autofocus'] == 'true';
    final autocorrect = props['autocorrect'] != 'false';
    final cursorColor = props.containsKey('cursor_color')
        ? parseHexColor(props['cursor_color']!)
        : null;
    final maxLength = int.tryParse(props['max_length'] ?? '');
    final contentPad = double.tryParse(props['content_padding'] ?? '');

    TextCapitalization textCapitalization = TextCapitalization.none;
    final tc = props['text_capitalization'];
    if (tc == 'words') textCapitalization = TextCapitalization.words;
    else if (tc == 'sentences') textCapitalization = TextCapitalization.sentences;
    else if (tc == 'characters') textCapitalization = TextCapitalization.characters;

    return TextField(
      controller: _controller,
      obscureText: isObscure,
      readOnly: readOnly,
      enabled: enabled,
      autofocus: autofocus,
      autocorrect: autocorrect,
      cursorColor: cursorColor,
      maxLength: maxLength,
      textCapitalization: textCapitalization,
      maxLines: maxLines,
      minLines: minLines,
      keyboardType: keyboardType,
      textAlign: textAlign,
      decoration: InputDecoration(
        labelText: props['label'],
        hintText: props['hint'] ?? props['placeholder'],
        helperText: props['helper_text'],
        errorText: props['error_text'],
        prefixIcon: prefixIcon,
        suffixIcon: suffixIcon,
        prefixText: props['prefix_text'],
        suffixText: props['suffix_text'],
        contentPadding: contentPad != null ? EdgeInsets.all(contentPad) : null,
        filled: filled,
        fillColor: fillColor,
        border: border,
        focusedBorder: focusedBorder,
      ),
      onChanged: (text) {
        if (widget.node.callbackId.isNotEmpty) {
          widget.sendEvent(widget.node.callbackId, {'value': text});
        }
      },
      onSubmitted: (text) {
        final submitCb = props['submit_callback_id'];
        if (submitCb != null && submitCb.isNotEmpty) {
          widget.sendEvent(submitCb, {'value': text});
        }
      },
    );
  }
}

/// Native Material DropdownButton with safe item fallback.
class PyDropdownButtonWidget extends StatefulWidget {
  final WidgetNode node;
  final void Function(String callbackId, Map<String, String> eventData) sendEvent;

  const PyDropdownButtonWidget({
    super.key,
    required this.node,
    required this.sendEvent,
  });

  @override
  State<PyDropdownButtonWidget> createState() => _PyDropdownButtonWidgetState();
}

class _PyDropdownButtonWidgetState extends State<PyDropdownButtonWidget> {
  String? _selectedValue;

  @override
  void initState() {
    super.initState();
    _updateSelectedValue();
  }

  @override
  void didUpdateWidget(covariant PyDropdownButtonWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    _updateSelectedValue();
  }

  void _updateSelectedValue() {
    final v = widget.node.props['value'];
    if (v != null && v.isNotEmpty) {
      _selectedValue = v;
    } else {
      _selectedValue = null;
    }
  }

  @override
  Widget build(BuildContext context) {
    final props = widget.node.props;
    final isExpanded = props['is_expanded'] != 'false';
    final iconName = props['icon'] ?? 'arrow_drop_down';
    final iconSize = double.tryParse(props['icon_size'] ?? '') ?? 24.0;
    final elevation = int.tryParse(props['elevation'] ?? '') ?? 8;
    final hintText = props['hint'];

    final List<DropdownMenuItem<String>> menuItems = [];
    final Set<String> validValues = {};

    for (final child in widget.node.children) {
      if (child.props['slot'] == 'hint') continue;
      final val = child.props['value'] ?? '';
      final label = child.props['label'] ?? val;
      final isEnabled = child.props['disabled'] != 'true';

      validValues.add(val);
      menuItems.add(
        DropdownMenuItem<String>(
          value: val,
          enabled: isEnabled,
          child: child.children.isNotEmpty
              ? buildFromNode(child.children.first, widget.sendEvent)
              : Text(label),
        ),
      );
    }

    final effectiveValue = (_selectedValue != null && validValues.contains(_selectedValue))
        ? _selectedValue
        : null;

    Widget? hintWidget;
    WidgetNode? hintChild;
    for (final c in widget.node.children) {
      if (c.props['slot'] == 'hint') {
        hintChild = c;
        break;
      }
    }
    if (hintChild != null) {
      hintWidget = buildFromNode(hintChild, widget.sendEvent);
    } else if (hintText != null && hintText.isNotEmpty) {
      hintWidget = Text(hintText);
    }

    return DropdownButton<String>(
      value: effectiveValue,
      hint: hintWidget,
      isExpanded: isExpanded,
      icon: Icon(resolveIcon(iconName), size: iconSize),
      elevation: elevation,
      items: menuItems,
      onChanged: (newVal) {
        if (newVal != null) {
          setState(() {
            _selectedValue = newVal;
          });
          if (widget.node.callbackId.isNotEmpty) {
            widget.sendEvent(widget.node.callbackId, {'value': newVal});
          }
        }
      },
    );
  }
}

/// Material 3 DropdownMenu widget with styled selection.
class PyDropdownMenuWidget extends StatelessWidget {
  final WidgetNode node;
  final void Function(String callbackId, Map<String, String> eventData) sendEvent;

  const PyDropdownMenuWidget({
    super.key,
    required this.node,
    required this.sendEvent,
  });

  @override
  Widget build(BuildContext context) {
    final props = node.props;
    final label = props['label'];
    final hint = props['hint_text'];
    final initialSelection = props['initial_selection'];
    final width = double.tryParse(props['width'] ?? '');

    final leadingIconName = props['leading_icon'];
    final trailingIconName = props['trailing_icon'];

    final entries = <DropdownMenuEntry<String>>[];
    for (final child in node.children) {
      final val = child.props['value'] ?? '';
      final labelText = child.props['label'] ?? val;
      final isEnabled = child.props['disabled'] != 'true';
      entries.add(
        DropdownMenuEntry<String>(
          value: val,
          label: labelText,
          enabled: isEnabled,
        ),
      );
    }

    return DropdownMenu<String>(
      width: width,
      initialSelection: initialSelection,
      label: label != null ? Text(label) : null,
      hintText: hint,
      leadingIcon: (leadingIconName != null && leadingIconName.isNotEmpty)
          ? Icon(resolveIcon(leadingIconName))
          : null,
      trailingIcon: (trailingIconName != null && trailingIconName.isNotEmpty)
          ? Icon(resolveIcon(trailingIconName))
          : null,
      dropdownMenuEntries: entries,
      onSelected: (val) {
        if (val != null && node.callbackId.isNotEmpty) {
          sendEvent(node.callbackId, {'value': val});
        }
      },
    );
  }
}

/// Recursively builds an InlineSpan for RichText.
InlineSpan _buildTextSpan(
  WidgetNode node,
  void Function(String callbackId, Map<String, String> eventData) sendEvent,
) {
  final text = node.props['text'] ?? '';
  final fontSize = double.tryParse(node.props['font_size'] ?? '');
  final color = parseHexColor(node.props['color'] ?? '');
  FontWeight? fontWeight;
  final fw = node.props['font_weight'];
  if (fw == 'bold') fontWeight = FontWeight.bold;
  final fontStyle = node.props['font_style'] == 'italic' ? FontStyle.italic : null;

  final children = <InlineSpan>[];
  for (final c in node.children) {
    if (c.type == 'TextSpan') {
      children.add(_buildTextSpan(c, sendEvent));
    }
  }

  GestureRecognizer? recognizer;
  if (node.callbackId.isNotEmpty) {
    recognizer = TapGestureRecognizer()
      ..onTap = () => sendEvent(node.callbackId, {});
  }

  return TextSpan(
    text: text,
    style: TextStyle(
      fontSize: fontSize,
      color: color,
      fontWeight: fontWeight,
      fontStyle: fontStyle,
    ),
    recognizer: recognizer,
    children: children.isNotEmpty ? children : null,
  );
}

/// Interactive WebView container with URL bar and navigation controls.
class PyWebViewWidget extends StatefulWidget {
  final WidgetNode node;
  final void Function(String callbackId, Map<String, String> eventData) sendEvent;

  const PyWebViewWidget({
    super.key,
    required this.node,
    required this.sendEvent,
  });

  @override
  State<PyWebViewWidget> createState() => _PyWebViewWidgetState();
}

class _PyWebViewWidgetState extends State<PyWebViewWidget> {
  late String _currentUrl;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _currentUrl = widget.node.props['url'] ?? 'about:blank';
  }

  @override
  void didUpdateWidget(PyWebViewWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    final newUrl = widget.node.props['url'];
    if (newUrl != null && newUrl != _currentUrl) {
      setState(() => _currentUrl = newUrl);
    }
  }

  @override
  Widget build(BuildContext context) {
    final width = double.tryParse(widget.node.props['width'] ?? '');
    final height = double.tryParse(widget.node.props['height'] ?? '') ?? 300.0;
    final showAddressBar = widget.node.props['show_address_bar'] != 'false';

    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: Colors.grey.shade300),
        borderRadius: BorderRadius.circular(8.0),
      ),
      child: Column(
        children: [
          if (showAddressBar)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
              color: Colors.grey.shade100,
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back, size: 18),
                    onPressed: () {},
                  ),
                  IconButton(
                    icon: const Icon(Icons.refresh, size: 18),
                    onPressed: () {
                      setState(() => _isLoading = true);
                      Future.delayed(const Duration(milliseconds: 600), () {
                        if (mounted) setState(() => _isLoading = false);
                      });
                      if (widget.node.callbackId.isNotEmpty) {
                        widget.sendEvent(widget.node.callbackId, {'action': 'reload', 'url': _currentUrl});
                      }
                    },
                  ),
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(4.0),
                        border: Border.all(color: Colors.grey.shade300),
                      ),
                      child: Text(
                        _currentUrl,
                        style: const TextStyle(fontSize: 12, color: Colors.black87),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          if (_isLoading)
            const LinearProgressIndicator(minHeight: 2),
          Expanded(
            child: Container(
              color: Colors.grey.shade50,
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.language, size: 40, color: Colors.blueAccent),
                    const SizedBox(height: 8),
                    Text(
                      'WebView: $_currentUrl',
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Interactive VideoPlayer viewport with controls.
class PyVideoPlayerWidget extends StatefulWidget {
  final WidgetNode node;
  final void Function(String callbackId, Map<String, String> eventData) sendEvent;

  const PyVideoPlayerWidget({
    super.key,
    required this.node,
    required this.sendEvent,
  });

  @override
  State<PyVideoPlayerWidget> createState() => _PyVideoPlayerWidgetState();
}

class _PyVideoPlayerWidgetState extends State<PyVideoPlayerWidget> {
  bool _isPlaying = false;
  double _position = 0.0;
  final double _duration = 180.0;

  @override
  void initState() {
    super.initState();
    _isPlaying = widget.node.props['auto_play'] == 'true';
  }

  @override
  Widget build(BuildContext context) {
    final width = double.tryParse(widget.node.props['width'] ?? '');
    final height = double.tryParse(widget.node.props['height'] ?? '') ?? 220.0;
    final url = widget.node.props['url'] ?? 'video.mp4';
    final showControls = widget.node.props['show_controls'] != 'false';

    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: Colors.black,
        borderRadius: BorderRadius.circular(8.0),
      ),
      child: Stack(
        children: [
          Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  _isPlaying ? Icons.play_circle_fill : Icons.pause_circle_filled,
                  size: 48,
                  color: Colors.white70,
                ),
                const SizedBox(height: 6),
                Text(
                  url,
                  style: const TextStyle(color: Colors.white60, fontSize: 11),
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          if (showControls)
            Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              child: Container(
                color: Colors.black54,
                padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
                child: Row(
                  children: [
                    IconButton(
                      icon: Icon(
                        _isPlaying ? Icons.pause : Icons.play_arrow,
                        color: Colors.white,
                        size: 20,
                      ),
                      onPressed: () {
                        setState(() => _isPlaying = !_isPlaying);
                        if (widget.node.callbackId.isNotEmpty) {
                          widget.sendEvent(widget.node.callbackId, {
                            'action': _isPlaying ? 'play' : 'pause',
                            'position': _position.toString(),
                          });
                        }
                      },
                    ),
                    Expanded(
                      child: Slider(
                        value: _position,
                        max: _duration,
                        activeColor: Colors.redAccent,
                        inactiveColor: Colors.white24,
                        onChanged: (val) {
                          setState(() => _position = val);
                          if (widget.node.callbackId.isNotEmpty) {
                            widget.sendEvent(widget.node.callbackId, {
                              'action': 'seek',
                              'position': val.toString(),
                            });
                          }
                        },
                      ),
                    ),
                    Text(
                      '${_position.toInt()}s / ${_duration.toInt()}s',
                      style: const TextStyle(color: Colors.white70, fontSize: 10),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}

/// Viewfinder widget displaying a live camera preview.
class PyCameraPreviewWidget extends StatelessWidget {
  final WidgetNode node;
  final void Function(String callbackId, Map<String, String> eventData) sendEvent;

  const PyCameraPreviewWidget({
    super.key,
    required this.node,
    required this.sendEvent,
  });

  @override
  Widget build(BuildContext context) {
    final width = double.tryParse(node.props['width'] ?? '');
    final height = double.tryParse(node.props['height'] ?? '') ?? 300.0;
    final cameraId = node.props['camera_id'] ?? '0';

    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: Colors.black,
        borderRadius: BorderRadius.circular(12.0),
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          const Center(
            child: Icon(Icons.camera_alt_outlined, size: 56, color: Colors.white30),
          ),
          Positioned(
            top: 12,
            left: 12,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.black54,
                borderRadius: BorderRadius.circular(4),
              ),
              child: Row(
                children: [
                  const Icon(Icons.circle, color: Colors.greenAccent, size: 8),
                  const SizedBox(width: 6),
                  Text('Camera $cameraId', style: const TextStyle(color: Colors.white, fontSize: 11)),
                ],
              ),
            ),
          ),
          Positioned(
            bottom: 16,
            child: FloatingActionButton.small(
              backgroundColor: Colors.white,
              onPressed: () {
                if (node.callbackId.isNotEmpty) {
                  sendEvent(node.callbackId, {'action': 'shutter', 'cameraId': cameraId});
                }
              },
              child: const Icon(Icons.camera, color: Colors.black87),
            ),
          ),
        ],
      ),
    );
  }
}

/// Interactive Chewie video player with full Material controls.
class PyChewieWidget extends StatefulWidget {
  final WidgetNode node;
  final void Function(String callbackId, Map<String, String> eventData) sendEvent;

  const PyChewieWidget({
    super.key,
    required this.node,
    required this.sendEvent,
  });

  @override
  State<PyChewieWidget> createState() => _PyChewieWidgetState();
}

class _PyChewieWidgetState extends State<PyChewieWidget> {
  bool _isPlaying = false;
  double _position = 0.0;
  final double _duration = 240.0;

  @override
  void initState() {
    super.initState();
    _isPlaying = widget.node.props['auto_play'] == 'true';
  }

  @override
  Widget build(BuildContext context) {
    final width = double.tryParse(widget.node.props['width'] ?? '');
    final height = double.tryParse(widget.node.props['height'] ?? '') ?? 240.0;
    final aspectRatio = double.tryParse(widget.node.props['aspect_ratio'] ?? '') ?? (16.0 / 9.0);

    return AspectRatio(
      aspectRatio: aspectRatio,
      child: Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
          color: Colors.black87,
          borderRadius: BorderRadius.circular(10.0),
        ),
        child: Stack(
          alignment: Alignment.center,
          children: [
            Center(
              child: IconButton(
                iconSize: 56,
                icon: Icon(
                  _isPlaying ? Icons.pause_circle_outline : Icons.play_circle_outline,
                  color: Colors.white,
                ),
                onPressed: () {
                  setState(() => _isPlaying = !_isPlaying);
                  if (widget.node.callbackId.isNotEmpty) {
                    widget.sendEvent(widget.node.callbackId, {
                      'action': _isPlaying ? 'play' : 'pause',
                      'position': _position.toString(),
                    });
                  }
                },
              ),
            ),
            Positioned(
              left: 12,
              bottom: 8,
              right: 12,
              child: Row(
                children: [
                  Text(
                    '${_position.toInt()}s',
                    style: const TextStyle(color: Colors.white, fontSize: 11),
                  ),
                  Expanded(
                    child: Slider(
                      value: _position,
                      max: _duration,
                      activeColor: Colors.deepOrangeAccent,
                      inactiveColor: Colors.white30,
                      onChanged: (val) {
                        setState(() => _position = val);
                        if (widget.node.callbackId.isNotEmpty) {
                          widget.sendEvent(widget.node.callbackId, {
                            'action': 'seek',
                            'position': val.toString(),
                          });
                        }
                      },
                    ),
                  ),
                  Text(
                    '${_duration.toInt()}s',
                    style: const TextStyle(color: Colors.white70, fontSize: 11),
                  ),
                  const SizedBox(width: 8),
                  const Icon(Icons.fullscreen, color: Colors.white70, size: 20),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}



