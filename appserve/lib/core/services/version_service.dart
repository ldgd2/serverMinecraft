import '../api/api_client.dart';
import '../models/version_model.dart';

class VersionService {
  final _client = ApiClient.instance;

  /// List installed/downloaded versions
  Future<List<VersionModel>> getInstalledVersions({bool grouped = false}) async {
    final res = await _client.get('/versions/', params: {'grouped': grouped});
    if (grouped) {
      // Not typically used this way in VersionProvider directly, but supported
      return [];
    }
    return (res.data['data'] as List).map((e) => VersionModel.fromJson(e)).toList();
  }

  /// Get remote versions for a specific loader (vanilla, paper, forge, fabric)
  Future<List<String>> getRemoteVersions(String loaderType) async {
    final res = await _client.get('/versions/remote/$loaderType');
    final data = res.data['data'] as Map<String, dynamic>;
    if (data.containsKey('versions')) {
      return List<String>.from(data['versions']);
    }
    return [];
  }

  /// Trigger download of a version
  Future<String> downloadVersion({
    required String loaderType,
    required String mcVersion,
    String loaderVersionId = 'latest',
  }) async {
    final res = await _client.post('/versions/download', data: {
      'loader_type': loaderType,
      'mc_version': mcVersion,
      'loader_version_id': loaderVersionId,
    });
    return res.data['data']['task_id'] as String;
  }
}
