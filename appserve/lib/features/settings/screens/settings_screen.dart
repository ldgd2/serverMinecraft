import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:appserve/core/api/api_client.dart';
import 'package:appserve/core/constants/app_constants.dart';
import 'package:appserve/core/providers/app_providers.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/core/services/update_service.dart';
import 'package:appserve/shared/widgets/mc_button.dart';
import 'package:appserve/shared/widgets/mc_card.dart';
import 'package:appserve/shared/widgets/mc_text_field.dart';
import 'package:appserve/shared/widgets/mc_widgets.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _serverUrlCtrl = TextEditingController();
  bool _saved = false;
  String _currentVersion = '...';
  bool _checkingUpdate = false;

  @override
  void initState() {
    super.initState();
    _loadCurrentUrl();
    _loadVersion();
  }

  Future<void> _loadCurrentUrl() async {
    final prefs = await SharedPreferences.getInstance();
    final url = prefs.getString(AppConstants.serverUrlKey) ?? AppConstants.baseUrl;
    _serverUrlCtrl.text = url;
    ApiClient.instance.setBaseUrl(url);
  }

  Future<void> _loadVersion() async {
    final v = await UpdateService.instance.getCurrentVersion();
    if (mounted) setState(() => _currentVersion = v);
  }

  Future<void> _saveUrl() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.serverUrlKey, _serverUrlCtrl.text.trim());
    ApiClient.instance.setBaseUrl(_serverUrlCtrl.text.trim());
    setState(() => _saved = true);
    await Future.delayed(const Duration(seconds: 2));
    if (mounted) setState(() => _saved = false);
  }

  Future<void> _checkUpdate() async {
    setState(() => _checkingUpdate = true);
    final info = await UpdateService.instance.checkForUpdate();
    if (!mounted) return;
    setState(() => _checkingUpdate = false);

    if (!info.hasUpdate || info.downloadUrl == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('✓  Ya tienes la última versión (v$_currentVersion)'),
          backgroundColor: const Color(0xFF2d333b),
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    // Mostrar diálogo de actualización
    await showDialog(
      context: context,
      builder: (_) => _UpdateMiniDialog(info: info),
    );
  }

  @override
  void dispose() {
    _serverUrlCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(gradient: AppColors.backgroundGradient),
      child: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 8),
              child: Text('Settings', style: TextStyle(color: AppColors.textPrimary, fontSize: 22, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 16),

            // === Server Connection ===
            const SectionHeader(title: 'SERVER CONNECTION'),
            const SizedBox(height: 12),
            McCard(
              child: Column(
                children: [
                  McTextField(
                    label: 'API URL',
                    hint: 'http://your-vps:8000',
                    controller: _serverUrlCtrl,
                    prefixIcon: Icons.link,
                    keyboardType: TextInputType.url,
                  ),
                  const SizedBox(height: 16),
                  McButton(
                    label: _saved ? 'Saved!' : 'Save Connection',
                    icon: _saved ? Icons.check : Icons.save_outlined,
                    onPressed: _saveUrl,
                    width: double.infinity,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // === Account ===
            const SectionHeader(title: 'ACCOUNT'),
            const SizedBox(height: 12),
            Consumer<AuthProvider>(
              builder: (_, auth, __) => McCard(
                child: Column(
                  children: [
                    McInfoRow(icon: Icons.person_outline, label: 'Username', value: auth.user?.username ?? '--'),
                    const Divider(color: AppColors.border, height: 20),
                    McInfoRow(icon: Icons.admin_panel_settings_outlined, label: 'Role', value: auth.user?.isAdmin == true ? 'Administrator' : 'User',
                        valueColor: auth.user?.isAdmin == true ? AppColors.gold : AppColors.textSecondary),
                    const SizedBox(height: 16),
                    McButton(
                      label: 'Sign Out',
                      icon: Icons.logout,
                      isDanger: true,
                      width: double.infinity,
                      onPressed: () async {
                        await auth.logout();
                        if (context.mounted) Navigator.pushReplacementNamed(context, '/login');
                      },
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),

            // === App Info ===
            const SectionHeader(title: 'ABOUT'),
            const SizedBox(height: 12),
            McCard(
              child: Column(
                children: [
                  McInfoRow(
                    icon: Icons.tag_rounded,
                    label: 'Versión',
                    value: 'v$_currentVersion',
                    valueColor: AppColors.textPrimary,
                  ),
                  const Divider(color: AppColors.border, height: 16),
                  McInfoRow(icon: Icons.dns_outlined, label: 'App', value: AppConstants.appName),
                  const SizedBox(height: 16),
                  McButton(
                    label: _checkingUpdate ? 'Verificando...' : 'Buscar actualización',
                    icon: _checkingUpdate ? Icons.hourglass_empty : Icons.system_update_outlined,
                    onPressed: _checkingUpdate ? () {} : _checkUpdate,
                    width: double.infinity,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Mini diálogo de actualización para Settings ──────────────────────────────

class _UpdateMiniDialog extends StatelessWidget {
  final UpdateInfo info;
  const _UpdateMiniDialog({required this.info});

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: const Color(0xFF161B22),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      title: const Row(
        children: [
          Icon(Icons.system_update_rounded, color: Color(0xFF5D8A3C)),
          SizedBox(width: 10),
          Text('Actualización disponible', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
        ],
      ),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(color: const Color(0xFF0D1117), borderRadius: BorderRadius.circular(10)),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Column(children: [
                  const Text('Actual', style: TextStyle(color: Color(0xFF8B949E), fontSize: 10)),
                  Text('v${info.currentVersion}', style: const TextStyle(color: Color(0xFF8B949E), fontSize: 14, fontWeight: FontWeight.bold)),
                ]),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 12),
                  child: Icon(Icons.arrow_forward_rounded, color: Color(0xFF5D8A3C), size: 20),
                ),
                Column(children: [
                  const Text('Nueva', style: TextStyle(color: Color(0xFF8B949E), fontSize: 10)),
                  Text('v${info.latestVersion}', style: const TextStyle(color: Color(0xFF7CBF52), fontSize: 14, fontWeight: FontWeight.bold)),
                ]),
              ],
            ),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancelar', style: TextStyle(color: Color(0xFF8B949E))),
        ),
        ElevatedButton.icon(
          style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF5D8A3C)),
          icon: const Icon(Icons.download_rounded, color: Colors.white, size: 18),
          label: const Text('Descargar', style: TextStyle(color: Colors.white)),
          onPressed: () async {
            if (info.downloadUrl != null) {
              await UpdateService.instance.openDownloadUrl(info.downloadUrl!);
            }
            if (context.mounted) Navigator.pop(context);
          },
        ),
      ],
    );
  }
}
