import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/providers/backup_provider.dart';
import 'package:intl/intl.dart';

class BackupsScreen extends StatefulWidget {
  const BackupsScreen({super.key});

  @override
  State<BackupsScreen> createState() => _BackupsScreenState();
}

class _BackupsScreenState extends State<BackupsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<BackupProvider>().fetchBackups();
    });
  }

  String _formatSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(2)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(2)} MB';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Backups de Sistema'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<BackupProvider>().fetchBackups(),
          ),
        ],
      ),
      body: Consumer<BackupProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading && provider.backups.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          if (provider.backups.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.backup_outlined, size: 80, color: Colors.grey[400]),
                  const SizedBox(height: 16),
                  const Text('No hay backups disponibles', style: TextStyle(fontSize: 18, color: Colors.grey)),
                ],
              ),
            );
          }

          return ListView.builder(
            itemCount: provider.backups.length,
            padding: const EdgeInsets.all(8),
            itemBuilder: (context, index) {
              final backup = provider.backups[index];
              final date = DateTime.parse(backup['created_at']);
              final formattedDate = DateFormat('dd/MM/yyyy HH:mm').format(date);

              return Card(
                elevation: 2,
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  leading: const CircleAvatar(
                    backgroundColor: Colors.blueAccent,
                    child: Icon(Icons.archive, color: Colors.white),
                  ),
                  title: Text(backup['filename'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                  subtitle: Text('$formattedDate • ${_formatSize(backup['size'])}'),
                  trailing: PopupMenuButton<String>(
                    onSelected: (value) async {
                      if (value == 'download') {
                        final path = await provider.downloadBackup(backup['filename']);
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text('Guardado en: $path')),
                        );
                      } else if (value == 'restore') {
                        _showRestoreDialog(context, backup['filename'], provider);
                      } else if (value == 'delete') {
                        provider.deleteBackup(backup['filename']);
                      }
                    },
                    itemBuilder: (context) => [
                      const PopupMenuItem(value: 'download', child: ListTile(leading: Icon(Icons.download), title: Text('Descargar'))),
                      const PopupMenuItem(value: 'restore', child: ListTile(leading: Icon(Icons.settings_backup_restore, color: Colors.orange), title: Text('Restaurar'))),
                      const PopupMenuItem(value: 'delete', child: ListTile(leading: Icon(Icons.delete, color: Colors.red), title: Text('Eliminar'))),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showCreateDialog(context),
        label: const Text('Nuevo Backup'),
        icon: const Icon(Icons.add),
      ),
    );
  }

  void _showCreateDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Crear Backup Total'),
        content: const Text('Se guardará la base de datos, mundos y modloaders. Esto puede tardar unos segundos.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              context.read<BackupProvider>().createBackup();
            },
            child: const Text('Crear'),
          ),
        ],
      ),
    );
  }

  void _showRestoreDialog(BuildContext context, String filename, BackupProvider provider) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('¿Restaurar Sistema?'),
        content: Text('ADVERTENCIA: Se sobrescribirán todos los archivos actuales con los de este backup ($filename).'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () {
              Navigator.pop(context);
              provider.restoreBackup(filename);
            },
            child: const Text('Restaurar Ahora', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}
