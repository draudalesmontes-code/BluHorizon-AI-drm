import 'package:shared_preferences/shared_preferences.dart';

/// Optional persistence for the active conversation id (int, matches the
/// Postgres `conversations.id`). Currently the chat screen keeps this in
/// memory; this store is here for when you want it to survive restarts.
class SessionStore {
  static const _key = 'chat_conversation_id';

  static Future<int?> getConversationId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(_key);
  }

  static Future<void> setConversationId(int id) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_key, id);
  }

  static Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }
}
