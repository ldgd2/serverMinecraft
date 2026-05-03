import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import 'package:appserve/core/providers/app_providers.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/shared/layouts/mc_screen_layout.dart';
import '../widgets/server_card.dart';

class ServersScreen extends StatefulWidget {
  const ServersScreen({super.key});

  @override
  State<ServersScreen> createState() => _ServersScreenState();
}

class _ServersScreenState extends State<ServersScreen> {
  @override
  void initState() {
    super.initState();
    // Load servers once on entry. Updates will come via WebSocket.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ServerProvider>().loadServers();
    });
  }

  @override
  void dispose() {
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<ServerProvider>(
      builder: (_, sp, __) {
        return McScreenLayout(
          title: 'Servers',
          actions: [
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: sp.loadServers,
            ),
          ],
          floatingActionButton: FloatingActionButton.extended(
            backgroundColor: AppColors.grassGreen,
            onPressed: () => Navigator.pushNamed(context, '/servers/create'),
            icon: const Icon(Icons.add, color: Colors.white),
            label: const Text('New Server', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          ),
          body: McAsyncLayout(
            isLoading: sp.isLoading && sp.servers.isEmpty,
            isEmpty: sp.servers.isEmpty,
            emptyMessage: 'No servers found.\nCreate your first Minecraft server!',
            onRetry: sp.loadServers,
            child: ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
              itemCount: sp.servers.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (_, i) => ServerCard(server: sp.servers[i])
                  .animate()
                  .fadeIn(delay: (i * 50).ms)
                  .slideY(begin: 0.1, end: 0),
            ),
          ),
        );
      },
    );
  }
}
