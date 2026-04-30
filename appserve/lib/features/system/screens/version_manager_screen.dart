import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import 'package:appserve/core/models/version_model.dart';
import 'package:appserve/core/providers/app_providers.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/shared/widgets/mc_card.dart';
import 'package:appserve/shared/widgets/mc_button.dart';
import 'package:appserve/shared/widgets/mc_widgets.dart';

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
      context.read<VersionProvider>().loadVersions();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundDeep,
      appBar: AppBar(
        title: const Text('Version Manager'),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppColors.grassGreen,
          tabs: const [
            Tab(text: 'Minecraft Versions'),
            Tab(text: 'Mod Loaders'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          const _MinecraftVersionsTab(),
          const _ModLoadersTab(),
        ],
      ),
    );
  }
}

class _MinecraftVersionsTab extends StatelessWidget {
  const _MinecraftVersionsTab();

  @override
  Widget build(BuildContext context) {
    return Consumer<VersionProvider>(
      builder: (_, vp, __) {
        if (vp.isLoading) return const Center(child: CircularProgressIndicator());
        if (vp.error != null) return Center(child: Text(vp.error!));

        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: vp.versions.length,
          itemBuilder: (context, index) {
            final version = vp.versions[index];
            final isDownloaded = vp.downloadedVersions.any((v) => v.id == version.id);

            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: McCard(
                child: Row(
                  children: [
                    const Icon(Icons.history_edu, color: AppColors.textSecondary),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(version.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                          Text(version.typeLabel, style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                        ],
                      ),
                    ),
                    if (isDownloaded)
                      const Icon(Icons.check_circle, color: AppColors.online)
                    else
                      IconButton(
                        icon: const Icon(Icons.download, color: AppColors.grassGreenLight),
                        onPressed: () => _confirmDownload(context, version),
                      ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  void _confirmDownload(BuildContext context, VersionModel version) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.backgroundCard,
        title: Text('Download ${version.name}?'),
        content: const Text('This will download the server files to the VPS.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          TextButton(
            onPressed: () {
              context.read<VersionProvider>().downloadVersion(version.id);
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Starting download of ${version.name}...')),
              );
            },
            child: const Text('Download'),
          ),
        ],
      ),
    );
  }
}

class _ModLoadersTab extends StatefulWidget {
  const _ModLoadersTab();

  @override
  State<_ModLoadersTab> createState() => _ModLoadersTabState();
}

class _ModLoadersTabState extends State<_ModLoadersTab> {
  String _selectedType = 'paper';
  String _selectedMcVersion = '1.21';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<VersionProvider>().loadModLoaders(_selectedType, mcVersion: _selectedMcVersion);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<String>(
                  value: _selectedType,
                  dropdownColor: AppColors.backgroundCard,
                  items: ['paper', 'fabric', 'forge', 'quilt'].map((t) => DropdownMenuItem(value: t, child: Text(t.toUpperCase()))).toList(),
                  onChanged: (v) {
                    setState(() => _selectedType = v!);
                    context.read<VersionProvider>().loadModLoaders(_selectedType, mcVersion: _selectedMcVersion);
                  },
                  decoration: const InputDecoration(labelText: 'Type'),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: DropdownButtonFormField<String>(
                  value: _selectedMcVersion,
                  dropdownColor: AppColors.backgroundCard,
                  items: ['1.21', '1.20.4', '1.20.1', '1.19.4'].map((v) => DropdownMenuItem(value: v, child: Text(v))).toList(),
                  onChanged: (v) {
                    setState(() => _selectedMcVersion = v!);
                    context.read<VersionProvider>().loadModLoaders(_selectedType, mcVersion: _selectedMcVersion);
                  },
                  decoration: const InputDecoration(labelText: 'MC Version'),
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: Consumer<VersionProvider>(
            builder: (_, vp, __) {
              if (vp.isLoading) return const Center(child: CircularProgressIndicator());
              if (vp.error != null) return Center(child: Text(vp.error!));

              return ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: vp.modLoaders.length,
                itemBuilder: (context, index) {
                  final loader = vp.modLoaders[index];
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: McCard(
                      child: Row(
                        children: [
                          const Icon(Icons.settings_input_component, color: AppColors.gold),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(loader.version, style: const TextStyle(fontWeight: FontWeight.bold)),
                                Text(loader.type.toUpperCase(), style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                              ],
                            ),
                          ),
                          McButton(
                            label: 'Install',
                            onPressed: () => _confirmInstall(context, loader),
                            isSecondary: true,
                          ),
                        ],
                      ),
                    ),
                  );
                },
              );
            },
          ),
        ),
      ],
    );
  }

  void _confirmInstall(BuildContext context, ModLoaderModel loader) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.backgroundCard,
        title: const Text('Install Mod Loader?'),
        content: Text('This will install ${loader.type.toUpperCase()} ${loader.version} for Minecraft ${_selectedMcVersion}.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          TextButton(
            onPressed: () {
              context.read<VersionProvider>().installModLoader(
                type: loader.type,
                loaderVersion: loader.version,
                minecraftVersion: _selectedMcVersion,
              );
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Starting installation...')),
              );
            },
            child: const Text('Install'),
          ),
        ],
      ),
    );
  }
}
