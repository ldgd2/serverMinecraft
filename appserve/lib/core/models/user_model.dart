class UserModel {
  final int id;
  final String username;
  final bool isAdmin;
  final bool isActive;

  const UserModel({
    required this.id,
    required this.username,
    required this.isAdmin,
    required this.isActive,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) => UserModel(
        id: json['id'] ?? 0,
        username: json['username'] ?? 'Unknown',
        isAdmin: json['is_admin'] ?? false,
        isActive: json['is_active'] ?? true,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'username': username,
        'is_admin': isAdmin,
        'is_active': isActive,
      };
}

class AuthResponse {
  final String accessToken;
  final String tokenType;
  final UserModel user;

  const AuthResponse({
    required this.accessToken,
    required this.tokenType,
    required this.user,
  });

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    final userMap = json['user'];
    return AuthResponse(
      accessToken: json['access_token'] ?? '',
      tokenType: json['token_type'] ?? 'bearer',
      user: UserModel.fromJson(userMap is Map<String, dynamic> ? userMap : <String, dynamic>{}),
    );
  }
}
