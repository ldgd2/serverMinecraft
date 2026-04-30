import '../api/api_client.dart';
import '../models/version_model.dart';

class VersionService {
  final _client = ApiClient.instance;

  /// List all available Minecraft versions (cached from Mojang manifest)
  Future<List<VersionModel>> getVersions({String? type}) async {
    final params = <String, dynamic>{};
    if (type != null) params['type'] = type;
    final res = await _client.get('/versions/', params: params);
    return (res.data as List).map((e) => VersionModel.fromJson(e)).toList();
  }

  /// List locally downloaded versions
  Future<List<VersionModel>> getDownloadedVersions() async {
    final res = await _client.get('/versions/downloaded');
    return (res.data as List).map((e) => VersionModel.fromJson(e)).toList();
  }

  /// Trigger download of a Minecraft version on the server
  Future<Map<String, dynamic>> downloadVersion(String versionId) async {
    final res = await _client.post('/versions/$versionId/download');
    return Map<String, dynamic>.from(res.data);
  }

  /// Delete a downloaded version
  Future<void> deleteVersion(String versionId) async {
    await _client.delete('/versions/$versionId');
  }

  // ─── MOD LOADERS ──────────────────────────────────────────────────────────

  /// List available mod loaders for a given Minecraft version
  Future<List<ModLoaderModel>> getModLoaders(String type, {String? minecraftVersion}) async {
    final params = <String, dynamic>{'type': type};
    if (minecraftVersion != null) params['mc_version'] = minecraftVersion;
    final res = await _client.get('/mod-loaders/', params: params);
    return (res.data as List).map((e) => ModLoaderModel.fromJson(e)).toList();
  }

  /// Install a mod loader on the server for a specific version
  Future<Map<String, dynamic>> installModLoader({
    required String type,
    required String loaderVersion,
    required String minecraftVersion,
  }) async {
    final res = await _client.post('/mod-loaders/install', data: {
      'type': type,
      'loader_version': loaderVersion,
      'minecraft_version': minecraftVersion,
    });
    return Map<String, dynamic>.from(res.data);
  }

  /// Get currently installed mod loaders
  Future<List<ModLoaderModel>> getInstalledModLoaders() async {
    final res = await _client.get('/mod-loaders/installed');
    return (res.data as List).map((e) => ModLoaderModel.fromJson(e)).toList();
  }

  /// Remove an installed mod loader
  Future<void> removeModLoader(String id) async {
    await _client.delete('/mod-loaders/$id');
  }
}
