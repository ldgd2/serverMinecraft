import 'package:flutter/material.dart';
import 'package:appserve/core/theme/app_colors.dart';

class McDialogs {
  /// Shows a standard confirmation dialog.
  static Future<bool> showConfirm(
    BuildContext context, {
    required String title,
    required String message,
    String confirmLabel = 'Confirm',
    String cancelLabel = 'Cancel',
    bool isDanger = false,
  }) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.backgroundCard,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: isDanger ? const BorderSide(color: AppColors.offline, width: 1) : const BorderSide(color: AppColors.border),
        ),
        title: Text(title, style: TextStyle(color: isDanger ? AppColors.offline : AppColors.textPrimary)),
        content: Text(message, style: const TextStyle(color: AppColors.textSecondary)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(cancelLabel, style: const TextStyle(color: AppColors.textMuted)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(
              confirmLabel,
              style: TextStyle(color: isDanger ? AppColors.offline : AppColors.grassGreenLight, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
    return result ?? false;
  }

  /// Shows an error dialog.
  static Future<void> showError(
    BuildContext context, {
    String title = 'Error',
    required String message,
  }) async {
    await showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.backgroundCard,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppColors.offline, width: 1),
        ),
        title: Row(
          children: [
            const Icon(Icons.error_outline, color: AppColors.offline),
            const SizedBox(width: 8),
            Text(title, style: const TextStyle(color: AppColors.offline)),
          ],
        ),
        content: Text(message, style: const TextStyle(color: AppColors.textSecondary)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK', style: TextStyle(color: AppColors.textPrimary)),
          ),
        ],
      ),
    );
  }
}
