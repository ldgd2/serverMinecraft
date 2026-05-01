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
    final res = await _client.put('/servers/$name', data: data);
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
}
