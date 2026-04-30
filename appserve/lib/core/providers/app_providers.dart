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

  List<ServerModel> _servers = [];
  ServerModel? _selectedServer;
  bool _isLoading = false;
  String? _error;
  String _consoleLogs = '';
  Map<String, dynamic> _systemStats = {};

  List<ServerModel> get servers => _servers;
  ServerModel? get selectedServer => _selectedServer;
  bool get isLoading => _isLoading;
  String? get error => _error;
  String get consoleLogs => _consoleLogs;
  Map<String, dynamic> get systemStats => _systemStats;

  int get onlineCount => _servers.where((s) => s.isOnline).length;
  int get offlineCount => _servers.where((s) => s.isOffline).length;

  Future<void> loadServers() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _servers = await _serverService.getServers();
    } catch (e) {
      _error = 'Failed to load servers';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> selectServer(int id) async {
    _isLoading = true;
    notifyListeners();
    
    final server = await _serverService.getServer(id);
    _selectedServer = server;
    _consoleLogs = ''; // Clear previous server logs
    
    // Load initial history
    try {
      _consoleLogs = await _serverService.getLogs(id);
    } catch (_) {}
    
    _closeWebSockets();
    _connectToConsole(server.name);
    _connectToStatus(server.name);
    
    _isLoading = false;
    notifyListeners();
  }

  void _closeWebSockets() {
    _consoleChannel?.sink.close();
    _statusChannel?.sink.close();
    _consoleChannel = null;
    _statusChannel = null;
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
      // Background status updates could be handled here
    }, onError: (e) {
      debugPrint('Status WS Error: $e');
    });
  }

  @override
  void dispose() {
    _closeWebSockets();
    super.dispose();
  }

  Future<void> startServer(int id) async {
    await _serverService.startServer(id);
    await loadServers();
  }

  Future<void> stopServer(int id) async {
    await _serverService.stopServer(id);
    await loadServers();
  }

  Future<void> restartServer(int id) async {
    await _serverService.restartServer(id);
    await loadServers();
  }

  Future<void> sendCommand(int id, String cmd) async {
    // Send command via API, output will stream back through WebSocket
    await _serverService.sendCommand(id, cmd);
    _consoleLogs += '\n> $cmd';
    notifyListeners();
  }

  Future<void> loadLogs(int id) async {
    _consoleLogs = await _serverService.getLogs(id);
    notifyListeners();
  }

  Future<void> loadSystemStats() async {
    try {
      _systemStats = await _serverService.getSystemStats();
      notifyListeners();
    } catch (_) {}
  }

  Future<ServerModel> createServer(Map<String, dynamic> data) async {
    final server = await _serverService.createServer(data);
    _servers.add(server);
    notifyListeners();
    return server;
  }

  Future<void> deleteServer(int id) async {
    await _serverService.deleteServer(id);
    _servers.removeWhere((s) => s.id == id);
    notifyListeners();
  }

  void clearConsole() {
    _consoleLogs = '';
    notifyListeners();
  }
}

class VersionProvider extends ChangeNotifier {
  final _versionService = VersionService();

  List<VersionModel> _versions = [];
  List<VersionModel> _downloadedVersions = [];
  List<ModLoaderModel> _modLoaders = [];
  bool _isLoading = false;
  String? _error;

  List<VersionModel> get versions => _versions;
  List<VersionModel> get downloadedVersions => _downloadedVersions;
  List<ModLoaderModel> get modLoaders => _modLoaders;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> loadVersions({String? type}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _versions = await _versionService.getVersions(type: type);
      _downloadedVersions = await _versionService.getDownloadedVersions();
    } catch (e) {
      _error = 'Failed to load versions';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> downloadVersion(String versionId) async {
    try {
      await _versionService.downloadVersion(versionId);
      await loadVersions();
    } catch (e) {
      _error = 'Failed to download version';
      notifyListeners();
    }
  }

  Future<void> loadModLoaders(String type, {String? mcVersion}) async {
    _isLoading = true;
    notifyListeners();
    try {
      _modLoaders = await _versionService.getModLoaders(type, minecraftVersion: mcVersion);
    } catch (e) {
      _error = 'Failed to load mod loaders';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> installModLoader({
    required String type,
    required String loaderVersion,
    required String minecraftVersion,
  }) async {
    _isLoading = true;
    notifyListeners();
    try {
      await _versionService.installModLoader(
        type: type,
        loaderVersion: loaderVersion,
        minecraftVersion: minecraftVersion,
      );
    } catch (e) {
      _error = 'Failed to install mod loader';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}

