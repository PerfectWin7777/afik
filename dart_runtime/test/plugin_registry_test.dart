import 'package:flutter_test/flutter_test.dart';
import 'package:pyflutter_dart_runtime/plugins/plugin_registry.dart';

class Plain implements PyFlutterPlugin {
  Map<String, String>? seen;
  @override
  Future<dynamic> handleMethodCall(String m, Map<String, String> a) async { seen = a; return 'ok'; }
}
class Structured implements StructuredPyFlutterPlugin {
  Map<String, dynamic>? seen;
  @override
  Future<dynamic> handleMethodCall(String m, Map<String, String> a) async => 'plain';
  @override
  Future<dynamic> handleRawCall(String m, Map<String, dynamic> a) async { seen = a; return 'raw'; }
}
void main() {
  test('plain plugins get JSON text, structured ones the raw values', () async {
    final p = Plain(); final s = Structured();
    PluginRegistry.register('p', p); PluginRegistry.register('s', s);
    final args = {'a': 'x', 'b': {'k': [1, 2]}, 'c': true, 'd': 1.5, 'e': null, 'f': [1, 'z']};
    expect(await PluginRegistry.dispatch('p', 'm', args), 'ok');
    expect(p.seen, {'a': 'x', 'b': '{"k":[1,2]}', 'c': 'true', 'd': '1.5', 'e': '', 'f': '[1,"z"]'});
    expect(await PluginRegistry.dispatch('s', 'm', args), 'raw');
    expect(s.seen!['b'], {'k': [1, 2]});
  });
}
