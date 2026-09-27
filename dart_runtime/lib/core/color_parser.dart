import 'package:flutter/material.dart';

/// Parses hex color strings into Flutter Color objects.
/// Supports 6-digit (#RRGGBB) and 8-digit (#AARRGGBB) hex formats.
Color? parseHexColor(String hex) {
  final cleaned = hex.replaceFirst('#', '');
  final value = int.tryParse(cleaned, radix: 16);
  if (value == null) return null;
  return Color(cleaned.length == 6 ? (0xFF000000 | value) : value);
}
