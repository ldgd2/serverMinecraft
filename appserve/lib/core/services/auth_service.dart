import 'package:dio/dio.dart';
import '../api/api_client.dart';
import '../models/user_model.dart';

class AuthService {
  final _client = ApiClient.instance;

  Future<AuthResponse> login(String username, String password) async {
    // Backend uses OAuth2 form encoding
    final res = await _client.dio.post(
      '/auth/login',
      data: {'username': username, 'password': password},
      options: Options(contentType: 'application/x-www-form-urlencoded'),
    );
    final auth = AuthResponse.fromJson(res.data);
    await _client.saveToken(auth.accessToken);
    return auth;
  }

  Future<void> logout() async {
    await _client.clearToken();
  }

  Future<UserModel?> getMe() async {
    try {
      final res = await _client.get('/auth/me');
      return UserModel.fromJson(res.data);
    } catch (_) {
      return null;
    }
  }

  Future<bool> isLoggedIn() async {
    final token = await _client.getToken();
    return token != null;
  }
}
