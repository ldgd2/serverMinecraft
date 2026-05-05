import 'dart:io';
import 'package:dio/dio.dart' as dio;
import '../api/api_client.dart';
import '../models/server_model.dart';

class ServerService {
  final _client = ApiClient.instance;

  Future<List<ServerModel>> getServers() async {
    final res = await _client.get('/servers/');
    return (res.data['data'] as List).map((e) => ServerModel.fromJson(e)).toList();
  }

  Future<ServerModel> getServer(String name) async {
    final res = await _client.get('/servers/$name');
    return ServerModel.fromJson(res.data['data']);
  }

  Future<ServerModel> createServer(Map<String, dynamic> data) async {
    final res = await _client.post('/servers/', data: data);
    return ServerModel.fromJson(res.data['data']);
  }

  Future<ServerModel> updateServer(String name, Map<String, dynamic> data) async {
    final res = await _client.patch('/servers/$name', data: data);
    return ServerModel.fromJson(res.data['data']);
  }

  Future<void> deleteServer(String name) async {
    await _client.delete('/servers/$name');
  }

  Future<void> startServer(String name) async {
    await _client.post('/servers/$name/control/start');
  }

  Future<void> stopServer(String name) async {
    await _client.post('/servers/$name/control/stop');
  }

  Future<void> restartServer(String name) async {
    await _client.post('/servers/$name/control/restart');
  }

  Future<String> sendCommand(String name, String command) async {
    final res = await _client.post('/servers/$name/command', data: {'command': command});
    final data = res.data['data'];
    return data != null ? (data['output'] ?? '') : '';
  }

  Future<String> getLogs(String name) async {
    final res = await _client.get('/servers/$name/logs');
    final data = res.data['data'];
    return data != null ? (data['logs'] ?? '') : '';
  }

  Future<Map<String, dynamic>> getPlayers(String name) async {
    final res = await _client.get('/servers/$name/players');
    return Map<String, dynamic>.from(res.data['data'] ?? {});
  }

  Future<void> kickPlayer(String serverName, String username, {String reason = "Kicked by admin"}) async {
    await _client.post('/servers/$serverName/players/$username/kick', data: {'reason': reason});
  }

  Future<void> banPlayer(String serverName, String username, {
    String reason = "Banned by admin",
    String mode = "username",
    String? expires
  }) async {
    await _client.post('/servers/$serverName/players/$username/ban', data: {
      'reason': reason,
      'mode': mode,
      'expires': expires ?? 'forever'
    });
  }

  Future<void> unbanPlayer(String serverName, String username) async {
    await _client.post('/servers/$serverName/players/$username/unban');
  }

  Future<void> teleport(String name, Map<String, dynamic> data) async {
    await _client.post('/servers/$name/teleport', data: data);
  }

  Future<Map<String, dynamic>> getSystemStats() async {
    try {
      final res = await _client.get('/system/stats');
      return Map<String, dynamic>.from(res.data['data']);
    } catch (_) {
      return {};
    }
  }

  Future<Map<String, dynamic>> getActiveCreations() async {
    try {
      final res = await _client.get('/servers/creations/active');
      return Map<String, dynamic>.from(res.data['data']);
    } catch (_) {
      return {};
    }
  }

  Future<void> restartDashboardService() async {
    await _client.post('/system/service/restart');
  }

  // --- Mod Management ---
  
  Future<List<dynamic>> getMods(String serverName) async {
    final res = await _client.get('/servers/$serverName/mods/');
    return res.data['data'] as List;
  }

  Future<void> deleteMod(String serverName, String filename) async {
    await _client.delete('/servers/$serverName/mods/$filename');
  }

  Future<void> renameMod(String serverName, String oldName, String newName) async {
    await _client.put('/servers/$serverName/mods/rename', data: {
      'old_name': oldName,
      'new_name': newName
    });
  }

  Future<void> uploadMod(String serverName, String filePath) async {
    final fileName = filePath.split(Platform.pathSeparator).last;
    final formData = dio.FormData.fromMap({
      'file': await dio.MultipartFile.fromFile(filePath, filename: fileName),
    });

    await _client.post(
      '/servers/$serverName/mods/upload',
      data: formData,
    );
  }

  Future<List<Map<String, dynamic>>> getChatHistory(String name) async {
    final res = await _client.get('/servers/$name/chat');
    return List<Map<String, dynamic>>.from(res.data['data'] ?? []);
  }
}
