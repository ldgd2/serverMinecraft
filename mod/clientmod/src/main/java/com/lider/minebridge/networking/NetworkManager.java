package com.lider.minebridge.networking;

import java.net.http.HttpClient;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Infraestructura de red para el cliente.
 */
public class NetworkManager {
    private static final HttpClient httpClient;
    private static final ExecutorService networkExecutor;

    static {
        ThreadFactory factory = new ThreadFactory() {
            private final AtomicInteger count = new AtomicInteger(1);
            @Override
            public Thread newThread(Runnable r) {
                Thread t = new Thread(r, "MineBridge-Client-Network-" + count.getAndIncrement());
                t.setDaemon(true);
                return t;
            }
        };

        networkExecutor = Executors.newFixedThreadPool(2, factory);
        httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .executor(networkExecutor)
                .build();
    }

    public static HttpClient getHttpClient() { return httpClient; }
    public static ExecutorService getExecutor() { return networkExecutor; }
}
