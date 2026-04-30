import 'package:flutter/material.dart';
import '../models/user_model.dart';
import '../models/server_model.dart';
import '../services/auth_service.dart';
import '../services/server_service.dart';

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
    _selectedServer = await _serverService.getServer(id);
    notifyListeners();
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
    final output = await _serverService.sendCommand(id, cmd);
    _consoleLogs += '\n> $cmd\n$output';
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
