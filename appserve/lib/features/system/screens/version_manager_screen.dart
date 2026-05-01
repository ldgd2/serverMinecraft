import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:appserve/core/providers/app_providers.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/shared/widgets/mc_card.dart';
import 'package:appserve/shared/widgets/mc_button.dart';
import 'package:appserve/shared/layouts/mc_screen_layout.dart';

class VersionManagerScreen extends StatefulWidget {
  const VersionManagerScreen({super.key});

  @override
  State<VersionManagerScreen> createState() => _VersionManagerScreenState();
}

class _VersionManagerScreenState extends State<VersionManagerScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<VersionProvider>().loadInstalledVersions();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return McScreenLayout(
      title: 'Version Manager',
      bottom: TabBar(
        controller: _tabController,
        indicatorColor: AppColors.grassGreen,
        tabs: const [
          Tab(text: 'Installed'),
          Tab(text: 'Download'),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          _InstalledVersionsTab(),
          _DownloadVersionsTab(),
        ],
      ),
    );
  }
}

class _InstalledVersionsTab extends StatelessWidget {
  const _InstalledVersionsTab();

  @override
  Widget build(BuildContext context) {
    return Consumer<VersionProvider>(
      builder: (_, vp, __) {
        return McAsyncLayout(
          isLoading: vp.isLoading,
          error: vp.error,
          isEmpty: vp.installedVersions.isEmpty,
          emptyMessage: 'No versions installed.',
          onRetry: () => context.read<VersionProvider>().loadInstalledVersions(),
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: vp.installedVersions.length,
            itemBuilder: (context, index) {
              final version = vp.installedVersions[index];
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: McCard(
                  child: Row(
                    children: [
                      const Icon(Icons.dns, color: AppColors.textSecondary),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(version.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                            Text('${version.typeLabel} • ${(version.fileSize / 1024 / 1024).toStringAsFixed(1)} MB', style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                          ],
                        ),
                      ),
                      const Icon(Icons.check_circle, color: AppColors.online)
                    ],
                  ),
                ),
              );
            },
          ),
        );
      },
    );
  }
}

class _DownloadVersionsTab extends StatefulWidget {
  const _DownloadVersionsTab();

  @override
  State<_DownloadVersionsTab> createState() => _DownloadVersionsTabState();
}

class _DownloadVersionsTabState extends State<_DownloadVersionsTab> {
  String _selectedLoader = 'PAPER';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<VersionProvider>().loadRemoteVersions(_selectedLoader);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: DropdownButtonFormField<String>(
            initialValue: _selectedLoader,
            dropdownColor: AppColors.backgroundCard,
            items: ['VANILLA', 'PAPER', 'FABRIC', 'FORGE'].map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
            onChanged: (v) {
              setState(() => _selectedLoader = v!);
              context.read<VersionProvider>().loadRemoteVersions(_selectedLoader);
            },
            decoration: const InputDecoration(labelText: 'Loader Type'),
          ),
        ),
        Expanded(
          child: Consumer<VersionProvider>(
            builder: (_, vp, __) {
              return McAsyncLayout(
                isLoading: vp.isLoading,
                error: vp.error,
                isEmpty: vp.remoteVersions.isEmpty,
                emptyMessage: 'No versions available for this loader.',
                onRetry: () => context.read<VersionProvider>().loadRemoteVersions(_selectedLoader),
                child: ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: vp.remoteVersions.length,
                  itemBuilder: (context, index) {
                    final mcVersion = vp.remoteVersions[index];
                    final isInstalled = vp.installedVersions.any((v) => v.loaderType.toUpperCase() == _selectedLoader && v.mcVersion == mcVersion);

                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: McCard(
                        child: Row(
                          children: [
                            const Icon(Icons.cloud_download_outlined, color: AppColors.diamond),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('$_selectedLoader $mcVersion', style: const TextStyle(fontWeight: FontWeight.bold)),
                                  const Text('Available for download', style: TextStyle(color: AppColors.textMuted, fontSize: 12)),
                                ],
                              ),
                            ),
                            if (isInstalled)
                              const Icon(Icons.check_circle, color: AppColors.online)
                            else
                              McButton(
                                label: 'Download',
                                onPressed: () => _confirmDownload(context, mcVersion),
                                isSecondary: true,
                              ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  void _confirmDownload(BuildContext context, String mcVersion) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.backgroundCard,
        title: const Text('Download Version?'),
        content: Text('This will download $_selectedLoader $mcVersion to the server.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          TextButton(
            onPressed: () {
              context.read<VersionProvider>().downloadVersion(
                loaderType: _selectedLoader,
                mcVersion: mcVersion,
              );
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Download started in background...')),
              );
            },
            child: const Text('Download'),
          ),
        ],
      ),
    );
  }
}
