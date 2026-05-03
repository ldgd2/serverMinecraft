import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:provider/provider.dart';
import 'core/theme/app_theme.dart';
import 'core/providers/app_providers.dart';
import 'core/providers/player_provider.dart';
import 'features/auth/screens/login_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'core/constants/app_constants.dart';
import 'core/api/api_client.dart';
import 'core/services/update_service.dart';
import 'features/home/screens/home_screen.dart';
import 'features/servers/screens/create_server_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: ".env");

  // Force portrait orientation for mobile
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // Transparent status bar for immersive look
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
    systemNavigationBarColor: Color(0xFF161B22),
    systemNavigationBarIconBrightness: Brightness.light,
  ));

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => ServerProvider()),
        ChangeNotifierProvider(create: (_) => VersionProvider()),
        ChangeNotifierProvider(create: (_) => PlayerProvider()),
      ],
      child: const MinecraftManagerApp(),
    ),
  );
}

class MinecraftManagerApp extends StatefulWidget {
  const MinecraftManagerApp({super.key});

  @override
  State<MinecraftManagerApp> createState() => _MinecraftManagerAppState();
}

class _MinecraftManagerAppState extends State<MinecraftManagerApp> {
  @override
  void initState() {
    super.initState();
    // Connect providers for real-time updates
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final serverProvider = context.read<ServerProvider>();
      final playerProvider = context.read<PlayerProvider>();
      
      serverProvider.onAchievementReceived = (sender) {
        // If the achievement belongs to the current player, refresh their profile
        if (sender == playerProvider.username) {
          playerProvider.notifyProfileUpdate();
        }
      };
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Minecraft Manager',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark,
      initialRoute: '/splash',
      routes: {
        '/splash': (_) => const SplashScreen(),
        '/login': (_) => const LoginScreen(),
        '/': (_) => const HomeScreen(),
        '/servers/create': (_) => const CreateServerScreen(),
      },
    );
  }
}

// ─── Splash Screen ────────────────────────────────────────────────────────────

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _scale;
  late Animation<double> _opacity;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1200));
    _scale = Tween<double>(begin: 0.6, end: 1.0).animate(CurvedAnimation(parent: _ctrl, curve: Curves.elasticOut));
    _opacity = Tween<double>(begin: 0.0, end: 1.0).animate(CurvedAnimation(parent: _ctrl, curve: const Interval(0, 0.5)));
    _ctrl.forward();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    await Future.delayed(const Duration(milliseconds: 1800));
    if (!mounted) return;
    
    // Load dynamic server URL before anything else
    final prefs = await SharedPreferences.getInstance();
    final savedUrl = prefs.getString(AppConstants.serverUrlKey);
    if (savedUrl != null && savedUrl.isNotEmpty) {
      AppConstants.baseUrl = savedUrl;
      ApiClient.instance.setBaseUrl(savedUrl);
    }
    
    final auth = context.read<AuthProvider>();
    final player = context.read<PlayerProvider>();
    final loggedIn = await auth.tryAutoLogin();
    await player.tryAutoLogin();
    if (!mounted) return;

    // ── Check for app update ──────────────────────────────────────────────────
    final updateInfo = await UpdateService.instance.checkForUpdate();
    if (mounted && updateInfo.hasUpdate && updateInfo.downloadUrl != null) {
      await _showUpdateDialog(updateInfo);
      if (!mounted) return;
    }
    // ─────────────────────────────────────────────────────────────────────────

    Navigator.pushReplacementNamed(context, loggedIn ? '/' : '/login');
  }

  Future<void> _showUpdateDialog(UpdateInfo info) async {
    await showDialog(
      context: context,
      barrierDismissible: true,
      builder: (ctx) => _UpdateDialog(info: info),
    );
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF0D1117), Color(0xFF1a3a1a), Color(0xFF0D1117)],
          ),
        ),
        child: Center(
          child: AnimatedBuilder(
            animation: _ctrl,
            builder: (_, __) => Opacity(
              opacity: _opacity.value,
              child: Transform.scale(
                scale: _scale.value,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 100,
                      height: 100,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [Color(0xFF5D8A3C), Color(0xFF3F6128)],
                        ),
                        borderRadius: BorderRadius.circular(22),
                        boxShadow: [
                          BoxShadow(color: const Color(0xFF5D8A3C).withOpacity(0.6), blurRadius: 40, spreadRadius: 4),
                        ],
                      ),
                      child: const Icon(Icons.dns_rounded, size: 56, color: Colors.white),
                    ),
                    const SizedBox(height: 28),
                    const Text(
                      'MINECRAFT',
                      style: TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.bold, letterSpacing: 4),
                    ),
                    const Text(
                      'SERVER MANAGER',
                      style: TextStyle(color: Color(0xFF7CBF52), fontSize: 13, letterSpacing: 6, fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 60),
                    const SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF5D8A3C)),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// ─── Update Dialog ────────────────────────────────────────────────────────────

class _UpdateDialog extends StatefulWidget {
  final UpdateInfo info;
  const _UpdateDialog({required this.info});

  @override
  State<_UpdateDialog> createState() => _UpdateDialogState();
}

class _UpdateDialogState extends State<_UpdateDialog>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _bounce;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 800))
      ..repeat(reverse: true);
    _bounce = Tween<double>(begin: 0, end: -8).animate(
      CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final info = widget.info;
    return AlertDialog(
      backgroundColor: const Color(0xFF161B22),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      contentPadding: const EdgeInsets.fromLTRB(24, 20, 24, 0),
      actionsPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
      title: Column(
        children: [
          AnimatedBuilder(
            animation: _bounce,
            builder: (_, child) => Transform.translate(
              offset: Offset(0, _bounce.value),
              child: child,
            ),
            child: Container(
              width: 64, height: 64,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF5D8A3C), Color(0xFF3F6128)],
                  begin: Alignment.topLeft, end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                boxShadow: [BoxShadow(color: const Color(0xFF5D8A3C).withOpacity(0.4), blurRadius: 20)],
              ),
              child: const Icon(Icons.system_update_rounded, color: Colors.white, size: 36),
            ),
          ),
          const SizedBox(height: 14),
          const Text(
            '¡Nueva versión disponible!',
            style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
            textAlign: TextAlign.center,
          ),
        ],
      ),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const SizedBox(height: 8),
          // Versión actual → nueva
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(
              color: const Color(0xFF0D1117),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _VersionBadge(label: 'Actual', version: info.currentVersion, color: const Color(0xFF8B949E)),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 12),
                  child: Icon(Icons.arrow_forward_rounded, color: Color(0xFF5D8A3C), size: 20),
                ),
                _VersionBadge(label: 'Nueva', version: info.latestVersion, color: const Color(0xFF7CBF52)),
              ],
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            'Actualiza para obtener las últimas mejoras y correcciones.',
            style: TextStyle(color: Color(0xFF8B949E), fontSize: 12),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Más tarde', style: TextStyle(color: Color(0xFF8B949E))),
        ),
        ElevatedButton.icon(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF5D8A3C),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
          ),
          icon: const Icon(Icons.download_rounded, color: Colors.white, size: 18),
          label: const Text('Descargar', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          onPressed: () async {
            if (info.downloadUrl != null) {
              await UpdateService.instance.openDownloadUrl(info.downloadUrl!);
            }
            if (context.mounted) Navigator.pop(context);
          },
        ),
      ],
    );
  }
}

class _VersionBadge extends StatelessWidget {
  final String label;
  final String version;
  final Color color;
  const _VersionBadge({required this.label, required this.version, required this.color});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(label, style: const TextStyle(color: Color(0xFF8B949E), fontSize: 10)),
        const SizedBox(height: 2),
        Text('v$version', style: TextStyle(color: color, fontSize: 14, fontWeight: FontWeight.bold)),
      ],
    );
  }
}
