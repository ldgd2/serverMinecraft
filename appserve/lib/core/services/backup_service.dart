import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';
import '../api/api_client.dart';
import 'dart:io';

class BackupService {
  final _client = ApiClient.instance;

  Future<List<Map<String, dynamic>>> getBackups() async {
    try {
      final response = await _client.get('/backups/');
      return List<Map<String, dynamic>>.from(response.data);
    } catch (e) {
      rethrow;
    }
  }

  Future<String> createBackup() async {
    try {
      final response = await _client.post('/backups/create');
      if (response.data['status'] == 'success') {
        return response.data['data']['filename'];
      }
      throw Exception(response.data['message'] ?? 'Error creating backup');
    } catch (e) {
      rethrow;
    }
  }

  Future<void> restoreBackup(String filename) async {
    try {
      await _client.post('/backups/restore/$filename');
    } catch (e) {
      rethrow;
    }
  }

  Future<void> deleteBackup(String filename) async {
    try {
      await _client.delete('/backups/$filename');
    } catch (e) {
      rethrow;
    }
  }

  Future<String> downloadBackup(String filename) async {
    try {
      Directory? directory;
      if (Platform.isAndroid) {
        directory = Directory('/storage/emulated/0/Download');
        if (!await directory.exists()) {
          directory = await getExternalStorageDirectory();
        }
      } else {
        directory = await getApplicationDocumentsDirectory();
      }

      final String savePath = '${directory!.path}/$filename';
      
      // Use the raw dio instance for specialized downloads
      await _client.dio.get(
        '/backups/download/$filename',
        options: Options(responseType: ResponseType.bytes),
      ).then((response) async {
        final File file = File(savePath);
        await file.writeAsBytes(response.data);
      });
      
      return savePath;
    } catch (e) {
      rethrow;
    }
  }
}
