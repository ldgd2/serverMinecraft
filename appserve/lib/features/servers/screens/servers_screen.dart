import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import 'package:appserve/core/models/server_model.dart';
import 'package:appserve/core/providers/app_providers.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/shared/widgets/mc_button.dart';
import 'package:appserve/shared/widgets/mc_card.dart';
import 'package:appserve/shared/widgets/mc_widgets.dart';
import 'server_detail_screen.dart';

class ServersScreen extends StatelessWidget {
  const ServersScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: Container(
        decoration: const BoxDecoration(gradient: AppColors.backgroundGradient),
        child: SafeArea(
          child: Column(
            children: [
              _buildHeader(context),
              Expanded(child: _buildBody(context)),
            ],
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppColors.grassGreen,
        onPressed: () => _showCreateServerSheet(context),
        icon: const Icon(Icons.add, color: Colors.white),
        label: const Text('New Server', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      child: Row(
        children: [
          const Text('Servers', style: TextStyle(color: AppColors.textPrimary, fontSize: 22, fontWeight: FontWeight.bold)),
          const Spacer(),
          Consumer<ServerProvider>(
            builder: (_, sp, __) => GestureDetector(
              onTap: sp.loadServers,
              child: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(color: AppColors.backgroundCard, borderRadius: BorderRadius.circular(8), border: Border.all(color: AppColors.border)),
                child: const Icon(Icons.refresh, size: 18, color: AppColors.textSecondary),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBody(BuildContext context) {
    return Consumer<ServerProvider>(
      builder: (_, sp, __) {
        if (sp.isLoading) {
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: 4,
            separatorBuilder: (_, __) => const SizedBox(height: 10),
            itemBuilder: (_, __) => const McShimmer(height: 90),
          );
        }
        if (sp.servers.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.dns_outlined, size: 64, color: AppColors.textMuted),
                const SizedBox(height: 16),
                const Text('No servers found', style: TextStyle(color: AppColors.textPrimary, fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                const Text('Create your first Minecraft server', style: TextStyle(color: AppColors.textMuted)),
                const SizedBox(height: 24),
                McButton(label: 'Create Server', icon: Icons.add, onPressed: () => _showCreateServerSheet(context)),
              ],
            ).animate().fadeIn(duration: 400.ms),
          );
        }
        return ListView.separated(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
          itemCount: sp.servers.length,
          separatorBuilder: (_, __) => const SizedBox(height: 10),
          itemBuilder: (_, i) => ServerCard(server: sp.servers[i]).animate().fadeIn(delay: (i * 50).ms).slideY(begin: 0.1, end: 0),
        );
      },
    );
  }

  void _showCreateServerSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const CreateServerSheet(),
    );
  }
}

// ─── Server Card ─────────────────────────────────────────────────────────────

class ServerCard extends StatelessWidget {
  final ServerModel server;
  const ServerCard({super.key, required this.server});

  @override
  Widget build(BuildContext context) {
    return McCard(
      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ServerDetailScreen(server: server))),
      borderColor: server.isOnline ? AppColors.grassGreen.withOpacity(0.25) : AppColors.border,
      child: Column(
        children: [
          Row(
            children: [
              // Server type icon
              Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  gradient: server.isOnline ? AppColors.grassGradient : null,
                  color: server.isOnline ? null : AppColors.backgroundOverlay,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(Icons.dns_rounded, size: 24, color: server.isOnline ? Colors.white : AppColors.textMuted),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(server.name, style: const TextStyle(color: AppColors.textPrimary, fontSize: 15, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        StatChip(icon: Icons.tag, value: 'v${server.version}'),
                        const SizedBox(width: 6),
                        StatChip(icon: Icons.wifi, value: ':${server.port}'),
                        const SizedBox(width: 6),
                        StatChip(icon: Icons.memory, value: server.ramFormatted),
                      ],
                    ),
                  ],
                ),
              ),
              ServerStatusBadge(status: server.status),
            ],
          ),
          const SizedBox(height: 14),
          const Divider(color: AppColors.border, height: 1),
          const SizedBox(height: 10),
          // Quick controls
          Row(
            children: [
              if (server.isOffline)
                Expanded(child: McButton(label: 'Start', icon: Icons.play_arrow, onPressed: () => context.read<ServerProvider>().startServer(server.name)))
              else if (server.isOnline) ...[
                Expanded(child: McButton(label: 'Stop', icon: Icons.stop, isDanger: true, onPressed: () => context.read<ServerProvider>().stopServer(server.name))),
                const SizedBox(width: 8),
                Expanded(child: McButton(label: 'Restart', icon: Icons.refresh, isSecondary: true, onPressed: () => context.read<ServerProvider>().restartServer(server.name))),
              ] else
                Expanded(child: McButton(label: 'Starting...', isLoading: true, onPressed: null)),
              const SizedBox(width: 8),
              McButton(
                label: 'Console',
                icon: Icons.terminal,
                isSecondary: true,
                onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ServerDetailScreen(server: server, initialTab: 1))),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ─── Create Server Sheet ──────────────────────────────────────────────────────

class CreateServerSheet extends StatefulWidget {
  const CreateServerSheet({super.key});

  @override
  State<CreateServerSheet> createState() => _CreateServerSheetState();
}

class _CreateServerSheetState extends State<CreateServerSheet> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _portCtrl = TextEditingController(text: '25565');
  final _motdCtrl = TextEditingController(text: 'A Minecraft Server');
  double _ram = 1024;
  String _version = '1.21';
  bool _onlineMode = true;
  bool _isLoading = false;

  final _versions = ['1.21', '1.20.4', '1.20.1', '1.19.4', '1.19.2', '1.18.2'];

  @override
  void dispose() {
    _nameCtrl.dispose();
    _portCtrl.dispose();
    _motdCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isLoading = true);
    try {
      await context.read<ServerProvider>().createServer({
        'name': _nameCtrl.text.trim(),
        'version': _version,
        'port': int.parse(_portCtrl.text),
        'ram_mb': _ram.toInt(),
        'motd': _motdCtrl.text.trim(),
        'online_mode': _onlineMode,
        'max_players': 20,
      });
      if (mounted) Navigator.pop(context);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.backgroundCard,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      padding: EdgeInsets.fromLTRB(24, 20, 24, MediaQuery.of(context).viewInsets.bottom + 24),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              // Handle
              Center(child: Container(width: 36, height: 4, decoration: BoxDecoration(color: AppColors.border, borderRadius: BorderRadius.circular(2)))),
              const SizedBox(height: 20),
              const Text('Create Server', style: TextStyle(color: AppColors.textPrimary, fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 20),

              _McFormField(
                label: 'SERVER NAME',
                hint: 'My Minecraft Server',
                controller: _nameCtrl,
                icon: Icons.dns_outlined,
                validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 16),

              Row(children: [
                Expanded(child: _McFormField(label: 'PORT', hint: '25565', controller: _portCtrl, icon: Icons.wifi, keyboardType: TextInputType.number)),
                const SizedBox(width: 12),
                Expanded(child: _VersionDropdown(value: _version, versions: _versions, onChanged: (v) => setState(() => _version = v!))),
              ]),
              const SizedBox(height: 16),

              _buildRamSlider(),
              const SizedBox(height: 16),

              _McFormField(label: 'SERVER MOTD', hint: 'A Minecraft Server', controller: _motdCtrl, icon: Icons.message_outlined),
              const SizedBox(height: 16),

              _OnlineModeToggle(value: _onlineMode, onChanged: (v) => setState(() => _onlineMode = v)),
              const SizedBox(height: 24),

              McButton(label: 'CREATE SERVER', onPressed: _submit, isLoading: _isLoading, width: double.infinity, icon: Icons.rocket_launch),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRamSlider() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text('RAM', style: TextStyle(color: AppColors.textSecondary, fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 0.3)),
            Text(_ram >= 1024 ? '${(_ram / 1024).toStringAsFixed(1)} GB' : '${_ram.toInt()} MB',
                style: const TextStyle(color: AppColors.grassGreenLight, fontSize: 12, fontWeight: FontWeight.bold)),
          ],
        ),
        SliderTheme(
          data: SliderTheme.of(context).copyWith(
            activeTrackColor: AppColors.grassGreen,
            inactiveTrackColor: AppColors.border,
            thumbColor: AppColors.grassGreenLight,
            overlayColor: AppColors.grassGreen.withOpacity(0.2),
            trackHeight: 4,
          ),
          child: Slider(value: _ram, min: 512, max: 8192, divisions: 15, onChanged: (v) => setState(() => _ram = v)),
        ),
      ],
    );
  }
}

class _McFormField extends StatelessWidget {
  final String label;
  final String hint;
  final TextEditingController controller;
  final IconData icon;
  final TextInputType? keyboardType;
  final String? Function(String?)? validator;

  const _McFormField({required this.label, required this.hint, required this.controller, required this.icon, this.keyboardType, this.validator});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: AppColors.textSecondary, fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 0.5)),
        const SizedBox(height: 6),
        TextFormField(
          controller: controller,
          keyboardType: keyboardType,
          validator: validator,
          style: const TextStyle(color: AppColors.textPrimary, fontSize: 14),
          decoration: InputDecoration(hintText: hint, prefixIcon: Icon(icon, size: 18)),
        ),
      ],
    );
  }
}

class _VersionDropdown extends StatelessWidget {
  final String value;
  final List<String> versions;
  final void Function(String?) onChanged;

  const _VersionDropdown({required this.value, required this.versions, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('VERSION', style: TextStyle(color: AppColors.textSecondary, fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 0.5)),
        const SizedBox(height: 6),
        DropdownButtonFormField<String>(
          initialValue: value,
          dropdownColor: AppColors.backgroundElevated,
          style: const TextStyle(color: AppColors.textPrimary, fontSize: 14),
          decoration: const InputDecoration(prefixIcon: Icon(Icons.gamepad_outlined, size: 18)),
          items: versions.map((v) => DropdownMenuItem(value: v, child: Text(v))).toList(),
          onChanged: onChanged,
        ),
      ],
    );
  }
}

class _OnlineModeToggle extends StatelessWidget {
  final bool value;
  final void Function(bool) onChanged;

  const _OnlineModeToggle({required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return McCard(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          const Icon(Icons.verified_user_outlined, size: 20, color: AppColors.textSecondary),
          const SizedBox(width: 12),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Online Mode', style: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w600, fontSize: 14)),
                Text('Authenticate players with Mojang', style: TextStyle(color: AppColors.textMuted, fontSize: 12)),
              ],
            ),
          ),
          Switch(value: value, onChanged: onChanged),
        ],
      ),
    );
  }
}
