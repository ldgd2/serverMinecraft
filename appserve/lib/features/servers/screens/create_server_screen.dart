import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:appserve/core/providers/app_providers.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/shared/widgets/mc_button.dart';
import 'package:appserve/shared/layouts/mc_screen_layout.dart';
import '../widgets/create_server_forms.dart';

class CreateServerScreen extends StatefulWidget {
  const CreateServerScreen({super.key});

  @override
  State<CreateServerScreen> createState() => _CreateServerScreenState();
}

class _CreateServerScreenState extends State<CreateServerScreen> {
  int _currentStep = 0;
  final _formKeys = List.generate(4, (_) => GlobalKey<FormState>());

  final _nameCtrl = TextEditingController();

  String _selectedLoader = 'PAPER';
  String? _selectedVersion;

  final _portCtrl = TextEditingController(text: '25565');
  final _motdCtrl = TextEditingController(text: 'A new Minecraft Server');
  bool _onlineMode = false;

  final _ramCtrl = TextEditingController(text: '2048');
  final _cpuCoresCtrl = TextEditingController(text: '1.0');
  final _maxPlayersCtrl = TextEditingController(text: '20');
  final _diskCtrl = TextEditingController(text: '10000');

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<VersionProvider>().loadInstalledVersions();
      context.read<ServerProvider>().loadSystemStats();
    });
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _portCtrl.dispose();
    _motdCtrl.dispose();
    _ramCtrl.dispose();
    _cpuCoresCtrl.dispose();
    _maxPlayersCtrl.dispose();
    _diskCtrl.dispose();
    super.dispose();
  }

  void _nextStep(int totalSteps) {
    if (_currentStep < totalSteps - 1) {
      if (_currentStep < 4 && !_formKeys[_currentStep].currentState!.validate()) {
        return;
      }
      if (_currentStep == 1 && _selectedVersion == null) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Please select a version')));
        return;
      }
      setState(() => _currentStep++);
    } else {
      _submit();
    }
  }

  void _prevStep() {
    if (_currentStep > 0) setState(() => _currentStep--);
  }

  void _submit() async {
    final data = {
      'name': _nameCtrl.text,
      'version': _selectedVersion,
      'mod_loader': _selectedLoader,
      'ram_mb': int.tryParse(_ramCtrl.text) ?? 2048,
      'cpu_cores': double.tryParse(_cpuCoresCtrl.text) ?? 1.0,
      'port': int.tryParse(_portCtrl.text) ?? 25565,
      'online_mode': _onlineMode,
      'motd': _motdCtrl.text,
      'max_players': int.tryParse(_maxPlayersCtrl.text) ?? 20,
      'disk_mb': int.tryParse(_diskCtrl.text) ?? 10000,
    };

    try {
      await context.read<ServerProvider>().createServer(data);
      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('Server created!')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return McScreenLayout(
      title: 'Create New Server',
      body: Consumer<VersionProvider>(
        builder: (_, vp, __) {
          final loaderVersions = vp.installedVersions
              .where((v) => v.loaderType.toUpperCase() == _selectedLoader)
              .map((v) => v.mcVersion)
              .toSet()
              .toList();

          if (loaderVersions.isNotEmpty &&
              !loaderVersions.contains(_selectedVersion)) {
            _selectedVersion = loaderVersions.first;
          } else if (loaderVersions.isEmpty) {
            _selectedVersion = null;
          }

          final steps = [
            _buildNameStep(),
            _buildSoftwareStep(loaderVersions),
            _buildConnectivityStep(),
            _buildResourcesStep(),
            _buildReviewStep(),
          ];

          return Theme(
            data: Theme.of(context).copyWith(
              colorScheme:
                  const ColorScheme.dark(primary: AppColors.grassGreenLight),
            ),
            child: Stepper(
              type: StepperType.vertical,
              physics: const ClampingScrollPhysics(),
              currentStep: _currentStep,
              onStepContinue: () => _nextStep(steps.length),
              onStepCancel: _prevStep,
              onStepTapped: (index) {
                // Allow jumping back, but require validation to go forward
                if (index < _currentStep) setState(() => _currentStep = index);
              },
              controlsBuilder: (context, details) {
                final isLast = _currentStep == steps.length - 1;
                return Padding(
                  padding: const EdgeInsets.only(top: 24),
                  child: Row(
                    children: [
                      Expanded(
                        child: McButton(
                          label: isLast ? 'Create Server' : 'Next',
                          icon: isLast ? Icons.add_circle : Icons.arrow_forward,
                          isLoading: isLast
                              ? context.watch<ServerProvider>().isLoading
                              : false,
                          onPressed: details.onStepContinue!,
                        ),
                      ),
                      if (_currentStep > 0) ...[
                        const SizedBox(width: 12),
                        McButton(
                          label: 'Back',
                          isSecondary: true,
                          onPressed: details.onStepCancel!,
                        ),
                      ],
                    ],
                  ),
                );
              },
              steps: steps,
            ),
          );
        },
      ),
    );
  }

  Step _buildNameStep() {
    return Step(
      state: _currentStep > 0 ? StepState.complete : StepState.indexed,
      isActive: _currentStep >= 0,
      title:
          const Text('Basics', style: TextStyle(fontWeight: FontWeight.bold)),
      content: Form(
        key: _formKeys[0],
        child: BasicsForm(nameCtrl: _nameCtrl),
      ),
    );
  }

  Step _buildSoftwareStep(List<String> loaderVersions) {
    return Step(
      state: _currentStep > 1 ? StepState.complete : StepState.indexed,
      isActive: _currentStep >= 1,
      title:
          const Text('Software', style: TextStyle(fontWeight: FontWeight.bold)),
      content: Form(
        key: _formKeys[1],
        child: SoftwareForm(
          selectedLoader: _selectedLoader,
          selectedVersion: _selectedVersion,
          loaderVersions: loaderVersions,
          onLoaderChanged: (loader) => setState(() {
            _selectedLoader = loader;
            _selectedVersion = null;
          }),
          onVersionChanged: (version) =>
              setState(() => _selectedVersion = version),
        ),
      ),
    );
  }

  Step _buildConnectivityStep() {
    return Step(
      state: _currentStep > 2 ? StepState.complete : StepState.indexed,
      isActive: _currentStep >= 2,
      title: const Text('Connectivity & Settings',
          style: TextStyle(fontWeight: FontWeight.bold)),
      content: Form(
        key: _formKeys[2],
        child: ConnectivityForm(
          portCtrl: _portCtrl,
          motdCtrl: _motdCtrl,
          onlineMode: _onlineMode,
          onOnlineModeChanged: (val) => setState(() => _onlineMode = val),
        ),
      ),
    );
  }

  Step _buildResourcesStep() {
    return Step(
      state: _currentStep > 3 ? StepState.complete : StepState.indexed,
      isActive: _currentStep >= 3,
      title: const Text('Resources',
          style: TextStyle(fontWeight: FontWeight.bold)),
      content: Consumer<ServerProvider>(
        builder: (context, sp, _) => Form(
          key: _formKeys[3],
          child: ResourcesForm(
            ramCtrl: _ramCtrl,
            cpuCoresCtrl: _cpuCoresCtrl,
            maxPlayersCtrl: _maxPlayersCtrl,
            diskCtrl: _diskCtrl,
            vpsRamMb: (sp.systemStats['memory_total'] as num?)?.toInt(),
            vpsCores: (sp.systemStats['cpu_count'] as num?)?.toDouble(),
          ),
        ),
      ),
    );
  }

  Step _buildReviewStep() {
    return Step(
      state: StepState.indexed,
      isActive: _currentStep >= 4,
      title:
          const Text('Review', style: TextStyle(fontWeight: FontWeight.bold)),
      content: ReviewSummary(
        name: _nameCtrl.text,
        loader: _selectedLoader,
        version: _selectedVersion,
        port: _portCtrl.text,
        onlineMode: _onlineMode,
        ram: _ramCtrl.text,
        cpuCores: _cpuCoresCtrl.text,
        maxPlayers: _maxPlayersCtrl.text,
        onEditStep: (step) => setState(() => _currentStep = step),
      ),
    );
  }
}
