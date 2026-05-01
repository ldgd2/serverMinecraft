import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import 'package:appserve/core/providers/player_provider.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/shared/widgets/mc_button.dart';
import 'package:appserve/shared/widgets/mc_card.dart';
import 'package:appserve/shared/widgets/mc_widgets.dart';

class PlayerProfileScreen extends StatefulWidget {
  const PlayerProfileScreen({super.key});

  @override
  State<PlayerProfileScreen> createState() => _PlayerProfileScreenState();
}

class _PlayerProfileScreenState extends State<PlayerProfileScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final pp = context.read<PlayerProvider>();
      if (pp.isLoggedIn) pp.refreshProfile();
      pp.loadLeaderboard();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<PlayerProvider>(
      builder: (context, pp, _) {
        if (!pp.isLoggedIn) {
          return _NotLoggedIn();
        }
        return _buildLoggedInView(pp);
      },
    );
  }

  Widget _buildLoggedInView(PlayerProvider pp) {
    final acctType = pp.accountType;
    final isPremium = acctType == 'premium';

    return Scaffold(
      backgroundColor: AppColors.backgroundDeep,
      body: NestedScrollView(
        headerSliverBuilder: (context, innerBoxIsScrolled) => [
          SliverAppBar(
            expandedHeight: 180,
            pinned: true,
            backgroundColor: AppColors.backgroundCard,
            flexibleSpace: FlexibleSpaceBar(
              background: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: isPremium
                        ? [const Color(0xFF1a3a1a), AppColors.backgroundCard]
                        : [const Color(0xFF2a2a1a), AppColors.backgroundCard],
                  ),
                ),
                child: SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            // Avatar
                            Container(
                              width: 64,
                              height: 64,
                              decoration: BoxDecoration(
                                color: AppColors.backgroundOverlay,
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(
                                  color: isPremium ? AppColors.grassGreen : AppColors.gold,
                                  width: 2,
                                ),
                                boxShadow: [
                                  BoxShadow(
                                    color: (isPremium ? AppColors.grassGreen : AppColors.gold)
                                        .withOpacity(0.3),
                                    blurRadius: 12,
                                  ),
                                ],
                              ),
                              child: Icon(
                                Icons.person_rounded,
                                size: 36,
                                color: isPremium ? AppColors.grassGreen : AppColors.gold,
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    pp.username,
                                    style: const TextStyle(
                                      color: AppColors.textPrimary,
                                      fontSize: 22,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  const SizedBox(height: 6),
                                  Row(
                                    children: [
                                      _AccountBadge(type: acctType),
                                      const SizedBox(width: 8),
                                      Text(
                                        '${pp.achievements.length} logros',
                                        style: const TextStyle(
                                          color: AppColors.textMuted,
                                          fontSize: 12,
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                            IconButton(
                              icon: const Icon(Icons.refresh, color: AppColors.textMuted),
                              onPressed: () => pp.refreshProfile(),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            bottom: TabBar(
              controller: _tabController,
              indicatorColor: isPremium ? AppColors.grassGreen : AppColors.gold,
              labelColor: AppColors.textPrimary,
              unselectedLabelColor: AppColors.textMuted,
              tabs: const [
                Tab(icon: Icon(Icons.bar_chart, size: 18), text: 'Stats'),
                Tab(icon: Icon(Icons.stars, size: 18), text: 'Jugadas'),
                Tab(icon: Icon(Icons.emoji_events, size: 18), text: 'Logros'),
                Tab(icon: Icon(Icons.leaderboard, size: 18), text: 'Ranking'),
              ],
            ),
          ),
        ],
        body: TabBarView(
          controller: _tabController,
          children: [
            _StatsTab(pp: pp),
            _HighlightsTab(pp: pp),
            _AchievementsTab(pp: pp),
            _LeaderboardTab(pp: pp),
          ],
        ),
      ),
    );
  }
}

// ─── Not Logged In ────────────────────────────────────────────────────────────

class _NotLoggedIn extends StatefulWidget {
  @override
  State<_NotLoggedIn> createState() => _NotLoggedInState();
}

class _NotLoggedInState extends State<_NotLoggedIn> {
  final _userCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  bool _isRegisterMode = false;
  bool _showPass = false;

  @override
  void dispose() {
    _userCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundDeep,
      body: Consumer<PlayerProvider>(
        builder: (context, pp, _) => SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [Color(0xFF1a3a1a), Color(0xFF0D1117)],
                    ),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.grassGreen.withOpacity(0.3)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.person_rounded, size: 48, color: AppColors.grassGreen),
                      const SizedBox(height: 12),
                      Text(
                        _isRegisterMode ? 'Crear Cuenta de Jugador' : 'Acceso de Jugador',
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'Guarda tus estadísticas, logros y posición en el ranking global.',
                        style: TextStyle(color: AppColors.textMuted, fontSize: 13),
                      ),
                    ],
                  ),
                ).animate().fadeIn(duration: 400.ms).slideY(begin: -0.1),

                const SizedBox(height: 32),

                // Form
                SectionHeader(
                  title: _isRegisterMode ? 'NUEVA CUENTA' : 'INICIAR SESIÓN',
                ),
                const SizedBox(height: 12),
                McCard(
                  child: Column(
                    children: [
                      TextField(
                        controller: _userCtrl,
                        style: const TextStyle(color: AppColors.textPrimary),
                        decoration: const InputDecoration(
                          labelText: 'Nombre de jugador',
                          labelStyle: TextStyle(color: AppColors.textMuted),
                          prefixIcon: Icon(Icons.person_outline, color: AppColors.textMuted),
                          border: InputBorder.none,
                          isDense: true,
                        ),
                      ),
                      const Divider(color: AppColors.border, height: 1),
                      TextField(
                        controller: _passCtrl,
                        obscureText: !_showPass,
                        style: const TextStyle(color: AppColors.textPrimary),
                        decoration: InputDecoration(
                          labelText: 'Contraseña',
                          labelStyle: const TextStyle(color: AppColors.textMuted),
                          prefixIcon: const Icon(Icons.lock_outline, color: AppColors.textMuted),
                          suffixIcon: IconButton(
                            icon: Icon(
                              _showPass ? Icons.visibility_off : Icons.visibility,
                              color: AppColors.textMuted,
                              size: 20,
                            ),
                            onPressed: () => setState(() => _showPass = !_showPass),
                          ),
                          border: InputBorder.none,
                          isDense: true,
                        ),
                      ),
                    ],
                  ),
                ).animate().fadeIn(delay: 100.ms),

                if (pp.error != null) ...[
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.offline.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: AppColors.offline.withOpacity(0.3)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.error_outline, color: AppColors.offline, size: 18),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(pp.error!,
                              style: const TextStyle(color: AppColors.offline, fontSize: 13)),
                        ),
                      ],
                    ),
                  ),
                ],

                const SizedBox(height: 20),

                McButton(
                  label: pp.isLoading
                      ? 'Cargando...'
                      : (_isRegisterMode ? 'Crear cuenta' : 'Iniciar sesión'),
                  icon: _isRegisterMode ? Icons.person_add : Icons.login,
                  isLoading: pp.isLoading,
                  width: double.infinity,
                  onPressed: pp.isLoading ? null : _submit,
                ).animate().fadeIn(delay: 200.ms),

                const SizedBox(height: 12),

                Center(
                  child: TextButton(
                    onPressed: () {
                      setState(() => _isRegisterMode = !_isRegisterMode);
                      context.read<PlayerProvider>().clearError();
                    },
                    child: Text(
                      _isRegisterMode
                          ? '¿Ya tienes cuenta? Inicia sesión'
                          : '¿No tienes cuenta? Regístrate',
                      style: const TextStyle(color: AppColors.grassGreenLight),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _submit() {
    final user = _userCtrl.text.trim();
    final pass = _passCtrl.text.trim();
    if (user.isEmpty || pass.isEmpty) return;
    HapticFeedback.lightImpact();
    final pp = context.read<PlayerProvider>();
    if (_isRegisterMode) {
      pp.register(user, pass);
    } else {
      pp.login(user, pass);
    }
  }
}

// ─── Stats Tab ────────────────────────────────────────────────────────────────

class _StatsTab extends StatelessWidget {
  final PlayerProvider pp;
  const _StatsTab({required this.pp});

  @override
  Widget build(BuildContext context) {
    final stats = pp.stats;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Big KD card
        _KDCard(
          kills: stats['kills'] ?? 0,
          deaths: stats['deaths'] ?? 0,
          kd: (stats['kd_ratio'] ?? 0.0).toDouble(),
        ).animate().fadeIn(duration: 350.ms).slideY(begin: 0.1),

        const SizedBox(height: 16),
        const SectionHeader(title: 'COMBATE'),
        const SizedBox(height: 8),
        McCard(
          child: Column(children: [
            _McStatIconRow(
              iconPath: 'assets/gui/sprites/statistics/item_used.png',
              label: 'Mejor racha de kills',
              value: '${stats['best_kill_streak'] ?? 0}',
              valueColor: AppColors.gold,
            ),
          ]),
        ).animate().fadeIn(delay: 100.ms),

        const SizedBox(height: 20),
        const SectionHeader(title: 'CONSTRUCCIÓN'),
        const SizedBox(height: 8),
        McCard(
          child: Column(children: [
            _McStatIconRow(
              iconPath: 'assets/gui/sprites/statistics/block_mined.png',
              label: 'Bloques rotos',
              value: _fmt(stats['blocks_broken'] ?? 0),
            ),
            const Divider(color: AppColors.border, height: 16),
            _McStatIconRow(
              iconPath: 'assets/gui/sprites/statistics/block_mined.png',
              label: 'Bloques colocados',
              value: _fmt(stats['blocks_placed'] ?? 0),
            ),
          ]),
        ).animate().fadeIn(delay: 150.ms),

        const SizedBox(height: 20),
        const SectionHeader(title: 'TIEMPO DE JUEGO'),
        const SizedBox(height: 8),
        McCard(
          child: Column(children: [
            _McStatIconRow(
              iconPath: 'assets/gui/sprites/join.png',
              label: 'Tiempo total',
              value: stats['playtime'] ?? '0h 0m',
              valueColor: AppColors.diamond,
            ),
            const Divider(color: AppColors.border, height: 16),
            _McStatIconRow(
              iconPath: 'assets/gui/sprites/info.png',
              label: 'Servidores visitados',
              value: '${pp.profile?['servers_played'] ?? 0}',
            ),
          ]),
        ).animate().fadeIn(delay: 200.ms),
      ],
    );
  }

  String _fmt(dynamic n) {
    final v = n is int ? n : int.tryParse(n.toString()) ?? 0;
    if (v >= 1000000) return '${(v / 1000000).toStringAsFixed(1)}M';
    if (v >= 1000) return '${(v / 1000).toStringAsFixed(1)}K';
    return v.toString();
  }
}

class _KDCard extends StatelessWidget {
  final int kills;
  final int deaths;
  final double kd;
  const _KDCard({required this.kills, required this.deaths, required this.kd});

  @override
  Widget build(BuildContext context) {
    final kdColor = kd >= 2.0 ? AppColors.grassGreen : kd >= 1.0 ? AppColors.gold : AppColors.offline;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.backgroundElevated, AppColors.backgroundCard],
        ),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _StatPill(label: '⚔️ KILLS', value: kills.toString(), color: AppColors.grassGreen),
          Column(
            children: [
              Text(kd.toStringAsFixed(2),
                  style: TextStyle(color: kdColor, fontSize: 32, fontWeight: FontWeight.bold)),
              Text('K/D RATIO', style: TextStyle(color: kdColor.withOpacity(0.7), fontSize: 11)),
            ],
          ),
          _StatPill(label: '💀 DEATHS', value: deaths.toString(), color: AppColors.offline),
        ],
      ),
    );
  }
}

class _StatPill extends StatelessWidget {
  final String label, value;
  final Color color;
  const _StatPill({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value, style: TextStyle(color: color, fontSize: 24, fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        Text(label, style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
      ],
    );
  }
}

// ─── Achievements Tab ─────────────────────────────────────────────────────────

class _AchievementsTab extends StatelessWidget {
  final PlayerProvider pp;
  const _AchievementsTab({required this.pp});

  @override
  Widget build(BuildContext context) {
    final achievements = pp.achievements;
    if (achievements.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.emoji_events_outlined, size: 64, color: AppColors.textMuted),
            const SizedBox(height: 16),
            const Text('Sin logros todavía',
                style: TextStyle(color: AppColors.textPrimary, fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            const Text('¡Juega para desbloquearlos!',
                style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: achievements.length,
      itemBuilder: (context, i) {
        final ach = achievements[i] as Map<String, dynamic>;
        return _AchievementCard(ach: ach, index: i);
      },
    );
  }
}

class _AchievementCard extends StatelessWidget {
  final Map<String, dynamic> ach;
  final int index;
  const _AchievementCard({required this.ach, required this.index});

  @override
  Widget build(BuildContext context) {
    final name = ach['name'] ?? 'Logro';
    final desc = ach['description'] ?? '';
    final server = ach['server_name'] ?? '';
    final unlocked = ach['unlocked_at'] ?? '';
    final date = unlocked.isNotEmpty ? unlocked.toString().substring(0, 10) : '';

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.backgroundElevated,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.gold.withOpacity(0.3)),
        boxShadow: [BoxShadow(color: AppColors.gold.withOpacity(0.05), blurRadius: 8)],
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppColors.gold.withOpacity(0.15),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Image.asset(
              'assets/gui/sprites/advancements/challenge_frame_obtained.png',
              filterQuality: FilterQuality.none,
              fit: BoxFit.contain,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name,
                    style: const TextStyle(
                        color: AppColors.gold, fontWeight: FontWeight.bold, fontSize: 14)),
                if (desc.isNotEmpty)
                  Text(desc, style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                const SizedBox(height: 4),
                Row(children: [
                  if (server.isNotEmpty) ...[
                    const Icon(Icons.location_on, size: 12, color: AppColors.textMuted),
                    const SizedBox(width: 2),
                    Text(server, style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
                    const SizedBox(width: 8),
                  ],
                  if (date.isNotEmpty)
                    Text(date, style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
                ]),
              ],
            ),
          ),
        ],
      ),
    ).animate().fadeIn(delay: (index * 50).ms).slideX(begin: 0.1);
  }
}

// ─── Leaderboard Tab ──────────────────────────────────────────────────────────

class _LeaderboardTab extends StatelessWidget {
  final PlayerProvider pp;
  const _LeaderboardTab({required this.pp});

  @override
  Widget build(BuildContext context) {
    if (pp.isLoading && pp.leaderboard.isEmpty) {
      return const Center(child: CircularProgressIndicator(color: AppColors.grassGreen));
    }
    if (pp.leaderboard.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.leaderboard_outlined, size: 64, color: AppColors.textMuted),
            const SizedBox(height: 16),
            const Text('Sin datos de ranking', style: TextStyle(color: AppColors.textMuted)),
            const SizedBox(height: 12),
            McButton(
              label: 'Recargar',
              icon: Icons.refresh,
              isSecondary: true,
              onPressed: () => pp.loadLeaderboard(),
            ),
          ],
        ),
      );
    }

    final currentUser = pp.username;

    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
      itemCount: pp.leaderboard.length + 1,
      itemBuilder: (context, i) {
        if (i == 0) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const SectionHeader(title: 'TOP JUGADORES (KILLS)'),
                IconButton(
                  icon: const Icon(Icons.refresh, color: AppColors.textSecondary, size: 20),
                  onPressed: () => pp.loadLeaderboard(),
                ),
              ],
            ),
          );
        }
        final entry = pp.leaderboard[i - 1];
        final isMe = entry['username'] == currentUser;
        return _LeaderboardRow(entry: entry, isMe: isMe, index: i - 1);
      },
    );
  }
}

class _LeaderboardRow extends StatelessWidget {
  final Map<String, dynamic> entry;
  final bool isMe;
  final int index;
  const _LeaderboardRow({required this.entry, required this.isMe, required this.index});

  @override
  Widget build(BuildContext context) {
    final rank = entry['rank'] ?? index + 1;
    final username = entry['username'] ?? '—';
    final kills = entry['kills'] ?? 0;
    final kd = entry['kd_ratio'] ?? 0.0;
    final hours = entry['playtime_hours'] ?? 0.0;
    final achs = entry['achievements_count'] ?? 0;

    Color rankColor;
    String rankEmoji;
    if (rank == 1) { rankColor = const Color(0xFFFFD700); rankEmoji = '🥇'; }
    else if (rank == 2) { rankColor = const Color(0xFFC0C0C0); rankEmoji = '🥈'; }
    else if (rank == 3) { rankColor = const Color(0xFFCD7F32); rankEmoji = '🥉'; }
    else { rankColor = AppColors.textMuted; rankEmoji = '#$rank'; }

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: isMe
            ? AppColors.grassGreen.withOpacity(0.12)
            : AppColors.backgroundElevated,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isMe ? AppColors.grassGreen.withOpacity(0.4) : AppColors.border,
          width: isMe ? 1.5 : 1,
        ),
      ),
      child: Row(
        children: [
          SizedBox(
            width: 36,
            child: Text(rankEmoji,
                style: TextStyle(color: rankColor, fontWeight: FontWeight.bold, fontSize: 15),
                textAlign: TextAlign.center),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  Text(username,
                      style: TextStyle(
                          color: isMe ? AppColors.grassGreenLight : AppColors.textPrimary,
                          fontWeight: FontWeight.bold,
                          fontSize: 14)),
                  if (isMe) ...[
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                      decoration: BoxDecoration(
                        color: AppColors.grassGreen.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: const Text('TÚ',
                          style: TextStyle(color: AppColors.grassGreen, fontSize: 9, fontWeight: FontWeight.bold)),
                    ),
                  ],
                ]),
                Text('${hours}h jugadas  •  $achs logros',
                    style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text('$kills kills',
                  style: const TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold, fontSize: 14)),
              Text('K/D $kd', style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
            ],
          ),
        ],
      ),
    ).animate().fadeIn(delay: (index * 40).ms);
  }
}

// ─── Highlights Tab ──────────────────────────────────────────────────────────

class _HighlightsTab extends StatelessWidget {
  final PlayerProvider pp;
  const _HighlightsTab({required this.pp});

  @override
  Widget build(BuildContext context) {
    final highlights = pp.highlights;
    if (highlights.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.stars_outlined, size: 64, color: AppColors.textMuted),
            const SizedBox(height: 16),
            const Text('Sin jugadas destacadas',
                style: TextStyle(color: AppColors.textPrimary, fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            const Text('Tus mejores momentos aparecerán aquí',
                style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: highlights.length,
      itemBuilder: (context, i) {
        final highlight = highlights[i].toString();
        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.backgroundElevated,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.diamond.withOpacity(0.3)),
          ),
          child: Row(
            children: [
              const Icon(Icons.auto_awesome, color: AppColors.diamond, size: 20),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  highlight,
                  style: const TextStyle(color: AppColors.textPrimary, fontSize: 14),
                ),
              ),
            ],
          ),
        ).animate().fadeIn(delay: (i * 50).ms).slideX(begin: 0.1);
      },
    );
  }
}

// ─── Account Badge ────────────────────────────────────────────────────────────

class _AccountBadge extends StatelessWidget {
  final String type;
  const _AccountBadge({required this.type});

  @override
  Widget build(BuildContext context) {
    Color bg;
    String label;
    switch (type) {
      case 'premium':
        bg = AppColors.grassGreen; label = 'PREMIUM'; break;
      case 'nopremium':
        bg = AppColors.gold; label = 'NO-PREMIUM'; break;
      default:
        bg = AppColors.textMuted; label = 'INVITADO';
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg.withOpacity(0.2),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: bg.withOpacity(0.5)),
      ),
      child: Text(label, style: TextStyle(color: bg, fontSize: 10, fontWeight: FontWeight.bold)),
    );
  }
}

class _McStatIconRow extends StatelessWidget {
  final String iconPath;
  final String label;
  final String value;
  final Color? valueColor;

  const _McStatIconRow({
    required this.iconPath,
    required this.label,
    required this.value,
    this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Image.asset(
            iconPath,
            width: 20,
            height: 20,
            filterQuality: FilterQuality.none,
          ),
          const SizedBox(width: 12),
          Text(
            label,
            style: const TextStyle(color: AppColors.textMuted, fontSize: 13),
          ),
          const Spacer(),
          Text(
            value,
            style: TextStyle(
              color: valueColor ?? AppColors.textPrimary,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
