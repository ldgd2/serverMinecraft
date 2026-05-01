import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../constants/app_constants.dart';
import '../models/user_model.dart';
import '../models/server_model.dart';
import '../models/version_model.dart';
import '../services/auth_service.dart';
import '../services/server_service.dart';
import '../services/version_service.dart';

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
    if (e.toString().contains('401')) return 'Incorrect username or password';
    if (e.toString().contains('connection')) return 'Cannot connect to server';
    return 'Login failed. Please try again.';
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
  String? _error;
  String _consoleLogs = '';
  Map<String, dynamic> _systemStats = {};
  Map<String, dynamic> _creationStats = {};
  String _systemLogs = '';
  List<Map<String, dynamic>> _chatMessages = [];
  List<dynamic> _onlinePlayers = [];
  List<dynamic> _bannedUsers = [];
  List<dynamic> _bannedIps = [];

  List<ServerModel> get servers => _servers;
  ServerModel? get selectedServer => _selectedServer;
  bool get isLoading => _isLoading;
  String? get error => _error;
  String get consoleLogs => _consoleLogs;
  Map<String, dynamic> get systemStats => _systemStats;
  Map<String, dynamic> get creationStats => _creationStats;
  String get systemLogs => _systemLogs;
  List<Map<String, dynamic>> get chatMessages => _chatMessages;
  List<dynamic> get onlinePlayers => _onlinePlayers;
  List<dynamic> get bannedUsers => _bannedUsers;
  List<dynamic> get bannedIps => _bannedIps;

  int get onlineCount => _servers.where((s) => s.isOnline).length;
  int get offlineCount => _servers.where((s) => s.isOffline).length;

  Future<void> loadServers() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _servers = await _serverService.getServers();
      await loadCreationStats();
      _connectToGlobalStatus();
    } catch (e) {
      _error = 'Failed to load servers';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> selectServer(String name) async {
    _isLoading = true;
    notifyListeners();
    
    // Find server in list if possible to avoid extra API call
    final server = _servers.firstWhere((s) => s.name == name, orElse: () => _selectedServer!);
    _selectedServer = server;
    _selectedServer = server;
    _consoleLogs = ''; // Clear previous server logs
    _chatMessages = []; // Clear previous server chat
    
    _closeWebSockets();
    _connectToConsole(name);
    _connectToStatus(name);
    _connectToChat(name);
    
    _isLoading = false;
    notifyListeners();
  }

  void _closeWebSockets() {
    _consoleChannel?.sink.close();
    _statusChannel?.sink.close();
    _consoleChannel = null;
    _statusChannel = null;
    _systemLogsChannel?.sink.close();
    _systemLogsChannel = null;
    _chatChannel?.sink.close();
    _chatChannel = null;
  }

  void _closeGlobalWebSocket() {
    _globalStatusChannel?.sink.close();
    _globalStatusChannel = null;
  }

  void _connectToGlobalStatus() {
    if (_globalStatusChannel != null) return;

    final wsUrl = AppConstants.baseUrl.replaceFirst('http', 'ws');
    _globalStatusChannel = WebSocketChannel.connect(
      Uri.parse('$wsUrl/servers/ws/status-updates'),
    );

    _globalStatusChannel!.stream.listen((message) {
      try {
        final data = jsonDecode(message);
        if (data['type'] == 'server_update') {
          final List updates = data['servers'];
          for (var update in updates) {
            final name = update['name'];
            final updateData = update['data'];
            
            final index = _servers.indexWhere((s) => s.name == name);
            if (index != -1) {
              _servers[index] = _servers[index].copyWith(
                status: updateData['status'],
                cpuUsage: (updateData['cpu'] ?? 0.0).toDouble(),
                ramUsage: updateData['ram'] ?? 0,
                diskUsage: updateData['disk'] ?? 0,
                currentPlayers: updateData['players'] ?? 0,
              );
              
              if (_selectedServer?.name == name) {
                _selectedServer = _servers[index];
              }
            }
          }
          notifyListeners();
        }
      } catch (e) {
        debugPrint('Global Status WS Error: $e');
      }
    }, onDone: () {
      _globalStatusChannel = null;
    }, onError: (e) {
      _globalStatusChannel = null;
    });
  }

  void _connectToConsole(String name) {
    final wsUrl = AppConstants.baseUrl.replaceFirst('http', 'ws');
    _consoleChannel = WebSocketChannel.connect(
      Uri.parse('$wsUrl/servers/$name/console'),
    );

    _consoleChannel!.stream.listen((message) {
      _consoleLogs += '\n$message';
      if (_consoleLogs.length > 15000) {
        _consoleLogs = _consoleLogs.substring(_consoleLogs.length - 10000);
      }
      notifyListeners();
    }, onError: (e) {
      debugPrint('Console WS Error: $e');
    });
  }

  void _connectToStatus(String name) {
    final wsUrl = AppConstants.baseUrl.replaceFirst('http', 'ws');
    _statusChannel = WebSocketChannel.connect(
      Uri.parse('$wsUrl/servers/$name/status'),
    );

    _statusChannel!.stream.listen((message) {
      try {
        final data = jsonDecode(message);
        final stats = data['stats'];
        
        if (_selectedServer != null && _selectedServer!.name == name) {
          _selectedServer = _selectedServer!.copyWith(
            status: stats['status'] ?? stats['state'], // Backend uses 'status' in some places and 'state' in others
            cpuUsage: (stats['cpu_usage_percent'] ?? stats['cpu'] ?? 0.0).toDouble(),
            ramUsage: stats['ram_usage_mb'] ?? stats['ram'] ?? 0,
            diskUsage: stats['disk_usage_mb'] ?? stats['disk'] ?? 0,
            currentPlayers: data['count'] ?? stats['players'] ?? 0,
          );
          
          // Also update in main list
          final index = _servers.indexWhere((s) => s.name == name);
          if (index != -1) {
            _servers[index] = _selectedServer!;
          }
          notifyListeners();
        }
      } catch (e) {
        debugPrint('Status WS Decode Error: $e');
      }
    }, onError: (e) {
      debugPrint('Status WS Error: $e');
    });
  }

  @override
  void dispose() {
    _closeWebSockets();
    _closeGlobalWebSocket();
    super.dispose();
  }

  Future<void> startServer(String name) async {
    await _serverService.startServer(name);
    await loadServers();
  }

  Future<void> stopServer(String name) async {
    await _serverService.stopServer(name);
    await loadServers();
  }

  Future<void> restartServer(String name) async {
    // Set local state to RESTARTING to give immediate feedback
    final index = _servers.indexWhere((s) => s.name == name);
    if (index != -1) {
      _servers[index] = _servers[index].copyWith(status: 'RESTARTING');
      if (_selectedServer?.name == name) {
        _selectedServer = _servers[index];
      }
      notifyListeners();
    }

    try {
      await _serverService.restartServer(name);
      // We don't need to loadServers here as the Global WS or individual WS will update us
    } catch (e) {
      debugPrint('Restart error: $e');
      _error = 'Failed to restart server';
      notifyListeners();
    }
  }

  Future<void> sendCommand(String name, String cmd) async {
    // Send command via API, output will stream back through WebSocket
    await _serverService.sendCommand(name, cmd);
    _consoleLogs += '\n> $cmd';
    notifyListeners();
  }

  Future<void> loadLogs(String name) async {
    _consoleLogs = await _serverService.getLogs(name);
    notifyListeners();
  }

  Future<void> loadSystemStats() async {
    try {
      _systemStats = await _serverService.getSystemStats();
      notifyListeners();
    } catch (_) {}
  }

  Future<void> loadCreationStats() async {
    try {
      _creationStats = await _serverService.getActiveCreations();
      notifyListeners();
    } catch (_) {}
  }

  Future<ServerModel> createServer(Map<String, dynamic> data) async {
    final server = await _serverService.createServer(data);
    _servers.add(server);
    notifyListeners();
    return server;
  }

  Future<void> deleteServer(String name) async {
    await _serverService.deleteServer(name);
    _servers.removeWhere((s) => s.name == name);
    notifyListeners();
  }

  Future<void> loadPlayers(String name) async {
    try {
      final res = await _serverService.getPlayers(name);
      _onlinePlayers = res['online_players'] ?? [];
      _bannedUsers = res['banned_users'] ?? [];
      _bannedIps = res['banned_ips'] ?? [];
      notifyListeners();
    } catch (e) {
      debugPrint('Load Players Error: $e');
    }
  }

  Future<void> kickPlayer(String serverName, String playerName) async {
    await _serverService.sendCommand(serverName, 'kick $playerName');
    await loadPlayers(serverName);
  }

  Future<void> banPlayer(String serverName, String playerName, {String reason = 'Banned by admin'}) async {
    await _serverService.sendCommand(serverName, 'ban $playerName $reason');
    await loadPlayers(serverName);
  }

  Future<void> unbanPlayer(String serverName, String playerName) async {
    await _serverService.sendCommand(serverName, 'pardon $playerName');
    await loadPlayers(serverName);
  }

  void clearConsole() {
    _consoleLogs = '';
    notifyListeners();
  }

  Future<void> restartDashboardService() async {
    await _serverService.restartDashboardService();
  }

  void connectToSystemLogs() {
    _systemLogsChannel?.sink.close();
    _systemLogs = 'Connecting to service logs...\n';
    notifyListeners();

    final wsUrl = AppConstants.baseUrl.replaceFirst('http', 'ws');
    _systemLogsChannel = WebSocketChannel.connect(
      Uri.parse('$wsUrl/system/service/logs'),
    );

    _systemLogsChannel!.stream.listen((message) {
      _systemLogs += '$message\n';
      if (_systemLogs.length > 20000) {
        _systemLogs = _systemLogs.substring(_systemLogs.length - 15000);
      }
      notifyListeners();
    }, onError: (e) {
      _systemLogs += 'Error connecting to logs: $e\n';
      notifyListeners();
    }, onDone: () {
      _systemLogs += 'Log stream closed.\n';
      notifyListeners();
    });
  }

  void _connectToChat(String name) {
    _chatChannel?.sink.close();
    final wsUrl = AppConstants.baseUrl.replaceFirst('http', 'ws');
    _chatChannel = WebSocketChannel.connect(
      Uri.parse('$wsUrl/servers/$name/chat'),
    );

    _chatChannel!.stream.listen((message) {
      try {
        final data = jsonDecode(message);
        if (data['type'] == 'chat') {
          _chatMessages.add({
            'sender': data['sender'],
            'message': data['message'],
            'is_system': data['is_system'] ?? false,
            'time': DateTime.now().toIso8601String(),
          });
          if (_chatMessages.length > 200) _chatMessages.removeAt(0);
          notifyListeners();
        }
      } catch (e) {
        debugPrint('Chat WS Decode Error: $e');
      }
    }, onError: (e) {
      debugPrint('Chat WS Error: $e');
    });
  }

  void sendChatMessage(String name, String message, String username) {
    if (_chatChannel == null) return;
    _chatChannel!.sink.add(jsonEncode({
      'type': 'send_chat',
      'username': username,
      'message': message,
    }));
  }
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
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _installedVersions = await _versionService.getInstalledVersions();
    } catch (e) {
      _error = 'Failed to load installed versions';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> loadRemoteVersions(String loaderType) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _remoteVersions = await _versionService.getRemoteVersions(loaderType);
    } catch (e) {
      _error = 'Failed to load remote versions';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> downloadVersion({
    required String loaderType,
    required String mcVersion,
    String loaderVersionId = 'latest',
  }) async {
    _isLoading = true;
    notifyListeners();
    try {
      await _versionService.downloadVersion(
        loaderType: loaderType,
        mcVersion: mcVersion,
        loaderVersionId: loaderVersionId,
      );
      // Wait a bit to ensure the backend registers it as downloading
      await Future.delayed(const Duration(seconds: 1));
      await loadInstalledVersions();
    } catch (e) {
      _error = 'Failed to download version: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}

