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
  final _searchCtrl = TextEditingController();
  String _filter = '';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ServerProvider>().loadAllPlayers();
    });
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return McSliverScreenLayout(
      backgroundGradientColors: const [Color(0xFF0F2027), Color(0xFF203A43), Color(0xFF2C5364)],
      headerContent: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Community', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
              Consumer<ServerProvider>(
                builder: (_, sp, __) => Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text('${sp.allPlayers.length} Players', style: const TextStyle(color: Colors.white70, fontSize: 12)),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Container(
            height: 44,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.white24),
            ),
            child: TextField(
              controller: _searchCtrl,
              onChanged: (v) => setState(() => _filter = v.toLowerCase()),
              style: const TextStyle(color: Colors.white, fontSize: 14),
              decoration: const InputDecoration(
                hintText: 'Search player by name...',
                hintStyle: TextStyle(color: Colors.white38),
                prefixIcon: Icon(Icons.search, color: Colors.white54, size: 20),
                border: InputBorder.none,
                contentPadding: EdgeInsets.symmetric(vertical: 10),
              ),
            ),
          ),
        ],
      ),
      body: Consumer<ServerProvider>(
        builder: (context, sp, child) {
          if (sp.isLoading && sp.allPlayers.isEmpty) {
            return const Center(child: CircularProgressIndicator(color: AppColors.diamond));
          }

          final filteredPlayers = sp.allPlayers.where((p) {
            final name = (p['name'] ?? '').toString().toLowerCase();
            return name.contains(_filter);
          }).toList();

          if (filteredPlayers.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.search_off, size: 64, color: AppColors.textMuted.withOpacity(0.5)),
                  const SizedBox(height: 16),
                  Text(_filter.isEmpty ? 'No players registered' : 'No players match "$_filter"', 
                    style: const TextStyle(color: AppColors.textMuted)),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => sp.loadAllPlayers(),
            color: AppColors.diamond,
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: filteredPlayers.length,
              itemBuilder: (context, index) {
                final player = filteredPlayers[index];
                return _PlayerCard(player: player).animate().fadeIn(delay: (index * 30).ms).slideX(begin: 0.05);
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
