import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import 'package:appserve/core/providers/app_providers.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/shared/widgets/mc_button.dart';
import 'package:appserve/shared/widgets/mc_text_field.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _usernameCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;
    final auth = context.read<AuthProvider>();
    final success = await auth.login(_usernameCtrl.text.trim(), _passwordCtrl.text);
    if (success && mounted) {
      Navigator.of(context).pushReplacementNamed('/');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(gradient: AppColors.backgroundGradient),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 40),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  const SizedBox(height: 24),

                  // === LOGO AREA ===
                  _buildLogo(),

                  const SizedBox(height: 48),

                  // === LOGIN FORM CARD ===
                  _buildLoginCard(),

                  const SizedBox(height: 32),

                  // === FOOTER ===
                  const Text(
                    'Minecraft Server Manager v1.0',
                    style: TextStyle(color: AppColors.textMuted, fontSize: 11),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLogo() {
    return Column(
      children: [
        // Minecraft grass block pixel icon
        Container(
          width: 90,
          height: 90,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            gradient: AppColors.grassGradient,
            boxShadow: [
              BoxShadow(color: AppColors.grassGreen.withOpacity(0.5), blurRadius: 30, spreadRadius: 2),
            ],
          ),
          child: const Icon(Icons.dns_rounded, size: 48, color: Colors.white),
        )
            .animate()
            .fadeIn(duration: 600.ms)
            .scale(begin: const Offset(0.6, 0.6), end: const Offset(1, 1), curve: Curves.elasticOut),

        const SizedBox(height: 20),

        const Text(
          'MINECRAFT MANAGER',
          style: TextStyle(
            color: AppColors.textPrimary,
            fontSize: 22,
            fontWeight: FontWeight.bold,
            letterSpacing: 2,
          ),
        ).animate().fadeIn(delay: 200.ms, duration: 500.ms).slideY(begin: 0.2, end: 0),

        const SizedBox(height: 8),

        const Text(
          'Server Administration Console',
          style: TextStyle(color: AppColors.textMuted, fontSize: 13, letterSpacing: 0.5),
        ).animate().fadeIn(delay: 350.ms, duration: 500.ms),
      ],
    );
  }

  Widget _buildLoginCard() {
    return Consumer<AuthProvider>(
      builder: (_, auth, __) => Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          gradient: AppColors.cardGradient,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.border),
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 20)],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Sign In',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            const Text('Access your server dashboard',
                style: TextStyle(color: AppColors.textMuted, fontSize: 13)),

            const SizedBox(height: 24),

            McTextField(
              label: 'USERNAME',
              hint: 'admin',
              controller: _usernameCtrl,
              prefixIcon: Icons.person_outline,
              textInputAction: TextInputAction.next,
              validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
            ),

            const SizedBox(height: 16),

            McTextField(
              label: 'PASSWORD',
              hint: '••••••••',
              controller: _passwordCtrl,
              prefixIcon: Icons.lock_outline,
              obscureText: _obscurePassword,
              textInputAction: TextInputAction.done,
              onSubmitted: (_) => _handleLogin(),
              validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
              suffix: IconButton(
                icon: Icon(
                  _obscurePassword ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                  size: 18,
                  color: AppColors.textMuted,
                ),
                onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
              ),
            ),

            if (auth.error != null) ...[
              const SizedBox(height: 14),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                decoration: BoxDecoration(
                  color: AppColors.offline.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.offline.withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.error_outline, size: 16, color: AppColors.offline),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(auth.error!,
                          style: const TextStyle(color: AppColors.offline, fontSize: 13)),
                    ),
                  ],
                ),
              ).animate().fadeIn(duration: 300.ms).shake(),
            ],

            const SizedBox(height: 24),

            McButton(
              label: 'SIGN IN',
              onPressed: _handleLogin,
              isLoading: auth.isLoading,
              icon: Icons.login,
              width: double.infinity,
            ),
          ],
        ),
      ).animate().fadeIn(delay: 400.ms, duration: 500.ms).slideY(begin: 0.15, end: 0),
    );
  }
}
