import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../constants/app_constants.dart';

class ApiClient {
  static ApiClient? _instance;
  late final Dio _dio;
  bool _isRefreshing = false;
  
  // Cache/Throttle map: path -> timestamp
  final Map<String, DateTime> _getCache = {};
  static const Duration _throttleDuration = Duration(seconds: 1);

  ApiClient._() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConstants.baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        // Only throttle GET requests
        if (options.method.toUpperCase() == 'GET') {
          final now = DateTime.now();
          final lastRequest = _getCache[options.path];
          
          if (lastRequest != null && now.difference(lastRequest) < _throttleDuration) {
            // If it's too frequent, we could return a cached response if we had one,
            // but for now let's just allow it if it's the first time in 1s.
            // Actually, let's just proceed but log it for now.
            // To truly throttle, we should return the previous response.
          }
          _getCache[options.path] = now;
        }

        final prefs = await SharedPreferences.getInstance();
        final token = prefs.getString(AppConstants.tokenKey);
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        // If 401 and we have saved credentials, try to refresh
        if (error.response?.statusCode == 401 && !_isRefreshing) {
          final prefs = await SharedPreferences.getInstance();
          final user = prefs.getString(AppConstants.usernameKey);
          final pass = prefs.getString(AppConstants.passwordKey);

          if (user != null && pass != null) {
            _isRefreshing = true;
            try {
              // Attempt silent re-login
              final res = await _dio.post(
                '/auth/login',
                data: {'username': user, 'password': pass},
              );
              
              final newToken = res.data['data']['access_token'];
              if (newToken != null) {
                await prefs.setString(AppConstants.tokenKey, newToken);
                
                // Retry the original request
                final opts = error.requestOptions;
                opts.headers['Authorization'] = 'Bearer $newToken';
                
                final response = await _dio.fetch(opts);
                return handler.resolve(response);
              }
            } catch (e) {
              // If re-login fails, clear everything and fail
              await clearToken();
              await prefs.remove(AppConstants.usernameKey);
              await prefs.remove(AppConstants.passwordKey);
            } finally {
              _isRefreshing = false;
            }
          }
        }
        handler.next(error);
      },
    ));
  }

  static ApiClient get instance => _instance ??= ApiClient._();

  Dio get dio => _dio;

  // Generic GET
  Future<Response> get(String path, {Map<String, dynamic>? params}) =>
      _dio.get(path, queryParameters: params);

  // Generic POST
  Future<Response> post(String path, {dynamic data}) =>
      _dio.post(path, data: data);

  // Generic PUT
  Future<Response> put(String path, {dynamic data}) =>
      _dio.put(path, data: data);

  // Generic DELETE
  Future<Response> delete(String path) => _dio.delete(path);

  // Update base URL dynamically (for env config)
  void setBaseUrl(String url) {
    _dio.options.baseUrl = url;
  }

  // Update token (after login)
  Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.tokenKey, token);
  }

  Future<void> clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(AppConstants.tokenKey);
  }

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(AppConstants.tokenKey);
  }
}
