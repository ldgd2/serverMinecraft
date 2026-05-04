import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';
import 'dart:io';
import '../api/api_client.dart';

/// Servicio de caché para cabezas de jugadores Minecraft.
/// 
/// Lógica:
/// - Descarga la cabeza desde el backend (/api/v1/players/skin/{username}/head)
/// - Cachea el archivo PNG localmente con la clave `{username}_{skin_hash}.png`
/// - Al pedir la cabeza, primero verifica si la skin_hash cambió vs la caché
/// - Si cambió → descarga nueva cabeza, elimina la vieja
/// - Si no cambió → devuelve el path local sin hacer ninguna petición extra
class PlayerHeadService {
  static final PlayerHeadService _instance = PlayerHeadService._();
  static PlayerHeadService get instance => _instance;
  PlayerHeadService._();

  final _client = ApiClient.instance;
  final Map<String, String> _skinHashCache = {}; // username → last known hash
  Directory? _cacheDir;

  Future<Directory> get _dir async {
    _cacheDir ??= Directory('${(await getApplicationCacheDirectory()).path}/player_heads');
    if (!await _cacheDir!.exists()) await _cacheDir!.create(recursive: true);
    return _cacheDir!;
  }

  /// Retorna el path local de la cabeza del jugador, descargando si es necesario.
  /// Llama a [onUpdated] si la cabeza fue actualizada.
  Future<File?> getHead(String username, {VoidCallback? onUpdated}) async {
    try {
      // 1. Pedir el hash actual de la skin al backend (endpoint ligero)
      final hashRes = await _client.dio.get('/v1/players/skin/$username/hash');
      final newHash = hashRes.data['data']?['hash'] as String? ?? username;

      final dir = await _dir;
      final safeUser = username.toLowerCase().replaceAll(RegExp(r'[^a-z0-9_]'), '');
      final cacheKey = '${safeUser}_$newHash';
      final file = File('${dir.path}/$cacheKey.png');

      // 2. Si ya tenemos el archivo para este hash, devolver directo (sin red)
      if (await file.exists()) {
        _skinHashCache[username] = newHash;
        return file;
      }

      // 3. Hash cambió o primer uso → descargar la nueva cabeza
      final headRes = await _client.dio.get<List<int>>(
        '/v1/players/skin/$username/head',
        options: Options(responseType: ResponseType.bytes),
      );
      await file.writeAsBytes(headRes.data!);

      // 4. Borrar caché vieja del mismo jugador con hash diferente
      final oldHash = _skinHashCache[username];
      if (oldHash != null && oldHash != newHash) {
        final oldFile = File('${dir.path}/${safeUser}_$oldHash.png');
        if (await oldFile.exists()) await oldFile.delete();
      }

      _skinHashCache[username] = newHash;
      onUpdated?.call();
      return file;
    } catch (e) {
      // Fallback: intentar devolver cualquier caché existente del jugador
      try {
        final dir = await _dir;
        final safeUser = username.toLowerCase().replaceAll(RegExp(r'[^a-z0-9_]'), '');
        final files = dir.listSync().whereType<File>().where((f) => f.path.contains(safeUser)).toList();
        if (files.isNotEmpty) return files.first;
      } catch (_) {}
      return null;
    }
  }

  /// Devuelve la URL de la cabeza del backend para usar con CachedNetworkImage.
  String headUrl(String username) {
    final base = _client.dio.options.baseUrl.replaceAll(RegExp(r'/api/v1$'), '');
    return '$base/api/v1/players/skin/$username/head';
  }

  /// Limpia TODO el caché de cabezas (útil en logout).
  Future<void> clearAll() async {
    try {
      final dir = await _dir;
      if (await dir.exists()) await dir.delete(recursive: true);
      _skinHashCache.clear();
    } catch (_) {}
  }
}
