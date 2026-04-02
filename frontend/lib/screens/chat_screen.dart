// lib/screens/chat_screen.dart
// Main chat screen
// Message style B: full width with subtle dividers
// Tool calls shown as cards above each Claude answer
// Tool toggles: Web Search ON, Code OFF, RAG ON by default

import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/message.dart';
import '../services/api_service.dart' as api;
import 'documents_drawer.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _inputController = TextEditingController();
  final _scrollController = ScrollController();
  final _scaffoldKey = GlobalKey<ScaffoldState>();

  final List<Message> _messages = [];
  String? _sessionId;

  bool _useWebSearch = true;
  bool _useCode = false;
  bool _useRag = true;
  bool _loading = false;

  Future<void> _send() async {
    final text = _inputController.text.trim();
    if (text.isEmpty || _loading) return;

    setState(() {
      _messages.add(Message(role: 'user', content: text));
      _loading = true;
    });
    _inputController.clear();
    _scrollToBottom();

    try {
      final data = await api.ApiService.runAgent(
        message: text,
        useWebSearch: _useWebSearch,
        useCode: _useCode,
        useRag: _useRag,
        sessionId: _sessionId,
      );

      _sessionId ??= data['session_id'] as String?;

      final toolCalls = (data['tool_calls_made'] as List? ?? [])
          .map((t) => ToolCall.fromJson(t as Map<String, dynamic>))
          .toList();

      setState(() {
        _messages.add(
          Message(
            role: 'assistant',
            content: data['final_answer'] ?? '',
            toolCalls: toolCalls,
          ),
        );
      });
    } catch (e) {
      setState(() {
        _messages.add(Message(role: 'error', content: e.toString()));
      });
    } finally {
      setState(() => _loading = false);
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 80), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: _scaffoldKey,
      backgroundColor: const Color(0xFF0F0F0F),
      endDrawer: DocumentsDrawer(),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0F0F0F),
        elevation: 0,
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(height: 1, color: const Color(0xFF222222)),
        ),
        title: Text(
          'GENAI AGENT',
          style: GoogleFonts.dmSans(
            fontSize: 13,
            fontWeight: FontWeight.w500,
            letterSpacing: 0.1,
            color: const Color(0xFFD4FF6E),
          ),
        ),
        actions: [
          TextButton.icon(
            onPressed: () => _scaffoldKey.currentState?.openEndDrawer(),
            icon: const Icon(Icons.add, size: 16, color: Color(0xFFD4FF6E)),
            label: Text(
              'Documents',
              style: GoogleFonts.dmSans(
                fontSize: 13,
                color: const Color(0xFF888888),
              ),
            ),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _messages.isEmpty
                ? _buildEmptyState()
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.symmetric(vertical: 24),
                    itemCount: _messages.length,
                    itemBuilder: (context, i) => _buildMessage(_messages[i]),
                  ),
          ),
          if (_loading)
            LinearProgressIndicator(
              backgroundColor: const Color(0xFF1A1A1A),
              valueColor: AlwaysStoppedAnimation<Color>(
                const Color(0xFFD4FF6E).withOpacity(0.6),
              ),
              minHeight: 1,
            ),
          _buildInputArea(),
        ],
      ),
    );
  }

  Widget _buildEmptyState() => Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              '◈',
              style: TextStyle(
                fontSize: 40,
                color: const Color(0xFF2A2A2A),
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'Ask anything. Tools activate automatically.',
              style: GoogleFonts.dmSans(
                fontSize: 14,
                color: const Color(0xFF444444),
              ),
            ),
          ],
        ),
      );

  Widget _buildMessage(Message message) {
    final isUser = message.role == 'user';
    final isError = message.role == 'error';
    final isAssistant = message.role == 'assistant';

    return Container(
      decoration: const BoxDecoration(
        border: Border(
          bottom: BorderSide(color: Color(0xFF1A1A1A), width: 1),
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 18),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                isUser ? 'You' : isError ? 'Error' : 'Claude',
                style: GoogleFonts.dmSans(
                  fontSize: 11,
                  fontWeight: FontWeight.w500,
                  letterSpacing: 0.08,
                  color: isUser
                      ? const Color(0xFF666666)
                      : isError
                          ? const Color(0xFFFF6B6B)
                          : const Color(0xFFD4FF6E),
                ),
              ),
              const SizedBox(height: 8),
              if (isAssistant && message.toolCalls.isNotEmpty) ...[
                ...message.toolCalls.map((t) => _buildToolCard(t)),
                const SizedBox(height: 10),
              ],
              if (isAssistant)
                MarkdownBody(
                  data: message.content,
                  styleSheet: MarkdownStyleSheet(
                    p: GoogleFonts.dmSans(
                      fontSize: 15,
                      height: 1.7,
                      color: const Color(0xFFE8E8E8),
                    ),
                    code: GoogleFonts.dmMono(
                      fontSize: 13,
                      color: const Color(0xFFD4FF6E),
                      backgroundColor: const Color(0xFF1A1A1A),
                    ),
                    codeblockDecoration: BoxDecoration(
                      color: const Color(0xFF1A1A1A),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0xFF2A2A2A)),
                    ),
                    blockquoteDecoration: BoxDecoration(
                      border: Border(
                        left: BorderSide(
                          color: const Color(0xFFD4FF6E),
                          width: 3,
                        ),
                      ),
                    ),
                    h1: GoogleFonts.dmSans(
                      fontSize: 20,
                      fontWeight: FontWeight.w500,
                      color: Colors.white,
                    ),
                    h2: GoogleFonts.dmSans(
                      fontSize: 17,
                      fontWeight: FontWeight.w500,
                      color: Colors.white,
                    ),
                    h3: GoogleFonts.dmSans(
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                      color: Colors.white,
                    ),
                  ),
                )
              else
                Text(
                  message.content,
                  style: GoogleFonts.dmSans(
                    fontSize: 15,
                    height: 1.7,
                    color: isError
                        ? const Color(0xFFFF6B6B)
                        : const Color(0xFFE8E8E8),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildToolCard(ToolCall tool) {
    Color accentColor;
    String displayName;

    switch (tool.toolName) {
      case 'web_search':
        accentColor = const Color(0xFF4A9EFF);
        displayName = 'web search';
        break;
      case 'execute_python':
        accentColor = const Color(0xFFD4FF6E);
        displayName = 'code';
        break;
      case 'search_documents':
        accentColor = const Color(0xFFA855F7);
        displayName = 'documents';
        break;
      default:
        accentColor = const Color(0xFF666666);
        displayName = tool.toolName;
    }

    final inputStr = tool.toolInput.values.isNotEmpty
        ? tool.toolInput.values.first.toString()
        : '';

    final outputPreview = tool.toolOutput.length > 100
        ? '${tool.toolOutput.substring(0, 100)}...'
        : tool.toolOutput;

    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(8),
        border: Border(
          left: BorderSide(color: accentColor, width: 2),
          top: const BorderSide(color: Color(0xFF2A2A2A)),
          right: const BorderSide(color: Color(0xFF2A2A2A)),
          bottom: const BorderSide(color: Color(0xFF2A2A2A)),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            displayName.toUpperCase(),
            style: GoogleFonts.dmSans(
              fontSize: 10,
              fontWeight: FontWeight.w500,
              letterSpacing: 0.08,
              color: accentColor,
            ),
          ),
          if (inputStr.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              inputStr,
              style: GoogleFonts.dmMono(
                fontSize: 11,
                color: const Color(0xFF666666),
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
          const SizedBox(height: 4),
          Text(
            outputPreview,
            style: GoogleFonts.dmSans(
              fontSize: 11,
              color: const Color(0xFF888888),
              height: 1.5,
            ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  Widget _buildInputArea() => Container(
        decoration: const BoxDecoration(
          color: Color(0xFF0F0F0F),
          border: Border(
            top: BorderSide(color: Color(0xFF1A1A1A)),
          ),
        ),
        padding: const EdgeInsets.fromLTRB(24, 12, 24, 20),
        child: Column(
          children: [
            Row(
              children: [
                _ToolToggle(
                  label: 'Web search',
                  active: _useWebSearch,
                  activeColor: const Color(0xFF4A9EFF),
                  activeBg: const Color(0xFF0D1F3A),
                  onTap: () => setState(() => _useWebSearch = !_useWebSearch),
                ),
                const SizedBox(width: 6),
                _ToolToggle(
                  label: 'Code',
                  active: _useCode,
                  activeColor: const Color(0xFFD4FF6E),
                  activeBg: const Color(0xFF162A06),
                  onTap: () => setState(() => _useCode = !_useCode),
                ),
                const SizedBox(width: 6),
                _ToolToggle(
                  label: 'RAG',
                  active: _useRag,
                  activeColor: const Color(0xFFA855F7),
                  activeBg: const Color(0xFF1A0A2E),
                  onTap: () => setState(() => _useRag = !_useRag),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Expanded(
                  child: TextField(
                    controller: _inputController,
                    maxLines: null,
                    style: GoogleFonts.dmSans(
                      fontSize: 14,
                      color: Colors.white,
                    ),
                    decoration: InputDecoration(
                      hintText: 'Ask something...',
                      hintStyle: GoogleFonts.dmSans(
                        fontSize: 14,
                        color: const Color(0xFF444444),
                      ),
                      filled: true,
                      fillColor: const Color(0xFF1A1A1A),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: const BorderSide(color: Color(0xFF2A2A2A)),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: const BorderSide(color: Color(0xFF2A2A2A)),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: const BorderSide(color: Color(0xFFD4FF6E)),
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 12,
                      ),
                    ),
                    onSubmitted: (_) => _send(),
                  ),
                ),
                const SizedBox(width: 8),
                GestureDetector(
                  onTap: _loading ? null : _send,
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 150),
                    width: 46,
                    height: 46,
                    decoration: BoxDecoration(
                      color: _loading
                          ? const Color(0xFF2A2A2A)
                          : const Color(0xFFD4FF6E),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Center(
                      child: _loading
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Color(0xFF666666),
                              ),
                            )
                          : const Icon(
                              Icons.arrow_upward_rounded,
                              size: 20,
                              color: Color(0xFF0A0A0A),
                            ),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      );

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}

class _ToolToggle extends StatelessWidget {
  final String label;
  final bool active;
  final Color activeColor;
  final Color activeBg;
  final VoidCallback onTap;

  const _ToolToggle({
    required this.label,
    required this.active,
    required this.activeColor,
    required this.activeBg,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) => GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
          decoration: BoxDecoration(
            color: active ? activeBg : Colors.transparent,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: active ? activeColor : const Color(0xFF2A2A2A),
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              AnimatedContainer(
                duration: const Duration(milliseconds: 150),
                width: 6,
                height: 6,
                decoration: BoxDecoration(
                  color: active ? activeColor : const Color(0xFF333333),
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 5),
              Text(
                label,
                style: GoogleFonts.dmSans(
                  fontSize: 12,
                  color: active ? activeColor : const Color(0xFF666666),
                ),
              ),
            ],
          ),
        ),
      );
}
