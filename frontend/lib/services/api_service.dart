import 'dart:convert';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'auth_store.dart';

/// Thrown when the backend rejects the token (401). Lets the UI bounce to login.
class UnauthorizedException implements Exception {
  final String message;
  UnauthorizedException(this.message);
  @override
  String toString() => message;
}

class ApiService {
  static String get baseUrl {
    const envUrl = String.fromEnvironment('API_BASE_URL', defaultValue: '');
    if (envUrl.isNotEmpty) return envUrl;

    if (kIsWeb) return 'http://localhost:8000';
    return 'http://10.0.2.2:8000';
  }

  /// JSON headers with the bearer token attached when we have one.
  static Future<Map<String, String>> _headers() async {
    final token = await AuthStore.getToken();
    return {
      'Content-Type': 'application/json',
      if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
    };
  }

  // ───────────────────────── Auth ─────────────────────────

  /// Creates a new account. Throws on failure (e.g. email already registered).
  static Future<void> register({
    required String email,
    required String password,
  }) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/auth/register'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'email': email, 'password': password}),
        )
        .timeout(const Duration(seconds: 30));

    if (response.statusCode == 200) return;
    throw Exception('Register failed: ${response.body}');
  }

  /// Logs in, stores the returned token, and returns it.
  static Future<String> login({
    required String email,
    required String password,
  }) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/auth/login'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'email': email, 'password': password}),
        )
        .timeout(const Duration(seconds: 30));

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final token = data['access_token'] as String;
      await AuthStore.setToken(token);
      return token;
    }
    throw Exception('Login failed: ${response.body}');
  }

  static Future<void> logout() async {
    await AuthStore.clear();
  }

  // ───────────────────────── Agent ─────────────────────────

  static Future<Map<String, dynamic>> runAgent({
    required String message,
    required bool useWebSearch,
    required bool useCode,
    required bool useRag,
    int? conversationId,
  }) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/agents/run'),
          headers: await _headers(),
          body: jsonEncode({
            'message': message,
            'conversation_id': conversationId,
            'persist': true,
            'use_web_search': useWebSearch,
            'use_code': useCode,
            'use_rag': useRag,
          }),
        )
        .timeout(const Duration(seconds: 120));

    if (response.statusCode == 200) return jsonDecode(response.body);
    if (response.statusCode == 401) {
      throw UnauthorizedException('Session expired. Please log in again.');
    }
    throw Exception('Agent failed: ${response.body}');
  }

  // ───────────────────────── Chat ─────────────────────────

  static Future<Map<String, dynamic>> chat({
    required String message,
    int? conversationId,
  }) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/chat/'),
          headers: await _headers(),
          body: jsonEncode({
            'message': message,
            'conversation_id': conversationId,
            'persist': true,
          }),
        )
        .timeout(const Duration(seconds: 120));

    if (response.statusCode == 200) return jsonDecode(response.body);
    if (response.statusCode == 401) {
      throw UnauthorizedException('Session expired. Please log in again.');
    }
    throw Exception('Chat failed: ${response.body}');
  }

  // ───────────────────────── RAG ─────────────────────────

  static Future<Map<String, dynamic>> ingest({
    required String text,
    required String source,
  }) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/rag/ingest'),
          headers: await _headers(),
          body: jsonEncode({
            'text': text,
            'source': source,
          }),
        )
        .timeout(const Duration(seconds: 60));

    if (response.statusCode == 200) return jsonDecode(response.body);
    if (response.statusCode == 401) {
      throw UnauthorizedException('Session expired. Please log in again.');
    }
    throw Exception('Ingest failed: ${response.body}');
  }

  static Future<List<String>> listDocuments() async {
    final response = await http
        .get(
          Uri.parse('$baseUrl/rag/documents'),
          headers: await _headers(),
        )
        .timeout(const Duration(seconds: 30));

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final docs = data['documents'] as List<dynamic>;
      return docs
          .map((d) => (d as Map<String, dynamic>)['filename'] as String)
          .toList();
    }
    if (response.statusCode == 401) {
      throw UnauthorizedException('Session expired. Please log in again.');
    }
    throw Exception('Failed to load documents: ${response.body}');
  }

  static Future<Map<String, dynamic>> uploadDocument({
    required PlatformFile file,
  }) async {
    if (file.bytes == null) {
      throw Exception('Selected file has no readable bytes');
    }

    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/rag/upload'),
    );

    final token = await AuthStore.getToken();
    if (token != null && token.isNotEmpty) {
      request.headers['Authorization'] = 'Bearer $token';
    }

    request.files.add(
      http.MultipartFile.fromBytes(
        'file',
        file.bytes!,
        filename: file.name,
      ),
    );

    final streamed = await request.send();
    final body = await streamed.stream.bytesToString();

    if (streamed.statusCode == 200) {
      return jsonDecode(body);
    }
    if (streamed.statusCode == 401) {
      throw UnauthorizedException('Session expired. Please log in again.');
    }

    throw Exception('Upload failed: $body');
  }
}
