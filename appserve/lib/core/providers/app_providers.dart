import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../constants/app_constants.dart';
import '../models/user_model.dart';
import '../models/server_model.dart';
import '../models/version_model.dart';
import '../services/auth_service.dart';
import '../services/server_service.dart';
import '../services/version_service.dart';
import '../services/backup_service.dart';
import '../api/api_client.dart';

/// Auth state — handles login/logout/session
class AuthProvider extends ChangeNotifier {
  final _authService = AuthService();

  UserModel? _user;
  bool _isLoading = false;
  String? _error;

  UserModel? get user => _user;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isAuthenticated => _user != null;

  Future<bool> tryAutoLogin() async {
    final isLoggedIn = await _authService.isLoggedIn();
    if (isLoggedIn) {
      _user = await _authService.getMe();
      if (_user == null) {
        await _authService.logout(); 
      }
      notifyListeners();
      return _user != null;
    }
    return false;
  }

  Future<bool> login(String username, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final auth = await _authService.login(username, password);
      _user = auth.user;
      return true;
    } catch (e) {
      _error = _parseError(e);
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await _authService.logout();
    _user = null;
    notifyListeners();
  }

  String _parseError(dynamic e) {
    if (e.toString().contains('401')) return 'Sesión vencida o credenciales incorrectas';
    if (e.toString().contains('connection')) return 'No se puede conectar al servidor';
    return 'Error al iniciar sesión. Intente de nuevo.';
  }
}

/// Server state — handles the list and individual server operations
class ServerProvider extends ChangeNotifier {
  final _serverService = ServerService();
  
  WebSocketChannel? _consoleChannel;
  WebSocketChannel? _statusChannel;
  WebSocketChannel? _globalStatusChannel;
  WebSocketChannel? _systemLogsChannel;
  WebSocketChannel? _chatChannel;

  List<ServerModel> _servers = [];
  ServerModel? _selectedServer;
  bool _isLoading = false;
  bool _isLoadingMods = false;
  String? _error;
  String _consoleLogs = '';
  Map<String, dynamic> _systemStats = {};
  Map<String, dynamic> _creationStats = {};
  String _systemLogs = '';
  List<Map<String, dynamic>> _chatMessages = [];
  
  // Players and Mods
  List<Map<String, dynamic>> _onlinePlayers = [];
  List<Map<String, dynamic>> _bannedUsers = [];
  List<Map<String, dynamic>> _installedMods = [];

  void Function(String)? onAchievementReceived;

  List<ServerModel> get servers => _servers;
  ServerModel? get selectedServer => _selectedServer;
  bool get isLoading => _isLoading;
  bool get isLoadingMods => _isLoadingMods;
  String? get error => _error;
  String get consoleLogs => _consoleLogs;
  Map<String, dynamic> get systemStats => _systemStats;
  Map<String, dynamic> get creationStats => _creationStats;
  String get systemLogs => _systemLogs;
  List<Map<String, dynamic>> get chatMessages => _chatMessages;
  
  List<Map<String, dynamic>> get onlinePlayers => _onlinePlayers;
  List<Map<String, dynamic>> get bannedUsers => _bannedUsers;
  List<Map<String, dynamic>> get installedMods => _installedMods;

  int get onlineCount => _servers.where((s) => s.isOnline).length;
  int get offlineCount => _servers.where((s) => s.isOffline).length;

  // ── Persistence ────────────────────────────────────────────────────────────

  Future<void> _saveServersToCache(List<ServerModel> servers) async {
    final prefs = await SharedPreferences.getInstance();
    final data = servers.map((s) => s.toJson()).toList();
    await prefs.setString('admin_servers_cache', jsonEncode(data));
  }

  Future<void> _loadServersFromCache() async {
    final prefs = await SharedPreferences.getInstance();
    final data = prefs.getString('admin_servers_cache');
    if (data != null) {
      final List decoded = jsonDecode(data);
      _servers = decoded.map((e) => ServerModel.fromJson(e)).toList();
      notifyListeners();
    }
  }

  final Map<String, DateTime> _throttles = {};

  bool _throttle(String key, Duration duration) {
    final now = DateTime.now();
    final last = _throttles[key];
    if (last != null && now.difference(last) < duration) return true;
    _throttles[key] = now;
    return false;
  }

  // ── Actions ────────────────────────────────────────────────────────────────

  Future<void> loadServers({bool force = false}) async {
    if (_isLoading) return;
    
    // If not forced and we have data, use cache/current state first
    if (!force && _servers.isNotEmpty) {
      // Throttle network requests to 60 seconds for the full list
      if (_throttle('loadServers', const Duration(seconds: 60))) {
        return; 
      }
    }

    _isLoading = true;
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(AppConstants.tokenKey);
    
    // Always try to show cache immediately if list is empty
    if (_servers.isEmpty) {
      await _loadServersFromCache();
    }
    
    if (token == null) {
      _isLoading = false;
      notifyListeners();
      return;
    }

    _error = null;
    notifyListeners();
    try {
      final fetchedServers = await _serverService.getServers();
      _servers = fetchedServers;
      await _saveServersToCache(_servers);
      
      // We don't automatically load creation stats every time to save IO
      // Global WebSocket will notify us if something changes
      _connectToGlobalStatus();
    } catch (e) {
      debugPrint('Load Servers Error: $e');
      if (e.toString().contains('401')) await ApiClient.instance.clearToken();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> selectServer(String name, String username) async {
    _isLoading = true;
    notifyListeners();
    
    final server = _servers.firstWhere((s) => s.name == name, orElse: () => _selectedServer!);
    _selectedServer = server;
    _consoleLogs = ''; 
    _chatMessages = [];
    
    _closeWebSockets();
    _connectToConsole(name);
    _connectToStatus(name);
    _connectToChat(name, username);
    await loadChatHistory(name);
    await loadPlayers(name);
    await loadMods(name);
    
    _isLoading = false;
    notifyListeners();
  }

  // --- Players Management ---

  Future<void> loadPlayers(String name) async {
    try {
      final data = await _serverService.getPlayers(name);
      _onlinePlayers = List<Map<String, dynamic>>.from(data['online_players'] ?? []);
      _bannedUsers = List<Map<String, dynamic>>.from(data['banned_users'] ?? []);
      notifyListeners();
    } catch (e) {
      debugPrint('Load Players Error: $e');
    }
  }

  Future<void> unbanPlayer(String serverName, String player) async {
    await _serverService.unbanPlayer(serverName, player);
    await loadPlayers(serverName);
  }

  Future<void> kickPlayer(String serverName, String player, String reason) async {
    await _serverService.kickPlayer(serverName, player, reason: reason);
    await loadPlayers(serverName);
  }

  Future<void> banPlayer(String serverName, String player, String reason, {String? expires}) async {
    await _serverService.banPlayer(serverName, player, reason: reason, expires: expires);
    await loadPlayers(serverName);
  }

  // --- Mod Management ---

  Future<void> loadMods(String serverName) async {
    _isLoadingMods = true;
    notifyListeners();
    try {
      final mods = await _serverService.getMods(serverName);
      _installedMods = List<Map<String, dynamic>>.from(mods);
    } catch (e) {
      debugPrint('Load Mods Error: $e');
    } finally {
      _isLoadingMods = false;
      notifyListeners();
    }
  }

  Future<void> uploadMod(String serverName, String filePath) async {
    await _serverService.uploadMod(serverName, filePath);
    await loadMods(serverName);
  }

  Future<void> deleteMod(String serverName, String modName) async {
    await _serverService.deleteMod(serverName, modName);
    await loadMods(serverName);
  }

  Future<void> renameMod(String serverName, String oldName, String newName) async {
    await _serverService.renameMod(serverName, oldName, newName);
    await loadMods(serverName);
  }

  // --- Console & Logs ---

  void clearConsole() {
    _consoleLogs = '';
    notifyListeners();
  }

  void connectToSystemLogs() {
    _systemLogsChannel?.sink.close();
    final wsUrl = AppConstants.baseUrl.replaceFirst('http', 'ws');
    _systemLogsChannel = WebSocketChannel.connect(Uri.parse('$wsUrl/system/logs/ws'));
    _systemLogsChannel!.stream.listen((msg) {
      _systemLogs += '\n$msg';
      if (_systemLogs.length > 20000) _systemLogs = _systemLogs.substring(10000);
      notifyListeners();
    });
  }

  // --- System ---

  Future<void> loadSystemStats({bool force = false}) async {
    if (!force && _throttle('loadSystemStats', const Duration(minutes: 5))) return;
    
    try {
      _systemStats = await _serverService.getSystemStats();
      notifyListeners();
    } catch (e) {
      debugPrint('Load System Stats Error: $e');
      if (e.toString().contains('401')) await ApiClient.instance.clearToken();
    }
  }

  Future<void> restartDashboardService() async {
    await _serverService.restartDashboardService();
  }

  // --- Helpers & WebSockets ---

  void _closeWebSockets() {
    _consoleChannel?.sink.close();
    _statusChannel?.sink.close();
    _systemLogsChannel?.sink.close();
    _chatChannel?.sink.close();
    _consoleChannel = null;
    _statusChannel = null;
    _systemLogsChannel = null;
    _chatChannel = null;
  }

  void _connectToConsole(String name) {
    final wsUrl = AppConstants.baseUrl.replaceFirst('http', 'ws');
    _consoleChannel = WebSocketChannel.connect(Uri.parse('$wsUrl/servers/$name/console'));
    _consoleChannel!.stream.listen((message) {
      _consoleLogs += '\n$message';
      if (_consoleLogs.length > 15000) _consoleLogs = _consoleLogs.substring(5000);
      notifyListeners();
    });
  }

  void _connectToStatus(String name) {
    final wsUrl = AppConstants.baseUrl.replaceFirst('http', 'ws');
    _statusChannel = WebSocketChannel.connect(Uri.parse('$wsUrl/servers/$name/status'));
    _statusChannel!.stream.listen((message) {
      try {
        final data = jsonDecode(message);
        final stats = data['stats'];
        if (_selectedServer?.name == name) {
          _selectedServer = _selectedServer!.copyWith(
            status: stats['status'] ?? stats['state'], 
            cpuUsage: (stats['cpu_usage_percent'] ?? 0.0).toDouble(),
            ramUsage: stats['ram_usage_mb'] ?? 0,
            diskUsage: stats['disk_usage_mb'] ?? 0,
            currentPlayers: data['count'] ?? 0,
          );
          notifyListeners();
        }
      } catch (_) {}
    });
  }

  void _connectToGlobalStatus() {
    if (_globalStatusChannel != null) return;
    final wsUrl = AppConstants.baseUrl.replaceFirst('http', 'ws');
    _globalStatusChannel = WebSocketChannel.connect(Uri.parse('$wsUrl/servers/ws/status-updates'));
    _globalStatusChannel!.stream.listen((message) {
      try {
        final data = jsonDecode(message);
        if (data['type'] == 'server_update') {
          for (var update in data['servers']) {
            final idx = _servers.indexWhere((s) => s.name == update['name']);
            if (idx != -1) {
              _servers[idx] = _servers[idx].copyWith(
                status: update['data']['status'],
                currentPlayers: update['data']['players'] ?? 0,
              );
            }
          }
          notifyListeners();
        }
      } catch (_) {}
    });
  }

  void _connectToChat(String name, String username) {
    final wsUrl = AppConstants.baseUrl.replaceFirst('http', 'ws');
    _chatChannel = WebSocketChannel.connect(Uri.parse('$wsUrl/servers/$name/chat?username=$username'));
    _chatChannel!.stream.listen((message) {
      try {
        final data = jsonDecode(message);
        if (data['type'] == 'chat') {
          _chatMessages.add({
            'sender': data['sender'] ?? 'System',
            'message': data['message'] ?? '',
            'is_system': data['is_system'] ?? false,
            'chat_type': data['chat_type'] ?? 'received',
            'time': DateTime.now().toIso8601String(),
          });
          if (data['chat_type'] == 'achievement' && onAchievementReceived != null) {
            onAchievementReceived!(data['sender'] ?? 'Player');
          }
          notifyListeners();
        }
      } catch (_) {}
    });
  }

  Future<void> loadChatHistory(String name) async {
    try {
      final history = await _serverService.getChatHistory(name);
      _chatMessages = List<Map<String, dynamic>>.from(history.map((m) => {
        'sender': m['user'],
        'message': m['text'],
        'is_system': m['type'] != 'chat',
        'chat_type': m['type'],
        'time': DateTime.fromMillisecondsSinceEpoch(m['time']).toIso8601String(),
      }));
      notifyListeners();
    } catch (_) {}
  }

  void sendChatMessage(String name, String message, String username) {
    _chatChannel?.sink.add(jsonEncode({'type': 'send_chat', 'username': username, 'message': message}));
  }

  Future<void> loadCreationStats({bool force = false}) async {
    // Only fetch if forced or if we have something active in cache (or if list is empty)
    if (!force && _creationStats.isEmpty && _throttle('loadCreationStats', const Duration(minutes: 2))) return;
    
    try { 
      _creationStats = await _serverService.getActiveCreations(); 
      notifyListeners(); 
    } catch (_) {}
  }

  Future<void> startServer(String name) async { await _serverService.startServer(name); }
  Future<void> stopServer(String name) async { await _serverService.stopServer(name); }
  Future<void> restartServer(String name) async { await _serverService.restartServer(name); }
  Future<void> sendCommand(String name, String cmd) async { await _serverService.sendCommand(name, cmd); }
  Future<void> loadLogs(String name) async { _consoleLogs = await _serverService.getLogs(name); notifyListeners(); }
  Future<ServerModel> createServer(Map<String, dynamic> data) async { 
    final s = await _serverService.createServer(data); 
    _servers.add(s); 
    notifyListeners(); 
    return s; 
  }
  Future<void> deleteServer(String name) async { 
    await _serverService.deleteServer(name); 
    _servers.removeWhere((s) => s.name == name); 
    notifyListeners(); 
  }

  Future<void> updateServerResources(String name, int ram, double cpu) async {
    final updated = await _serverService.updateServer(name, {
      'ram_mb': ram,
      'cpu_cores': cpu,
    });
    
    final idx = _servers.indexWhere((s) => s.name == name);
    if (idx != -1) {
      _servers[idx] = updated;
    }
    if (_selectedServer?.name == name) {
      _selectedServer = updated;
    }
    notifyListeners();
  }

  Future<void> teleportPlayerToPlayer(String name, String player, String target) async {
    await _serverService.teleport(name, {
      'player': player,
      'target': target,
      'mode': 'player_to_player'
    });
  }

  Future<void> teleportPlayerToCoords(String name, String player, double x, double y, double z) async {
    await _serverService.teleport(name, {
      'player': player,
      'x': x,
      'y': y,
      'z': z,
      'mode': 'player_to_coords'
    });
  }

  Future<void> teleportPlayersToPlayer(String name, List<String> players, String target) async {
    await _serverService.teleport(name, {
      'players': players,
      'target': target,
      'mode': 'players_to_player'
    });
  }

  @override
  void dispose() { _closeWebSockets(); _globalStatusChannel?.sink.close(); super.dispose(); }
}

class VersionProvider extends ChangeNotifier {
  final _versionService = VersionService();
  List<VersionModel> _installedVersions = [];
  List<String> _remoteVersions = [];
  bool _isLoading = false;
  String? _error;

  List<VersionModel> get installedVersions => _installedVersions;
  List<String> get remoteVersions => _remoteVersions;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> loadInstalledVersions() async {
    _isLoading = true; _error = null; notifyListeners();
    try { _installedVersions = await _versionService.getInstalledVersions(); } catch (e) { _error = e.toString(); } finally { _isLoading = false; notifyListeners(); }
  }

  Future<void> loadRemoteVersions(String type) async {
    _isLoading = true; _error = null; notifyListeners();
    try { _remoteVersions = await _versionService.getRemoteVersions(type); } catch (e) { _error = e.toString(); } finally { _isLoading = false; notifyListeners(); }
  }

  Future<void> downloadVersion(String type, String version) async {
    _isLoading = true; _error = null; notifyListeners();
    try { await _versionService.downloadVersion(loaderType: type, mcVersion: version); await loadInstalledVersions(); } catch (e) { _error = e.toString(); } finally { _isLoading = false; notifyListeners(); }
  }
}

class BackupProvider extends ChangeNotifier {
  final _backupService = BackupService();
  List<Map<String, dynamic>> _backups = [];
  bool _isLoading = false;
  List<Map<String, dynamic>> get backups => _backups;
  bool get isLoading => _isLoading;

  Future<void> fetchBackups() async {
    _isLoading = true; notifyListeners();
    try { _backups = await _backupService.getBackups(); } finally { _isLoading = false; notifyListeners(); }
  }
}
