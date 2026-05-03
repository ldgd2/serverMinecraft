import 'package:shared_preferences/shared_preferences.dart';
import '../api/api_client.dart';
import '../models/user_model.dart';
import '../constants/app_constants.dart';

class AuthService {
  final _client = ApiClient.instance;

  Future<AuthResponse> login(String username, String password) async {
    // Backend uses OAuth2 form encoding or JSON (AuthController handles both)
    final res = await _client.dio.post(
      '/auth/login',
      data: {'username': username, 'password': password},
    );
    final auth = AuthResponse.fromJson(res.data['data']);
    
    // Save token
    await _client.saveToken(auth.accessToken);
    
    // Save credentials for auto-refresh
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.usernameKey, username);
    await prefs.setString(AppConstants.passwordKey, password);
    
    return auth;
  }

  Future<void> logout() async {
    await _client.clearToken();
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(AppConstants.usernameKey);
    await prefs.remove(AppConstants.passwordKey);
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
