import 'dart:convert';
import 'package:flutter/material.dart';
import '../services/player_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Manages player account state — separate from AdminProvider
class PlayerProvider extends ChangeNotifier {
  final _service = PlayerService();

  // ── State ─────────────────────────────────────────────────────────────────

  Map<String, dynamic>? _profile;
  List<Map<String, dynamic>> _leaderboard = [];
  bool _isLoading = false;
  String? _error;
  String? _playerToken; 

  // ── Getters ───────────────────────────────────────────────────────────────

  Map<String, dynamic>? get profile => _profile;
  List<Map<String, dynamic>> get leaderboard => _leaderboard;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isLoggedIn => _playerToken != null;
  String? get playerToken => _playerToken;

  Map<String, dynamic> get stats => _profile?['stats'] ?? {};
  List<dynamic> get achievements => _profile?['achievements'] ?? [];
  List<dynamic> get highlights => _profile?['highlights'] ?? [];
  String get username => _profile?['username'] ?? '';
  String get accountType => _profile?['account_type'] ?? 'unknown';

  // ── Auth ──────────────────────────────────────────────────────────────────

  Future<bool> login(String username, String password) async {
    _setLoading(true);
    _error = null;
    try {
      final data = await _service.login(username, password);
      _playerToken = data['access_token'];
      await _savePlayerToken(_playerToken!);
      await _loadProfile(force: true); // Login always forces a fresh profile
      return true;
    } catch (e) {
      _error = _parseError(e);
      notifyListeners();
      return false;
    } finally {
      _setLoading(false);
    }
  }

  Future<bool> register(String username, String password) async {
    _setLoading(true);
    _error = null;
    try {
      final data = await _service.register(username, password);
      _playerToken = data['access_token'];
      await _savePlayerToken(_playerToken!);
      await _loadProfile(force: true);
      return true;
    } catch (e) {
      _error = _parseError(e);
      notifyListeners();
      return false;
    } finally {
      _setLoading(false);
    }
  }

  void logout() async {
    _playerToken = null;
    _profile = null;
    await _clearPlayerToken();
    await _clearProfileCache();
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }

  // ── Persistence ───────────────────────────────────────────────────────────

  Future<void> _savePlayerToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('player_token', token);
  }

  Future<void> _clearPlayerToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('player_token');
  }

  Future<void> _saveProfileToCache(Map<String, dynamic> profile) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('player_profile_cache', jsonEncode(profile));
  }

  Future<Map<String, dynamic>?> _loadProfileFromCache() async {
    final prefs = await SharedPreferences.getInstance();
    final data = prefs.getString('player_profile_cache');
    if (data != null) {
      return jsonDecode(data) as Map<String, dynamic>;
    }
    return null;
  }

  Future<void> _clearProfileCache() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('player_profile_cache');
  }

  Future<void> tryAutoLogin() async {
    final prefs = await SharedPreferences.getInstance();
    _playerToken = prefs.getString('player_token');
    if (_playerToken != null) {
      // 1. Load from cache immediately for instant UI
      _profile = await _loadProfileFromCache();
      if (_profile != null) notifyListeners();
      
      // 2. Load from network in background ONLY if cache is empty
      if (_profile == null) {
        await _loadProfile();
      }
    }
  }

  // ── Data Loading ──────────────────────────────────────────────────────────

  Future<void> _loadProfile({bool force = false}) async {
    if (_playerToken == null) return;
    
    // If not forced and we already have a profile, don't hit the network
    if (!force && _profile != null) return;

    try {
      final freshProfile = await _service.getProfile(_playerToken!);
      _profile = freshProfile;
      await _saveProfileToCache(freshProfile);
      notifyListeners();
    } catch (e) {
      debugPrint('PlayerProvider profile error: $e');
    }
  }

  /// Forces a network refresh — should be called from "Refresh" button
  Future<void> refreshProfile() async {
    if (_playerToken == null) return;
    _setLoading(true);
    await _loadProfile(force: true);
    _setLoading(false);
  }

  /// Called when server notifies about a change via WebSocket
  void notifyProfileUpdate() {
    // We don't fetch immediately to avoid spamming, but we can clear local flag 
    // or wait for the user to be on the profile screen.
    // For now, let's just force a refresh in the background
    _loadProfile(force: true);
  }

  Future<void> loadLeaderboard() async {
    _setLoading(true);
    try {
      _leaderboard = await _service.getLeaderboard();
    } catch (e) {
      _error = _parseError(e);
    } finally {
      _setLoading(false);
    }
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  void _setLoading(bool v) {
    _isLoading = v;
    notifyListeners();
  }

  String _parseError(dynamic e) {
    final msg = e.toString();
    if (msg.contains('401')) return 'Credenciales incorrectas';
    if (msg.contains('400')) return 'El usuario ya existe o datos inválidos';
    if (msg.contains('403')) return 'Cuenta baneada o inactiva';
    if (msg.contains('Connection')) return 'No se puede conectar al servidor';
    return 'Error: $msg';
  }
}
