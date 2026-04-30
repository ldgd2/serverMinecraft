import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import 'package:appserve/core/models/server_model.dart';
import 'package:appserve/core/providers/app_providers.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/shared/widgets/mc_button.dart';
import 'package:appserve/shared/widgets/mc_card.dart';
import 'package:appserve/shared/widgets/mc_widgets.dart';

class ServerDetailScreen extends StatefulWidget {
  final ServerModel server;
  final int initialTab;

  const ServerDetailScreen({super.key, required this.server, this.initialTab = 0});

  @override
  State<ServerDetailScreen> createState() => _ServerDetailScreenState();
}

class _ServerDetailScreenState extends State<ServerDetailScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  late ServerModel _server;

  @override
  void initState() {
    super.initState();
    _server = widget.server;
    _tabController = TabController(length: 3, vsync: this, initialIndex: widget.initialTab);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ServerProvider>().selectServer(_server.name);
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundDeep,
      body: NestedScrollView(
        headerSliverBuilder: (_, __) => [_buildSliverAppBar()],
        body: Column(
          children: [
            _buildTabBar(),
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  _OverviewTab(server: _server),
                  _ConsoleTab(server: _server),
                  _SettingsTab(server: _server),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  SliverAppBar _buildSliverAppBar() {
    return SliverAppBar(
      expandedHeight: 200,
      pinned: true,
      backgroundColor: AppColors.backgroundCard,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back_ios, color: AppColors.textPrimary, size: 20),
        onPressed: () => Navigator.pop(context),
      ),
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: _server.isOnline
                  ? [const Color(0xFF1a3a1a), AppColors.backgroundCard]
                  : [AppColors.backgroundElevated, AppColors.backgroundCard],
            ),
          ),
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 56, 20, 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 56,
                        height: 56,
                        decoration: BoxDecoration(
                          gradient: _server.isOnline ? AppColors.grassGradient : null,
                          color: _server.isOnline ? null : AppColors.backgroundOverlay,
                          borderRadius: BorderRadius.circular(14),
                          boxShadow: _server.isOnline
                              ? [BoxShadow(color: AppColors.grassGreen.withOpacity(0.4), blurRadius: 16)]
                              : null,
                        ),
                        child: Icon(Icons.dns_rounded, size: 28, color: _server.isOnline ? Colors.white : AppColors.textMuted),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(_server.name,
                                style: const TextStyle(color: AppColors.textPrimary, fontSize: 20, fontWeight: FontWeight.bold)),
                            const SizedBox(height: 4),
                            ServerStatusBadge(status: _server.status, large: true),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      StatChip(icon: Icons.tag, value: 'v${_server.version}', color: AppColors.diamond),
                      const SizedBox(width: 8),
                      StatChip(icon: Icons.wifi, value: ':${_server.port}', color: AppColors.gold),
                      const SizedBox(width: 8),
                      StatChip(icon: Icons.memory, value: _server.ramFormatted, color: AppColors.emerald),
                      const SizedBox(width: 8),
                      StatChip(icon: Icons.people_outline, value: '${_server.maxPlayers} max', color: AppColors.lapis),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTabBar() {
    return Container(
      color: AppColors.backgroundCard,
      child: TabBar(
        controller: _tabController,
        indicatorColor: AppColors.grassGreen,
        indicatorWeight: 2,
        labelColor: AppColors.grassGreenLight,
        unselectedLabelColor: AppColors.textMuted,
        labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
        tabs: const [
          Tab(icon: Icon(Icons.info_outline, size: 18), text: 'Overview'),
          Tab(icon: Icon(Icons.terminal, size: 18), text: 'Console'),
          Tab(icon: Icon(Icons.settings_outlined, size: 18), text: 'Settings'),
        ],
      ),
    );
  }
}

// ─── Overview Tab ─────────────────────────────────────────────────────────────

class _OverviewTab extends StatelessWidget {
  final ServerModel server;
  const _OverviewTab({required this.server});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Control buttons
        _buildControls(context),
        const SizedBox(height: 20),
        const SectionHeader(title: 'SERVER INFO'),
        const SizedBox(height: 10),
        McCard(
          child: Column(
            children: [
              McInfoRow(icon: Icons.dns_rounded, label: 'Name', value: server.name),
              const Divider(color: AppColors.border, height: 16),
              McInfoRow(icon: Icons.gamepad_outlined, label: 'Version', value: server.version),
              const Divider(color: AppColors.border, height: 16),
              McInfoRow(icon: Icons.wifi, label: 'Port', value: server.port.toString()),
              const Divider(color: AppColors.border, height: 16),
              McInfoRow(icon: Icons.memory, label: 'RAM', value: server.ramFormatted),
              const Divider(color: AppColors.border, height: 16),
              McInfoRow(icon: Icons.people_outline, label: 'Max Players', value: server.maxPlayers.toString()),
              const Divider(color: AppColors.border, height: 16),
              McInfoRow(icon: Icons.verified_user_outlined, label: 'Online Mode', value: server.onlineMode ? 'Enabled' : 'Disabled',
                  valueColor: server.onlineMode ? AppColors.online : AppColors.offline),
            ],
          ),
        ).animate().fadeIn(duration: 350.ms),
        if (server.motd != null) ...[
          const SizedBox(height: 16),
          const SectionHeader(title: 'MOTD'),
          const SizedBox(height: 10),
          McCard(
            child: Text(server.motd!, style: const TextStyle(color: AppColors.grassGreenLight, fontFamily: 'monospace', fontSize: 14)),
          ).animate().fadeIn(delay: 100.ms),
        ],
      ],
    );
  }

  Widget _buildControls(BuildContext context) {
    return Consumer<ServerProvider>(
      builder: (_, sp, __) => Row(
        children: [
          if (server.isOffline)
            Expanded(child: McButton(label: 'Start', icon: Icons.play_arrow, onPressed: () async { await sp.startServer(server.name); }))
          else if (server.isOnline) ...[
            Expanded(child: McButton(label: 'Stop', icon: Icons.stop, isDanger: true, onPressed: () async { await sp.stopServer(server.name); })),
            const SizedBox(width: 8),
            Expanded(child: McButton(label: 'Restart', icon: Icons.refresh, isSecondary: true, onPressed: () async { await sp.restartServer(server.name); })),
          ] else
            Expanded(child: McButton(label: 'Starting...', isLoading: true, onPressed: null)),
        ],
      ),
    );
  }
}

// ─── Console Tab ─────────────────────────────────────────────────────────────

class _ConsoleTab extends StatefulWidget {
  final ServerModel server;
  const _ConsoleTab({required this.server});

  @override
  State<_ConsoleTab> createState() => _ConsoleTabState();
}

class _ConsoleTabState extends State<_ConsoleTab> {
  final _cmdCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();

  @override
  void dispose() {
    _cmdCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    if (_scrollCtrl.hasClients) {
      _scrollCtrl.animateTo(_scrollCtrl.position.maxScrollExtent, duration: 200.ms, curve: Curves.easeOut);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Console output
        Expanded(
          child: Consumer<ServerProvider>(
            builder: (_, sp, __) {
              WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());
              return Container(
                margin: const EdgeInsets.all(12),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFF0A0E14),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppColors.border),
                ),
                child: SingleChildScrollView(
                  controller: _scrollCtrl,
                  child: SelectableText(
                    sp.consoleLogs.isEmpty ? 'No logs available.' : sp.consoleLogs,
                    style: const TextStyle(
                      color: Color(0xFF4ADE80),
                      fontFamily: 'monospace',
                      fontSize: 11,
                      height: 1.6,
                    ),
                  ),
                ),
              );
            },
          ),
        ),

        // Command input
        Container(
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
          decoration: const BoxDecoration(
            color: AppColors.backgroundCard,
            border: Border(top: BorderSide(color: AppColors.border)),
          ),
          child: Row(
            children: [
              const Text('>', style: TextStyle(color: AppColors.grassGreenLight, fontSize: 16, fontFamily: 'monospace', fontWeight: FontWeight.bold)),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: _cmdCtrl,
                  style: const TextStyle(color: AppColors.textPrimary, fontFamily: 'monospace', fontSize: 13),
                  decoration: const InputDecoration(
                    hintText: 'Enter command...',
                    border: InputBorder.none,
                    contentPadding: EdgeInsets.zero,
                    isDense: true,
                  ),
                  onSubmitted: (_) => _sendCommand(),
                ),
              ),
              Row(
                children: [
                  IconButton(
                    onPressed: () => context.read<ServerProvider>().loadLogs(widget.server.name),
                    icon: const Icon(Icons.refresh, size: 20, color: AppColors.textMuted),
                    tooltip: 'Refresh logs',
                  ),
                  IconButton(
                    onPressed: () { HapticFeedback.mediumImpact(); _sendCommand(); },
                    icon: const Icon(Icons.send, size: 20, color: AppColors.grassGreenLight),
                    tooltip: 'Send command',
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _sendCommand() {
    final cmd = _cmdCtrl.text.trim();
    if (cmd.isEmpty) return;
    context.read<ServerProvider>().sendCommand(widget.server.name, cmd);
    _cmdCtrl.clear();
  }
}

// ─── Settings Tab ─────────────────────────────────────────────────────────────

class _SettingsTab extends StatelessWidget {
  final ServerModel server;
  const _SettingsTab({required this.server});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const SectionHeader(title: 'DANGER ZONE'),
        const SizedBox(height: 10),
        McCard(
          borderColor: AppColors.offline.withOpacity(0.3),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Delete Server', style: TextStyle(color: AppColors.offline, fontWeight: FontWeight.bold, fontSize: 15)),
              const SizedBox(height: 6),
              const Text('This action cannot be undone. All server data will be permanently deleted.', style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
              const SizedBox(height: 16),
              McButton(
                label: 'Delete Server',
                icon: Icons.delete_forever,
                isDanger: true,
                width: double.infinity,
                onPressed: () => _confirmDelete(context),
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _confirmDelete(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.backgroundCard,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: AppColors.offline, width: 1)),
        title: const Text('Delete Server', style: TextStyle(color: AppColors.offline)),
        content: Text('Are you sure you want to delete "${server.name}"? This cannot be undone.', style: const TextStyle(color: AppColors.textSecondary)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel', style: TextStyle(color: AppColors.textMuted))),
          TextButton(
            onPressed: () async {
              await context.read<ServerProvider>().deleteServer(server.name);
              if (context.mounted) { Navigator.pop(context); Navigator.pop(context); }
            },
            child: const Text('Delete', style: TextStyle(color: AppColors.offline, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }
}
