import 'dart:io';
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../services/player_head_service.dart';

/// Widget que muestra la cabeza pixelada de un jugador Minecraft.
/// 
/// - Usa CachedNetworkImage para la entrega rápida desde red/caché HTTP
/// - Verifica el hash de la skin en background — si cambió, actualiza sola
/// - Cuando el jugador no tiene skin o hay error, muestra el avatar por defecto (Steve)
class PlayerHead extends StatefulWidget {
  final String username;
  final double size;
  final double borderRadius;
  final Color? borderColor;
  final double borderWidth;

  const PlayerHead({
    super.key,
    required this.username,
    this.size = 40,
    this.borderRadius = 6,
    this.borderColor,
    this.borderWidth = 0,
  });

  @override
  State<PlayerHead> createState() => _PlayerHeadState();
}

class _PlayerHeadState extends State<PlayerHead> {
  File? _localFile;
  bool _checked = false;

  @override
  void initState() {
    super.initState();
    _checkAndCache();
  }

  @override
  void didUpdateWidget(PlayerHead old) {
    super.didUpdateWidget(old);
    if (old.username != widget.username) {
      _checked = false;
      _checkAndCache();
    }
  }

  Future<void> _checkAndCache() async {
    if (_checked) return;
    _checked = true;
    final file = await PlayerHeadService.instance.getHead(
      widget.username,
      onUpdated: () {
        if (mounted) setState(() {});
      },
    );
    if (mounted && file != null) {
      setState(() => _localFile = file);
    }
  }

  @override
  Widget build(BuildContext context) {
    Widget image;

    if (_localFile != null) {
      image = Image.file(
        _localFile!,
        fit: BoxFit.cover,
        filterQuality: FilterQuality.none, // pixel-art sharpness
        errorBuilder: (_, __, ___) => _fallback(),
      );
    } else {
      // While local file loads, show network image from cache
      final url = PlayerHeadService.instance.headUrl(widget.username);
      image = CachedNetworkImage(
        imageUrl: url,
        fit: BoxFit.cover,
        filterQuality: FilterQuality.none,
        memCacheWidth: (widget.size * 2).toInt(),
        memCacheHeight: (widget.size * 2).toInt(),
        placeholder: (_, __) => _loading(),
        errorWidget: (_, __, ___) => _fallback(),
      );
    }

    Widget container = Container(
      width: widget.size,
      height: widget.size,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(widget.borderRadius),
        border: widget.borderColor != null && widget.borderWidth > 0
            ? Border.all(color: widget.borderColor!, width: widget.borderWidth)
            : null,
      ),
      child: image,
    );

    return container;
  }

  Widget _loading() {
    return Container(
      color: const Color(0xFF21262D),
      child: const Center(
        child: SizedBox(
          width: 12,
          height: 12,
          child: CircularProgressIndicator(strokeWidth: 1.5, color: Color(0xFF5D8A3C)),
        ),
      ),
    );
  }

  Widget _fallback() {
    // Default Steve pixel-art look
    return Container(
      color: const Color(0xFF3C3F43),
      child: Icon(Icons.person, size: widget.size * 0.6, color: const Color(0xFF8B949E)),
    );
  }
}
