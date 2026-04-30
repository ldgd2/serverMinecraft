import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:appserve/core/providers/app_providers.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/shared/widgets/mc_card.dart';
import 'package:appserve/shared/widgets/mc_widgets.dart';

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
                          _GaugeCard(label: 'CPU Usage', value: (stats['cpu_percent'] as num?)?.toDouble() ?? 0, unit: '%', color: AppColors.diamond),
                          const SizedBox(height: 12),
                          _GaugeCard(label: 'RAM Usage', value: (stats['ram_percent'] as num?)?.toDouble() ?? 0, unit: '%', color: AppColors.gold),
                          const SizedBox(height: 12),
                          _GaugeCard(label: 'Disk Usage', value: (stats['disk_percent'] as num?)?.toDouble() ?? 0, unit: '%', color: AppColors.emerald),
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

class _GaugeCard extends StatelessWidget {
  final String label;
  final double value;
  final String unit;
  final Color color;

  const _GaugeCard({required this.label, required this.value, required this.unit, required this.color});

  @override
  Widget build(BuildContext context) {
    return McCard(
      borderColor: color.withOpacity(0.2),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13, fontWeight: FontWeight.w600)),
              Text('${value.toInt()}$unit', style: TextStyle(color: color, fontSize: 20, fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: (value / 100).clamp(0, 1),
              minHeight: 8,
              backgroundColor: AppColors.backgroundOverlay,
              valueColor: AlwaysStoppedAnimation<Color>(
                value > 80 ? AppColors.offline : value > 60 ? AppColors.starting : color,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
