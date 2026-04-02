// lib/main.dart
// App entry point

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/chat_screen.dart';

void main() {
  runApp(const GenAIApp());
}

class GenAIApp extends StatelessWidget {
  const GenAIApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'GenAI Agent',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.dark(
          primary:   const Color(0xFFD4FF6E),
          surface:   const Color(0xFF1A1A1A),
          background: const Color(0xFF0F0F0F),
        ),
        scaffoldBackgroundColor: const Color(0xFF0F0F0F),
        textTheme: GoogleFonts.dmSansTextTheme(
          ThemeData.dark().textTheme,
        ),
        useMaterial3: true,
      ),
      home: const ChatScreen(),
    );
  }
}