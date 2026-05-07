package com.lider.minebridge.networking;

import java.net.http.HttpClient;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Centraliza la infraestructura de red del mod para asegurar aislamiento total del hilo principal.
 * Utiliza un pool de hilos dedicado para aprovechar los núcleos extra del procesador.
 */
public class NetworkManager {
    private static final HttpClient httpClient;
    private static final ExecutorService networkExecutor;
    private static final ScheduledExecutorService scheduler;

    static {
        // Determinamos el número de hilos óptimo (al menos 2, máximo 4 para no saturar si hay pocos núcleos)
        int cores = Runtime.getRuntime().availableProcessors();
        int threads = Math.max(2, Math.min(cores, 4));

        ThreadFactory factory = new ThreadFactory() {
            private final AtomicInteger count = new AtomicInteger(1);
            @Override
            public Thread newThread(Runnable r) {
                Thread t = new Thread(r, "MineBridge-Network-" + count.getAndIncrement());
                t.setDaemon(true);
                t.setPriority(Thread.NORM_PRIORITY - 1);
                return t;
            }
        };

        networkExecutor = Executors.newFixedThreadPool(threads, factory);
        scheduler = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "MineBridge-Scheduler");
            t.setDaemon(true);
            return t;
        });

        httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .executor(networkExecutor)
                .build();
    }

    public static HttpClient getHttpClient() {
        return httpClient;
    }

    public static ExecutorService getExecutor() {
        return networkExecutor;
    }

    public static ScheduledExecutorService getScheduler() {
        return scheduler;
    }

    public static void shutdown() {
        networkExecutor.shutdown();
        scheduler.shutdown();
    }
}
