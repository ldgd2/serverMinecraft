import 'package:flutter_dotenv/flutter_dotenv.dart';

class AppConstants {
  AppConstants._();

  // API
  static String baseUrl = dotenv.get('API_URL', fallback: 'http://localhost:8000/api/v1');
  static const String tokenKey = 'auth_token';
  static const String userKey = 'user_data';
  static const String serverUrlKey = 'server_url';
  
  // Credentials for auto-refresh
  static const String usernameKey = 'saved_username';
  static const String passwordKey = 'saved_password';

  // App
  static const String appName = 'Minecraft Manager';
  static const String appVersion = '1.0.0';

  // Routes
  static const String routeLogin = '/login';
  static const String routeHome = '/';
  static const String routeServers = '/servers';
  static const String routeServerDetail = '/servers/:id';
  static const String routeConsole = '/servers/:id/console';
  static const String routePlayers = '/servers/:id/players';
  static const String routeWorlds = '/servers/:id/worlds';
  static const String routeBackup = '/servers/:id/backup';
  static const String routeSettings = '/settings';
  static const String routeSystem = '/system';
}
