import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:appserve/core/models/server_model.dart';
import 'package:appserve/core/providers/app_providers.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/shared/widgets/mc_button.dart';
import 'package:appserve/shared/widgets/mc_card.dart';
import 'package:appserve/shared/widgets/mc_widgets.dart';
import 'package:appserve/features/servers/screens/server_detail_screen.dart';

class ServerCard extends StatelessWidget {
  final ServerModel server;
  const ServerCard({super.key, required this.server});

  @override
  Widget build(BuildContext context) {
    return McCard(
      onTap: () => Navigator.push(
          context,
          MaterialPageRoute(
              builder: (_) => ServerDetailScreen(server: server))),
      borderColor: server.isOnline
          ? AppColors.grassGreen.withOpacity(0.25)
          : AppColors.border,
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
                child: Icon(Icons.dns_rounded,
                    size: 24,
                    color:
                        server.isOnline ? Colors.white : AppColors.textMuted),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(server.name,
                        style: const TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 15,
                            fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        StatChip(icon: Icons.tag, value: 'v${server.version}'),
                        const SizedBox(width: 6),
                        StatChip(icon: Icons.wifi, value: ':${server.port}'),
                        const SizedBox(width: 6),
                        StatChip(
                            icon: Icons.memory, value: server.ramFormatted),
                      ],
                    ),
                  ],
                ),
              ),
              ServerStatusBadge(status: server.status),
            ],
          ),
          const SizedBox(height: 14),
          if (server.isOnline) ...[
            const Divider(color: AppColors.border, height: 1),
            const SizedBox(height: 12),
            Row(
              children: [
                _ResourceMonitor(
                  label: 'CPU',
                  value: '${server.cpuUsage.toStringAsFixed(1)}%',
                  total: '${server.cpuCores.toStringAsFixed(1)} Cores',
                  progress: server.cpuProgress,
                  color: AppColors.diamond,
                ),
                const SizedBox(width: 12),
                _ResourceMonitor(
                  label: 'RAM',
                  value: server.ramUsageFormatted,
                  total: server.ramFormatted,
                  progress: server.ramProgress,
                  color: AppColors.starting,
                ),
                const SizedBox(width: 12),
                _ResourceMonitor(
                  label: 'DISK',
                  value: server.diskUsageFormatted,
                  total: server.diskFormatted,
                  progress: server.diskProgress,
                  color: AppColors.textMuted,
                ),
              ],
            ),
          ],
          const SizedBox(height: 14),
          const Divider(color: AppColors.border, height: 1),
          const SizedBox(height: 10),
          // Quick controls
          Row(
            children: [
              if (server.isOffline)
                Expanded(
                    child: McButton(
                        label: 'Start',
                        icon: Icons.play_arrow,
                        onPressed: () => context
                            .read<ServerProvider>()
                            .startServer(server.name)))
              else if (server.isOnline) ...[
                Expanded(
                    child: McButton(
                        label: 'Stop',
                        icon: Icons.stop,
                        isDanger: true,
                        onPressed: () => context
                            .read<ServerProvider>()
                            .stopServer(server.name))),
                const SizedBox(width: 8),
                Expanded(
                    child: McButton(
                        label: 'Restart',
                        icon: Icons.refresh,
                        isSecondary: true,
                        onPressed: () => context
                            .read<ServerProvider>()
                            .restartServer(server.name))),
              ] else if (server.isRestarting) ...[
                const Expanded(
                    child: McButton(
                        label: 'Restarting...',
                        isLoading: true,
                        onPressed: null)),
              ] else if (server.isStopping) ...[
                const Expanded(
                    child: McButton(
                        label: 'Stopping...',
                        isLoading: true,
                        onPressed: null)),
              ] else if (server.isCreating) ...[
                Builder(builder: (context) {
                  final creationInfo = context
                      .watch<ServerProvider>()
                      .creationStats
                      .values
                      .firstWhere(
                        (v) => v['name'] == server.name,
                        orElse: () => null,
                      );

                  final progress = (creationInfo?['progress'] ?? 0) / 100.0;
                  final details =
                      creationInfo?['details'] ?? 'Preparing files...';

                  return Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(details,
                                style: const TextStyle(
                                    color: AppColors.textSecondary,
                                    fontSize: 10,
                                    fontWeight: FontWeight.w500)),
                            Text('${(progress * 100).toInt()}%',
                                style: const TextStyle(
                                    color: AppColors.diamond,
                                    fontSize: 10,
                                    fontWeight: FontWeight.bold)),
                          ],
                        ),
                        const SizedBox(height: 6),
                        ClipRRect(
                          borderRadius: BorderRadius.circular(4),
                          child: LinearProgressIndicator(
                            value: progress,
                            minHeight: 6,
                            backgroundColor: AppColors.backgroundOverlay,
                            valueColor: const AlwaysStoppedAnimation<Color>(
                                AppColors.diamond),
                          ),
                        ),
                      ],
                    ),
                  );
                }),
              ] else
                const Expanded(
                    child: McButton(
                        label: 'Starting...',
                        isLoading: true,
                        onPressed: null)),
              const SizedBox(width: 8),
              McButton(
                label: 'Console',
                icon: Icons.terminal,
                isSecondary: true,
                onPressed: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (_) =>
                            ServerDetailScreen(server: server, initialTab: 1))),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _ResourceMonitor extends StatelessWidget {
  final String label;
  final String value;
  final String total;
  final double progress;
  final Color color;

  const _ResourceMonitor({
    required this.label,
    required this.value,
    required this.total,
    required this.progress,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label,
                  style: const TextStyle(
                      color: AppColors.textMuted,
                      fontSize: 9,
                      fontWeight: FontWeight.bold)),
              Text('$value / $total',
                  style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 9,
                      fontWeight: FontWeight.w500)),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(2),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 3,
              backgroundColor: AppColors.backgroundOverlay,
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
        ],
      ),
    );
  }
}
