import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/api_service.dart';

class DocumentsDrawer extends StatefulWidget {
  const DocumentsDrawer({super.key});

  @override
  State<DocumentsDrawer> createState() => _DocumentsDrawerState();
}

class _DocumentsDrawerState extends State<DocumentsDrawer> {
  List<String> _documents = [];
  bool _uploading = false;

  @override
  void initState() {
    super.initState();
    _loadDocuments();
  }

  Future<void> _loadDocuments() async {
    try {
      final docs = await ApiService.listDocuments();
      if (mounted) setState(() => _documents = docs);
    } catch (_) {}
  }

  Future<void> _pickAndUpload() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        withData: true,
        allowedExtensions: [
          'txt',
          'md',
          'json',
          'py',
          'java',
          'csv',
          'pdf',
          'docx',
          'xlsx',
        ],
      );

      if (result == null || result.files.isEmpty) return;

      final file = result.files.first;
      if (file.bytes == null) {
        throw Exception('Could not read file bytes');
      }

      setState(() => _uploading = true);

      await ApiService.uploadDocument(file: file);
      await _loadDocuments();

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${file.name} uploaded')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Upload failed: $e')),
      );
    } finally {
      if (mounted) {
        setState(() => _uploading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Drawer(
      backgroundColor: const Color(0xFF0F0F0F),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Documents',
                style: GoogleFonts.dmSans(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: const Color(0xFFD4FF6E),
                ),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _uploading ? null : _pickAndUpload,
                  child: Text(_uploading ? 'Uploading...' : 'Upload document'),
                ),
              ),
              const SizedBox(height: 16),
              Expanded(
                child: _documents.isEmpty
                    ? Text(
                        'No documents uploaded yet.',
                        style: GoogleFonts.dmSans(
                          fontSize: 14,
                          color: const Color(0xFFBBBBBB),
                        ),
                      )
                    : ListView.builder(
                        itemCount: _documents.length,
                        itemBuilder: (context, index) {
                          return ListTile(
                            title: Text(
                              _documents[index],
                              style: GoogleFonts.dmSans(
                                color: Colors.white,
                                fontSize: 14,
                              ),
                            ),
                          );
                        },
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
