import 'dart:convert';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class ApiService {
  static String get baseUrl {
    const envUrl = String.fromEnvironment('API_BASE_URL', defaultValue: '');
    if (envUrl.isNotEmpty) return envUrl;

    if (kIsWeb) return 'http://localhost:8000';
    return 'http://10.0.2.2:8000';
  }

  static Future<Map<String, dynamic>> runAgent({
    required String message,
    required bool useWebSearch,
    required bool useCode,
    required bool useRag,
    String? sessionId,
  }) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/agents/run'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'message': message,
            'session_id': sessionId,
            'persist': true,
            'use_web_search': useWebSearch,
            'use_code': useCode,
            'use_rag': useRag,
          }),
        )
        .timeout(const Duration(seconds: 120));

    if (response.statusCode == 200) return jsonDecode(response.body);
    throw Exception('Agent failed: ${response.body}');
  }

  static Future<Map<String, dynamic>> ingest({
    required String text,
    required String source,
    required String docId,
  }) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/rag/ingest'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'text': text,
            'source': source,
            'doc_id': docId,
          }),
        )
        .timeout(const Duration(seconds: 60));

    if (response.statusCode == 200) return jsonDecode(response.body);
    throw Exception('Ingest failed: ${response.body}');
  }

  static Future<Map<String, dynamic>> chat({
    required String message,
    String? sessionId,
  }) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/chat'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'message': message,
            'session_id': sessionId,
            'persist': true,
          }),
        )
        .timeout(const Duration(seconds: 120));

    if (response.statusCode == 200) return jsonDecode(response.body);
    throw Exception('Chat failed: ${response.body}');
  }

  static Future<List<String>> listDocuments() async {
    final response = await http
        .get(Uri.parse('$baseUrl/rag/documents'))
        .timeout(const Duration(seconds: 30));

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final docs = data['documents'] as List<dynamic>;
      return docs.map((d) => (d as Map<String, dynamic>)['filename'] as String).toList();
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

    throw Exception('Upload failed: $body');
  }
}
