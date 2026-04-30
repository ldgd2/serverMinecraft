import '../api/api_client.dart';
import '../models/server_model.dart';

class ServerService {
  final _client = ApiClient.instance;

  Future<List<ServerModel>> getServers() async {
    final res = await _client.get('/servers/');
    return (res.data as List).map((e) => ServerModel.fromJson(e)).toList();
  }

  Future<ServerModel> getServer(int id) async {
    final res = await _client.get('/servers/$id');
    return ServerModel.fromJson(res.data);
  }

  Future<ServerModel> createServer(Map<String, dynamic> data) async {
    final res = await _client.post('/servers/', data: data);
    return ServerModel.fromJson(res.data);
  }

  Future<ServerModel> updateServer(int id, Map<String, dynamic> data) async {
    final res = await _client.put('/servers/$id', data: data);
    return ServerModel.fromJson(res.data);
  }

  Future<void> deleteServer(int id) async {
    await _client.delete('/servers/$id');
  }

  Future<void> startServer(int id) async {
    await _client.post('/servers/$id/start');
  }

  Future<void> stopServer(int id) async {
    await _client.post('/servers/$id/stop');
  }

  Future<void> restartServer(int id) async {
    await _client.post('/servers/$id/restart');
  }

  Future<String> sendCommand(int id, String command) async {
    final res = await _client.post('/servers/$id/command', data: {'command': command});
    return res.data['output'] ?? '';
  }

  Future<String> getLogs(int id) async {
    final res = await _client.get('/servers/$id/logs');
    return res.data['logs'] ?? '';
  }

  Future<Map<String, dynamic>> getSystemStats() async {
    final res = await _client.get('/system/stats');
    return Map<String, dynamic>.from(res.data);
  }
}
