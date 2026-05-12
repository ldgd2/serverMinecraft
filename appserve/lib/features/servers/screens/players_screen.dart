import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:appserve/core/providers/app_providers.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/shared/widgets/mc_card.dart';
import 'package:appserve/shared/layouts/mc_screen_layout.dart';
import 'package:appserve/shared/widgets/player_head.dart';
import 'package:flutter_animate/flutter_animate.dart';

class PlayersScreen extends StatefulWidget {
  const PlayersScreen({super.key});

  @override
  State<PlayersScreen> createState() => _PlayersScreenState();
}

class _PlayersScreenState extends State<PlayersScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ServerProvider>().loadAllPlayers();
    });
  }

  @override
  Widget build(BuildContext context) {
    return McSliverScreenLayout(
      backgroundGradientColors: const [Color(0xFF0F2027), Color(0xFF203A43), Color(0xFF2C5364)],
      headerContent: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          const Text('Community', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Consumer<ServerProvider>(builder: (_, sp, __) => Text('${sp.allPlayers.length} Registered Players', style: const TextStyle(color: Colors.white70, fontSize: 14))),
        ],
      ),
      body: Consumer<ServerProvider>(
        builder: (context, sp, child) {
          if (sp.isLoading && sp.allPlayers.isEmpty) {
            return const Center(child: CircularProgressIndicator(color: AppColors.diamond));
          }

          if (sp.allPlayers.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.people_outline, size: 64, color: AppColors.textMuted.withOpacity(0.5)),
                  const SizedBox(height: 16),
                  const Text('No players found in database', style: TextStyle(color: AppColors.textMuted)),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => sp.loadAllPlayers(),
            color: AppColors.diamond,
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: sp.allPlayers.length,
              itemBuilder: (context, index) {
                final player = sp.allPlayers[index];
                return _PlayerCard(player: player).animate().fadeIn(delay: (index * 50).ms).slideX();
              },
            ),
          );
        },
      ),
    );
  }
}

class _PlayerCard extends StatelessWidget {
  final Map<String, dynamic> player;
  const _PlayerCard({required this.player});

  @override
  Widget build(BuildContext context) {
    final name = player['name'] ?? 'Unknown';
    final lastJoined = player['last_joined'] != null 
        ? DateTime.parse(player['last_joined']).toLocal() 
        : null;
    final playtime = player['total_playtime'] ?? 0;
    
    // Formatting playtime
    final hours = playtime ~/ 3600;
    final minutes = (playtime % 3600) ~/ 60;
    final playtimeStr = hours > 0 ? '${hours}h ${minutes}m' : '${minutes}m';

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: McCard(
        child: ListTile(
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
          leading: PlayerHead(username: name, size: 40),
          title: Text(name, style: const TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold)),
          subtitle: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 4),
              Row(
                children: [
                  const Icon(Icons.timer_outlined, size: 12, color: AppColors.textMuted),
                  const SizedBox(width: 4),
                  Text(playtimeStr, style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
                  const SizedBox(width: 12),
                  const Icon(Icons.history, size: 12, color: AppColors.textMuted),
                  const SizedBox(width: 4),
                  Text(
                    lastJoined != null ? _formatDate(lastJoined) : 'Never',
                    style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
                  ),
                ],
              ),
            ],
          ),
          trailing: const Icon(Icons.chevron_right, color: AppColors.border),
          onTap: () {
            // Navigate to profile details if implemented
          },
        ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);
    if (diff.inDays == 0) return 'Today';
    if (diff.inDays == 1) return 'Yesterday';
    if (diff.inDays < 7) return '${diff.inDays} days ago';
    return '${date.day}/${date.month}/${date.year}';
  }
}
