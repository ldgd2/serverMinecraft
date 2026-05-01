import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:appserve/core/providers/app_providers.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/shared/widgets/mc_card.dart';
import 'package:appserve/shared/widgets/mc_button.dart';
import 'package:appserve/shared/widgets/mc_widgets.dart';
import 'package:appserve/shared/widgets/mc_cards.dart';
import 'service_log_screen.dart';
import 'backups_screen.dart';
import '../../../core/providers/backup_provider.dart';

class SystemScreen extends StatefulWidget {
  const SystemScreen({super.key});

  @override
  State<SystemScreen> createState() => _SystemScreenState();
}

class _SystemScreenState extends State<SystemScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ServerProvider>().loadSystemStats();
    });
  }

  void _confirmRestart(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.backgroundElevated,
        title: const Text('Restart Dashboard?', style: TextStyle(color: AppColors.textPrimary)),
        content: const Text('This will restart the VPS dashboard service. The app will lose connection for a few seconds.',
            style: TextStyle(color: AppColors.textSecondary)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          McButton(
            label: 'Restart Now',
            icon: Icons.refresh,
            isDanger: true,
            onPressed: () {
              Navigator.pop(ctx);
              context.read<ServerProvider>().restartDashboardService();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Restarting dashboard service... Connection will drop temporarily.')),
              );
            },
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(gradient: AppColors.backgroundGradient),
      child: SafeArea(
        child: CustomScrollView(
          slivers: [
            SliverAppBar(
              backgroundColor: Colors.transparent,
              floating: true,
              title: const Text('System Monitor', style: TextStyle(color: AppColors.textPrimary, fontSize: 18, fontWeight: FontWeight.bold)),
              actions: [
                IconButton(
                  icon: const Icon(Icons.refresh, color: AppColors.textSecondary),
                  onPressed: () => context.read<ServerProvider>().loadSystemStats(),
                ),
              ],
            ),
            SliverPadding(
              padding: const EdgeInsets.all(16),
              sliver: SliverList(
                delegate: SliverChildListDelegate([
                  Consumer<ServerProvider>(
                    builder: (_, sp, __) {
                      final stats = sp.systemStats;
                      if (stats.isEmpty) return const McShimmer(height: 200);
                      return Column(
                        children: [
                          McGaugeCard(label: 'CPU Usage', value: (stats['cpu_percent'] as num?)?.toDouble() ?? 0, unit: '%', color: AppColors.diamond),
                          const SizedBox(height: 12),
                          McGaugeCard(label: 'RAM Usage', value: (stats['ram_percent'] as num?)?.toDouble() ?? 0, unit: '%', color: AppColors.gold),
                          const SizedBox(height: 12),
                          McGaugeCard(label: 'Disk Usage', value: (stats['disk_percent'] as num?)?.toDouble() ?? 0, unit: '%', color: AppColors.emerald),
                          const SizedBox(height: 24),
                          const SectionHeader(title: 'VPS SERVICE'),
                          const SizedBox(height: 12),
                          McCard(
                            child: Column(
                              children: [
                                Row(
                                  children: [
                                    const Icon(Icons.settings_suggest, color: AppColors.gold, size: 24),
                                    const SizedBox(width: 12),
                                    const Expanded(
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text('Dashboard Service', style: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold, fontSize: 14)),
                                          Text('Manages the web dashboard and API', style: TextStyle(color: AppColors.textMuted, fontSize: 11)),
                                        ],
                                      ),
                                    ),
                                    McButton(
                                      label: 'Restart',
                                      icon: Icons.refresh,
                                      isSecondary: true,
                                      onPressed: () => _confirmRestart(context),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 16),
                                McButton(
                                  label: 'Backups & Recovery',
                                  icon: Icons.backup,
                                  width: double.infinity,
                                  onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const BackupsScreen())),
                                ),
                                const SizedBox(height: 12),
                                McButton(
                                  label: 'View Live Service Logs',
                                  icon: Icons.terminal,
                                  width: double.infinity,
                                  onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ServiceLogScreen())),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 24),
                          const SectionHeader(title: 'DETAILS'),
                          const SizedBox(height: 12),
                          McCard(
                            child: Column(children: [
                              McInfoRow(icon: Icons.memory, label: 'Total RAM', value: '${stats['memory_total'] ?? '--'} MB'),
                              const Divider(color: AppColors.border, height: 16),
                              McInfoRow(icon: Icons.memory_outlined, label: 'RAM Used', value: '${stats['memory_used'] ?? '--'} MB'),
                              const Divider(color: AppColors.border, height: 16),
                              McInfoRow(icon: Icons.sd_storage, label: 'Disk Usage', value: '${stats['disk'] ?? '--'}%'),
                              if (stats['uptime'] != null) ...[
                                const Divider(color: AppColors.border, height: 16),
                                McInfoRow(icon: Icons.timer_outlined, label: 'Uptime', value: _formatUptime(stats['uptime'])),
                              ],
                              if (stats['os'] != null) ...[
                                const Divider(color: AppColors.border, height: 16),
                                McInfoRow(icon: Icons.computer, label: 'OS', value: stats['os'].toString()),
                              ],
                            ]),
                          ),
                        ],
                      );
                    },
                  ),
                ]),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatUptime(dynamic seconds) {
    if (seconds == null) return '--';
    final duration = Duration(seconds: seconds is int ? seconds : int.tryParse(seconds.toString()) ?? 0);
    final days = duration.inDays;
    final hours = duration.inHours.remainder(24);
    final minutes = duration.inMinutes.remainder(60);
    if (days > 0) return '${days}d ${hours}h ${minutes}m';
    if (hours > 0) return '${hours}h ${minutes}m';
    return '${minutes}m';
  }
}
