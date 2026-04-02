 class ToolCall {
  final String toolName;
  final Map<String, dynamic> toolInput;
  final String toolOutput;
 
  ToolCall({
    required this.toolName,
    required this.toolInput,
    required this.toolOutput,
  });
 
  factory ToolCall.fromJson(Map<String, dynamic> json) => ToolCall(
        toolName:   json['tool_name']   ?? '',
        toolInput:  Map<String, dynamic>.from(json['tool_input'] ?? {}),
        toolOutput: json['tool_output'] ?? '',
      );
}
 
class Message {
  final String role;       // 'user' | 'assistant' | 'error'
  final String content;
  final List<ToolCall> toolCalls;
 
  Message({
    required this.role,
    required this.content,
    this.toolCalls = const [],
  });
}
 