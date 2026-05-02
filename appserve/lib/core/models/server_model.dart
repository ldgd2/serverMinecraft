class ServerModel {
  final int id;
  final String name;
  final String version;
  final int port;
  final int ramMb;
  final String status;
  final String? motd;
  final int maxPlayers;
  final bool onlineMode;
  final double cpuCores;
  final int diskMb;
  final double cpuUsage;
  final int ramUsage;
  final int diskUsage;
  final int currentPlayers;
  final DateTime? createdAt;

  const ServerModel({
    required this.id,
    required this.name,
    required this.version,
    required this.port,
    required this.ramMb,
    required this.status,
    this.motd,
    required this.maxPlayers,
    required this.onlineMode,
    this.cpuCores = 1.0,
    this.diskMb = 2048,
    this.cpuUsage = 0.0,
    this.ramUsage = 0,
    this.diskUsage = 0,
    this.currentPlayers = 0,
    this.createdAt,
  });

  factory ServerModel.fromJson(Map<String, dynamic> json) => ServerModel(
        id: json['id'] ?? 0,
        name: json['name'] ?? 'Unknown',
        version: json['version'] ?? '?',
        port: json['port'] ?? 25565,
        ramMb: json['ram_mb'] ?? 1024,
        status: json['status'] ?? 'OFFLINE',
        motd: json['motd'],
        maxPlayers: json['max_players'] ?? 20,
        onlineMode: json['online_mode'] ?? false,
        cpuCores: (json['cpu_cores'] ?? 1.0).toDouble(),
        diskMb: json['disk_mb'] ?? 2048,
        cpuUsage: (json['cpu_usage'] ?? 0.0).toDouble(),
        ramUsage: json['ram_usage'] ?? 0,
        diskUsage: json['disk_usage'] ?? 0,
        currentPlayers: json['current_players'] ?? 0,
        createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at']) : null,
      );

  Map<String, dynamic> toJson() => {
        'name': name,
        'version': version,
        'port': port,
        'ram_mb': ramMb,
        'status': status,
        'motd': motd,
        'max_players': maxPlayers,
        'online_mode': onlineMode,
      };

  bool get isOnline => status == 'ONLINE';
  bool get isStarting => status == 'STARTING';
  bool get isOffline => status == 'OFFLINE';
  bool get isCreating => status == 'CREATING';
  bool get isRestarting => status == 'RESTARTING';
  bool get isStopping => status == 'STOPPING';
  bool get isLoading => status == 'LOADING';
  bool get isPreparing => status == 'PREPARING';
  bool get isError => status.toUpperCase().contains('ERROR');

  double get ramProgress => ramMb > 0 ? (ramUsage / ramMb).clamp(0.0, 1.0) : 0.0;
  double get diskProgress => diskMb > 0 ? (diskUsage / diskMb).clamp(0.0, 1.0) : 0.0;
  double get cpuProgress => (cpuUsage / 100.0).clamp(0.0, 1.0);

  String get ramFormatted => ramMb >= 1024 ? '${(ramMb / 1024).toStringAsFixed(1)} GB' : '$ramMb MB';
  String get ramUsageFormatted => ramUsage >= 1024 ? '${(ramUsage / 1024).toStringAsFixed(1)} GB' : '$ramUsage MB';
  String get diskFormatted => diskMb >= 1024 ? '${(diskMb / 1024).toStringAsFixed(1)} GB' : '$diskMb MB';
  String get diskUsageFormatted => diskUsage >= 1024 ? '${(diskUsage / 1024).toStringAsFixed(1)} GB' : '$diskUsage MB';

  ServerModel copyWith({
    int? id,
    String? name,
    String? version,
    int? port,
    int? ramMb,
    String? status,
    String? motd,
    int? maxPlayers,
    bool? onlineMode,
    double? cpuCores,
    int? diskMb,
    double? cpuUsage,
    int? ramUsage,
    int? diskUsage,
    int? currentPlayers,
    DateTime? createdAt,
  }) {
    return ServerModel(
      id: id ?? this.id,
      name: name ?? this.name,
      version: version ?? this.version,
      port: port ?? this.port,
      ramMb: ramMb ?? this.ramMb,
      status: status ?? this.status,
      motd: motd ?? this.motd,
      maxPlayers: maxPlayers ?? this.maxPlayers,
      onlineMode: onlineMode ?? this.onlineMode,
      cpuCores: cpuCores ?? this.cpuCores,
      diskMb: diskMb ?? this.diskMb,
      cpuUsage: cpuUsage ?? this.cpuUsage,
      ramUsage: ramUsage ?? this.ramUsage,
      diskUsage: diskUsage ?? this.diskUsage,
      currentPlayers: currentPlayers ?? this.currentPlayers,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}
