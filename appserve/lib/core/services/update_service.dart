import 'package:dio/dio.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import '../api/api_client.dart';

class UpdateInfo {
  final bool hasUpdate;
  final String currentVersion;
  final String latestVersion;
  final String? downloadUrl;

  const UpdateInfo({
    required this.hasUpdate,
    required this.currentVersion,
    required this.latestVersion,
    this.downloadUrl,
  });

  factory UpdateInfo.noUpdate(String current) => UpdateInfo(
        hasUpdate: false,
        currentVersion: current,
        latestVersion: current,
      );
}

class UpdateService {
  static UpdateService? _instance;
  static UpdateService get instance => _instance ??= UpdateService._();
  UpdateService._();

  final _client = ApiClient.instance;
  String? _cachedVersion;

  /// Devuelve la versión instalada de la app.
  Future<String> getCurrentVersion() async {
    if (_cachedVersion != null) return _cachedVersion!;
    try {
      final info = await PackageInfo.fromPlatform();
      _cachedVersion = info.version;
      return _cachedVersion!;
    } catch (_) {
      return '1.0.0';
    }
  }

  /// Consulta el backend y retorna info de actualización.
  Future<UpdateInfo> checkForUpdate() async {
    final current = await getCurrentVersion();
    try {
      final response = await _client.get(
        '/updates/check/app',
        params: {'current_version': current},
      );

      final body = response.data;
      final data = body?['data'] as Map<String, dynamic>?;
      if (data == null) return UpdateInfo.noUpdate(current);

      return UpdateInfo(
        hasUpdate: data['has_update'] == true,
        currentVersion: current,
        latestVersion: data['latest_version']?.toString() ?? current,
        downloadUrl: data['download_url']?.toString(),
      );
    } on DioException catch (_) {
      return UpdateInfo.noUpdate(current);
    } catch (_) {
      return UpdateInfo.noUpdate(current);
    }
  }

  /// Abre la URL de descarga en el navegador del dispositivo.
  Future<bool> openDownloadUrl(String url) async {
    final uri = Uri.tryParse(url);
    if (uri == null) return false;
    return launchUrl(uri, mode: LaunchMode.externalApplication);
  }
}
