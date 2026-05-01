import 'package:flutter/material.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/shared/widgets/mc_text_field.dart';

class BasicsForm extends StatelessWidget {
  final TextEditingController nameCtrl;

  const BasicsForm({super.key, required this.nameCtrl});

  @override
  Widget build(BuildContext context) {
    return McTextField(
      controller: nameCtrl,
      label: 'Server Name',
      prefixIcon: Icons.dns,
      hint: 'e.g., Survival SMP',
      validator: (v) {
        if (v == null || v.isEmpty) return 'Required';
        if (v.contains(' ')) return 'No spaces allowed';
        return null;
      },
    );
  }
}

class SoftwareForm extends StatelessWidget {
  final String selectedLoader;
  final String? selectedVersion;
  final List<String> loaderVersions;
  final ValueChanged<String> onLoaderChanged;
  final ValueChanged<String?> onVersionChanged;

  const SoftwareForm({
    super.key,
    required this.selectedLoader,
    required this.selectedVersion,
    required this.loaderVersions,
    required this.onLoaderChanged,
    required this.onVersionChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        DropdownButtonFormField<String>(
          initialValue: selectedLoader,
          dropdownColor: AppColors.backgroundCard,
          items: ['VANILLA', 'PAPER', 'FABRIC', 'FORGE']
              .map((t) => DropdownMenuItem(value: t, child: Text(t)))
              .toList(),
          onChanged: (v) {
            if (v != null) onLoaderChanged(v);
          },
          decoration: const InputDecoration(
              labelText: 'Mod Loader',
              prefixIcon: Icon(Icons.settings_input_component)),
        ),
        const SizedBox(height: 16),
        DropdownButtonFormField<String?>(
          initialValue: selectedVersion,
          dropdownColor: AppColors.backgroundCard,
          items: loaderVersions
              .map((v) => DropdownMenuItem(value: v, child: Text(v)))
              .toList(),
          onChanged: onVersionChanged,
          decoration: const InputDecoration(
              labelText: 'Minecraft Version',
              prefixIcon: Icon(Icons.history_edu)),
          hint: Text(loaderVersions.isEmpty
              ? 'No versions installed for this loader'
              : 'Select Version'),
          validator: (v) => v == null ? 'Please select a version' : null,
        ),
        if (loaderVersions.isEmpty)
          const Padding(
            padding: EdgeInsets.only(top: 8, left: 4),
            child: Row(
              children: [
                Icon(Icons.warning_amber_rounded,
                    color: Colors.orange, size: 16),
                SizedBox(width: 6),
                Expanded(
                    child: Text('Download versions in Version Manager first.',
                        style: TextStyle(color: Colors.orange, fontSize: 12))),
              ],
            ),
          ),
      ],
    );
  }
}

class ConnectivityForm extends StatelessWidget {
  final TextEditingController portCtrl;
  final TextEditingController motdCtrl;
  final bool onlineMode;
  final ValueChanged<bool> onOnlineModeChanged;

  const ConnectivityForm({
    super.key,
    required this.portCtrl,
    required this.motdCtrl,
    required this.onlineMode,
    required this.onOnlineModeChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        McTextField(
          controller: portCtrl,
          label: 'Port',
          prefixIcon: Icons.wifi,
          keyboardType: TextInputType.number,
          validator: (v) {
            if (v == null || v.isEmpty) return 'Required';
            final port = int.tryParse(v);
            if (port == null || port < 1024 || port > 65535) {
              return 'Invalid port (1024-65535)';
            }
            return null;
          },
        ),
        const SizedBox(height: 16),
        McTextField(
          controller: motdCtrl,
          label: 'MOTD (Message of the Day)',
          prefixIcon: Icons.message,
        ),
        const SizedBox(height: 16),
        SwitchListTile(
          title: const Text('Premium Mode (Online Mode)'),
          subtitle: Text(onlineMode
              ? 'Only players with paid accounts can join.'
              : 'Cracked accounts can join. Authenticate via plugins.'),
          value: onlineMode,
          activeThumbColor: AppColors.grassGreenLight,
          contentPadding: EdgeInsets.zero,
          onChanged: onOnlineModeChanged,
        ),
      ],
    );
  }
}

class ResourcesForm extends StatelessWidget {
  final TextEditingController ramCtrl;
  final TextEditingController maxPlayersCtrl;
  final TextEditingController diskCtrl;

  const ResourcesForm({
    super.key,
    required this.ramCtrl,
    required this.maxPlayersCtrl,
    required this.diskCtrl,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: McTextField(
                controller: ramCtrl,
                label: 'RAM (MB)',
                prefixIcon: Icons.memory,
                keyboardType: TextInputType.number,
                validator: (v) {
                  if (v == null || v.isEmpty) return 'Required';
                  final ram = int.tryParse(v);
                  if (ram == null || ram < 512) return 'Min 512MB';
                  return null;
                },
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: McTextField(
                controller: maxPlayersCtrl,
                label: 'Max Players',
                prefixIcon: Icons.people,
                keyboardType: TextInputType.number,
                validator: (v) {
                  if (v == null || v.isEmpty) return 'Required';
                  if (int.tryParse(v) == null) return 'Must be a number';
                  return null;
                },
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        McTextField(
          controller: diskCtrl,
          label: 'Disk Limit (MB)',
          prefixIcon: Icons.storage,
          keyboardType: TextInputType.number,
          hint: '10000',
          validator: (v) {
            if (v == null || v.isEmpty) return 'Required';
            if (int.tryParse(v) == null) return 'Must be a number';
            return null;
          },
        ),
      ],
    );
  }
}

class ReviewSummary extends StatelessWidget {
  final String name;
  final String loader;
  final String? version;
  final String port;
  final bool onlineMode;
  final String ram;
  final String maxPlayers;
  final ValueChanged<int> onEditStep;

  const ReviewSummary({
    super.key,
    required this.name,
    required this.loader,
    required this.version,
    required this.port,
    required this.onlineMode,
    required this.ram,
    required this.maxPlayers,
    required this.onEditStep,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.backgroundCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _ReviewRow('Name', name, onEdit: () => onEditStep(0)),
          const Divider(color: AppColors.border, height: 24),
          _ReviewRow('Software', '$loader ${version ?? ""}',
              onEdit: () => onEditStep(1)),
          const Divider(color: AppColors.border, height: 24),
          _ReviewRow('Port', port, onEdit: () => onEditStep(2)),
          const SizedBox(height: 12),
          _ReviewRow('Mode', onlineMode ? 'Premium' : 'Cracked',
              onEdit: () => onEditStep(2)),
          const Divider(color: AppColors.border, height: 24),
          _ReviewRow('Resources', '${ram}MB RAM • $maxPlayers Slots',
              onEdit: () => onEditStep(3)),
        ],
      ),
    );
  }
}

class _ReviewRow extends StatelessWidget {
  final String label;
  final String value;
  final VoidCallback onEdit;

  const _ReviewRow(this.label, this.value, {required this.onEdit});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label,
                style:
                    const TextStyle(color: AppColors.textMuted, fontSize: 12)),
            const SizedBox(height: 4),
            Text(value,
                style: const TextStyle(
                    color: AppColors.textPrimary, fontWeight: FontWeight.bold)),
          ],
        ),
        IconButton(
          icon: const Icon(Icons.edit,
              size: 18, color: AppColors.grassGreenLight),
          onPressed: onEdit,
          visualDensity: VisualDensity.compact,
        ),
      ],
    );
  }
}
