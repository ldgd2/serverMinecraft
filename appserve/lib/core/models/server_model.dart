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
    this.createdAt,
  });

  factory ServerModel.fromJson(Map<String, dynamic> json) => ServerModel(
        id: json['id'],
        name: json['name'] ?? 'Unknown',
        version: json['version'] ?? '?',
        port: json['port'] ?? 25565,
        ramMb: json['ram_mb'] ?? 1024,
        status: json['status'] ?? 'OFFLINE',
        motd: json['motd'],
        maxPlayers: json['max_players'] ?? 20,
        onlineMode: json['online_mode'] ?? false,
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

  String get ramFormatted => ramMb >= 1024 ? '${(ramMb / 1024).toStringAsFixed(1)} GB' : '$ramMb MB';
}
