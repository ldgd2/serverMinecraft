import 'package:flutter/material.dart';
import '../services/backup_service.dart';

class BackupProvider extends ChangeNotifier {
  final BackupService _backupService = BackupService();
  
  List<Map<String, dynamic>> _backups = [];
  bool _isLoading = false;
  String? _error;

  List<Map<String, dynamic>> get backups => _backups;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchBackups() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _backups = await _backupService.getBackups();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> createBackup() async {
    _isLoading = true;
    notifyListeners();
    try {
      await _backupService.createBackup();
      await fetchBackups();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> restoreBackup(String filename) async {
    _isLoading = true;
    notifyListeners();
    try {
      await _backupService.restoreBackup(filename);
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> deleteBackup(String filename) async {
    try {
      await _backupService.deleteBackup(filename);
      _backups.removeWhere((b) => b['filename'] == filename);
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  Future<String> downloadBackup(String filename) async {
    try {
      return await _backupService.downloadBackup(filename);
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }
}
