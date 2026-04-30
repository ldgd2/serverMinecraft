class VersionModel {
  final String id;
  final String name;
  final String type; // 'release' | 'snapshot' | 'old_beta'
  final bool isDownloaded;
  final DateTime? releaseTime;

  const VersionModel({
    required this.id,
    required this.name,
    required this.type,
    this.isDownloaded = false,
    this.releaseTime,
  });

  factory VersionModel.fromJson(Map<String, dynamic> json) => VersionModel(
        id: json['id'] ?? json['name'] ?? '',
        name: json['name'] ?? json['id'] ?? '',
        type: json['type'] ?? 'release',
        isDownloaded: json['is_downloaded'] ?? false,
        releaseTime: json['release_time'] != null ? DateTime.tryParse(json['release_time']) : null,
      );

  bool get isRelease => type == 'release';
  bool get isSnapshot => type == 'snapshot';

  String get typeLabel {
    switch (type) {
      case 'release': return 'Release';
      case 'snapshot': return 'Snapshot';
      case 'old_beta': return 'Beta';
      default: return type;
    }
  }
}

class ModLoaderModel {
  final String id;
  final String name;
  final String type; // 'fabric' | 'forge' | 'paper' | 'quilt'
  final String version;
  final String? minecraftVersion;
  final bool isInstalled;
  final bool isStable;

  const ModLoaderModel({
    required this.id,
    required this.name,
    required this.type,
    required this.version,
    this.minecraftVersion,
    this.isInstalled = false,
    this.isStable = true,
  });

  factory ModLoaderModel.fromJson(Map<String, dynamic> json) => ModLoaderModel(
        id: json['id'] ?? '',
        name: json['name'] ?? '',
        type: json['type'] ?? '',
        version: json['version'] ?? '',
        minecraftVersion: json['minecraft_version'],
        isInstalled: json['is_installed'] ?? false,
        isStable: json['stable'] ?? true,
      );
}

class DownloadTask {
  final String id;
  final String name;
  final String type; // 'version' | 'modloader'
  double progress;
  String status; // 'pending' | 'downloading' | 'done' | 'error'
  String? error;

  DownloadTask({
    required this.id,
    required this.name,
    required this.type,
    this.progress = 0,
    this.status = 'pending',
    this.error,
  });
}
