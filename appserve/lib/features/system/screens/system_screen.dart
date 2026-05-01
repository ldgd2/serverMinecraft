import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:appserve/core/providers/app_providers.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/shared/widgets/mc_card.dart';
import 'package:appserve/shared/widgets/mc_widgets.dart';
import 'package:appserve/shared/widgets/mc_cards.dart';

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
                          const SizedBox(height: 20),
                          const SectionHeader(title: 'DETAILS'),
                          const SizedBox(height: 10),
                          McCard(
                            child: Column(children: [
                              McInfoRow(icon: Icons.memory, label: 'Total RAM', value: stats['ram_total'] ?? '--'),
                              const Divider(color: AppColors.border, height: 16),
                              McInfoRow(icon: Icons.memory_outlined, label: 'RAM Used', value: stats['ram_used'] ?? '--'),
                              const Divider(color: AppColors.border, height: 16),
                              McInfoRow(icon: Icons.sd_storage, label: 'Disk Total', value: stats['disk_total'] ?? '--'),
                              const Divider(color: AppColors.border, height: 16),
                              McInfoRow(icon: Icons.storage, label: 'Disk Used', value: stats['disk_used'] ?? '--'),
                              if (stats['uptime'] != null) ...[
                                const Divider(color: AppColors.border, height: 16),
                                McInfoRow(icon: Icons.timer_outlined, label: 'Uptime', value: stats['uptime'].toString()),
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
}
