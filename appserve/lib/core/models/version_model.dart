class VersionModel {
  final int id;
  final String name;
  final String loaderType;
  final String mcVersion;
  final String loaderVersion;
  final int fileSize;
  final bool isDownloaded;
  final String? localPath;

  const VersionModel({
    required this.id,
    required this.name,
    required this.loaderType,
    required this.mcVersion,
    required this.loaderVersion,
    required this.fileSize,
    this.isDownloaded = false,
    this.localPath,
  });

  factory VersionModel.fromJson(Map<String, dynamic> json) => VersionModel(
        id: json['id'] is int ? json['id'] : int.tryParse(json['id']?.toString() ?? '0') ?? 0,
        name: json['name'] ?? '',
        loaderType: json['loader_type'] ?? 'VANILLA',
        mcVersion: json['mc_version'] ?? '',
        loaderVersion: json['loader_version'] ?? '',
        fileSize: json['file_size'] ?? 0,
        isDownloaded: json['downloaded'] ?? false,
        localPath: json['local_path'],
      );

  String get typeLabel => loaderType.toUpperCase();
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
