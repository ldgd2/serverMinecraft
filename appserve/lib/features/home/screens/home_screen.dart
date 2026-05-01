import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import 'package:appserve/core/providers/app_providers.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/shared/widgets/mc_card.dart';
import 'package:appserve/shared/widgets/mc_widgets.dart';
import 'package:appserve/features/servers/screens/servers_screen.dart';
import 'package:appserve/features/system/screens/system_screen.dart';
import 'package:appserve/features/settings/screens/settings_screen.dart';
import 'package:appserve/features/system/screens/version_manager_screen.dart';
import 'package:appserve/shared/utils/mc_dialogs.dart';
import 'package:appserve/shared/widgets/mc_cards.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

  final _screens = const [
    _DashboardTab(),
    ServersScreen(),
    SystemScreen(),
    SettingsScreen(),
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ServerProvider>().loadServers();
      context.read<ServerProvider>().loadSystemStats();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _selectedIndex, children: _screens),
      bottomNavigationBar: _buildBottomNav(),
    );
  }

  Widget _buildBottomNav() {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.backgroundCard,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _NavItem(icon: Icons.dashboard_outlined, activeIcon: Icons.dashboard, label: 'Dashboard', index: 0, selected: _selectedIndex, onTap: (i) => setState(() => _selectedIndex = i)),
              _NavItem(icon: Icons.dns_outlined, activeIcon: Icons.dns, label: 'Servers', index: 1, selected: _selectedIndex, onTap: (i) => setState(() => _selectedIndex = i)),
              _NavItem(icon: Icons.monitor_heart_outlined, activeIcon: Icons.monitor_heart, label: 'System', index: 2, selected: _selectedIndex, onTap: (i) => setState(() => _selectedIndex = i)),
              _NavItem(icon: Icons.settings_outlined, activeIcon: Icons.settings, label: 'Settings', index: 3, selected: _selectedIndex, onTap: (i) => setState(() => _selectedIndex = i)),
            ],
          ),
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  final IconData icon;
  final IconData activeIcon;
  final String label;
  final int index;
  final int selected;
  final void Function(int) onTap;

  const _NavItem({required this.icon, required this.activeIcon, required this.label, required this.index, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final isSelected = index == selected;
    return GestureDetector(
      onTap: () => onTap(index),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.grassGreen.withValues(alpha: 0.15) : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(isSelected ? activeIcon : icon,
                size: 22, color: isSelected ? AppColors.grassGreenLight : AppColors.textMuted),
            const SizedBox(height: 3),
            Text(label,
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                  color: isSelected ? AppColors.grassGreenLight : AppColors.textMuted,
                )),
          ],
        ),
      ),
    );
  }
}

class _DashboardTab extends StatelessWidget {
  const _DashboardTab();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: Container(
        decoration: const BoxDecoration(gradient: AppColors.backgroundGradient),
        child: SafeArea(
          child: CustomScrollView(
            slivers: [
              _buildAppBar(context),
              SliverPadding(
                padding: const EdgeInsets.all(16),
                sliver: SliverList(
                  delegate: SliverChildListDelegate([
                    _buildWelcomeBanner(context),
                    const SizedBox(height: 20),
                    _buildStatCards(context),
                    const SizedBox(height: 20),
                    const SectionHeader(title: 'QUICK ACTIONS'),
                    const SizedBox(height: 12),
                    _buildQuickActions(context),
                    const SizedBox(height: 20),
                    const SectionHeader(title: 'RECENT SERVERS'),
                    const SizedBox(height: 12),
                    _buildRecentServers(context),
                  ]),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  SliverAppBar _buildAppBar(BuildContext context) {
    return SliverAppBar(
      backgroundColor: Colors.transparent,
      floating: true,
      pinned: false,
      title: Row(
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              gradient: AppColors.grassGradient,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.dns_rounded, size: 18, color: Colors.white),
          ),
          const SizedBox(width: 10),
          const Text('Mine Manager', style: TextStyle(color: AppColors.textPrimary, fontSize: 17, fontWeight: FontWeight.bold)),
        ],
      ),
      actions: [
        Consumer<AuthProvider>(
          builder: (_, auth, __) => GestureDetector(
            onTap: () => _showLogoutDialog(context, auth),
            child: Container(
              margin: const EdgeInsets.only(right: 16),
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: AppColors.backgroundCard,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.border),
              ),
              child: Row(
                children: [
                  const Icon(Icons.person_outline, size: 16, color: AppColors.textSecondary),
                  const SizedBox(width: 6),
                  Text(auth.user?.username ?? '', style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildWelcomeBanner(BuildContext context) {
    return Consumer<ServerProvider>(
      builder: (_, sp, __) => Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: AppColors.grassGradient,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [BoxShadow(color: AppColors.grassGreen.withValues(alpha: 0.3), blurRadius: 20)],
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Server Network', style: TextStyle(color: Colors.white70, fontSize: 12, letterSpacing: 0.5)),
                  const SizedBox(height: 4),
                  Text(
                    '${sp.onlineCount} Online',
                    style: const TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.bold),
                  ),
                  Text(
                    '${sp.servers.length} total servers',
                    style: const TextStyle(color: Colors.white60, fontSize: 13),
                  ),
                ],
              ),
            ),
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(14),
              ),
              child: const Icon(Icons.public, size: 32, color: Colors.white),
            ),
          ],
        ),
      ).animate().fadeIn(duration: 400.ms).slideX(begin: -0.05, end: 0),
    );
  }

  Widget _buildStatCards(BuildContext context) {
    return Consumer<ServerProvider>(
      builder: (_, sp, __) {
        final stats = sp.systemStats;
        return Row(
          children: [
            Expanded(child: McStatCard(label: 'CPU', value: stats['cpu_percent'] != null ? '${stats['cpu_percent']}%' : '--', icon: Icons.memory, color: AppColors.diamond)),
            const SizedBox(width: 10),
            Expanded(child: McStatCard(label: 'RAM', value: stats['ram_percent'] != null ? '${stats['ram_percent']}%' : '--', icon: Icons.storage, color: AppColors.gold)),
            const SizedBox(width: 10),
            Expanded(child: McStatCard(label: 'DISK', value: stats['disk_percent'] != null ? '${stats['disk_percent']}%' : '--', icon: Icons.sd_storage, color: AppColors.emerald)),
          ],
        );
      },
    );
  }

  Widget _buildQuickActions(BuildContext context) {
    return Row(
      children: [
        Expanded(child: McActionCard(icon: Icons.add_circle_outline, label: 'New Server', color: AppColors.grassGreen, onTap: () => Navigator.pushNamed(context, '/servers/create'))),
        const SizedBox(width: 10),
        Expanded(child: McActionCard(icon: Icons.download_for_offline_outlined, label: 'Versions', color: AppColors.diamond, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const VersionManagerScreen())))),
        const SizedBox(width: 10),
        Expanded(child: McActionCard(icon: Icons.refresh, label: 'Refresh', color: AppColors.lapis, onTap: () => context.read<ServerProvider>().loadServers())),
      ],
    );
  }

  Widget _buildRecentServers(BuildContext context) {
    return Consumer<ServerProvider>(
      builder: (_, sp, __) {
        if (sp.isLoading) return const McShimmer(height: 80);
        if (sp.servers.isEmpty) {
          return const McCard(
            child: Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Column(
                  children: [
                    Icon(Icons.dns_outlined, size: 40, color: AppColors.textMuted),
                    SizedBox(height: 12),
                    Text('No servers yet', style: TextStyle(color: AppColors.textMuted)),
                  ],
                ),
              ),
            ),
          );
        }
        return Column(
          children: sp.servers.take(3).map((s) => Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: McCard(
              onTap: () => Navigator.pushNamed(context, '/servers/${s.id}'),
              child: Row(
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: s.isOnline ? AppColors.grassGreen.withValues(alpha: 0.15) : AppColors.backgroundOverlay,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: s.isOnline ? AppColors.grassGreen.withValues(alpha: 0.3) : AppColors.border),
                    ),
                    child: Icon(Icons.dns_rounded, size: 22, color: s.isOnline ? AppColors.grassGreenLight : AppColors.textMuted),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(s.name, style: const TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold, fontSize: 14)),
                        const SizedBox(height: 3),
                        Text('v${s.version} • Port ${s.port}', style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                      ],
                    ),
                  ),
                  ServerStatusBadge(status: s.status),
                ],
              ),
            ),
          )).toList(),
        );
      },
    );
  }

  void _showLogoutDialog(BuildContext context, AuthProvider auth) async {
    final confirmed = await McDialogs.showConfirm(
      context,
      title: 'Sign Out',
      message: 'Are you sure you want to sign out?',
      confirmLabel: 'Sign Out',
      isDanger: true,
    );

    if (confirmed) {
      await auth.logout();
      if (context.mounted) Navigator.pushReplacementNamed(context, '/login');
    }
  }
}

