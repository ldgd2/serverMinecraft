import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:file_picker/file_picker.dart';
import 'package:provider/provider.dart';
import 'package:appserve/core/models/server_model.dart';
import 'package:appserve/core/providers/app_providers.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/shared/widgets/mc_button.dart';
import 'package:appserve/shared/widgets/mc_card.dart';
import 'package:appserve/shared/widgets/mc_widgets.dart';
import 'package:appserve/shared/layouts/mc_screen_layout.dart';
import 'package:appserve/shared/utils/mc_dialogs.dart';
import 'package:appserve/shared/widgets/player_head.dart';

class ServerDetailScreen extends StatefulWidget {
  final ServerModel server;
  final int initialTab;

  const ServerDetailScreen({super.key, required this.server, this.initialTab = 0});

  @override
  State<ServerDetailScreen> createState() => _ServerDetailScreenState();
}

class _ServerDetailScreenState extends State<ServerDetailScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  late ServerModel _server;

  @override
  void initState() {
    super.initState();
    _server = widget.server;
    _tabController = TabController(length: 7, vsync: this, initialIndex: widget.initialTab);
    
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final auth = context.read<AuthProvider>();
      final username = auth.user?.username ?? 'Admin';
      context.read<ServerProvider>().selectServer(_server.name, username);
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return McSliverScreenLayout(
      backgroundGradientColors: _server.isOnline
          ? [const Color(0xFF1a3a1a), AppColors.backgroundCard]
          : [AppColors.backgroundElevated, AppColors.backgroundCard],
      headerContent: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          Row(
            children: [
              Container(
                width: 56, height: 56,
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
                    Text(_server.name, style: const TextStyle(color: AppColors.textPrimary, fontSize: 20, fontWeight: FontWeight.bold)),
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
      tabBar: Container(
        color: AppColors.backgroundCard,
        child: TabBar(
          controller: _tabController,
          isScrollable: true,
          indicatorColor: AppColors.grassGreen,
          indicatorWeight: 2,
          labelColor: AppColors.grassGreenLight,
          unselectedLabelColor: AppColors.textMuted,
          labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
          tabs: const [
            Tab(icon: Icon(Icons.info_outline, size: 18), text: 'Info'),
            Tab(icon: Icon(Icons.bolt, size: 18), text: 'Cmds'),
            Tab(icon: Icon(Icons.terminal, size: 18), text: 'Console'),
            Tab(icon: Icon(Icons.chat_bubble_outline, size: 18), text: 'Chat'),
            Tab(icon: Icon(Icons.people_outline, size: 18), text: 'Players'),
            Tab(icon: Icon(Icons.extension_outlined, size: 18), text: 'Mods'),
            Tab(icon: Icon(Icons.settings_outlined, size: 18), text: 'Settings'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _OverviewTab(server: _server),
          _CommandsTab(server: _server),
          _ConsoleTab(server: _server),
          _ChatTab(server: _server),
          _PlayersTab(server: _server),
          _ModsTab(server: _server),
          _SettingsTab(server: _server),
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
        _buildControls(context),
        const SizedBox(height: 20),
        
        if (server.isOnline) ...[
          const SectionHeader(title: 'RESOURCE USAGE'),
          const SizedBox(height: 10),
          McCard(
            child: Column(
              children: [
                _ResourceRow(
                  label: 'CPU Usage',
                  value: '${server.cpuUsage.toStringAsFixed(1)}%',
                  total: '${server.cpuCores} Cores',
                  progress: server.cpuProgress,
                  color: AppColors.diamond,
                ),
                const Divider(color: AppColors.border, height: 24),
                _ResourceRow(
                  label: 'Memory (RAM)',
                  value: server.ramUsageFormatted,
                  total: server.ramFormatted,
                  progress: server.ramProgress,
                  color: AppColors.starting,
                ),
              ],
            ),
          ).animate().fadeIn(),
          const SizedBox(height: 20),
        ],

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
              McInfoRow(
                icon: Icons.verified_user_outlined, 
                label: 'Online Mode', 
                value: server.onlineMode ? 'Enabled' : 'Disabled',
                valueColor: server.onlineMode ? AppColors.online : AppColors.offline,
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildControls(BuildContext context) {
    return Consumer<ServerProvider>(
      builder: (_, sp, __) => Row(
        children: [
          if (server.isOffline)
            Expanded(child: McButton(label: 'Start', icon: Icons.play_arrow, onPressed: () => sp.startServer(server.name)))
          else if (server.isOnline) ...[
            Expanded(child: McButton(label: 'Stop', icon: Icons.stop, isDanger: true, onPressed: () => sp.stopServer(server.name))),
            const SizedBox(width: 8),
            Expanded(child: McButton(label: 'Restart', icon: Icons.refresh, isSecondary: true, onPressed: () => sp.restartServer(server.name))),
          ] else
            const Expanded(child: McButton(label: 'Processing...', isLoading: true, onPressed: null)),
        ],
      ),
    );
  }
}

class _ResourceRow extends StatelessWidget {
  final String label;
  final String value;
  final String total;
  final double progress;
  final Color color;

  const _ResourceRow({required this.label, required this.value, required this.total, required this.progress, required this.color});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: const TextStyle(color: AppColors.textPrimary, fontSize: 13, fontWeight: FontWeight.bold)),
            Text('$value / $total', style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
          ],
        ),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: progress,
            minHeight: 6,
            backgroundColor: AppColors.backgroundOverlay,
            valueColor: AlwaysStoppedAnimation<Color>(color),
          ),
        ),
      ],
    );
  }
}

// ─── Commands Tab ────────────────────────────────────────────────────────────

class _CommandsTab extends StatelessWidget {
  final ServerModel server;
  const _CommandsTab({required this.server});

  @override
  Widget build(BuildContext context) {
    if (!server.isOnline) {
      return const Center(child: Text('Server must be online to use commands', style: TextStyle(color: AppColors.textMuted)));
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const SectionHeader(title: 'COMMUNITY & EVENTS'),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(child: _CmdButton(label: 'Glow Aura', icon: Icons.auto_awesome, color: AppColors.diamond, type: 'global_glow')),
            const SizedBox(width: 10),
            Expanded(child: _CmdButton(label: 'Visual Ray', icon: Icons.bolt, color: AppColors.gold, type: 'visual_lightning')),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(child: _CmdButton(label: 'Announce', icon: Icons.campaign, color: AppColors.emerald, type: 'global_title', params: {'text': 'ANUNCIO IMPORTANTE'})),
            const SizedBox(width: 10),
            Expanded(child: _CmdButton(label: 'Clean Lag', icon: Icons.cleaning_services, isSecondary: true, type: 'purge_items')),
          ],
        ),
        const SizedBox(height: 20),
        const SectionHeader(title: 'SECURITY'),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(child: _CmdButton(label: 'Whitelist ON', icon: Icons.lock, color: AppColors.emerald, type: 'whitelist_on')),
            const SizedBox(width: 10),
            Expanded(child: _CmdButton(label: 'Whitelist OFF', icon: Icons.lock_open, color: AppColors.offline, type: 'whitelist_off')),
          ],
        ),
        const SizedBox(height: 10),
        McCard(
          child: _CmdListTile(label: 'Check Server TPS (Lag)', icon: Icons.speed, type: 'check_tps'),
        ),
      ],
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

  void _scrollToBottom() {
    if (_scrollCtrl.hasClients) {
      _scrollCtrl.jumpTo(_scrollCtrl.position.maxScrollExtent);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: Consumer<ServerProvider>(
            builder: (_, sp, __) {
              WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());
              return Container(
                margin: const EdgeInsets.all(12),
                padding: const EdgeInsets.all(12),
                width: double.infinity,
                decoration: BoxDecoration(
                  color: const Color(0xFF0A0E14),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppColors.border),
                ),
                child: SingleChildScrollView(
                  controller: _scrollCtrl,
                  child: SelectableText(
                    sp.consoleLogs.isEmpty ? 'No logs available.' : sp.consoleLogs,
                    style: const TextStyle(color: Color(0xFF4ADE80), fontFamily: 'monospace', fontSize: 11),
                  ),
                ),
              );
            },
          ),
        ),
        Container(
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
          child: Row(
            children: [
              const Text('>', style: TextStyle(color: AppColors.grassGreenLight, fontWeight: FontWeight.bold)),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: _cmdCtrl,
                  decoration: const InputDecoration(hintText: 'Enter command...', border: InputBorder.none),
                  onSubmitted: (_) => _sendCommand(),
                ),
              ),
              IconButton(onPressed: _sendCommand, icon: const Icon(Icons.send, color: AppColors.grassGreenLight)),
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

// ─── Chat Tab ────────────────────────────────────────────────────────────────

class _ChatTab extends StatefulWidget {
  final ServerModel server;
  const _ChatTab({required this.server});

  @override
  State<_ChatTab> createState() => _ChatTabState();
}

class _ChatTabState extends State<_ChatTab> {
  final _msgCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();

  void _scrollToBottom() {
    if (_scrollCtrl.hasClients) {
      _scrollCtrl.animateTo(_scrollCtrl.position.maxScrollExtent, duration: 200.ms, curve: Curves.easeOut);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: Consumer<ServerProvider>(
            builder: (_, sp, __) {
              WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());
              return ListView.builder(
                controller: _scrollCtrl,
                padding: const EdgeInsets.all(12),
                itemCount: sp.chatMessages.length,
                itemBuilder: (context, index) {
                  final msg = sp.chatMessages[index];
                  final sender = msg['sender'] ?? 'System';
                  final text = msg['message'] ?? '';
                  final isMe = sender == context.read<AuthProvider>().user?.username;
                  
                  return _ChatMessageWidget(
                    sender: sender,
                    content: text,
                    isMe: isMe,
                    isSystem: msg['is_system'] ?? false,
                  );
                },
              );
            },
          ),
        ),
        Container(
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _msgCtrl,
                  decoration: const InputDecoration(hintText: 'Say something...', border: InputBorder.none),
                  onSubmitted: (_) => _sendMessage(),
                ),
              ),
              IconButton(onPressed: _sendMessage, icon: const Icon(Icons.send, color: AppColors.grassGreenLight)),
            ],
          ),
        ),
      ],
    );
  }

  void _sendMessage() {
    final text = _msgCtrl.text.trim();
    if (text.isEmpty) return;
    final username = context.read<AuthProvider>().user?.username ?? 'Admin';
    context.read<ServerProvider>().sendChatMessage(widget.server.name, text, username);
    _msgCtrl.clear();
  }
}

// ─── Players Tab ─────────────────────────────────────────────────────────────

class _PlayersTab extends StatelessWidget {
  final ServerModel server;
  const _PlayersTab({required this.server});

  @override
  Widget build(BuildContext context) {
    return Consumer<ServerProvider>(
      builder: (_, sp, __) {
        final players = sp.onlinePlayers;
        if (players.isEmpty) return const Center(child: Text('No players online', style: TextStyle(color: AppColors.textMuted)));
        
        return ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: players.length,
          separatorBuilder: (_, __) => const SizedBox(height: 8),
          itemBuilder: (context, index) => _PlayerListItem(
            player: players[index],
            onTap: () {},
            onKick: () => sp.sendCommand(server.name, 'kick ${players[index]['name']}'),
            onBan: () => sp.sendCommand(server.name, 'ban ${players[index]['name']}'),
          ),
        );
      },
    );
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
              const Text('Delete Server', style: TextStyle(color: AppColors.offline, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              McButton(
                label: 'Delete Forever', 
                icon: Icons.delete_forever, 
                isDanger: true,
                onPressed: () async {
                  final confirm = await McDialogs.showConfirm(context, title: 'Delete Server', message: 'Are you sure?');
                  if (confirm) context.read<ServerProvider>().deleteServer(server.name);
                },
              ),
            ],
          ),
        ),
      ],
    );
  }
}

// ─── Helper Widgets ──────────────────────────────────────────────────────────

class _CmdButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color? color;
  final bool isSecondary;
  final String type;
  final Map<String, dynamic> params;

  const _CmdButton({required this.label, required this.icon, this.color, this.isSecondary = false, required this.type, this.params = const {}});

  @override
  Widget build(BuildContext context) {
    return McButton(
      label: label, icon: icon, color: color, isSecondary: isSecondary,
      onPressed: () => context.read<ServerProvider>().executeQuickCommand(context.read<ServerProvider>().selectedServer!.name, type, params),
    );
  }
}

class _CmdListTile extends StatelessWidget {
  final String label;
  final IconData icon;
  final String type;

  const _CmdListTile({required this.label, required this.icon, required this.type});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: AppColors.textMuted, size: 20),
      title: Text(label, style: const TextStyle(color: AppColors.textPrimary, fontSize: 14)),
      trailing: const Icon(Icons.chevron_right, size: 16, color: AppColors.border),
      onTap: () => context.read<ServerProvider>().executeQuickCommand(context.read<ServerProvider>().selectedServer!.name, type, {}),
    );
  }
}

class _PlayerListItem extends StatelessWidget {
  final Map<String, dynamic> player;
  final VoidCallback onTap;
  final VoidCallback onKick;
  final VoidCallback onBan;

  const _PlayerListItem({required this.player, required this.onTap, required this.onKick, required this.onBan});

  @override
  Widget build(BuildContext context) {
    final name = player['name'] ?? 'Unknown';
    return McCard(
      onTap: onTap,
      child: Row(
        children: [
          PlayerHead(username: name, size: 40),
          const SizedBox(width: 12),
          Expanded(child: Text(name, style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.textPrimary))),
          IconButton(icon: const Icon(Icons.logout, size: 18, color: AppColors.starting), onPressed: onKick),
          IconButton(icon: const Icon(Icons.block, size: 18, color: AppColors.offline), onPressed: onBan),
        ],
      ),
    );
  }
}

class _ChatMessageWidget extends StatelessWidget {
  final String sender;
  final String content;
  final bool isMe;
  final bool isSystem;

  const _ChatMessageWidget({required this.sender, required this.content, required this.isMe, required this.isSystem});

  @override
  Widget build(BuildContext context) {
    if (isSystem) {
      return Center(
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 4),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
          decoration: BoxDecoration(color: AppColors.backgroundOverlay, borderRadius: BorderRadius.circular(12)),
          child: Text(content, style: const TextStyle(color: AppColors.textMuted, fontSize: 11, fontStyle: FontStyle.italic)),
        ),
      );
    }
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: isMe ? MainAxisAlignment.end : MainAxisAlignment.start,
        children: [
          if (!isMe) PlayerHead(username: sender, size: 24),
          const SizedBox(width: 8),
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: isMe ? AppColors.grassGreen.withOpacity(0.2) : AppColors.backgroundOverlay,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: isMe ? AppColors.grassGreen.withOpacity(0.4) : AppColors.border),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (!isMe) Text(sender, style: const TextStyle(color: AppColors.gold, fontSize: 10, fontWeight: FontWeight.bold)),
                  Text(content, style: const TextStyle(color: AppColors.textPrimary, fontSize: 13)),
                ],
              ),
            ),
          ),
          if (isMe) ...[const SizedBox(width: 8), PlayerHead(username: sender, size: 24)],
        ],
      ),
    );
  }
}

// ─── Mods Tab ────────────────────────────────────────────────────────────────

class _ModsTab extends StatefulWidget {
  final ServerModel server;
  const _ModsTab({required this.server});

  @override
  State<_ModsTab> createState() => _ModsTabState();
}

class _ModsTabState extends State<_ModsTab> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ServerProvider>().loadMods(widget.server.name);
    });
  }

  Future<void> _pickAndUploadMod() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['jar', 'zip'],
    );

    if (result != null && result.files.single.path != null) {
      final sp = context.read<ServerProvider>();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Uploading mod...'), duration: Duration(seconds: 2)),
      );
      try {
        await sp.uploadMod(widget.server.name, result.files.single.path!);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Mod uploaded successfully!'), backgroundColor: AppColors.online),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Upload failed: \$e'), backgroundColor: AppColors.offline),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<ServerProvider>(
      builder: (_, sp, __) {
        final mods = sp.installedMods;
        
        return Scaffold(
          backgroundColor: Colors.transparent,
          body: mods.isEmpty && !sp.isLoadingMods
              ? const Center(child: Text('No mods installed', style: TextStyle(color: AppColors.textMuted)))
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: mods.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final mod = mods[index];
                    final name = mod['name'] ?? 'Unknown Mod';
                    final size = mod['size_formatted'] ?? '';
                    final isZip = name.endsWith('.zip');

                    return McCard(
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: (isZip ? AppColors.gold : AppColors.diamond).withOpacity(0.1),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Icon(
                              isZip ? Icons.folder_zip_outlined : Icons.extension_outlined,
                              color: isZip ? AppColors.gold : AppColors.diamond,
                              size: 20,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(name, 
                                  style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.textPrimary, fontSize: 13),
                                  maxLines: 1, overflow: TextOverflow.ellipsis,
                                ),
                                if (size.isNotEmpty)
                                  Text(size, style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
                              ],
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete_outline, size: 20, color: AppColors.offline),
                            onPressed: () async {
                              final confirm = await McDialogs.showConfirm(
                                context, 
                                title: 'Delete Mod', 
                                message: 'Are you sure you want to delete "\$name"?',
                                isDanger: true,
                              );
                              if (confirm) {
                                await sp.deleteMod(widget.server.name, name);
                              }
                            },
                          ),
                        ],
                      ),
                    );
                  },
                ),
          floatingActionButton: FloatingActionButton(
            onPressed: _pickAndUploadMod,
            backgroundColor: AppColors.grassGreen,
            child: const Icon(Icons.add, color: Colors.white),
          ),
        );
      },
    );
  }
}
