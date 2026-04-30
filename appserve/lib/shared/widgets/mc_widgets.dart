import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:appserve/core/theme/app_colors.dart';

/// Animated status badge showing ONLINE / OFFLINE / STARTING
class ServerStatusBadge extends StatelessWidget {
  final String status;
  final bool large;

  const ServerStatusBadge({super.key, required this.status, this.large = false});

  Color get _color {
    switch (status.toUpperCase()) {
      case 'ONLINE': return AppColors.online;
      case 'STARTING': return AppColors.starting;
      default: return AppColors.offline;
    }
  }

  String get _label => status.toUpperCase();

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Pulsing dot for online
        Container(
          width: large ? 10 : 7,
          height: large ? 10 : 7,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: _color,
            boxShadow: [BoxShadow(color: _color.withOpacity(0.5), blurRadius: 6, spreadRadius: 1)],
          ),
        ).animate(onPlay: (c) => c.repeat())
            .scale(begin: const Offset(1, 1), end: const Offset(1.4, 1.4), duration: 900.ms)
            .then()
            .scale(begin: const Offset(1.4, 1.4), end: const Offset(1, 1), duration: 900.ms),
        const SizedBox(width: 6),
        Text(
          _label,
          style: TextStyle(
            color: _color,
            fontSize: large ? 13 : 10,
            fontWeight: FontWeight.bold,
            letterSpacing: 0.5,
          ),
        ),
      ],
    );
  }
}

/// Section header with divider
class SectionHeader extends StatelessWidget {
  final String title;
  final Widget? trailing;

  const SectionHeader({super.key, required this.title, this.trailing});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Text(title,
              style: const TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.2)),
          const SizedBox(width: 12),
          const Expanded(child: Divider(color: AppColors.border, height: 1)),
          if (trailing != null) ...[const SizedBox(width: 12), trailing!],
        ],
      ),
    );
  }
}

/// Loading shimmer placeholder
class McShimmer extends StatelessWidget {
  final double height;
  final double? width;
  final double borderRadius;

  const McShimmer({super.key, required this.height, this.width, this.borderRadius = 8});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height,
      width: width,
      decoration: BoxDecoration(
        color: AppColors.backgroundOverlay,
        borderRadius: BorderRadius.circular(borderRadius),
      ),
    ).animate(onPlay: (c) => c.repeat())
        .shimmer(duration: 1200.ms, color: AppColors.border.withOpacity(0.5));
  }
}

/// Stat chip — e.g. RAM: 2GB
class StatChip extends StatelessWidget {
  final IconData icon;
  final String value;
  final Color? color;

  const StatChip({super.key, required this.icon, required this.value, this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.backgroundOverlay,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: color ?? AppColors.textSecondary),
          const SizedBox(width: 4),
          Text(value,
              style: TextStyle(
                  color: color ?? AppColors.textSecondary,
                  fontSize: 11,
                  fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
