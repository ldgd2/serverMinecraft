import 'package:dio/dio.dart';
import '../api/api_client.dart';

class PlayerService {
  final _client = ApiClient.instance;

  Options _bearerOptions(String token) =>
      Options(headers: {'Authorization': 'Bearer $token'});

  /// Register a new no-premium player account
  Future<Map<String, dynamic>> register(String username, String password) async {
    final res = await _client.dio.post(
      '/player-auth/register',
      data: {'username': username, 'password': password},
    );
    return Map<String, dynamic>.from(res.data['data'] ?? {});
  }

  /// Login with username/password
  Future<Map<String, dynamic>> login(String username, String password) async {
    final res = await _client.dio.post(
      '/player-auth/login',
      data: {'username': username, 'password': password},
    );
    return Map<String, dynamic>.from(res.data['data'] ?? {});
  }

  /// Get current player profile (requires player token)
  Future<Map<String, dynamic>> getProfile(String playerToken) async {
    final res = await _client.dio.get(
      '/player-auth/profile',
      options: _bearerOptions(playerToken),
    );
    return Map<String, dynamic>.from(res.data['data'] ?? {});
  }

  /// Get global leaderboard (public)
  Future<List<Map<String, dynamic>>> getLeaderboard() async {
    try {
      final res = await _client.dio.get('/player-auth/leaderboard');
      return (res.data['data'] as List)
          .map((e) => Map<String, dynamic>.from(e))
          .toList();
    } catch (_) {
      return [];
    }
  }
}
