package com.lider.minebridge.core;

import com.lider.minebridge.MineBridge;
import com.lider.minebridge.networking.NetworkManager;
import net.minecraft.server.MinecraftServer;

import java.util.concurrent.TimeUnit;

/**
 * MineCore — El núcleo de procesamiento asíncrono de MineBridge.
 * Permite aislar tareas pesadas del Tick Loop principal para evitar lag.
 */
public class MineCore {

    private static final MinecraftServer server = MineBridge.getServer();

    /**
     * SISTEMA DE RED (NETWORK): Gestiona el envío de datos sin esperar respuesta.
     */
    public static class Network {
        /**
         * Envía un payload a un jugador de forma inmediata y asíncrona.
         * El juego NO espera a que el paquete sea entregado.
         */
        public static void send(net.minecraft.server.network.ServerPlayerEntity player, net.minecraft.network.packet.CustomPayload payload) {
            // Fabric's send is thread-safe and non-blocking (queues the packet)
            net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.send(player, payload);
        }

        /**
         * Envía una petición HTTP al Backend de forma aislada.
         */
        public static void request(Runnable requestTask) {
            async(requestTask);
        }
    }

    /**
     * SISTEMA DE DATOS (DATA): Ideal para "pedir prestado" datos al backend sin lag.
     */
    public static class Data {
        /**
         * Pide datos al BACKEND/RED y vuelve al hilo principal.
         */
        public static <T> void borrow(java.util.concurrent.CompletableFuture<T> request, java.util.function.Consumer<T> callback) {
            request.thenAccept(result -> {
                sync(() -> callback.accept(result));
            }).exceptionally(ex -> {
                MineBridge.LOGGER.error("[MineCore] Error en petición de datos: " + ex.getMessage());
                return null;
            });
        }

        /**
         * CAPTURA datos del JUEGO y los procesa en SEGUNDO PLANO.
         */
        public static <T> void snapshot(java.util.function.Supplier<T> capture, java.util.function.Consumer<T> processor) {
            sync(() -> {
                T data = capture.get();
                async(() -> processor.accept(data));
            });
        }
    }

    /**
     * SISTEMA DE PROCESAMIENTO (PROCESSOR): Gestiona cálculos y datos.
     */
    public static class Processor {
        /**
         * Procesa datos en segundo plano.
         */
        public static void run(Runnable task) {
            async(task);
        }

        /**
         * Procesa y luego regresa al hilo principal.
         */
        public static void runAndSync(Runnable backgroundTask, Runnable syncTask) {
            async(() -> {
                backgroundTask.run();
                sync(syncTask);
            });
        }
    }

    /**
     * AISLAMIENTO TOTAL: Ejecuta una tarea en un hilo dedicado fuera del Main Tick.
     */
    public static void async(Runnable task) {
        NetworkManager.getExecutor().execute(task);
    }

    /**
     * TAREA REPETITIVA ASINCRONA.
     */
    public static void repeating(Runnable task, long initialDelay, long period, TimeUnit unit) {
        NetworkManager.getScheduler().scheduleAtFixedRate(task, initialDelay, period, unit);
    }

    /**
     * RETORNO SEGURO al hilo principal.
     */
    public static void sync(Runnable task) {
        MinecraftServer s = MineBridge.getServer();
        if (s != null) {
            s.execute(task);
        }
    }

    /**
     * Ejecución con retraso asíncrono.
     */
    public static void delayed(Runnable task, long delay, TimeUnit unit) {
        NetworkManager.getScheduler().schedule(task, delay, unit);
    }
}
