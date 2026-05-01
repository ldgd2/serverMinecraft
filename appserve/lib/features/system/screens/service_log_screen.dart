import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:appserve/core/providers/app_providers.dart';
import 'package:appserve/core/theme/app_colors.dart';

class ServiceLogScreen extends StatefulWidget {
  const ServiceLogScreen({super.key});

  @override
  State<ServiceLogScreen> createState() => _ServiceLogScreenState();
}

class _ServiceLogScreenState extends State<ServiceLogScreen> {
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ServerProvider>().connectToSystemLogs();
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundDeep,
      appBar: AppBar(
        backgroundColor: AppColors.backgroundCard,
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Service Logs', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            Text('Live VPS Dashboard Output', style: TextStyle(fontSize: 10, color: AppColors.textMuted)),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_sweep_outlined),
            onPressed: () => context.read<ServerProvider>().clearConsole(),
          ),
        ],
      ),
      body: Consumer<ServerProvider>(
        builder: (context, sp, child) {
          // Auto-scroll to bottom
          if (_scrollController.hasClients) {
            _scrollController.animateTo(
              _scrollController.position.maxScrollExtent,
              duration: const Duration(milliseconds: 200),
              curve: Curves.easeOut,
            );
          }

          return Container(
            width: double.infinity,
            height: double.infinity,
            margin: const EdgeInsets.all(12),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.black,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppColors.border),
            ),
            child: SingleChildScrollView(
              controller: _scrollController,
              child: SelectableText(
                sp.systemLogs.isEmpty ? 'Waiting for logs...' : sp.systemLogs,
                style: const TextStyle(
                  color: Color(0xFFD4D4D4),
                  fontFamily: 'monospace',
                  fontSize: 12,
                  height: 1.4,
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
