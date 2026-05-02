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

class ServerDetailScreen extends StatefulWidget {
  final ServerModel server;
  final int initialTab;

  const ServerDetailScreen(
      {super.key, required this.server, this.initialTab = 0});

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
    _tabController =
        TabController(length: 6, vsync: this, initialIndex: widget.initialTab);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final username = context.read<AuthProvider>().user?.username ?? 'Admin';
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
      tabBar: _buildTabBar(),
      body: TabBarView(
        controller: _tabController,
        children: [
          _OverviewTab(server: _server),
          _ConsoleTab(server: _server),
          _ChatTab(server: _server),
          _PlayersTab(server: _server),
          _ModsTab(server: _server),
          _SettingsTab(server: _server),
        ],
      ),
    );
  }

  Widget _buildTabBar() {
    return Container(
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
          Tab(icon: Icon(Icons.info_outline, size: 18), text: 'Overview'),
          Tab(icon: Icon(Icons.terminal, size: 18), text: 'Console'),
          Tab(icon: Icon(Icons.chat_bubble_outline, size: 18), text: 'Chat'),
          Tab(icon: Icon(Icons.people_outline, size: 18), text: 'Players'),
          Tab(icon: Icon(Icons.extension_outlined, size: 18), text: 'Mods'),
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
        
        if (server.isOnline) ...[
          const SectionHeader(title: 'RESOURCE USAGE'),
          const SizedBox(height: 10),
          McCard(
            child: Column(
              children: [
                _DetailResourceRow(
                  label: 'CPU Usage',
                  value: '${server.cpuUsage.toStringAsFixed(1)}%',
                  total: '${server.cpuCores.toStringAsFixed(1)} Cores',
                  progress: server.cpuProgress,
                  color: AppColors.diamond,
                ),
                const Divider(color: AppColors.border, height: 24),
                _DetailResourceRow(
                  label: 'Memory (RAM)',
                  value: server.ramUsageFormatted,
                  total: server.ramFormatted,
                  progress: server.ramProgress,
                  color: AppColors.starting,
                ),
                const Divider(color: AppColors.border, height: 24),
                _DetailResourceRow(
                  label: 'Disk Space',
                  value: server.diskUsageFormatted,
                  total: server.diskFormatted,
                  progress: server.diskProgress,
                  color: AppColors.textMuted,
                ),
              ],
            ),
          ).animate().fadeIn(duration: 350.ms),
          const SizedBox(height: 20),
        ],

        const SectionHeader(title: 'SERVER INFO'),
        const SizedBox(height: 10),
        McCard(
          child: Column(
            children: [
              McInfoRow(
                  icon: Icons.dns_rounded, label: 'Name', value: server.name),
              const Divider(color: AppColors.border, height: 16),
              McInfoRow(
                  icon: Icons.gamepad_outlined,
                  label: 'Version',
                  value: server.version),
              const Divider(color: AppColors.border, height: 16),
              McInfoRow(
                  icon: Icons.wifi,
                  label: 'Port',
                  value: server.port.toString()),
              const Divider(color: AppColors.border, height: 16),
              McInfoRow(
                  icon: Icons.memory, label: 'RAM', value: server.ramFormatted),
              const Divider(color: AppColors.border, height: 16),
              McInfoRow(
                  icon: Icons.people_outline,
                  label: 'Max Players',
                  value: server.maxPlayers.toString()),
              const Divider(color: AppColors.border, height: 16),
              McInfoRow(
                  icon: Icons.verified_user_outlined,
                  label: 'Online Mode',
                  value: server.onlineMode ? 'Enabled' : 'Disabled',
                  valueColor:
                      server.onlineMode ? AppColors.online : AppColors.offline),
            ],
          ),
        ).animate().fadeIn(delay: 100.ms),
        if (server.motd != null) ...[
          const SizedBox(height: 16),
          const SectionHeader(title: 'MOTD'),
          const SizedBox(height: 10),
          McCard(
            child: Text(server.motd!,
                style: const TextStyle(
                    color: AppColors.grassGreenLight,
                    fontFamily: 'monospace',
                    fontSize: 14)),
          ).animate().fadeIn(delay: 200.ms),
        ],
      ],
    );
  }

  Widget _buildControls(BuildContext context) {
    return Consumer<ServerProvider>(
      builder: (_, sp, __) => Row(
        children: [
          if (server.isOffline)
            Expanded(
                child: McButton(
                    label: 'Start',
                    icon: Icons.play_arrow,
                    onPressed: () async {
                      await sp.startServer(server.name);
                    }))
          else if (server.isOnline) ...[
            Expanded(
                child: McButton(
                    label: 'Stop',
                    icon: Icons.stop,
                    isDanger: true,
                    onPressed: () async {
                      await sp.stopServer(server.name);
                    })),
            const SizedBox(width: 8),
            Expanded(
                child: McButton(
                    label: 'Restart',
                    icon: Icons.refresh,
                    isSecondary: true,
                    onPressed: () async {
                      await sp.restartServer(server.name);
                    })),
          ] else if (server.isRestarting) ...[
            const Expanded(
                child: McButton(
                    label: 'Restarting...', isLoading: true, onPressed: null)),
          ] else if (server.isStopping) ...[
            const Expanded(
                child: McButton(
                    label: 'Stopping...', isLoading: true, onPressed: null)),
          ] else if (server.isStarting) ...[
             Expanded(
                child: McButton(
                    label: 'Starting...', isLoading: true, onPressed: null)),
             const SizedBox(width: 8),
             IconButton(
               onPressed: () async {
                 final confirm = await showDialog<bool>(
                   context: context,
                   builder: (context) => AlertDialog(
                     title: const Text('Force Stop?'),
                     content: const Text('The server is stuck starting. Do you want to force kill it?'),
                     actions: [
                       TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
                       TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Force Kill')),
                     ],
                   ),
                 );
                 if (confirm == true) {
                   await sp.stopServer(server.name);
                 }
               },
               icon: Icon(Icons.cancel_outlined, color: Colors.redAccent),
               tooltip: 'Force Stop',
             ),
          ] else
            const Expanded(
                child: McButton(
                    label: 'Processing...', isLoading: true, onPressed: null)),
        ],
      ),
    );
  }
}

class _DetailResourceRow extends StatelessWidget {
  final String label;
  final String value;
  final String total;
  final double progress;
  final Color color;

  const _DetailResourceRow({
    required this.label,
    required this.value,
    required this.total,
    required this.progress,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label,
                style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 13,
                    fontWeight: FontWeight.bold)),
            Text('$value / $total',
                style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12,
                    fontWeight: FontWeight.w500)),
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
  bool _isAtBottom = true;
  bool _showScrollFab = false;

  @override
  void initState() {
    super.initState();
    _scrollCtrl.addListener(_scrollListener);
  }

  void _scrollListener() {
    if (!_scrollCtrl.hasClients) return;
    
    // Check if we are near the bottom (within 50 pixels)
    final atBottom = _scrollCtrl.position.pixels >= 
                     (_scrollCtrl.position.maxScrollExtent - 50);
    
    if (atBottom != _isAtBottom) {
      setState(() {
        _isAtBottom = atBottom;
        if (_isAtBottom) _showScrollFab = false;
      });
    }

    // Show FAB if we are not at bottom and there's space to scroll
    final showFab = _scrollCtrl.position.pixels < 
                   (_scrollCtrl.position.maxScrollExtent - 100);
    if (showFab != _showScrollFab) {
      setState(() => _showScrollFab = showFab);
    }
  }

  @override
  void dispose() {
    _cmdCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _scrollToBottom({bool force = false}) {
    if (_scrollCtrl.hasClients && (_isAtBottom || force)) {
      _scrollCtrl.animateTo(_scrollCtrl.position.maxScrollExtent,
          duration: 200.ms, curve: Curves.easeOut);
    }
  }

  void _copyAllLogs(String logs) {
    if (logs.isEmpty) return;
    Clipboard.setData(ClipboardData(text: logs));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Logs copied to clipboard'),
        duration: Duration(seconds: 1),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Console output
        Expanded(
          child: Consumer<ServerProvider>(
            builder: (_, sp, __) {
              // Only auto-scroll if user was already at the bottom
              WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());
              
              return Stack(
                children: [
                  Container(
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
                      physics: const AlwaysScrollableScrollPhysics(),
                      child: SelectableText(
                        sp.consoleLogs.isEmpty
                            ? 'No logs available.'
                            : sp.consoleLogs,
                        style: const TextStyle(
                          color: Color(0xFF4ADE80),
                          fontFamily: 'monospace',
                          fontSize: 11,
                          height: 1.6,
                        ),
                      ),
                    ),
                  ),
                  if (_showScrollFab)
                    Positioned(
                      right: 25,
                      bottom: 25,
                      child: FloatingActionButton.small(
                        onPressed: () => _scrollToBottom(force: true),
                        backgroundColor: AppColors.grassGreenLight.withOpacity(0.8),
                        child: const Icon(Icons.arrow_downward, color: Colors.white),
                      ).animate().fadeIn().scale(),
                    ),
                ],
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
              const Text('>',
                  style: TextStyle(
                      color: AppColors.grassGreenLight,
                      fontSize: 16,
                      fontFamily: 'monospace',
                      fontWeight: FontWeight.bold)),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: _cmdCtrl,
                  style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontFamily: 'monospace',
                      fontSize: 13),
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
                    onPressed: () => _copyAllLogs(context.read<ServerProvider>().consoleLogs),
                    icon: const Icon(Icons.copy_all,
                        size: 20, color: AppColors.textMuted),
                    tooltip: 'Copy all logs',
                  ),
                  IconButton(
                    onPressed: () => context
                        .read<ServerProvider>()
                        .loadLogs(widget.server.name),
                    icon: const Icon(Icons.refresh,
                        size: 20, color: AppColors.textMuted),
                    tooltip: 'Refresh logs',
                  ),
                  IconButton(
                    onPressed: () {
                      HapticFeedback.mediumImpact();
                      _sendCommand();
                    },
                    icon: const Icon(Icons.send,
                        size: 20, color: AppColors.grassGreenLight),
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

  void _sendCommand() async {
    final cmd = _cmdCtrl.text.trim();
    if (cmd.isEmpty) return;
    
    try {
      await context.read<ServerProvider>().sendCommand(widget.server.name, cmd);
      _cmdCtrl.clear();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to send command: $e'),
            backgroundColor: AppColors.offline,
          ),
        );
      }
    }
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
              const Text('Delete Server',
                  style: TextStyle(
                      color: AppColors.offline,
                      fontWeight: FontWeight.bold,
                      fontSize: 15)),
              const SizedBox(height: 6),
              const Text(
                  'This action cannot be undone. All server data will be permanently deleted.',
                  style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
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

  void _confirmDelete(BuildContext context) async {
    final confirmed = await McDialogs.showConfirm(
      context,
      title: 'Delete Server',
      message: 'Are you sure you want to delete "${server.name}"? This cannot be undone.',
      confirmLabel: 'Delete',
      isDanger: true,
    );

    if (confirmed) {
      await context.read<ServerProvider>().deleteServer(server.name);
      if (context.mounted) {
        Navigator.pop(context);
      }
    }
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
  static final int _sessionSalt = DateTime.now().millisecondsSinceEpoch;

  Color _getSenderColor(String? name, bool isAdmin) {
    if (isAdmin) return AppColors.gold;
    if (name == null || name.isEmpty) return AppColors.textMuted;
    
    final List<Color> colors = [
      AppColors.diamond,
      const Color(0xFFF472B6), // Pink
      const Color(0xFFA78BFA), // Purple
      const Color(0xFFFB923C), // Orange
      const Color(0xFF2DD4BF), // Teal
      const Color(0xFF60A5FA), // Blue
      const Color(0xFFF87171), // Red
      AppColors.emerald,
    ];

    int hash = _sessionSalt;
    for (int i = 0; i < name.length; i++) {
      hash = name.codeUnitAt(i) + ((hash << 5) - hash);
    }
    return colors[hash.abs() % colors.length];
  }

  @override
  void dispose() {
    _msgCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    if (_scrollCtrl.hasClients) {
      _scrollCtrl.animateTo(_scrollCtrl.position.maxScrollExtent,
          duration: 200.ms, curve: Curves.easeOut);
    }
  }

  void _sendMessage() {
    final msg = _msgCtrl.text.trim();
    if (msg.isEmpty) return;

    final auth = context.read<AuthProvider>();
    final username = auth.user?.username ?? 'Admin';

    context.read<ServerProvider>().sendChatMessage(widget.server.name, msg, username);
    _msgCtrl.clear();
    HapticFeedback.lightImpact();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: Consumer<ServerProvider>(
            builder: (_, sp, __) {
              WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());

              if (sp.chatMessages.isEmpty) {
                return const Center(child: Text('No messages yet', style: TextStyle(color: AppColors.textMuted)));
              }

              return ListView.builder(
                controller: _scrollCtrl,
                padding: const EdgeInsets.all(12),
                itemCount: sp.chatMessages.length,
                itemBuilder: (context, index) {
                  final msg = sp.chatMessages[index];
                  final chatType = msg['chat_type'] ?? (msg['is_system'] == true ? 'system' : 'received');
                  final sender = msg['sender']?.toString() ?? (chatType == 'system' ? 'System' : 'Unknown');
                  final text = msg['message']?.toString() ?? '';
                  
                  // System / Join / Leave messages (Centered)
                  if (chatType == 'join' || chatType == 'leave' || chatType == 'system' || chatType == 'achievement') {
                    IconData icon = Icons.info_outline;
                    Color iconColor = AppColors.textMuted;
                    
                    if (chatType == 'join') {
                      icon = Icons.login_rounded;
                      iconColor = AppColors.online;
                    } else if (chatType == 'leave') {
                      icon = Icons.logout_rounded;
                      iconColor = AppColors.offline;
                    } else if (chatType == 'achievement') {
                      icon = Icons.emoji_events_outlined;
                      iconColor = AppColors.gold;
                    }

                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      child: Center(
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: AppColors.backgroundOverlay.withOpacity(0.3),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: AppColors.border.withOpacity(0.5)),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(icon, size: 12, color: iconColor),
                              const SizedBox(width: 6),
                              Text(
                                text,
                                style: TextStyle(
                                  color: iconColor.withOpacity(0.8),
                                  fontSize: 11,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  }

                  final currentUsername = context.read<AuthProvider>().user?.username;
                  final isMe = chatType == 'sent' && sender == currentUsername;
                  final isOtherAdmin = chatType == 'sent' && !isMe;

                  return Align(
                    alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
                    child: Container(
                      margin: EdgeInsets.fromLTRB(isMe ? 60 : 0, 4, isMe ? 0 : 60, 4),
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      decoration: BoxDecoration(
                        color: isMe ? AppColors.grassGreen.withOpacity(0.15) : AppColors.backgroundElevated,
                        borderRadius: BorderRadius.only(
                          topLeft: const Radius.circular(16),
                          topRight: const Radius.circular(16),
                          bottomLeft: Radius.circular(isMe ? 16 : 4),
                          bottomRight: Radius.circular(isMe ? 4 : 16),
                        ),
                        border: Border.all(
                          color: isMe ? AppColors.grassGreen.withOpacity(0.4) : AppColors.border,
                          width: 1,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.1),
                            blurRadius: 4,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: Column(
                        crossAxisAlignment: isMe ? CrossAxisAlignment.end : CrossAxisAlignment.start,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          if (!isMe)
                            Padding(
                              padding: const EdgeInsets.only(bottom: 4),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Text(
                                    sender,
                                    style: TextStyle(
                                      color: _getSenderColor(sender, isOtherAdmin),
                                      fontWeight: FontWeight.bold,
                                      fontSize: 11,
                                      letterSpacing: 0.5,
                                    ),
                                  ),
                                  if (isOtherAdmin) ...[
                                    const SizedBox(width: 4),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                                      decoration: BoxDecoration(
                                        color: AppColors.gold.withOpacity(0.2),
                                        borderRadius: BorderRadius.circular(4),
                                        border: Border.all(color: AppColors.gold.withOpacity(0.5), width: 0.5),
                                      ),
                                      child: const Text(
                                        'ADMIN',
                                        style: TextStyle(
                                          color: AppColors.gold,
                                          fontSize: 7,
                                          fontWeight: FontWeight.w900,
                                        ),
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            ),
                          Text(
                            text,
                            style: TextStyle(
                              color: isMe ? AppColors.grassGreenGlow : AppColors.textPrimary,
                              fontSize: 14,
                              height: 1.3,
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              );
            },
          ),
        ),
        Container(
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
          decoration: const BoxDecoration(
            color: AppColors.backgroundCard,
            border: Border(top: BorderSide(color: AppColors.border)),
          ),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _msgCtrl,
                  style: const TextStyle(color: AppColors.textPrimary, fontSize: 14),
                  decoration: const InputDecoration(
                    hintText: 'Type a message...',
                    border: InputBorder.none,
                    isDense: true,
                  ),
                  onSubmitted: (_) => _sendMessage(),
                ),
              ),
              IconButton(
                onPressed: _sendMessage,
                icon: const Icon(Icons.send, color: AppColors.gold),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

// ─── Players Tab ─────────────────────────────────────────────────────────────

class _PlayersTab extends StatefulWidget {
  final ServerModel server;
  const _PlayersTab({required this.server});

  @override
  State<_PlayersTab> createState() => _PlayersTabState();
}

class _PlayersTabState extends State<_PlayersTab> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ServerProvider>().loadPlayers(widget.server.name);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<ServerProvider>(
      builder: (context, sp, child) {
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            SectionHeader(
              title: 'ONLINE PLAYERS (${sp.onlinePlayers.length})',
              trailing: IconButton(
                icon: const Icon(Icons.refresh, size: 20, color: AppColors.textSecondary),
                onPressed: () => sp.loadPlayers(widget.server.name),
              ),
            ),
            const SizedBox(height: 8),
            if (sp.onlinePlayers.isEmpty)
              const McCard(child: Center(child: Padding(
                padding: EdgeInsets.all(20.0),
                child: Text('No players online', style: TextStyle(color: AppColors.textMuted)),
              )))
            else
              ...sp.onlinePlayers.map((p) {
                final playerData = p is Map ? p : {'username': p.toString()};
                final username = playerData['username'] ?? p.toString();
                return _PlayerListItem(
                  player: playerData,
                  isBanned: false,
                  onTap: () => _showPlayerDetail(context, widget.server.name, playerData),
                  onKick: () => _handleKick(context, sp, widget.server.name, username),
                  onBan: () => _showBanDialog(context, sp, widget.server.name, username),
                );
              }),

            const SizedBox(height: 24),
            SectionHeader(title: 'BANNED PLAYERS (${sp.bannedUsers.length})'),
            const SizedBox(height: 8),
            if (sp.bannedUsers.isEmpty)
              const McCard(child: Center(child: Padding(
                padding: EdgeInsets.all(20.0),
                child: Text('No banned players', style: TextStyle(color: AppColors.textMuted)),
              )))
            else
              ...sp.bannedUsers.map((p) {
                final playerData = p is Map ? p : {'username': p.toString()};
                final username = playerData['username'] ?? playerData['name'] ?? p.toString();
                return _PlayerListItem(
                  player: playerData,
                  isBanned: true,
                  onUnban: () => sp.unbanPlayer(widget.server.name, username),
                );
              }),
          ],
        );
      },
    );
  }

  void _handleKick(BuildContext context, ServerProvider sp, String serverName, String username) async {
    final confirmed = await McDialogs.showConfirm(
      context,
      title: 'Kick Player',
      message: 'Are you sure you want to kick $username?',
      confirmLabel: 'Kick',
      isDanger: true,
    );
    if (confirmed) {
      await sp.kickPlayer(serverName, username);
    }
  }

  void _showPlayerDetail(BuildContext context, String serverName, Map<dynamic, dynamic> player) {
    final username = player['username'] ?? 'Unknown';
    final uuid = player['uuid'] ?? 'Unknown';
    final ip = player['ip'] ?? 'Unknown';
    final joined = player['joined_at'] ?? 'Unknown';

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.backgroundCard,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: AppColors.border)),
        title: Row(
          children: [
            const Icon(Icons.person, color: AppColors.grassGreenLight),
            const SizedBox(width: 10),
            Text(username, style: const TextStyle(color: AppColors.textPrimary)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _DetailRow(label: 'UUID', value: uuid),
            _DetailRow(label: 'IP Address', value: ip),
            _DetailRow(label: 'Joined At', value: joined),
            const SizedBox(height: 16),
            const Text('History', style: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold, fontSize: 14)),
            const SizedBox(height: 8),
            Container(
              height: 100,
              width: double.maxFinite,
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(color: AppColors.backgroundDeep, borderRadius: BorderRadius.circular(8)),
              child: const Center(child: Text('Audit history loading...', style: TextStyle(color: AppColors.textMuted, fontSize: 12))),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Close', style: TextStyle(color: AppColors.textMuted))),
        ],
      ),
    );
  }

  void _showBanDialog(BuildContext context, ServerProvider sp, String serverName, String username) {
    String reason = 'Banned by admin';
    bool isPermanent = true;
    DateTime? selectedDate;
    TimeOfDay? selectedTime;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          backgroundColor: AppColors.backgroundCard,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: AppColors.offline)),
          title: Text('Ban $username', style: const TextStyle(color: AppColors.offline)),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: const InputDecoration(labelText: 'Reason', labelStyle: TextStyle(color: AppColors.textMuted)),
                  onChanged: (v) => reason = v,
                ),
                const SizedBox(height: 16),
                SwitchListTile(
                  title: const Text('Permanent Ban', style: TextStyle(color: AppColors.textPrimary)),
                  value: isPermanent,
                  activeColor: AppColors.offline,
                  onChanged: (v) => setState(() => isPermanent = v),
                ),
                if (!isPermanent) ...[
                  const SizedBox(height: 8),
                  ListTile(
                    title: Text(selectedDate == null ? 'Select Expiry Date' : 'Expires: ${selectedDate!.toString().split(' ')[0]}'),
                    trailing: const Icon(Icons.calendar_today, color: AppColors.gold),
                    onTap: () async {
                      final date = await showDatePicker(
                        context: context,
                        initialDate: DateTime.now().add(const Duration(days: 1)),
                        firstDate: DateTime.now(),
                        lastDate: DateTime.now().add(const Duration(days: 3650)),
                      );
                      if (date != null) setState(() => selectedDate = date);
                    },
                  ),
                  ListTile(
                    title: Text(selectedTime == null ? 'Select Expiry Time' : 'Time: ${selectedTime!.format(context)}'),
                    trailing: const Icon(Icons.access_time, color: AppColors.gold),
                    onTap: () async {
                      final time = await showTimePicker(context: context, initialTime: const TimeOfDay(hour: 0, minute: 0));
                      if (time != null) setState(() => selectedTime = time);
                    },
                  ),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
            McButton(
              label: 'Confirm Ban',
              isDanger: true,
              onPressed: () {
                String? expires;
                if (!isPermanent && selectedDate != null) {
                  final hr = selectedTime?.hour ?? 0;
                  final mn = selectedTime?.minute ?? 0;
                  final dt = DateTime(selectedDate!.year, selectedDate!.month, selectedDate!.day, hr, mn);
                  // Format: 2026-05-01 16:30:00 +0000
                  expires = "${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')} "
                            "${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}:00 +0000";
                }
                sp.banPlayer(serverName, username, reason: reason, expires: expires);
                Navigator.pop(context);
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  final String label, value;
  const _DetailRow({required this.label, required this.value});
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label, style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
        Text(value, style: const TextStyle(color: AppColors.textPrimary, fontSize: 13, fontFamily: 'monospace')),
      ]),
    );
  }
}

class _PlayerListItem extends StatelessWidget {
  final Map<dynamic, dynamic> player;
  final bool isBanned;
  final VoidCallback? onTap;
  final VoidCallback? onKick;
  final VoidCallback? onBan;
  final VoidCallback? onUnban;

  const _PlayerListItem({
    required this.player,
    this.isBanned = false,
    this.onTap,
    this.onKick,
    this.onBan,
    this.onUnban,
  });

  @override
  Widget build(BuildContext context) {
    final name = player['username']?.toString() ?? player['name']?.toString() ?? 'Unknown';
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: McCard(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: AppColors.backgroundOverlay,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.person, color: AppColors.textSecondary),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(name, style: const TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold)),
                    if (!isBanned && player['ip'] != null)
                      Text(player['ip'].toString(), style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
                  ],
                ),
              ),
              if (isBanned)
                McButton(
                  label: 'Unban',
                  icon: Icons.undo,
                  isSecondary: true,
                  onPressed: onUnban,
                )
              else ...[
                IconButton(
                  icon: const Icon(Icons.logout, color: AppColors.gold, size: 20),
                  onPressed: onKick,
                  tooltip: 'Kick',
                ),
                IconButton(
                  icon: const Icon(Icons.gavel, color: AppColors.offline, size: 20),
                  onPressed: onBan,
                  tooltip: 'Ban',
                ),
              ]
            ],
          ),
        ),
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

  @override
  Widget build(BuildContext context) {
    return Consumer<ServerProvider>(
      builder: (context, sp, child) {
        if (sp.isLoadingMods && sp.installedMods.isEmpty) {
          return const Center(child: CircularProgressIndicator(color: AppColors.grassGreen));
        }

        return RefreshIndicator(
          onRefresh: () => sp.loadMods(widget.server.name),
          color: AppColors.grassGreen,
          backgroundColor: AppColors.backgroundCard,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              SectionHeader(
                title: 'INSTALLED MODS (${sp.installedMods.length})',
                trailing: IconButton(
                  icon: const Icon(Icons.upload_file, color: AppColors.gold),
                  onPressed: () => _pickAndUploadMod(context, sp),
                  tooltip: 'Upload Mod',
                ),
              ),
              const SizedBox(height: 12),
              if (sp.installedMods.isEmpty && !sp.isLoadingMods)
                const McCard(
                  child: Center(
                    child: Padding(
                      padding: EdgeInsets.all(40.0),
                      child: Column(
                        children: [
                          Icon(Icons.extension_off_outlined, size: 48, color: AppColors.textMuted),
                          SizedBox(height: 16),
                          Text('No mods found in the mods folder', style: TextStyle(color: AppColors.textMuted)),
                        ],
                      ),
                    ),
                  ),
                )
              else
                ...sp.installedMods.map((mod) => _ModListItem(
                      mod: mod,
                      onDelete: () => _confirmDelete(context, sp, mod['filename']),
                      onRename: () => _showRenameDialog(context, sp, mod['filename']),
                    )),
              const SizedBox(height: 80), // Space for fab-like interaction
            ],
          ),
        );
      },
    );
  }

  void _pickAndUploadMod(BuildContext context, ServerProvider sp) async {
    try {
      // 1. Just call the picker directly. 
      // Modern Android (11, 12, 13, 14) doesn't need storage permissions for the SYSTEM PICKER.
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.any,
        allowMultiple: false,
      );

      if (result != null && result.files.single.path != null) {
        final filePath = result.files.single.path!;
        final fileName = result.files.single.name;
        
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Uploading $fileName...'),
              backgroundColor: AppColors.gold,
              duration: const Duration(seconds: 2),
            ),
          );
        }

        // 2. Perform upload
        await sp.uploadMod(widget.server.name, filePath);

        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('✓ $fileName uploaded successfully!'),
              backgroundColor: AppColors.grassGreen,
            ),
          );
        }
      }
    } catch (e) {
      if (context.mounted) {
        // If it really was a permission issue, the catch will show it here
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $e'),
            backgroundColor: AppColors.offline,
          ),
        );
      }
    }
  }

  void _confirmDelete(BuildContext context, ServerProvider sp, String filename) async {
    final confirmed = await McDialogs.showConfirm(
      context,
      title: 'Delete Mod',
      message: 'Are you sure you want to permanently delete "$filename"?',
      confirmLabel: 'Delete',
      isDanger: true,
    );
    if (confirmed) {
      await sp.deleteMod(widget.server.name, filename);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Mod deleted successfully')));
      }
    }
  }

  void _showRenameDialog(BuildContext context, ServerProvider sp, String filename) {
    final ctrl = TextEditingController(text: filename);
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.backgroundCard,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: AppColors.border)),
        title: const Text('Rename/Disable Mod', style: TextStyle(color: AppColors.textPrimary, fontSize: 18)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Renaming to .disabled will deactivate the mod.', style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
            const SizedBox(height: 16),
            TextField(
              controller: ctrl,
              style: const TextStyle(color: AppColors.textPrimary),
              decoration: InputDecoration(
                labelText: 'Filename',
                labelStyle: const TextStyle(color: AppColors.textMuted),
                filled: true,
                fillColor: AppColors.backgroundDeep,
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide.none),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel', style: TextStyle(color: AppColors.textMuted))),
          TextButton(
            onPressed: () {
              sp.renameMod(widget.server.name, filename, ctrl.text);
              Navigator.pop(context);
            },
            child: const Text('Apply', style: TextStyle(color: AppColors.gold, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }
}

class _ModListItem extends StatelessWidget {
  final dynamic mod;
  final VoidCallback onDelete;
  final VoidCallback onRename;

  const _ModListItem({required this.mod, required this.onDelete, required this.onRename});

  @override
  Widget build(BuildContext context) {
    final filename = mod['filename'].toString();
    final isFolder = mod['is_directory'] == true;
    final isDisabled = filename.endsWith('.disabled') || filename.endsWith('.bak') || filename.endsWith('.off');
    
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: McCard(
        child: ListTile(
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
          leading: Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: isFolder ? AppColors.gold.withOpacity(0.1) : (isDisabled ? AppColors.textMuted.withOpacity(0.05) : AppColors.diamond.withOpacity(0.1)),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(
              isFolder ? Icons.folder_rounded : Icons.extension_rounded,
              color: isFolder ? AppColors.gold : (isDisabled ? AppColors.textMuted : AppColors.diamond),
              size: 20,
            ),
          ),
          title: Text(
            mod['name']?.toString() ?? mod['filename']?.toString() ?? 'Unknown',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              color: isDisabled ? AppColors.textMuted : AppColors.textPrimary,
              fontSize: 14,
              fontWeight: FontWeight.bold,
              decoration: isDisabled ? TextDecoration.lineThrough : null,
            ),
          ),
          subtitle: Row(
            children: [
              Text(
                isFolder ? 'Folder' : '${(mod['size'] / 1024 / 1024).toStringAsFixed(2)} MB',
                style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
              ),
              if (isDisabled) ...[
                const SizedBox(width: 8),
                const Text('• DISABLED', style: TextStyle(color: AppColors.offline, fontSize: 10, fontWeight: FontWeight.bold)),
              ]
            ],
          ),
          trailing: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              IconButton(
                icon: const Icon(Icons.drive_file_rename_outline_rounded, size: 20, color: AppColors.textMuted),
                onPressed: onRename,
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
              ),
              const SizedBox(width: 12),
              IconButton(
                icon: const Icon(Icons.delete_sweep_rounded, size: 20, color: AppColors.offline),
                onPressed: onDelete,
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
