import 'package:flutter/material.dart';

class AppColors {
  AppColors._();

  // === MINECRAFT DARK BACKGROUND PALETTE ===
  static const Color backgroundDeep = Color(0xFF0D1117);
  static const Color backgroundCard = Color(0xFF161B22);
  static const Color backgroundElevated = Color(0xFF1C2230);
  static const Color backgroundOverlay = Color(0xFF21262D);

  // === MINECRAFT GRASS GREEN ===
  static const Color grassGreen = Color(0xFF5D8A3C);
  static const Color grassGreenLight = Color(0xFF7CBF52);
  static const Color grassGreenDark = Color(0xFF3F6128);
  static const Color grassGreenGlow = Color(0xFF8FD45A);

  // === DIRT / STONE ACCENTS ===
  static const Color stoneGray = Color(0xFF6B7280);
  static const Color stoneDark = Color(0xFF374151);
  static const Color dirtBrown = Color(0xFF7C5C3A);
  static const Color dirtLight = Color(0xFF9C7A50);

  // === STATUS COLORS ===
  static const Color online = Color(0xFF4ADE80);
  static const Color offline = Color(0xFFEF4444);
  static const Color starting = Color(0xFFFACC15);
  static const Color loading = Color(0xFF60A5FA);

  // === TEXT ===
  static const Color textPrimary = Color(0xFFE6EDF3);
  static const Color textSecondary = Color(0xFF8B949E);
  static const Color textMuted = Color(0xFF484F58);
  static const Color textAccent = Color(0xFF7CBF52);

  // === BORDER ===
  static const Color border = Color(0xFF30363D);
  static const Color borderAccent = Color(0xFF5D8A3C);

  // === GRADIENTS ===
  static const LinearGradient grassGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF5D8A3C), Color(0xFF3F6128)],
  );

  static const LinearGradient cardGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Color(0xFF1C2230), Color(0xFF161B22)],
  );

  static const LinearGradient backgroundGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Color(0xFF0D1117), Color(0xFF161B22)],
  );

  // === MINECRAFT SPECIFIC ===
  static const Color gold = Color(0xFFFFAA00);
  static const Color diamond = Color(0xFF4AEAC4);
  static const Color redstone = Color(0xFFFF3333);
  static const Color lapis = Color(0xFF1D4ED8);
  static const Color emerald = Color(0xFF10B981);
  static const Color netherite = Color(0xFF3D3343);
}
