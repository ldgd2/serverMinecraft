package com.lider.minebridge.core;

import com.lider.minebridge.networking.NetworkManager;
import net.minecraft.client.MinecraftClient;

import java.util.concurrent.TimeUnit;

/**
 * MineCore — El núcleo de procesamiento asíncrono para el Cliente.
 * Asegura que la interfaz y el renderizado no se congelen por tareas de red.
 */
public class MineCore {

    /**
     * SISTEMA DE RED (NETWORK): Envío asíncrono al servidor.
     */
    public static class Network {
        /**
         * Envía un payload al servidor sin bloquear el renderizado.
         */
        public static void send(net.minecraft.network.packet.CustomPayload payload) {
            net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking.send(payload);
        }
    }

    /**
     * SISTEMA DE DATOS (DATA): Pide datos al servidor o backend sin lag.
     */
    public static class Data {
        /**
         * Pide datos al servidor/backend.
         */
        public static <T> void borrow(java.util.concurrent.CompletableFuture<T> request, java.util.function.Consumer<T> callback) {
            request.thenAccept(result -> {
                sync(() -> callback.accept(result));
            }).exceptionally(ex -> {
                return null;
            });
        }

        /**
         * CAPTURA datos del juego (ej. lista de entidades) y los procesa en SEGUNDO PLANO.
         */
        public static <T> void snapshot(java.util.function.Supplier<T> capture, java.util.function.Consumer<T> processor) {
            sync(() -> {
                T data = capture.get();
                async(() -> processor.accept(data));
            });
        }
    }

    /**
     * SISTEMA DE PROCESAMIENTO (PROCESSOR).
     */
    public static class Processor {
        public static void run(Runnable task) {
            async(task);
        }
        
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
     * Ejecuta una tarea asíncrona con retraso.
     */
    public static void delayed(Runnable task, long delay, TimeUnit unit) {
        async(() -> {
            try {
                unit.sleep(delay);
                task.run();
            } catch (InterruptedException ignored) {}
        });
    }

    /**
     * RETORNO SEGURO al hilo de renderizado.
     */
    public static void sync(Runnable task) {
        MinecraftClient client = MinecraftClient.getInstance();
        if (client != null) {
            client.execute(task);
        }
    }
}
