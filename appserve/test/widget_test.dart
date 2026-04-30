import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:appserve/main.dart';
import 'package:appserve/core/providers/app_providers.dart';

void main() {
  testWidgets('App smoke test - renders MaterialApp', (WidgetTester tester) async {
    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => AuthProvider()),
          ChangeNotifierProvider(create: (_) => ServerProvider()),
        ],
        child: const MinecraftManagerApp(),
      ),
    );
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
