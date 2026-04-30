import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:appserve/core/theme/app_colors.dart';

/// Primary Minecraft-styled button
class McButton extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool isLoading;
  final bool isDanger;
  final bool isSecondary;
  final double? width;

  const McButton({
    super.key,
    required this.label,
    this.onPressed,
    this.icon,
    this.isLoading = false,
    this.isDanger = false,
    this.isSecondary = false,
    this.width,
  });

  @override
  Widget build(BuildContext context) {
    Color bg = isDanger
        ? AppColors.offline
        : isSecondary
            ? AppColors.backgroundOverlay
            : AppColors.grassGreen;

    Color border = isDanger
        ? AppColors.offline.withOpacity(0.5)
        : isSecondary
            ? AppColors.border
            : AppColors.grassGreenDark;

    return SizedBox(
      width: width,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: isLoading ? null : onPressed,
          borderRadius: BorderRadius.circular(8),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 150),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 13),
            decoration: BoxDecoration(
              color: onPressed == null ? bg.withOpacity(0.5) : bg,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: border, width: 1.5),
              boxShadow: onPressed != null && !isSecondary
                  ? [BoxShadow(color: bg.withOpacity(0.25), blurRadius: 8, offset: const Offset(0, 3))]
                  : null,
            ),
            child: Row(
              mainAxisSize: width != null ? MainAxisSize.max : MainAxisSize.min,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (isLoading) ...[
                  const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  ),
                  const SizedBox(width: 10),
                ] else if (icon != null) ...[
                  Icon(icon, size: 18, color: Colors.white),
                  const SizedBox(width: 8),
                ],
                Text(
                  label,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                    letterSpacing: 0.3,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    ).animate().fadeIn(duration: 200.ms);
  }
}
