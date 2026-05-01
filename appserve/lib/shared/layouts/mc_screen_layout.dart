import 'package:flutter/material.dart';
import 'package:appserve/core/theme/app_colors.dart';
import 'package:appserve/shared/widgets/mc_states.dart';

/// A standard Minecraft-styled screen layout.
/// Replaces the boilerplate of Scaffold, AppBar, and background color.
class McScreenLayout extends StatelessWidget {
  final String title;
  final Widget body;
  final List<Widget>? actions;
  final Widget? floatingActionButton;
  final PreferredSizeWidget? bottom;
  final Color backgroundColor;

  const McScreenLayout({
    super.key,
    required this.title,
    required this.body,
    this.actions,
    this.floatingActionButton,
    this.bottom,
    this.backgroundColor = AppColors.backgroundDeep,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: backgroundColor,
      appBar: AppBar(
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        actions: actions,
        bottom: bottom,
        elevation: 0,
        backgroundColor: Colors.transparent,
      ),
      body: body,
      floatingActionButton: floatingActionButton,
    );
  }
}

/// A layout optimized for loading data.
/// Automatically handles loading spinners and error states.
class McAsyncLayout<T> extends StatelessWidget {
  final bool isLoading;
  final String? error;
  final bool isEmpty;
  final String emptyMessage;
  final Widget child;
  final VoidCallback? onRetry;

  const McAsyncLayout({
    super.key,
    required this.isLoading,
    this.error,
    required this.isEmpty,
    this.emptyMessage = 'No data available',
    required this.child,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    if (isLoading && isEmpty) {
      return const McLoadingState();
    }
    
    if (error != null && isEmpty) {
      return McErrorState(error: error!, onRetry: onRetry);
    }

    if (isEmpty) {
      return McEmptyState(message: emptyMessage);
    }

    return child;
  }
}

/// A layout for detail screens that feature a large, expanding sliver app bar with a gradient background.
/// Useful for Entity Detail screens (like ServerDetail, UserDetail, etc.)
class McSliverScreenLayout extends StatelessWidget {
  final Widget headerContent;
  final Widget body;
  final List<Color>? backgroundGradientColors;
  final double expandedHeight;
  final Widget? tabBar;

  const McSliverScreenLayout({
    super.key,
    required this.headerContent,
    required this.body,
    this.backgroundGradientColors,
    this.expandedHeight = 200,
    this.tabBar,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundDeep,
      body: NestedScrollView(
        headerSliverBuilder: (context, _) => [
          SliverAppBar(
            expandedHeight: expandedHeight,
            pinned: true,
            backgroundColor: AppColors.backgroundCard,
            leading: IconButton(
              icon: const Icon(Icons.arrow_back_ios, color: AppColors.textPrimary, size: 20),
              onPressed: () => Navigator.pop(context),
            ),
            flexibleSpace: FlexibleSpaceBar(
              background: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: backgroundGradientColors ?? [AppColors.backgroundElevated, AppColors.backgroundCard],
                  ),
                ),
                child: SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(20, 56, 20, 20),
                    child: headerContent,
                  ),
                ),
              ),
            ),
          ),
        ],
        body: Column(
          children: [
            if (tabBar != null) tabBar!,
            Expanded(child: body),
          ],
        ),
      ),
    );
  }
}

