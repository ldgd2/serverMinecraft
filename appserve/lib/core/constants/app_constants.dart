class AppConstants {
  AppConstants._();

  // API
  static const String baseUrl = 'http://YOUR_VPS_IP:8000';
  static const String tokenKey = 'auth_token';
  static const String userKey = 'user_data';
  static const String serverUrlKey = 'server_url';

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
