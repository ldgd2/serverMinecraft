import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:appserve/core/api/api_client.dart';
import 'package:appserve/core/constants/app_constants.dart';
import 'package:appserve/core/providers/app_providers.dart';
import 'package:appserve/core/theme/app_colors.dart';
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

  @override
  void initState() {
    super.initState();
    _loadCurrentUrl();
  }

  Future<void> _loadCurrentUrl() async {
    final prefs = await SharedPreferences.getInstance();
    final url = prefs.getString(AppConstants.serverUrlKey) ?? AppConstants.baseUrl;
    _serverUrlCtrl.text = url;
    ApiClient.instance.setBaseUrl(url);
  }

  Future<void> _saveUrl() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.serverUrlKey, _serverUrlCtrl.text.trim());
    ApiClient.instance.setBaseUrl(_serverUrlCtrl.text.trim());
    setState(() => _saved = true);
    await Future.delayed(const Duration(seconds: 2));
    if (mounted) setState(() => _saved = false);
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
              child: Column(children: [
                McInfoRow(icon: Icons.info_outline, label: 'Version', value: AppConstants.appVersion),
                const Divider(color: AppColors.border, height: 16),
                McInfoRow(icon: Icons.dns_outlined, label: 'App', value: AppConstants.appName),
              ]),
            ),
          ],
        ),
      ),
    );
  }
}
